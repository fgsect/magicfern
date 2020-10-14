//
// Created by henrik on 04.05.17.
//

//standard
#include <iostream>
#include <omp.h>
#include <pthread.h>
#include <opencv2/core/ocl.hpp>
#include <math.h>

//opencv
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>

//intern
#include "filter_mask.h"
#include "fingerprint_determination.h"
#include "noise_extraction.h"
#include "intensity_scale.h"
#include "saturation.h"
#include "../further_processing/zero_mean_total.h"

using namespace cv;

struct thread_data{
    int  thread_id;
    cv::Mat image;
    std::vector<Mat> imNoise;
    std::vector<Mat> inten;
    double* qmf;
    int sigma, dLvl;
};
struct thread_data_finished{
    std::vector<Mat> imNoise;
    std::vector<Mat> inten;
};

void *threaded_work(void *thread_arg)
{
    time_t t = clock();
    struct thread_data *my_data;

    my_data = (struct thread_data * ) thread_arg;

    my_data->image.convertTo(my_data->image, CV_64FC3);       //converts images to floating point with 8 bytes


    for(int i = 0; i < 3; i++)
    {
        my_data->imNoise.push_back(cv::Mat::zeros(my_data->image.size(), CV_64FC1));       //Reference Pattern with size of the first image
        my_data->inten.push_back(cv::Mat::zeros(my_data->image.size(), CV_64FC1));       // http://ninghang.blogspot.de/2012/11/list-of-mat-type-in-opencv.html
    }


    std::vector<Mat>channels(3);
    cv::Mat saturMask;
    cv::split(my_data->image, channels);     //splits RGB image into three single channel images and stores them in 3dim vector
    //my_data->image.release();

    //#pragma omp parallel for
    for(int dim = 0; dim < 3; dim++)
    {
        my_data->imNoise[dim] = noiseExtract(channels[dim], my_data->qmf, my_data->sigma, my_data->dLvl);

        my_data->inten[dim] = intenScale(channels[dim]);                         //intenScale scales the intensity - look at the method for detailed information

        saturMask = getSaturationMask(channels[dim]);              //getSaturationMask returns a binary mask with ones when there is a peak value and the neighbours have the same value

        my_data->inten[dim] = my_data->inten[dim].mul(saturMask);
    }

    pthread_exit(NULL);
}

