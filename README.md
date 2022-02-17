# MagicFern 

This repository contains the native C++ implementation to camera noise extraction based on PRNU from images and determining the affiliation to other camera noise fingerprints using the Peak-to-correlation energy (PCE).  
The code was used for our paper **Camera Fingerprinting Authentication Revisited**.

Paper
-----------
> [Camera Fingerprinting Authentication Revisited](https://www.usenix.org/conference/raid2020/presentation/maier)  
> D. Maier, H. Erb, P. Mullan and V. Haupert  
> The 23rd International Symposium on Research in Attacks, Intrusions and Defenses (RAID 2020)

If you find our work useful in your research please consider citing our paper:  
	
~~~~
@inproceedings {259727,  
author = {Dominik Maier and Henrik Erb and Patrick Mullan and Vincent Haupert},  
title = {Camera Fingerprinting Authentication Revisited},  
booktitle = {23rd International Symposium on Research in Attacks, Intrusions and Defenses ({RAID} 2020)},  
year = {2020},  
isbn = {978-1-939133-18-2},  
address = {San Sebastian},  
pages = {31--46},  
url = {https://www.usenix.org/conference/raid2020/presentation/maier},  
publisher = {{USENIX} Association},  
month = oct,  
}  
~~~~

What is it?
-----------

This program is a C++ implementation of a digital fingerprint extraction from a camera sensor  
and determines the Peak-correlation-to-correlation-ratio (PCE) detection statistic.  
The code is based on a Matlab implementation from M. Goljan et. al.. More information about their  
work is found here: http://dde.binghamton.edu/download/camera_fingerprint/  
  
To work properly the program needs a stack of images of the same camera sensor. It is advisable  
to use around 20 images for fingerprint determination.  
With these, the camera fingerprint is determined. Then the fingerprint is compared with the noise  
residual of a reference image. The program returns the Peak to Correlation energy, the false alarm  
probability and the pvalue. For authentication purposes the PCE is sufficient. A value  
above at least 60 can be considered as the same camera sensor. 


Requirements
-----------

To get started, it is necessary to have OpenCV 3.1.0 preinstalled.


Usage - example
------------------

The arguments need to be file directories to the images,  
which should be used for the Camera Identification.  
  
**Example:**  
MagicFern [-h] --references REFERENCES [REFERENCES ...] [--candidates  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CANDIDATES [CANDIDATES ...]] [--crop CROP] [--valid-format]  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[--save-reference]  
  
**Positional arguments:**  
--references REFERENCES [REFERENCES ...], -r REFERENCES [REFERENCES ...]  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A list of images used to calculate the fingerprint.  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Alternatively, one might also specify a single path  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pointing to a YML file containing the reference finger-  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;print directly as an OpenCV matrix.  
  
**Optional arguments:**  
-h, --help            shows this help message and exits  

--candidates CANDIDATES [CANDIDATES ...], -c CANDIDATES [CANDIDATES ...]  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A list of images, each used as a candidate for the  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;calculated fingerprint.  
  
--crop CROP, -s CROP  Number of pixel to use for a quadratic center crop of  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;the images. Defaults to the minimum size of the  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;smallest image.  
  
--valid-format, -v    Only determines PCE from candidates with the same size  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;like the reference images.  
  
--save-reference, -o  Path to save the reference image to. Needs to end with  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".yml", e.g., "referenceFingerprint.yml".  

  
  
Contacts - Copyright
--------------------
This code is for non-commercial use only.  
For bug reports feel free to open an issue.
