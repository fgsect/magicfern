//
// Created by henrik on 04.09.17.
//

#ifndef MAGICFERN_CANDIDATE_PROCESSING_H
#define MAGICFERN_CANDIDATE_PROCESSING_H

#include <opencv2/core/mat.hpp>

void compareWithCandidates(cv::Mat &, std::vector<cv::Mat> &, int, bool);

#endif //MAGICFERN_CANDIDATE_PROCESSING_H