cv::Mat getFingerprint(std::vector<cv::Mat> &images, int sigma)
{

    time_t t = clock();

    //parameters for decomposition - denoising filter
    int dLvl = 4; // number of decomposition levels

    std::vector<double> qmfVec;
    qmfVec = makeONFilter("Daubechies", 8); //qmf - quadratur mirror filter, sets filter mask for dwt
    double* qmf = &qmfVec[0];

    int sizeX = 0;      //dimensions of the first image
    int sizeY = 0;
    Size sizeRef;
    Size sizeTemp;

    cv::Mat imNoise, inten, saturMask;std::vector<Mat>channels(3);
    std::vector<Mat>sumRP(3), sumNN(3);

     ///*

    unsigned int counter = 0;
    //#pragma omp parallel for
    for(unsigned int i = 0; i < images.size(); i++)
    {

        if(images[i].channels() == 3)       //only RGB-images allowed
        {
            if(sizeX == 0 || sizeY == 0)        //if refSize isnt initiallized
            {
                sizeRef = images[i].size();
                sizeX = sizeRef.width;
                sizeY = sizeRef.height;

                for(int i = 0; i < 3; i++)
                {
                    sumRP[i] = cv::Mat::zeros(sizeRef, CV_64FC1);       //Reference Pattern with size of the first image
                    sumNN[i] = cv::Mat::zeros(sizeRef, CV_64FC1);       // http://ninghang.blogspot.de/2012/11/list-of-mat-type-in-opencv.html
                }
            }

            sizeTemp = images[i].size();

            if(sizeTemp != sizeRef)         //images have to have the same dimensions
            {

                images.erase(images.begin() + i);
                i--;
            }
        }
        counter++;
    }


    if(images.size() == 0)
    {
        std::cerr << "No matching images to determine the fingerprint\n";
        exit(-1);
    }
    else if(counter != images.size()) // counter original images size - if difference -> some picutres have been erased
    {
        std::cerr << "Some images did not fullfill all requirements and couldnt be considered for fingerprint determination\n";
    }

    t = clock() - t;
    std::cout << "creating matrices and checking size: " << t << std::endl;
    t = clock();

    // multithreading
    int rc;
    int i;
    int NUM_THREADS;// = images.size();
    std::vector<thread_data_finished> thread_vec;
    double max_threads = 8.0;
    double rounds = 1.0;
    if(images.size() > max_threads){
        //std::cout << "rounds: " << rounds << std::endl;
        NUM_THREADS = max_threads;
        rounds = ceil(images.size()/max_threads);
        std::cout << rounds << std::endl;
    }else{
        NUM_THREADS = images.size();
    }

    pthread_t threads[NUM_THREADS];
    struct thread_data td[NUM_THREADS];
    pthread_attr_t attr;
    void *status;

    std::vector<Mat> tmpImNoise;
    std::vector<Mat> tmpInten;



    for(int round = 0; round < rounds; round++) {

        // Initialize and set thread joinable
        pthread_attr_init(&attr);
        //pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);

        for (int i = 0; i < NUM_THREADS; i++) {

            if(i + round*max_threads >= images.size()) break;

            /*
            for(int i = 0; i < 3; i++)
            {
                tmpImNoise.push_back(cv::Mat::zeros(images[0].size(), CV_64FC1));       //Reference Pattern with size of the first image
                tmpInten.push_back(cv::Mat::zeros(images[0].size(), CV_64FC1));       // http://ninghang.blogspot.de/2012/11/list-of-mat-type-in-opencv.html
            }
            */

            std::cout << "main() : creating thread, " << i << std::endl;
            td[i].image = images[i+round*max_threads];

            //td[i].imNoise = tmpImNoise;
            //td[i].inten = tmpInten;

            td[i].dLvl = dLvl;
            td[i].qmf = qmf;
            td[i].sigma = sigma;
            td[i].thread_id = i;
            rc = pthread_create(&threads[i], &attr, threaded_work, (void *) &td[i]);

            if (rc) {
                std::cout << "Error: unable to create thread: " << strerror(rc) << std::endl;
                exit(-1);
            }
        }

        // free attribute and wait for the other threads
        pthread_attr_destroy(&attr);

        for (i = 0; i < NUM_THREADS; i++) {

            if(i + round*max_threads >= images.size()) break;

            rc = pthread_join(threads[i], &status);

            if (rc) {
                std::cout << "Error:unable to join," << rc << std::endl;
                exit(-1);
            }
            // smaller struct to safe RAM
            thread_data_finished tdf;
            tdf.inten = td[i].inten;
            tdf.imNoise = td[i].imNoise;

            thread_vec.push_back(tdf);
            //std::cout << "Main: completed thread id :" << i;
            std::cout << "  exiting with status :" << status << std::endl;
        }
    }


    t = clock() - t;
    std::cout << "threads(saturation, noise extraction, intensity scale): " << t << std::endl;
    t = clock();

    //#pragma omp parallel for
    for(unsigned int i = 0; i < images.size(); i++ ) {

        for (int dim = 0; dim < 3; dim++) {
            sumRP[dim] = sumRP[dim] + thread_vec[i].imNoise[dim].mul(thread_vec[i].inten[dim]);
            cv::pow(thread_vec[i].inten[dim], 2.0, thread_vec[i].inten[dim]);
            sumNN[dim] = sumNN[dim] + thread_vec[i].inten[dim];
        }

    }

    //*/
     /*

    int counter  = 0;
    for(int i = 0; i < images.size(); i++)
    {
        images[i].convertTo(images[i], CV_64FC3);       //converts images to floating point with 8 bytes

        if(images[i].channels() == 3)       //only RGB-images allowed
        {
            if(sizeX == 0 || sizeY == 0)        //if refSize isnt initiallized
            {
                sizeRef = images[i].size();
                sizeX = sizeRef.width;
                sizeY = sizeRef.height;

                for(int i = 0; i < 3; i++)
                {
                    sumRP[i] = cv::Mat::zeros(sizeRef, CV_64FC1);       //Reference Pattern with size of the first image
                    sumNN[i] = cv::Mat::zeros(sizeRef, CV_64FC1);       // http://ninghang.blogspot.de/2012/11/list-of-mat-type-in-opencv.html
                }
            }

            sizeTemp = images[i].size();

            if(sizeTemp == sizeRef)         //images have to have the same dimensions
            {
                cv::split(images[i], channels);     //splits RGB image into three single channel images and stores them in 3dim vector
                //#pragma omp parallel for
                for(int dim = 0; dim < 3; dim++)
                {
                    imNoise = noiseExtract(channels[dim], qmf, sigma, dLvl);
                    inten = intenScale(channels[dim]);                         //intenScale scales the intensity - look at the method for detailed information

                    saturMask = getSaturationMask(channels[dim]);              //getSaturationMask returns a binary mask with ones when there is a peak value and the neighbours have the same value

                    inten = inten.mul(saturMask);
                    sumRP[dim] = sumRP[dim] + imNoise.mul(inten);
                    cv::pow(inten, 2.0, inten);
                    sumNN[dim] = sumNN[dim] + inten;
                }
            }
        }
        counter++;
    }
    // */
    /*
    int counter  = 0;
    for(int i = 0; i < images.size(); i++)
    {

        if(images[i].channels() == 3)       //only RGB-images allowed
        {
            if(sizeX == 0 || sizeY == 0)        //if refSize isnt initiallized
            {
                sizeRef = images[i].size();
                sizeX = sizeRef.width;
                sizeY = sizeRef.height;

                for(int i = 0; i < 3; i++)
                {
                    sumRP[i] = cv::Mat::zeros(sizeRef, CV_64FC1);       //Reference Pattern with size of the first image
                    sumNN[i] = cv::Mat::zeros(sizeRef, CV_64FC1);       // http://ninghang.blogspot.de/2012/11/list-of-mat-type-in-opencv.html
                }
            }

            sizeTemp = images[i].size();

            if(sizeTemp != sizeRef)         //images have to have the same dimensions
            {

                images.erase(images.begin() + i);
                i--;
            }
        }
        counter++;
    }

    std::vector<std::vector<cv::Mat>> imNoiseVec;
    std::vector<std::vector<cv::Mat>> intenVec;
    std::vector<cv::Mat>tmp;
    for(int i = 0; i < images.size(); i++){
        imNoiseVec.push_back(tmp);
        intenVec.push_back(tmp);
    }
    #pragma omp parallel for
    for(int i = 0; i < images.size(); i++)
    {
        images[i].convertTo(images[i], CV_64FC3);       //converts images to floating point with 8 bytes
        std::vector<cv::Mat> imNoise1;
        std::vector<cv::Mat>inten1;
        cv::Mat test1;
        cv::Mat test2;

                cv::split(images[i], channels);     //splits RGB image into three single channel images and stores them in 3dim vector
                //#pragma omp parallel for
                for(int dim = 0; dim < 3; dim++)
                {
                    imNoise1.push_back(noiseExtract(channels[dim], qmf, sigma, dLvl));
                    test1 = intenScale(channels[dim]);                         //intenScale scales the intensity - look at the method for detailed information

                    test2 = getSaturationMask(channels[dim]);              //getSaturationMask returns a binary mask with ones when there is a peak value and the neighbours have the same value

                    inten1.push_back(test1.mul(test2));

                    //sumRP[dim] = sumRP[dim] + imNoise.mul(inten);
                    //cv::pow(inten, 2.0, inten);
                    //sumNN[dim] = sumNN[dim] + inten;

                }
        imNoiseVec[i] = imNoise1;
        intenVec[i] = inten1;


        counter++;
    }

    for(int i=0; i < images.size(); i++ ) {

        for (int dim = 0; dim < 3; dim++) {
            sumRP[dim] = sumRP[dim] + imNoiseVec[i][dim].mul(intenVec[i][dim]);
            cv::pow(intenVec[i][dim], 2.0, intenVec[i][dim]);
            sumNN[dim] = sumNN[dim] + intenVec[i][dim];
        }
    }
    // */

    if(counter == 0)
    {
        std::cerr << "No matching images to determine the fingerprint!\n";
        exit(1);
    }
    else if(counter != images.size())
    {
        std::cout << "Some images did not fullfill all requirements and couldnt be considered for fingerprint determination\n";
    }
    // */

    for(int i = 0; i < 3; i++)
    {
        sumRP[i] = sumRP[i]/(sumNN[i]+1);
    }



    t = clock() - t;
    std::cout << "addition of the noise: " << t << std::endl;
    t = clock();

    // concats the three dimensions of the pattern and stores them in referencePattern
    cv::Mat referencePattern;
    cv::merge(sumRP, referencePattern);

    //ZEROMEAN - subtracts mean from all black and all white subsets of columns and rows in the checkerboard pattern
    //referencePattern = getZeroMeanTotal(referencePattern);


    t = clock() - t;
    //std::cout << "zeroMeanTotal: " << t << std::endl;
    t = clock();

    return referencePattern;

}
