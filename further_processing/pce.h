//
// Created by henrik on 21.06.17.
//

#ifndef MAGICFERN_PCE_H
#define MAGICFERN_PCE_H


#include <opencv2/core/mat.hpp>

std::vector<double> getPCE(cv::Mat &);

cv::Mat removeNeighbourhood(cv::Mat &, cv::Point, int);

void fa_from_PCE(double pce, double search_space, double &, double &);


#endif //MAGICFERN_PCE_H
