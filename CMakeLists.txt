cmake_minimum_required(VERSION 3.5)
project(MagicFern)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
message("CMAKE_BUILD_TYPE = ${CMAKE_BUILD_TYPE}")

#set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -fopenmp -Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

set(SOURCE_FILES main.cpp fingerprint_determination/fingerprint_determination.h fingerprint_determination/fingerprint_determination.cpp fingerprint_determination/filter_mask.h fingerprint_determination/filter_mask.cpp fingerprint_determination/noise_extraction.cpp fingerprint_determination/noise_extraction.h fingerprint_determination/mdwt_r.cpp fingerprint_determination/mdwt_r.h fingerprint_determination/wave_noise.cpp fingerprint_determination/wave_noise.h fingerprint_determination/threshold_function.cpp fingerprint_determination/threshold_function.h fingerprint_determination/midwt_r.cpp fingerprint_determination/midwt_r.h fingerprint_determination/intensity_scale.cpp fingerprint_determination/intensity_scale.h fingerprint_determination/shift.hpp fingerprint_determination/saturation.cpp fingerprint_determination/saturation.h further_processing/wienerFiltering.cpp further_processing/wienerFiltering.h further_processing/fastFourierTransformation.cpp further_processing/fastFourierTransformation.h fingerprint_determination/image_noise_extraction.cpp fingerprint_determination/image_noise_extraction.h further_processing/crosscorrelation.cpp further_processing/crosscorrelation.h further_processing/zero_mean_total.cpp further_processing/zero_mean_total.h test.h further_processing/pce.cpp further_processing/pce.h print_result.h parse_arguments.cpp parse_arguments.h image_load.cpp image_load.h candidate_processing.cpp candidate_processing.h print_result.cpp)

#define __STDC_WANT_DEC_FP__ 1
add_definitions(-D__STDC_WANT_DEC_FP__=1)

if (APPLE)
  # The llvm shipped with Mac OS X does not include OpenMP support
  set(CMAKE_C_COMPILER "/usr/local/opt/llvm/bin/clang")
  set(CMAKE_CXX_COMPILER "/usr/local/opt/llvm/bin/clang++")
  #set(CMAKE_EXE_LINKER_FLAGS "/usr/local/opt/llvm/bin/ld.lld")
  # This is only required if OpenCV 3 was installed using Homebrew on Mac
  set(OpenCV_DIR "/usr/local/opt/opencv3/share/OpenCV")
  # Specify where the OpenMP library relies
  link_directories("/usr/local/opt/llvm/lib")
endif()

# Find OpenCV v3, you may need to set OpenCV_DIR variable
# to the absolute path to the directory containing OpenCVConfig.cmake file
# via the command line or GUI
find_package(OpenCV 3 REQUIRED)

# If the package has been found, several variables will
# be set, you can find the full list with descriptions
# in the OpenCVConfig.cmake file.
# Print some message showing some of them
message(STATUS "OpenCV library status:")
message(STATUS "    version: ${OpenCV_VERSION}")
message(STATUS "    libraries: ${OpenCV_LIBS}")
message(STATUS "    include path: ${OpenCV_INCLUDE_DIRS}")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

add_executable(MagicFern ${SOURCE_FILES})

include_directories(${OpenCV_INCLUDE_DIRS})
target_link_libraries( MagicFern ${OpenCV_LIBS} )

include_directories(${OpenCL_INCLUDE_DIRS})
target_link_libraries( MagicFern ${OpenCL_LIBS} )
