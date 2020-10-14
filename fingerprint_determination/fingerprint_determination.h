//
// Created by henrik on 04.05.17.
//

#ifndef MAGICFERN_FINGERPRINT_DETERMINATION_H
#define MAGICFERN_FINGERPRINT_DETERMINATION_H

#include <opencv2/core/mat.hpp>

cv::Mat getFingerprint(std::vector<cv::Mat> &, int);

#endif //MAGICFERN_FINGERPRINT_DETERMINATION_H
