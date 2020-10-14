//
// Created by henrik on 16.05.17.
//

#include <iostream>

#include <opencv2/core.hpp>
#include <cv.hpp>


#include "noise_extraction.h"
#include "mdwt_r.h"
#include "wave_noise.h"
#include "midwt_r.h"

using namespace cv;

cv::Mat noiseExtract(cv::Mat img, double* &qmf, int sigma, int dLvl) {

    time_t t = clock();

    double noiseVar = sigma * sigma * 1.0;
    double minpad = 2;                     // minimal amount of padded rows and cols
    cv::Size size = img.size();
    double bM = size.height;
    double bN = size.width;
    double m = 1;
    for (int i = 0; i < dLvl; i++) {
        m = m * 2;
    }


    // calculate the amount of rows and cols that have to be padded to get a symmetric matrix
    int nr, nc, pr, prd, pc, pcr;
    nr = ceil((bM + minpad) / m) * m;     // dimensions of the padded image (always pad 8 pixels or more)
    nc = ceil((bN + minpad) / m) * m;
    pr = ceil((nr - bM) / 2);             // number of padded rows on the top - 1
    prd = (nr - bM) / 2;                  // number of padded rows at the bottom - 1
    pc = ceil((nc - bN) / 2);             // number of padded columns on the left - 4
    pcr = (nc - bN) / 2;                  // number of padded columns on the right - 4

    // pads some rows and columns on the image to do a discrete wavelet transform
    cv::copyMakeBorder(img, img, pr, prd, pc, pcr, cv::BORDER_REFLECT);     // http://docs.opencv.org/trunk/d3/df2/tutorial_py_basic_ops.html

    double* arrayImgOut;// = (double*) img.data;  //&vectorImgOut[0];
    double* arrayImg = (double*) img.data;//&vectorImg[0];

    arrayImgOut = new double[img.total()];

    // does discrete wavelet transformation
    arrayImgOut = mDWT(arrayImg, img.cols, img.rows, qmf, sizeof(qmf), dLvl, arrayImgOut);

    t = clock() - t;
    std::cout << "mDWT: " << t << std::endl;
    t = clock();

    cv::Mat wave_trans(img.rows, img.cols, CV_64FC1);
    wave_trans.data = (uchar*) arrayImgOut;

    int hhigh, hlow, vhigh, vlow;

    for(int i = 0; i < dLvl; i++)
    {
        hhigh = (nc/2+1);
        hlow = (nc/2);
        vhigh = (nr/2+1);
        vlow = (nr/2);
        //#pragma omp parallel
        {
            // Horizontal noise extraction
            cv::Mat subimage1 = cv::Mat(wave_trans, cv::Rect(hhigh - 1, 0, nc - (hhigh - 1), vlow - 0));
            subimage1 = waveNoiseExtract(subimage1, noiseVar);
            subimage1.copyTo(wave_trans(cv::Rect(hhigh - 1, 0, nc - (hhigh - 1), vlow - 0)));

            // Vertical noise extraction
            cv::Mat subimage2(wave_trans, cv::Rect(0, vhigh - 1, hlow - 0, nr - (vhigh - 1)));
            subimage2 = waveNoiseExtract(subimage2, noiseVar);
            subimage2.copyTo(wave_trans(cv::Rect(0, vhigh - 1, hlow - 0, nr - (vhigh - 1))));

            // Diagonal noise extraction
            cv::Mat subimage3(wave_trans, cv::Rect(hhigh - 1, vhigh - 1, nc - (hhigh - 1), nr - (vhigh - 1)));
            subimage3 = waveNoiseExtract(subimage3, noiseVar);
            subimage3.copyTo(wave_trans(cv::Rect(hhigh - 1, vhigh - 1, nc - (hhigh - 1), nr - (vhigh - 1))));
        }
        nc = nc/2;
        nr = nr/2;
    }

    // Last, coarest level noise extraction
    cv::Mat subimage4 = cv::Mat(wave_trans, cv::Rect(0, 0, nc-0, nr-0));
    subimage4 = 0;

    t = clock() - t;
    std::cout << "wave Noise extract: " << t << std::endl;
    t = clock();


    double* arrayIDWTImg;// = arrayTmp;
    arrayIDWTImg = new double [wave_trans.total()];

    //double* arrayIDWTImg = (double*) wave_trans.data; //&vectorIDWTImg[0];
    double* arrayIDWT = (double*) wave_trans.data; //&vectorIDWT[0];


    // does inverse discrete wavelet transformation
    MIDWT(arrayIDWTImg, wave_trans.cols, wave_trans.rows, qmf, sizeof(qmf), dLvl, arrayIDWT);

    cv::Mat image_noise = cv::Mat(wave_trans.rows, wave_trans.cols, CV_64FC1, (uchar*)arrayIDWTImg, cv::Mat::AUTO_STEP);


    t = clock() - t;
    std::cout << "idwt: " << t << std::endl;
    t = clock();


    // erases the padded rows and columns
    cv::Mat image_noiseOrig(image_noise.clone(), cv::Rect(pc, pr, pc+bN-(pc), pr+bM-(pr)));

    delete[] arrayIDWTImg;
    delete[] arrayImgOut;

    return image_noiseOrig;
}
