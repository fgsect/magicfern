//
// Created by henrik on 01.09.17.
//

#include <iostream>
#include "parse_arguments.h"

void printUsage() {
    std::cout << 
R"(
usage: MagicFern [-h] --references REFERENCES [REFERENCES ...] [--candidates
                      CANDIDATES [CANDIDATES ...]] [--crop CROP] [--save-reference]

positional arguments:
--references REFERENCES [REFERENCES ...], -r REFERENCES [REFERENCES ...]
                      A list of images used to calculate the fingerprint.
                      Alternatively, one might also specify a single path
                      pointing to a YML file containing the reference finger-
                      print directly as an OpenCV matrix.

optional arguments:
-h, --help            show this help message and exit

--candidates CANDIDATES [CANDIDATES ...], -c CANDIDATES [CANDIDATES ...]
                      A list of images, each used as a candidate for the
                      calculated fingerprint.

--crop CROP, -s CROP  Number of pixel to use for a quadratic center crop of
                      the images. Defaults to the minimum size of the
                      smallest image.

--valid-format, -v    Only determines PCE from candidates with the same size
                      like the reference images.

--save-reference, -o  Path to save the reference image to. Needs to end with
                      ".yml", e.g., "referenceFingerprint.yml".

)";
}

void parseArguments(int argc, char *argv[], std::vector<std::string> & referenceImages, std::vector<std::string> & candidates, double & crop, bool & validFormat, std::string &referencePath)
{
    bool bReferences = false;
    bool bCandidates = false;
    bool bCropping = false;
    bool bReferencePath = false;

    std::string arg;

    for(int i = 1; i < argc; i++)
    {
        arg = argv[i];
        if(!arg.compare("-h") || !arg.compare("--help"))
        {
            std::cout << "\nHELP MESSAGE:\n\n" << std::endl;
            printUsage();
            exit(0);
        }
        else if(!arg.compare("-c") || !arg.compare("--candidates"))
        {
            bCandidates = true;
            bReferences = bCropping = bReferencePath = false;
        }
        else if(!arg.compare("-r") || !arg.compare("--references"))
        {
            bReferences = true;
            bCandidates = bCropping = bReferencePath = false;
        }
        else if(!arg.compare("-s") || !arg.compare("--crop"))
        {
            bCropping = true;
            bReferences = bCandidates = bReferencePath = false;
        }
        else if(!arg.compare("-v") || !arg.compare("--valid-format"))
        {
            validFormat = true;
            bCropping = bReferences = bCandidates = bReferencePath = false;
        }
        else if(!arg.compare("-o") || !arg.compare("--save-reference"))
        {
            bReferencePath = true;
            bCropping = bReferences = bCandidates = false;
        }
        else if(bCandidates)
        {
            candidates.push_back(arg);
            std::cout << "candidates: " << arg << std::endl;
        }
        else if(bReferences)
        {
            referenceImages.push_back(arg);
        }
        else if(bCropping)
        {
            crop = stoi(arg);
            std::cout << "crop: " << crop << std::endl;
        }
        else if(bReferencePath)
        {
            referencePath = arg;
        }
        else
        {
            std::cout << "unknown argument: " << arg << std::endl << std::endl;
            printUsage();
            exit(1);
        }
    }

    if (candidates.empty()) {
        if (referenceImages.empty()) {
      std::cout << "No candidates and no references images." << std::endl;
      printUsage();
      exit(1);
        }

        candidates.push_back(referenceImages[referenceImages.size() - 1]);
        referenceImages.pop_back();
        std::cout << "candidates: " << candidates.at(0) << std::endl;
    }

    for (unsigned i = 0; i < referenceImages.size(); i++) {
              std::cout << "references: " << referenceImages[i] << std::endl;
    }
}
