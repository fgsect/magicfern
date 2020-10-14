#!/usr/bin/env python3
import os
import json
import sys
from magicfern import MagicFern

"""
Pipe the output to a file to get json. Usage might be;
./compare_two.py $(pwd)/iphone_comparison/henrik_iphone $(pwd)/iphone_comparison/own_iphone_hdr > comparison_result_henrik_hdr.json          

Extract data later using something like:
should_match_pces = [list(x["result"]["candidates"].values())[0]["pce"] for x in results if x["shouldMatch"]]
"""

def is_image(path, filename):
    #TODO: This could be nicer using file(), trying to load the images, or at least providing a proper list or something
    return filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg")

example_result = """
{'crop': 1024, 'references': {'paths': ['/home/domenukk/evaluation/iphone_comparison/henrik_iphone/Foto_18.06.19,_16_30_19.jpg', '/home/domenukk/evaluation/iphone_comparison/henrik_iphone/Foto_18.06.19,_13_50_36.jpg', '/home/domenukk/evaluation/iphone_comparison/henrik_iphone/Foto_18.06.19,_13_50_37.jpg']}, 'candidates': {'/home/domenukk/evaluation/iphone_comparison/own_iphone/IMG_
0053.JPG': {'pce': 1.051887906168799, 'pvalue': 0.1525363427365899, 'pFA': 0.1525363427365899, 'pFALog10': -0.8166266706151879, 'matchesReferenceDimensions': False, 'width': 1024, 'height': 1024}}}
"""

def list_images_from_folder(folder: str):
    ret = []
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in [f for f in filenames if is_image(dirpath, f)]:
            ret.append(os.path.join(dirpath, filename))
    return ret

def print_json_results(refs: list, img: str, should_match: bool, phoneid: int):
    mf = MagicFern(references=refs, crop=(1024,1024))
    print("{")
    print('"shouldMatch": {},'.format('true' if should_match else 'false'))
    print('"phoneId": {},'.format(phoneid))
    
    sys.stderr.write("Comparing {}, should_match={}\n".format(img, should_match))

    print('"result": {}'.format(json.dumps(mf.compare([img]))))

    print('}')


def compare_two_folders(folder1: str, folder2: str):
    """
    We'll manually output the final json line for line so that it's not super slow.
    """
    images1 = list_images_from_folder(folder1)
    images2 = list_images_from_folder(folder2)
    first = True

    print("[")


    for image1 in images1:
        if first:
            first = False
        else:
            print(',')

        refs = [x for x in images1 if x != image1]
        print_json_results(refs, image1, should_match=True, phoneid=1)
        print(',')
        print_json_results(images2, image1, should_match=False, phoneid=1)

    for image2 in images2:
        print(',')
        refs = [x for x in images2 if x != image2]
        print_json_results(refs, image2, should_match=True, phoneid=2)
        print(',')
        print_json_results(images1, image2, should_match=False, phoneid=2)

    print("]")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./compare_two.py [folder1] [folder2]")
        exit(1)
    else:
        compare_two_folders(sys.argv[1], sys.argv[2])
