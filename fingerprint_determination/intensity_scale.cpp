//
// Created by henrik on 30.05.17.
//

//values above 252 are smaller than 1 (254 -> 0.5134; 255 -> 0.22313)
//values below 252 are divided by 252

#include "intensity_scale.h"
#include <iostream>
#include <opencv2/core.hpp>
#include <cv.hpp>

cv::Mat intenScale(cv::Mat &image)
{

    cv::Mat outImage(image.size(), CV_64FC1);
    double t = 252.0;
    double v = 6.0;

    outImage = image - t;
    cv::pow(outImage, 2.0, outImage);
    outImage = -1 * outImage/v;


    cv::exp(outImage, outImage);
    ///*
    cv::Mat mask_img = image < t;
    cv::Mat tmp = image/t;
    tmp.copyTo(outImage, mask_img);
    //*/
    /*
    for(int y = 0; y < outImage.rows; y++)
    {
        for(int x = 0; x < outImage.cols; x++)
        {
            if(image.at<double>(y, x) < t)
            {
                outImage.at<double>(y, x) = image.at<double>(y, x)/t;
            }
        }
    }
    //*/

    return outImage;
}
