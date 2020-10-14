//
// Created by henrik on 21.06.17.
//

#include <opencv2/core.hpp>
#include <iostream>
#include "pce.h"
#include "../fingerprint_determination/shift.hpp"

std::vector<double> getPCE(cv::Mat &corrMat)
{
    int squaresize = 11;

    /*
    out.PCE             peak-to-correlation energy (PCE)
    out.PeakLocation    location of the primary peak, [0 0] when correlated signals are not shifted to each other
    out.pvalue          probability of obtaining peakheight or higher (under Gaussian assumption)
    out.P_FA            probability of false alarm (increases with increasing range of admissible shifts (shift_range)
    */

    std::vector<double> out;        // PCE <0>, pvalue <1>, PeakLocation - y: <2>, x: <3>, P_FA <4>

    //cv::Vec2d shift_range = (0.0, 0.0);
    double xpeak = 0; double ypeak = 0;

    if(cv::countNonZero(corrMat) < 1)
    {
        out.push_back(0.0);        // PCE
        out.push_back(1.0);        // pvalue
        out.push_back(0.0);        // y PeakLocation
        out.push_back(0.0);        // x PeakLocation
        out.push_back(0.0);        // P_FA
        out.push_back(0.0);        // log10P_FA
        return out;
    }


    double correl = corrMat.at<float>(corrMat.rows-1, corrMat.cols-1);
    double peakheight = correl;

    cv::Mat corrMat_without_peak = removeNeighbourhood(corrMat, cv::Point(ypeak, xpeak), squaresize);

    cv::Scalar pce_energyScalar = cv::mean(corrMat_without_peak.mul(corrMat_without_peak));

    double pce_energy = pce_energyScalar(0);

    double pce;

    if(peakheight < 0)
    {
        pce = peakheight*peakheight/pce_energy*-1;
    }else{
        pce = peakheight*peakheight/pce_energy;
    }
    out.push_back(pce);

    double pvalue = 1/2.0 * std::erfc(peakheight/(cv::sqrt(pce_energy)*cv::sqrt(2.0)));

    //pushes back the pvalue - out[1] = pvalue
    out.push_back(pvalue);
    //pushes back the peak position (0, 0) - out[2] = y-position, out[3] = x-position
    out.push_back(ypeak);
    out.push_back(xpeak);

    double p_FA, log10P_FA;

    // shift_range is 0 -> 0 + 1 = 1
    fa_from_PCE(pce, 1, p_FA, log10P_FA);

    // pushes back the false alarm probability p_FA
    out.push_back(p_FA);
    // pushes back the log10 of the P_FA
    out.push_back(log10P_FA);

    return out;
}

// Removes a 2-D neighborhood around peak from matrix X and output a 1-D vector Y
// ssize     square neighborhood has size (ssize x ssize) square
cv::Mat removeNeighbourhood(cv::Mat &matX, cv::Point peak, int squaresize)
{
    int radius = (squaresize-1) / 2;
    cv::Mat matXShifted;

    // shifts peak to the beginning of the matrix
    shift(matX, matXShifted, cv::Point(radius - peak.y +1, radius - peak.x +1), IPL_BORDER_WRAP);

    // extracts the first eleven columns and 11 till end of the rows
    cv::Mat matY = cv::Mat(matXShifted, cv::Rect(0, squaresize, squaresize, matX.rows-squaresize));

    cv::Mat yClone = matY.clone();
    yClone = yClone.reshape(0, 1);
    yClone = yClone.t();

    // extracts 11-end cols and all rows - first eleven cols missing
    cv::Mat matY2 = cv::Mat(matXShifted, cv::Rect(squaresize, 0, matXShifted.cols-squaresize, matXShifted.rows));
    cv::Mat y2Clone = matY2.clone();
    y2Clone = y2Clone.reshape(0, 1);
    y2Clone = y2Clone.t();

    cv::Mat returnMat;
    cv::vconcat(yClone, y2Clone, returnMat);        // concat the two clones -> the first 11x11 pixels are missing - the 121 around the peak

    return returnMat;
}

// Calculates false alarm probability from having peak-to-cross-correlation (PCE) measure of the peak
// seach_space   number of correlation samples from which the maximum is taken
void fa_from_PCE(double pce, double search_space, double &p_FA, double &log10P_FA)
{
    double x = cv::sqrt(cv::abs(pce));
    double q, logQ;

    if(x < 0)
        x = x * (-1);

    if(x < 37.5) {
        q = 1/2.0 * std::erfc(x/(cv::sqrt(2)));
        logQ = std::log(q);
    } else {
        q = 1.0 / (cv::sqrt(2 * CV_PI) * x) * cv::exp(-(x*x)/2);
        logQ = -(x * x) / 2.0 - cv::log(x) - 1/2.0 * cv::log(2 * CV_PI);
    }

    if(pce < 50.0) {
        double tmp = 1;

        for(int i = 0; i < search_space; i++)
        {
            tmp = tmp * (1 - q);
        }
        // p_FA = 1 - (1 - q)^search_space
        p_FA = 1 - tmp;

    } else {
        p_FA = search_space * q;
    }

    if(p_FA == 0.0) {
        p_FA = search_space * q;
        log10P_FA = cv::log(search_space)/cv::log(10) + logQ * cv::log(2);
    } else {
        log10P_FA = cv::log(p_FA)/cv::log(10);
    }
}
