//
// Created by henrik on 01.09.17.
//

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <iostream>
#include "image_load.h"

// gets a vector with strings and a cv::Mat vector. The function loads the images from the strings into
// the cv::Mat vector and crops them, if crop > 0.
void loadImages(std::vector<std::string> &imgStrings, std::vector <cv::Mat> &imagesVec, double &crop)
{
    cv::Mat subimage;
    double max_cols = crop;
    double max_rows = crop;

    // can not be parallelized because otherwise the order of the candidates gets distorted
    for(unsigned int i = 0; i < imgStrings.size(); i++)
    {
        if(crop > 0)
        {
            subimage = cv::imread(imgStrings[i].c_str(), cv::IMREAD_COLOR);

            if(subimage.cols > max_cols && subimage.rows > max_rows){
                subimage = cv::Mat(subimage, cv::Rect(subimage.cols/2-(max_cols/2), subimage.rows/2-(max_rows/2), max_cols, max_rows));
            }
            else if(subimage.cols > max_cols){
                subimage = cv::Mat(subimage, cv::Rect(subimage.cols/2-(max_cols/2), 0, max_cols, subimage.rows));
            }
            else if(subimage.rows > max_rows){
                subimage = cv::Mat(subimage, cv::Rect(0, subimage.rows/2-(max_rows/2), subimage.cols, max_rows));
            }

            imagesVec.push_back(subimage);
        }
        else
        {
            imagesVec.push_back(cv::imread(imgStrings[i].c_str(), cv::IMREAD_COLOR));
        }
    }
}
