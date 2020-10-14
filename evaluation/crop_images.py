#!/usr/bin/env python3
import concurrent
from concurrent.futures import ThreadPoolExecutor

import cv2
import os, sys

from magicfern_config import *


def crop_center(img, cropx: int, cropy: int):
    y, x, _ = img.shape
    startx = int(x / 2 - (cropx / 2))
    starty = int(y / 2 - (cropy / 2))
    return img[starty:starty + cropy, startx:startx + cropx, :]


def crop_save_image(inpath: str, outpath: str, crop: int):
    im = cv2.imread(inpath)
    if crop > im.shape[0] or crop > im.shape[1]:
        raise Exception("Crop bigger than image dimension!")

    cropped_im = crop_center(im, crop, crop)

    cv2.imwrite(outpath, cropped_im)

    return outpath


def crop_images(indir: str, outdir: str, crop: int, threads: int = None) -> None:
    futures_to_filename = {}
    with ThreadPoolExecutor(max_workers=threads) as tpe:

        mc = get_mysql_connection()
        c = mc.cursor()
        c.execute("SELECT filename FROM images")
        all_image_filenames = [x[0] for x in c.fetchall()]

        for f in all_image_filenames:
            basename, ext = os.path.splitext(f)
            inpath = os.path.join(indir, f)
            outpath = os.path.join(outdir, "{}_{}{}".format(basename, crop, ext))

            future = tpe.submit(crop_save_image, inpath, outpath, crop)
            futures_to_filename[future] = f

        for i, future in enumerate(concurrent.futures.as_completed(futures_to_filename)):
            filename = futures_to_filename[future]

            try:
                resultpath = future.result()
            except Exception as exc:
                print('\n{} generated an exception: {}'.format(filename, exc))
            else:
                resultname = os.path.basename(resultpath)
                sys.stdout.write("\r{} {}".format(i, resultname))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("indir", type=str)
    parser.add_argument("outdir", type=str)
    parser.add_argument("crop", type=int)
    parser.add_argument("--threads", "-t", type=int, default=None)
    args = parser.parse_args()

    crop_images(args.indir, args.outdir, args.crop, args.threads)
