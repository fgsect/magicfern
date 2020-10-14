from PIL import Image
from subprocess import call
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def find_qtable_index(qtable, qtable_list = []):
    """
    Finds where querry qutable matches a qtable in a list of qtables
    Note: The entries in the qtable have to be valid quantization tables. No error checking perforemed
    :param qtable: querry qtalbe
    :param qtable_list: list of qtables (can be empty)
    :return:
        index, if a match was found
        -1 if no match was found
        -2 if qtalbe of wrong size (needs to be (8,8) or array of lenght 64)
    """
    # invalid shape
    if len(qtable) != 64:
        return -2
    # empty qlist
    #if len(qtable_list) == 0:
    #    return 0

    # search for matching qtable
    for qtable_index in range(0,len(qtable_list)):
        if qtable == qtable_list[qtable_index]:
            return qtable_index
    # no matching qtable found
    return len(qtable_list)

def append_qtable(qtable_index, qtable, qtable_list, qtable_histogram = []):
    if qtable_index == len(qtable_list):  # new qtable found
        qtable_list.append(qtable)
        qtable_histogram.append(1)
        return qtable_list, qtable_histogram
    if qtable_index >= 0 and qtable_index < len(qtable_list):  # qtable already present
        qtable_histogram[qtable_index] += 1
        return qtable_list, qtable_histogram

def test():
    print('loefft')

if __name__ == "__main__":
    qtable_list = []
    qtable_histogram = []
    qtable_invalid = 0
    for filename in glob.glob("../../images/munich/*.jpeg"):
        im = Image.open(filename)
        qtable = im.quantization[0] # 0 = lum, 1 = col (i think)
        qtable_index = find_qtable_index(qtable, qtable_list)
        qtable_list, qtable_histogram = append_qtable(qtable_index, qtable, qtable_list, qtable_histogram)

    print(len(qtable_histogram))
    print(qtable_histogram)

