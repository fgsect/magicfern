//
// Created by henrik on 04.09.17.
//

#include <iostream>
#include <vector>

void printResult(std::vector<double> &out, int i, bool unequal)
{
    std::cout << "--Candidate number " << i << "--" << std::endl;
    if(unequal) std::cout << "Format is unequal to fingerprint.\n";
    std::cout << "PeakLocation:\n\n        [" << out[2] << ", " << out[3] << "]\n\n";
    std::cout << "PCE:       " << out[0] << std::endl;
    std::cout << "pvalue:    " << out[1] << std::endl;
    std::cout << "P_FA:      " << out[4] << std::endl;
    std::cout << "log10P_FA: " << out[5] << "\n\n";
}