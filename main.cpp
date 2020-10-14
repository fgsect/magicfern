
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// The implementation of digital camera fingerprint extraction is based on an existing matlab code from Miroslav Goljan et. al. //
// "http://dde.binghamton.edu/download/camera_fingerprint/" - 28th of June 2017                                                 //
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#include <iostream>
#include <typeinfo>

//opencv
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/core/ocl.hpp>

#include "fingerprint_determination/fingerprint_determination.h"
#include "further_processing/wienerFiltering.h"
#include "fingerprint_determination/image_noise_extraction.h"
#include "further_processing/crosscorrelation.h"
#include "further_processing/pce.h"
#include "print_result.h"
#include "further_processing/zero_mean_total.h"
#include "parse_arguments.h"
#include "image_load.h"
#include "candidate_processing.h"

using namespace cv;
using namespace std;

inline bool ends_with(std::string const & value, std::string const & ending)
{
      if (ending.size() > value.size()) return false;
      return std::equal(ending.rbegin(), ending.rend(), value.rbegin());
}

int main(int argc, char *argv[])
{
    if (!cv::ocl::haveOpenCL())
        cout << "OpenCL is not avaiable..." << endl;
    else cout << "OpenCL is AVAILABLE! :) " << endl;

    std::vector<std::string> references;
    std::vector<std::string> candidates;
    double crop = 0;
    bool validFormat = false;
    std::string referencePath;

    parseArguments(argc, argv, references, candidates, crop, validFormat, referencePath);

    int sigmaFP = 3;
    int sigmaCA = 2;
    cv::Mat fingerprint;

    if (references.size() == 1 && ends_with(references.at(0), ".yml")) {
        // load a saved fingerprint
        FileStorage file(references.at(0), FileStorage::READ);
        file["referenceFingerprint"] >> fingerprint;
    } else {
        // calculate the reference fingerprint
        std::vector<cv::Mat> refImages;

        // load reference images
        loadImages(references, refImages, crop);

        // determine fingerprint
        cv::Mat referencePattern = getFingerprint(refImages, sigmaFP);

        // removes compression artifacts
        referencePattern = getZeroMeanTotal(referencePattern);

        cv::Mat referencePatternGrey(referencePattern.size(), CV_32FC1);

        referencePattern.convertTo(referencePattern, CV_32FC3);
        cv::cvtColor( referencePattern, referencePatternGrey, cv::COLOR_BGR2GRAY  );

        cv::Mat mean = cv::Mat::zeros(1, 1, CV_64FC1);
        cv::Mat stdDev = cv::Mat::zeros(1, 1, CV_64FC1);
        cv::meanStdDev(referencePatternGrey, mean, stdDev);

        // use wiener filter in frequency domain to remove non-unique sensor artefacts
        fingerprint = wienerFilteringInDFT(referencePatternGrey, stdDev.at<double>(0));

        if (!referencePath.empty()) {
            cout << "Saving image to " << referencePath << "." << std::endl;
            cv::FileStorage file(referencePath, cv::FileStorage::WRITE);
            file << "referenceFingerprint" << fingerprint;
        }
    }

    std::vector<cv::Mat> candidateImages;

    // load candidate images
    loadImages(candidates, candidateImages, crop);

    // compare fingerprint with candidates
    compareWithCandidates(fingerprint, candidateImages, sigmaCA, validFormat);

    return 0;
}
