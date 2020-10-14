#!/usr/bin/env python3
import os,sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

import subprocess
import re

MAGIC_FERN_BINARY = os.path.join(_SCRIPT_PATH, "MagicFern")

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("dir", type=str, help="Directory to determine fingerprint of")
parser.add_argument("--candidate-image", "-c", type=str, help="Candidate image", default="")
parser.add_argument("--resolution", "-r", type=int, help="How to crop images", default=0)
parser.add_argument("--silent", "-s", action="store_true", default=False)
args = parser.parse_args()

all_jpgs = [ os.path.join(args.dir, x) for x in os.listdir(args.dir) ]

if args.candidate_image:
    all_jpgs = all_jpgs[:-1] + [args.candidate_image]

exec_list = [MAGIC_FERN_BINARY, str(args.resolution)] + all_jpgs
if not args.silent:
    print("[*] Executing `{}`\n".format(" ".join(exec_list)))

while True:
    try:
        output = subprocess.check_output(exec_list)
    except subprocess.CalledProcessError as ex:
        if ex.returncode == -11:
            print("MagicFern crashed, restarting")
            continue
        else:
            print("Called with MagicFern with wrong arguments!")

    break

m = re.search(r"PCE:\s+(-?\d+\.\d+)", output.decode())
print(m.group(1))
