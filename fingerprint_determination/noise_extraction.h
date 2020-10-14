//
// Created by henrik on 16.05.17.
//

#ifndef MAGICFERN_NOISE_EXTRACTION_H
#define MAGICFERN_NOISE_EXTRACTION_H

#include <opencv2/core/mat.hpp>

cv::Mat noiseExtract(cv::Mat, double* &, int, int);

#endif //MAGICFERN_NOISE_EXTRACTION_H
