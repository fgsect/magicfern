//
// Created by henrik on 07.06.17.
// erases additive noise after fourier transformation in the frequency domain by dividing the used filter H* with (H²+constant)
// this is way better than just dividing the fft of the degradation function H (https://www.youtube.com/watch?v=l3LMVLbDCic)
// - erases noise of an obeserved noisy process
#include <iostream>

#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

#include "wienerFiltering.h"
#include "fastFourierTransformation.h"
#include "../fingerprint_determination/wave_noise.h"

using namespace cv;

cv::Mat wienerFilteringInDFT(cv::Mat &imNoise, double sigma)
{
    cv::Mat f;
    // fourier transform of the noiseimage
    f = fft2(imNoise);

    // planes[0] real part, planes[1] imaginary part of the fft
    cv::Mat planes[] = {cv::Mat_<float>(f), cv::Mat(f.size(), CV_32FC1, cv::Scalar(0.0f))};
    cv::split(f, planes);


    cv::Mat fmag = cv::Mat(planes[0].size(), planes[0].type(), cv::Scalar(1.0f));
    // magnitude of the real and imaginary part of the fft
    cv::magnitude(planes[0], planes[1], fmag );

    // scaling factor
    fmag = fmag/(cv::sqrt(fmag.rows*fmag.cols));


    double noiseVar = sigma * sigma;
    cv::Mat fmag1 = fmag.clone();

    fmag1 = waveNoiseExtract(fmag1, noiseVar);

    cv::Mat mask_img = fmag == 0.0f;
    fmag.setTo(1.0f, mask_img);
    fmag1.setTo(0.0f, mask_img);

    /*
    for(int j = 0; j < fmag.rows; j++)
    {
        for(int i = 0; i < fmag.cols; i++)
        {
            if(fmag.at<float>(j, i) == 0.0f)
            {
                fmag.at<float>(j, i) = 1.0f;
                fmag1.at<float>(j, i) = 0.0f;
            }
        }
    }
    */

    cv::Mat tmp;
    cv::divide(fmag1, fmag, tmp);

    cv::Mat noiseClean = planes[0].mul(tmp);
    planes[1] = planes[1].mul(tmp);

    cv::Mat planes1[] = {cv::Mat_<float>(noiseClean), cv::Mat_<float>(planes[1])};
    cv::merge(planes1, 2, noiseClean);

    // inverse fourier transform
    noiseClean = ifft2(noiseClean);


    return noiseClean;
}