//
// Created by henrik on 14.06.17.
//

#include <opencv2/core.hpp>
#include <cv.hpp>
#include <iostream>

#include "zero_mean_total.h"

cv::Mat getZeroMeanTotal(cv::Mat &xImage)
{
    // this is for 3 dimensional images, here the inner for-loop is multiplicated with three because of three dimnensions and because opencv
    // does not handle 3dim access with its at() function
    time_t t = clock();

    if(xImage.type() == CV_64FC3 || xImage.type() == CV_32FC3)
    {
        cv::Mat yImage = cv::Mat(xImage.rows, xImage.cols, xImage.type(), cv::Scalar(1.0, 1.0, 1.0));
        cv::Mat subimage = cv::Mat(xImage.rows/2, xImage.cols/2, xImage.type(), cv::Scalar(1.0, 1.0, 1.0));

        int x = 0;
        int y = 0;
        for(int starty = 0; starty < 2; starty++)
        {
            for(int startx = 0; startx < 2; startx++)
            {
                y = starty;
                for (int i = 0; i < subimage.rows; i++) {
                    x = startx;
                    for (int j = 0; j < subimage.cols; j++) {

                        subimage.at<cv::Vec3d>(i, j) = xImage.at<cv::Vec3d>(y, x);
                        x = x + 2;

                    }
                    y = y + 2;
                }

                subimage = zeroMean(subimage);

                y = starty;
                for (int i = 0; i < subimage.rows; i++) {
                    x = startx;
                    for (int j = 0; j < subimage.cols; j++) {

                        yImage.at<cv::Vec3d>(y, x) = subimage.at<cv::Vec3d>(i, j);
                        x = x + 2;

                    }
                    y = y + 2;
                }
            }
        }
        t = clock() - t;
        //std::cout << "zeroMeanTotal: " << t << std::endl;;
        return yImage;
    }
    else        //this is for 1 dimensional images, get more information at the beginning of the if-condition
    {
        cv::Mat yImage = cv::Mat(xImage.rows, xImage.cols, xImage.type(), cv::Scalar(1.0f));
        cv::Mat subimage = cv::Mat(xImage.rows/2, xImage.cols/2, xImage.type(), cv::Scalar(1.0f));

        int x = 0;
        int y = 0;
        for(int starty = 0; starty < 2; starty++)
        {
            for(int startx = 0; startx < 2; startx++)
            {
                y = starty;
                for (int i = 0; i < subimage.rows; i++) {
                    x = startx;
                    for (int j = 0; j < subimage.cols; j++) {

                        subimage.at<cv::Vec<float,1>>(i, j) = xImage.at<cv::Vec<float,1>>(y, x);
                        x = x + 2;

                    }
                    y = y + 2;
                }

                subimage = zeroMean(subimage);

                y = starty;
                for (int i = 0; i < subimage.rows; i++) {
                    x = startx;
                    for (int j = 0; j < subimage.cols; j++) {

                        yImage.at<cv::Vec<float,1>>(y, x) = subimage.at<cv::Vec<float,1>>(i, j);
                        x = x + 2;

                    }
                    y = y + 2;
                }
            }
        }
        t = clock() - t;
        //std::cout << "zeroMeanTotal: " << t << std::endl;

        return yImage;
    }
}


cv::Mat zeroMean(cv::Mat &xImage)
{
    // this is for the three dimensional images, to iterate thru the images it has to be differenced between color and gray images
    if(xImage.type() == CV_64FC3 || xImage.type() == CV_32FC3)
    {
        cv::Mat tmp(xImage.size(), xImage.type(), cv::Scalar(0.0, 0.0, 0.0));
        tmp = xImage - cv::mean(xImage);

        cv::Mat row_mean, col_mean;
        cv::reduce(tmp, row_mean, 1, CV_REDUCE_AVG);
        cv::reduce(tmp, col_mean, 0, CV_REDUCE_AVG);

        cv::Mat colMat(xImage.size(), xImage.type(), cv::Scalar(0.0, 0.0, 0.0));
        cv::Mat rowMat(xImage.size(), xImage.type(), cv::Scalar(0.0, 0.0, 0.0));

        /*
        for (int i = 0; i < xImage.rows; i++) {
            for (int j = 0; j < xImage.cols; j++) {
                colMat.at<cv::Vec3d>(i, j) = col_mean.at<cv::Vec3d>(j);
                rowMat.at<cv::Vec3d>(i, j) = row_mean.at<cv::Vec3d>(i);
            }
        }
        */
        for(int i = 0; i < xImage.rows; i++){
            col_mean.copyTo(colMat.row(i));
        }
        for(int i = 0; i < xImage.cols; i++){
            row_mean.copyTo(rowMat.col(i));
        }
        cv::Mat yImage(xImage.size(), xImage.type());
        yImage = tmp - colMat;
        yImage = yImage - rowMat;

        return yImage;
    }

    // else-condition for gray images
    else
    {
        cv::Mat tmp(xImage.size(), CV_32FC1, cv::Scalar(0.0f));
        tmp = xImage - cv::mean(xImage);

        cv::Mat row_mean, col_mean;
        cv::reduce(tmp, row_mean, 1, CV_REDUCE_AVG);
        cv::reduce(tmp, col_mean, 0, CV_REDUCE_AVG);

        cv::Mat colMat(xImage.size(), CV_32FC1, cv::Scalar(0.0f));
        cv::Mat rowMat(xImage.size(), CV_32FC1, cv::Scalar(0.0f));

        /*
        for(int i = 0; i < xImage.rows; i++)
        {
            for(int j = 0; j < xImage.cols; j++)
            {
                colMat.at<cv::Vec<float,1>>(i, j) = col_mean.at<cv::Vec<float,1>>(j);
                rowMat.at<cv::Vec<float,1>>(i, j) = row_mean.at<cv::Vec<float,1>>(i);
            }
        }
        */
        for(int i = 0; i < xImage.rows; i++){
            col_mean.copyTo(colMat.row(i));
        }
        for(int i = 0; i < xImage.cols; i++){
            row_mean.copyTo(rowMat.col(i));
        }

        cv::Mat yImage(xImage.size(), xImage.type());
        yImage = tmp - colMat;
        yImage = yImage - rowMat;

        return yImage;
    }
}