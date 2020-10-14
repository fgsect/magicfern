//
// Created by henrik on 07.06.17.
//

#include <cv.hpp>
#include <iostream>
#include "fastFourierTransformation.h"

using namespace cv;

// discrete fourier transform
cv::Mat fft2(cv::Mat &I)
{

    cv::Mat f = I.clone();
    dft(f, f, cv::DFT_COMPLEX_OUTPUT);

    return f;
}

// inverse discrete fourier transform
cv::Mat ifft2(cv::Mat &complexI)
{
    cv::Mat clone = complexI.clone();
    dft(clone, clone, cv::DFT_INVERSE|cv::DFT_REAL_OUTPUT|cv::DFT_SCALE);
    cv::Mat planes[] = {cv::Mat_<float>(clone), cv::Mat::zeros(clone.size(), CV_32F)};
    split(clone, planes);

    return planes[0];
}