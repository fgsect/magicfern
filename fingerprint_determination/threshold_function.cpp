//
// Created by henrik on 24.05.17.
//

#include <iostream>
#include "threshold_function.h"

// values negative after subtraction are set to zero, other values stay the same (after subtraction)
cv::Mat var_Thresholding(cv::Mat &estVar, double noiseVar)
{

    cv::Mat result = estVar - noiseVar;

    cv::Mat absRes = cv::abs(result);

    cv::Mat thresholdVar = absRes.clone();

    thresholdVar = (result + absRes) / 2.0;
    return thresholdVar;
}
