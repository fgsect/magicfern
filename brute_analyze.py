#!/usr/bin/env python3
import os,sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

import subprocess
import re
import itertools
import json

MAGIC_FERN_BINARY = os.path.join(_SCRIPT_PATH, "MagicFern")


def get_jpgs(path):
    jpgs = []
    for root, dirs, files in os.walk(path):
        l = [ os.path.join(root, x) for x in files if x.lower().endswith("jpg") or x.lower().endswith("jpeg") ]
        if l:
            jpgs.append(l)

    return jpgs

def execute(references, candidates, output_f=None):
    exec_list = [MAGIC_FERN_BINARY, "--references"] + references + ["--candidates"] + candidates
    try:
        output = subprocess.check_output(exec_list).decode()
    except:
        sys.stderr.write("Error during executing the following command:\n{}".format(" \\\n\t".join(exec_list)))
        return None

    if output_f:
        output_f.write(output)
        output_f.write("\n")

    print("Reference images:")
    for i, r in enumerate(references):
        print("  {:>3} {}".format(i, r))

    candidates_pce = []
    print("Candidate results:")
    for i in range(0, len(candidates)):
        index1 = output.find("--Candidate number {}--".format(i + 1))
        if index1 == -1:
            raise RuntimeException("Could not find index {} in output!".format(index1))

        if i == len(candidates) - 1:
            s = output[index1:]
        else:
            index2 = output.find("--Candidate number {}--".format(i + 2))
            s = output[index1:index2]

        m = re.search(r"PCE:\s+(.*)", s)
        pce = float(m.group(1))
        formatMatches = "Format is unequal to fingerprint" not in s

        candidates_pce.append({
            "path": candidates[i],
            "pce": pce,
            "formatMatches": formatMatches
        })

        print("  {:>3} {} {}".format(i + 1, pce, candidates[i]))

    return {
        "references": references,
        "candidates": candidates_pce
    }

def iterate(path):
    jpgs = get_jpgs(args.dir)
    results = []

    with open("output.txt", "w") as output_f:
        for i in range(len(jpgs)):
            references = sorted(jpgs[i])
            candidates = []
            for x in (jpgs[:i] + jpgs[i+1:]):
                candidates += x

            candidates.append(references.pop())

            res = execute(references, candidates, output_f)
            if res:
                results.append(res)

    return results

def write_print_results(results):
    s = json.dumps(json.loads(results), indent=2, separators=(',', ': '), sort_keys=True)
    path = os.path(_SCRIPT_PATH, "results.json")

    with open(path, "w") as f:
        f.write(s)

    print(s)
    print()

    print("Results written as JSON to {}.".format(path))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=str, help="Directory to determine fingerprint of")
    args = parser.parse_args()

    results = iterate(args.dir)
    write_print_results(results)

    sys.exit(0)
