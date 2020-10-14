#!/usr/bin/env python3

import concurrent
import os, sys
import numpy as np
import json
import imageio
from collections import namedtuple

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import mysql.connector

IMAGES_BASE_PATH = "/media/storage/camfinger/images"

PIXEL_COUNT = 256
HIST_BIN_COUNT = PIXEL_COUNT

from magicfern_config import *

Vals = namedtuple("Vals",
                  ["fft_mean", "fft_sum", "hist", "unif", "freq_comp_taxicab", "freq_comp_eucl", "freq_comp_max",
                   "freq_comp_sum", "freq_comp_taxi_normalized", "freq_comp_eucl_normalized", "freq_comp_eucl_alt",
                   "local_std"])


def impath(filename):
    return os.path.join(IMAGES_BASE_PATH, filename)


def rgb2gray(rgb):
    if np.ndim(rgb) == 2:  # already bw
        return rgb
    return np.dot(rgb[..., :3], [0.299, 0.587, 0.114])


def myfft(bwim):
    f = np.fft.fft2(bwim)
    fshift = np.fft.fftshift(f)
    return np.abs(fshift)


def get_all_images():
    query = """
        SELECT images.id, images.filename
        FROM images
        LEFT JOIN imagesMeta ON images.id = imagesMeta.image
        WHERE imagesMeta.id IS NULL;
        """

    mc = get_mysql_connection().cursor()
    mc.execute(query)

    return list(mc)


def local_std(grayimg, sample=100):
    (height, width) = grayimg.shape
    varimg = np.zeros(int((height * width)/sample))

    henrikcount = 0

    kernelsize = 3
    tmparr = np.zeros(kernelsize * kernelsize)
    offset = int(kernelsize / 2)

    for index, val in np.ndenumerate(grayimg):

        if (index[0] + index[1]) % sample > 0:
            continue

        ykmin = index[0] - offset
        xkmin = index[1] - offset
        ykmax = index[0] + offset + 1
        xkmax = index[1] + offset + 1
        # print(ykmin, xkmin, ykmax, xkmax)
        if (xkmin < 0 or ykmin < 0 or xkmax >=
                width or ykmax >= height):
            varimg[henrikcount] = 0
            # print("hi")
        else:
            # print(greyimg[index])
            counter = 0
            for y in range(ykmin, ykmax):
                for x in range(xkmin, xkmax):
                    tmparr[counter] = grayimg[y, x]
                    counter += 1

            varimg[henrikcount] = tmparr.std()
            # print(tmparr.var())

        henrikcount += 1

    return varimg.mean() / ((PIXEL_COUNT - 1) / 2)  # Max Mean is pixel count. Master Henrik can explain.


def histogram(bwim, hist_bin_count=HIST_BIN_COUNT):
    hist, _ = np.histogram(bwim.ravel(), bins=range(0, hist_bin_count + 1), normed=True)
    return hist.tolist()


def uniform(hist_or_img):
    if np.ndim(hist_or_img) > 1 and len(hist_or_img) != HIST_BIN_COUNT:
        # probably maybe an image, create histogram.
        hist = histogram(hist_or_img)
    else:
        hist = hist_or_img
    return len([x for x in hist if x]) == 1


def fft_weights(img):
    fft = myfft(img)

    (height, width) = np.shape(fft)

    y_center = height / 2
    x_center = width / 2

    # intensities/Fourier Coefficient, weighted by distance from center
    # weight[0]: dist(x, center(x)) + dist(y, center(y))
    # weight[1]: eucledian distance (xy->center(x,y))

    weighted_intensities = np.ndarray((height * width, 2))

    intensity_sum = 0
    max_intensity = 0

    for (y, x), intensity in np.ndenumerate(fft):
        intensity_sum += intensity
        max_intensity = max(intensity, max_intensity)
        weighted_intensities[y * width + x] = [
            intensity * (np.abs(y - y_center) + np.abs(x - x_center)),  # add_unnormalized
            intensity * np.sqrt((y - y_center) ** 2 + (x - x_center) ** 2),  # eucl_unnormalized
        ]

    additional_normalization = height / 2 + width / 2
    eucledian_normalization = np.sqrt(y_center ** 2 + x_center ** 2)

    complete_size = height * width

    sums = np.sum(weighted_intensities, axis=0)

    max_intensity_total = eucledian_normalization * height * width

    def normalize_adds(unnormalized_add):
        # divide each intensity through the amount of frequencies / pixel
        # Also device by the total sum of intensity
        # and divide through the max distance from the middle in both axis
        return unnormalized_add / (intensity_sum * additional_normalization)

    def normalize_eucls(unnormalized_eucl):
        # divide each intensity through the amount of frequencies / pixel
        # Also device by the total sum of intensity
        # and divide through the max distance from the middle (eucledian distance)
        return unnormalized_eucl / (intensity_sum * eucledian_normalization)

    def normalize_eucls_max_intensity_total(unnormalized_eucl):
        # divide each intensity through the amount of frequencies / pixel
        # Also device by the total sum of intensity
        # and divide through the max distance from the middle (eucledian distance)
        return unnormalized_eucl / (max_intensity_total * eucledian_normalization)

    normalized = (normalize_adds(sums[0]), normalize_eucls(sums[1]), normalize_eucls_max_intensity_total(sums[1]))

    return sums, max_intensity, intensity_sum, normalized


