//
// Created by henrik on 04.09.17.
//

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include "candidate_processing.h"
#include "fingerprint_determination/image_noise_extraction.h"
#include "further_processing/wienerFiltering.h"
#include "further_processing/crosscorrelation.h"
#include "further_processing/pce.h"
#include "print_result.h"

// compares the fingerprint with candidates. Therefore candidates contains the candidate images,
// sigma the stdDev for Wiener-filtering. validFormat is a boolean which decides if candidates with
// different formats get compared with the fingerprint.
void compareWithCandidates(cv::Mat &fingerprint, std::vector<cv::Mat> &candidates, int sigma, bool validFormat)
{
    std::vector<double> results [candidates.size()];
    bool unequals [candidates.size()];

    // for-loop for every candidate
    #pragma omp parallel for
    for(unsigned int i = 0; i < candidates.size(); i++)
    {
        bool jodelPreprocessing = false;
        bool unequal = false;
        int min_rows = fingerprint.rows;
        int min_cols = fingerprint.cols;
        cv::Mat croppedFP, croppedC, noiseEx;

        if(candidates[i].cols < min_cols)
        {
            min_cols = candidates[i].cols;
        }

        if(candidates[i].rows < min_rows)
        {
            min_rows = candidates[i].rows;
        }

	    unequal = fingerprint.rows != candidates[i].rows || fingerprint.cols != candidates[i].cols;

        if(validFormat && unequal)
        {
            unequals[i] = unequal;
        }
        else
        {
            if(unequal)
            {
                // crops fingerprint
                if(fingerprint.cols > min_cols && fingerprint.rows > min_rows){
                    croppedFP = cv::Mat(fingerprint, cv::Rect(fingerprint.cols/2-(min_cols/2), fingerprint.rows/2-(min_rows/2), min_cols, min_rows));
                }
                else if(fingerprint.cols > min_cols){
                    croppedFP = cv::Mat(fingerprint, cv::Rect(fingerprint.cols/2-(min_cols/2), 0, min_cols, fingerprint.rows));
                }
                else if(fingerprint.rows > min_rows){
                    croppedFP = cv::Mat(fingerprint, cv::Rect(0, fingerprint.rows/2-(min_rows/2), fingerprint.cols, min_rows));
                }
                else {
                    croppedFP = fingerprint;
                }

                // crops candidate
                if(candidates[i].cols > min_cols && candidates[i].rows > min_rows){
                    croppedC = cv::Mat(candidates[i], cv::Rect(candidates[i].cols/2-(min_cols/2), candidates[i].rows/2-(min_rows/2), min_cols, min_rows));
                }
                else if(candidates[i].cols > min_cols){
                    croppedC = cv::Mat(candidates[i], cv::Rect(candidates[i].cols/2-(min_cols/2), 0, min_cols, candidates[i].rows));
                }
                else if(candidates[i].rows > min_rows){
                    croppedC = cv::Mat(candidates[i], cv::Rect(0, candidates[i].rows/2-(min_rows/2), candidates[i].cols, min_rows));
                }
                else {
                    croppedC = candidates[i];
                }
            }

            cv::Mat mean = cv::Mat::zeros(1, 1, CV_64FC1);
            cv::Mat stdDev = cv::Mat::zeros(1, 1, CV_64FC1);

            // test method for image cropping, related to the jodel cropping
            // this function is not adapted to the circumstances and does not work.
            // This just stores an old function.
            if(jodelPreprocessing){
                cv::Size tmp;
                tmp.height = 0; tmp.width = 0;
                double jodelConst = 1.322;

                // cuts off the image on the left and right side
                if(candidates[i].cols > 1470){
                    double subimg_start = candidates[i].cols/2.0 - candidates[i].cols/jodelConst/2.0;
                    double subimg_length = candidates[i].cols - 2.0*subimg_start;
                    std::cout << "col start: " << subimg_start << "col end: " << subimg_length << "  " << candidates[i].cols-subimg_start << std::endl;
                    candidates[i] = cv::Mat(candidates[i], cv::Rect( subimg_start, 0, subimg_length, candidates[i].rows));
                    std::cout << "test" << std::endl;
                }

                cv::resize(candidates[i], candidates[i], tmp, 640.0/candidates[i].cols, 640.0/candidates[i].cols);
                std::cout << "test" << std::endl;
            }

            // calculate the the noise pattern of the compared image
            if(unequal)
            {
                noiseEx = noiseExtractFromImage(croppedC, sigma);
            }
            else
            {
                noiseEx = noiseExtractFromImage(candidates[i], sigma);
            }

            // removes blockness
            cv::meanStdDev(noiseEx, mean, stdDev);
            noiseEx = wienerFilteringInDFT(noiseEx, stdDev.at<double>(0));

            cv::Mat crossC;
            if(unequal)
            {
                cv::Mat imageC32;
                croppedC.convertTo(imageC32, CV_32FC3);
                cv::Mat greyCandidate = cv::Mat::ones(croppedC.size(), CV_32FC1);
                cv::cvtColor( imageC32, greyCandidate, cv::COLOR_BGR2GRAY );
                crossC = getCrossCorrelation(noiseEx, greyCandidate.mul(croppedFP));
            }
            else
            {
                cv::Mat imageC32;
                candidates[i].convertTo(imageC32, CV_32FC3);
                cv::Mat greyCandidate = cv::Mat::ones(candidates[i].size(), CV_32FC1);
                cv::cvtColor( imageC32, greyCandidate, cv::COLOR_BGR2GRAY );
                crossC = getCrossCorrelation(noiseEx, greyCandidate.mul(fingerprint));
            }

            unequals[i] = unequal;
            results[i] = getPCE(crossC);
        }
    }

    for (unsigned int i = 0; i < candidates.size(); i++) {

        // prints only the determined PCE
        if(!(unequals[i] && validFormat))
        {
            printResult(results[i], i + 1, unequals[i]);
        }
    }
}
