//
// Created by henrik on 15.05.17.
// returns filtermask for wavelet transformation
//
#include <string>
#include <vector>
#include <cmath>
#include <iostream>

using namespace std;

std::vector<double> makeONFilter(string type, int par)
{

    std::vector<double> tmp;
    if(!type.compare("Haar"))
    {
        double filter[2] = {1/sqrt(2), 1/sqrt(2)};
        for(int i = 0; i < 2; i++)
        {
            tmp.push_back(filter[i]);
        }
        return tmp;
    }
    else if(!type.compare("Daubechies"))
    {
        if(par == 8)
        {
            double filter[8] = {0.230377813309, 0.714846570553, 0.630880767930, -0.027983769417, -0.187034811719, 0.030841381836, 0.032883011667, -0.010597401785};
            for(int i = 0; i < 8; i++)
            {
                tmp.push_back(filter[i]);
            }
            return tmp;
        }
        else
        {
            perror("This version of the quadratur mirror filter has not been added until now");
        }
    }
    else
    {
        perror("This version of the quadratur mirror filter does not exist or has not been added until now");
    }


    return tmp;
}