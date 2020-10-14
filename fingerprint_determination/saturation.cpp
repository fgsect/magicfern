//
// Created by henrik on 30.05.17.
//
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>

#include <iostream>

#include "saturation.h"
#include "shift.hpp"

cv::Mat getSaturationMask(cv::Mat &x)
{

    double min, max;
    cv::minMaxLoc(x, &min, &max);
    if(max <= 250)      // returns binary mask with everywhere ones if there are no values bigger than 250
    {
        cv::Mat satMask = cv::Mat::ones(x.size(), CV_64FC1);
        return satMask;
    }

    cv::Mat xH, xV, xHback, xVback;
    cv::Mat saturMap = cv::Mat::zeros(x.size(), CV_64FC1);
    shift(x, xH, cv::Point(0, 1) ,IPL_BORDER_WRAP);
    shift(x, xV, cv::Point(1, 0) ,IPL_BORDER_WRAP);
    xH = x - xH;
    xV = x - xV;
    shift(xH, xHback, cv::Point(0, -1) ,IPL_BORDER_WRAP);
    shift(xV, xVback, cv::Point(-1, 0) ,IPL_BORDER_WRAP);

    ///*
    cv::Mat img_mask = (xH != 0.0 & xHback != 0.0 & xV != 0.0 & xVback != 0.0);
    saturMap.setTo(1.0, img_mask);

    cv::Mat img_mask2 = (x != max | saturMap != 0.0);
    saturMap.setTo(1.0, img_mask2);
    //*/

     /*
    for(int j = 0; j < saturMap.rows; j++)
    {
        for(int i = 0; i < saturMap.cols; i++)
        {
            if(xH.at<double>(j, i) != 0.0 && xHback.at<double>(j, i) != 0.0 && xV.at<double>(j, i) != 0.0 && xVback.at<double>(j, i) != 0.0)
            saturMap.at<double>(j, i) = 1.0;
        }
    }

    for(int j = 0; j < saturMap.rows; j++)
    {
        for(int i = 0; i < saturMap.cols; i++)
        {
            if(x.at<double>(j, i) == max && saturMap.at<double>(j,i) == 0.0)
                saturMap.at<double>(j, i) = 0.0;
            else
                saturMap.at<double>(j, i) = 1.0;
        }
    }
    // */


    return saturMap;
}
