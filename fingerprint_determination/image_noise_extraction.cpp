//
// Created by henrik on 13.06.17.
//

#include <opencv2/core/mat.hpp>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <cv.hpp>
#include <iostream>

#include "image_noise_extraction.h"
#include "filter_mask.h"
#include "noise_extraction.h"
#include "../further_processing/zero_mean_total.h"

cv::Mat noiseExtractFromImage(cv::Mat image, int sigma)
{

    time_t t = clock();time_t a = clock();

    //parameters for decomposition - denoising filter
    int dLvl = 4; // number of decomposition levels

    std::vector<double> qmfVec;
    qmfVec = makeONFilter("Daubechies", 8); //qmf - quadratur mirror filter, sets filter mask for dwt
    double* qmf = &qmfVec[0];

    image.convertTo(image, CV_64FC3);

    std::vector<cv::Mat>channels(3), imNoise(3);
    cv::split(image, channels);


    //#pragma omp parallel for
    for(int dim = 0; dim < 3; dim++)
    {
        t = clock();
        imNoise[dim] = noiseExtract(channels[dim], qmf, sigma, dLvl);
        t = clock() - t;
        //std::cout << "dim " << dim << " time: " << t << std::endl;
    }
    cv::Mat imNoiseBGR;
    cv::merge(imNoise, imNoiseBGR);

    cv::Mat imNoiseGray(imNoiseBGR.size(), CV_32FC1);
    imNoiseBGR.convertTo(imNoiseBGR, CV_32FC3);

    cv::cvtColor( imNoiseBGR, imNoiseGray, cv::COLOR_BGR2GRAY );

    a = clock() - a;
    std::cout << "noiseEx: " << a << std::endl;
    t = clock();
    //ZERO MEAN
    imNoiseGray = getZeroMeanTotal(imNoiseGray);
    t = clock() - t;
    std::cout << "zeroMean 2: " << t << std::endl;
    t = clock();

    return imNoiseGray;
}
