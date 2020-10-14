#!/usr/bin/env python3

# MagicFern Wrapper class
from io import StringIO
from pprint import pprint
from typing import List, Union, Tuple, Any, Dict

import subprocess
import sys, os
import imageio
import tempfile

import json

from magicfern_config import *

DEVNULL = open("/dev/null", "w")
ERRLOG = open("error.log", "w")


class MagicFern:

    def __init__(self, references: Union[str, List[str]], crop: Tuple[int, int] = (0, 0)):
        self.references = references if isinstance(references, list) else [references]
        self.crop = crop

        self._sanity_check_references()

    def _relative_to_absolute_image_path(self, images: List[str]) -> List[str]:
        for i, p in enumerate(images):
            if not os.path.isabs(p):
                images[i] = os.path.join(IMAGES_DIR_PATH, p)

        return images

    def _sanity_check_references(self) -> None:
        self.references = self._relative_to_absolute_image_path(self.references)

        crop_given = self.crop[0] > 0 and self.crop[1] > 0
        if not crop_given:
            self.crop = (0, 0)

        self.shape_min = (0, 0)
        self.shape_max = (0, 0)
        last_shape = None

        for i, p in enumerate(self.references):
            try:
                im = imageio.imread(p)
            except FileNotFoundError:
                raise Exception("Reference image {} does not exist!".format(p))

            if crop_given:
                if last_shape and im.shape != last_shape:
                    raise Exception("The dimensions of {} do not match.".format(os.path.basename(p)))
                last_shape = im.shape

            for i in range(2):
                if im.shape[i] < self.crop[i]:
                    raise Exception("The given crop size is bigger than the dimensions of {}!".format(p))

            if crop_given:
                if self.crop[0] != self.crop[1]:
                    raise Exception("We currently only support quadratic crops :(")

                im_res = im.shape[0] * im.shape[1]
                if self.shape_min[0] * self.shape_min[1] < im_res:
                    self.shape_min = im.shape
                elif self.shape_max[0] * self.shape_max[1] < im_res:
                    self.shape_max = im.shape
            else:
                self.shape_min = im.shape
                self.shape_max = im.shape

    def compare(self, candidates: Union[str, List[str]]) -> Dict[str, Any]:
        candidates = candidates if isinstance(candidates, list) else [candidates]
        candidates = self._relative_to_absolute_image_path(candidates)

        for c in candidates:
            im = imageio.imread(c)

            if not self.crop[0] and im.shape[0] < self.shape_min[0] and im.shape[1] < self.shape_min[1]:
                raise Exception("The candidate {} has smaller dimensions than the reference fingerprint")

        res = self._exec_magicfern(candidates)

        return res

    def _exec_magicfern(self, candidates: List[str]) -> Dict[str, Any]:

        with tempfile.TemporaryDirectory() as d:
            result_path = os.path.join(d, "result.json")

            args = [MAGICFERN_BINARY_PATH, "--references"] + self.references + ["--candidates"] + candidates + [
                "--save-results", result_path] + ["--crop", str(self.crop[0])]

            # TODO: Better error logging

            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            if process.returncode != 0:
                raise Exception("MagicFern exited with status {}:\n{}!\n(Called: '{}')".format(process.returncode, process.stderr.read(), args))

            with open(result_path, "r") as f:
                res = json.load(f)

            return res


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Python Wrapper for MagicFern.")
    parser.add_argument("--references", "-r", nargs="+", type=str, required=True,
                        help="A list of filenames or paths of images to calculate the reference fingerprint.")
    parser.add_argument("--candidates", "-c", nargs="*", type=str,
                        help="A list of filenames or paths of images to compare to the reference fingerprint.")
    parser.add_argument("--crop", "-s", nargs="+", type=int, required=False, default=[512, 512],
                        help="Crop the reference and candidate images to the given size prior to computation. " +
                             "Currently only supports square crops.")

    args = parser.parse_args()

    mf = MagicFern(args.references, tuple(args.crop))
    res = mf.compare(args.candidates)

    pprint(res)

    sys.exit(0)