def query_or_calc_and_add(id, path, crop_width=0, crop_height=0):
    print("Finding image {}".format(id))

    # TODO: Query image
    cursor = get_mysql_connection().cursor()
    cursor.execute("""
        SELECT 
            fftMean,
            fftSum,
            histogramNormalized,
            isHomogenous,
            freqCompTaxicab,
            freqCompEuclidian,
            freqCompMax,
            freqCompSum,
            freqCompTaxicabNormalized,
            freqCompEuclidianNormalized,
            freqCompEuclidianNormalizedAlt,
            localStd
        FROM `imagesMeta`
        WHERE image = {}
        AND cropWidth = {}
        AND cropHeight = {}
        AND localStd IS NOT NULL 
        """.format(id, crop_width, crop_height))

    rows = cursor.fetchall()

    if not len(rows):
        vals = calculate(path)
        add_to_db(id, *vals, crop_width=crop_width, crop_height=crop_height)
        return vals

    result = list(rows[0])
    result[2] = json.loads(result[2])

    return Vals(*result)


def calculate(path):
    print("Processing {} ...".format(path))
    rgbim = imageio.imread(path)
    bwim = rgb2gray(rgbim)

    fft = myfft(bwim)

    hist = histogram(bwim)

    unif = uniform(list(hist))

    (freq_comp_taxicab, freq_comp_euclidian), freq_comp_max, freq_comp_sum, \
    (freq_comp_taxicab_normalized, freq_comp_euclidian_normalized, freq_comp_euclidian_alt) = fft_weights(fft)

    std = local_std(bwim)

    return Vals(np.mean(fft), np.sum(fft), hist, unif, freq_comp_taxicab,
                freq_comp_euclidian, freq_comp_max, freq_comp_sum, freq_comp_taxicab_normalized,
                freq_comp_euclidian_normalized, freq_comp_euclidian_alt, std)


def add_to_db(image, fft_mean, fft_sum, hist, unif, freq_comp_taxicab, freq_comp_euclidian, freq_comp_max,
              freq_comp_sum, freq_comp_taxicab_normalized, freq_comp_euclidian_normalized, freq_comp_euclidian_alt,
              localStd,
              crop_width=0, crop_height=0):
    query = """
        INSERT INTO `imagesMeta` (
          image,
          histogramNormalized,
          fftMean,
          fftSum,
          isHomogenous,
          freqCompTaxicab,
          freqCompTaxicabNormalized,
          freqCompEuclidian,
          freqCompEuclidianNormalized,
          freqCompEuclidianNormalizedAlt,
          freqCompMax,
          freqCompSum,
          cropWidth,
          cropHeight,
          localStd)
        VALUES (
          {image},
          "{histogramNormalized}",
          {fftMean},
          {fftSum},
          {isHomogenous},
          {freqCompTaxicab},
          {freqCompTaxicabNormalized},
          {freqCompEuclidian},
          {freqCompEuclidianNormalized},
          {freqCompEuclidianNormalizedAlt},
          {freqCompMax},
          {freqCompSum},
          {cropWidth},
          {cropHeight},
          {localStd}
        )
        """.format(
        image=image,
        histogramNormalized=json.dumps(hist),
        fftMean=fft_mean,
        fftSum=fft_sum,
        isHomogenous=int(unif),
        freqCompTaxicab=freq_comp_taxicab,
        freqCompTaxicabNormalized=freq_comp_taxicab_normalized,
        freqCompEuclidian=freq_comp_euclidian,
        freqCompEuclidianNormalized=freq_comp_euclidian_normalized,
        freqCompEuclidianNormalizedAlt=freq_comp_euclidian_alt,
        localStd=localStd,
        freqCompMax=freq_comp_max,
        freqCompSum=freq_comp_sum,
        cropWidth=crop_width,
        cropHeight=crop_height
    )

    mc = get_mysql_connection().cursor()
    mc.execute(query)

    get_mysql_connection().commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", "-t", type=int, default=1, required=False)
    args = parser.parse_args()

    ims = get_all_images()

    with ProcessPoolExecutor(max_workers=args.threads) as tpe:

        future_to_id = {tpe.submit(calculate, impath(filename)): (id, filename) for id, filename in ims}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_id)):
            id, filename = future_to_id[future]

            try:
                r = future.result()
                add_to_db(id, *r)
            except Exception as exc:
                print('\n%r generated an exception: %s' % (id, exc))
            else:
                sys.stderr.write("\rAdded for image {}".format(id))
                sys.stderr.flush()
