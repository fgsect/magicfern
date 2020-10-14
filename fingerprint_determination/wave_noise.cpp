//
// Created by henrik on 23.05.17.
//

#include <opencv2/imgproc.hpp>

#include "wave_noise.h"
#include "threshold_function.h"

cv::Mat waveNoiseExtract(cv::Mat subimage, double noiseVar)
{
    cv::Size size = subimage.size();
    cv::Mat tc = cv::Mat(size, CV_64FC1, cv::Scalar(0.0));
    cv::pow(subimage, 2, tc);

    cv::Mat kernel(3, 3, CV_64FC1, cv::Scalar(1/9.0));

    //filter2(ones(3,3)/(3*3), tc)
    cv::Mat coeffVar;
    cv::filter2D(tc, coeffVar, -1, kernel, cv::Point(-1, -1), 0, cv::BORDER_CONSTANT);
    coeffVar = var_Thresholding(coeffVar, noiseVar);

    cv::Mat estVar;
    for(double i = 5; i < 10; i = i + 2)
    {
        cv::Mat kernel(i, i, CV_64FC1, 1.0/(i*i));
        cv::filter2D(tc, estVar, -1, kernel, cv::Point(-1, -1), 0, cv::BORDER_CONSTANT);
        estVar = var_Thresholding(estVar, noiseVar);
        coeffVar = cv::min(coeffVar, estVar);
    }

    tc = subimage * noiseVar / (coeffVar + noiseVar);

    return tc;
}
