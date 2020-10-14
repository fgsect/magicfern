//
// Created by henrik on 13.06.17.
//

#include <opencv2/core.hpp>
#include <iostream>
#include <opencv2/imgproc.hpp>
#include <cv.hpp>
#include "crosscorrelation.h"
#include "fastFourierTransformation.h"

cv::Mat getCrossCorrelation(cv::Mat mat1, cv::Mat mat2)
{

    cv::Mat dftMat1, dftMat2;
    //#pragma omp parallel
    {
        mat1 = mat1 - cv::mean(mat1);
        mat2 = mat2 - cv::mean(mat2);
    }

        cv::Mat tilted_mat2;

        // rotates the matrix 180 degrees
        cv::flip(mat2, tilted_mat2, -1);

    //#pragma omp parallel
    {
        dftMat1 = fft2(mat1);
        dftMat2 = fft2(tilted_mat2);
    }

    cv::Mat dftRes;
    // multiplicates the spectrums of two fft without conjugating (false)
    cv::mulSpectrums(dftMat1, dftMat2, dftRes, 0, false);

    mat1 = ifft2(dftRes);


    return mat1;
}