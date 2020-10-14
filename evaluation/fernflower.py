#!/usr/bin/env python3
# THIS CODE IS AWESOME QUALITY
# MADE WITH <3

import random
import concurrent
import os, sys
import statistics
import time

import numpy as np
import json
import imageio

from typing import List, Tuple, Dict, Any, NamedTuple, Callable

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import mysql.connector
import threading

import image_metadata as caco
from collections import namedtuple

import magicfern as magicfernalize

from magicfern_config import *

CROP_SIZE = 1024

HIST_BIN_COUNT = 257

RANDOM_SEED = 1337  # reproducably random

Constraints = namedtuple("Constraints",
                         ["local_std", "dark", "dark_percentile", "bright", "bright_percentile", "upper_frequency",
                          "empty_bins"])

Candidate = namedtuple("Candidate", ["vals", "id", "filepath", "fcache"])
Fingerprint = namedtuple("Fingerprint", ["id", "images", "fern"])
Comparison = namedtuple("Comparison", ["id", "fingerprint", "image", "result"])

PceStats = NamedTuple("PceStats", [("min", float), ("max", float), ("median", float), ("mean", float)])

#mConn = get_mysql_connection()

def get_cursor():
    try:
        return get_mysql_connection().cursor()
    except Exception as ex:
        raise Exception("Could not get cursor! Message: ", ex)

def commit_db():
    try:
        get_mysql_connection().commit()
    except:
        raise Exception("Could not commit!")

def cropped(filename):
    return os.path.join(IMAGES_CROPPED_DIR_PATH, filename)


def compare_all(user, fingerprint_candidates, comparison_candidates, fingerprint_map):
    """
    Compare a list of fingerprint_candidates to comparison candidates.
    Optionally, pass in a fingerprint map that will be used for caching.
    It will alter the candidates to also add a cache.
    """
    if not comparison_candidates:
        return {"fingerprint": None, "comparisons": []}

    fingerprint = get_fingerprint_for_candidates(user, fingerprint_candidates, fingerprint_map)

    new_candidates = [x for x in comparison_candidates if fingerprint.id not in x.fcache]

    # query = """
    # SELECT candidate
    # FROM comparisonCropped
    # WHERE
    # reference = {},
    # candidate IN ({}),
    # cropHeight = {},
    # cropWidth = {}
    # """.format(fingerprint.id, ",".join(new_candidates), CROP_SIZE, CROP_SIZE)
    # cursor = getCursor()
    # cursor.execute(query)
    #
    # rows = cursor.fetchall()
    # rows = [x[0] for x in rows]
    #
    # new_candidates = [x for x in new_candidates if x.id in rows]

    if new_candidates:
        result_json = fingerprint.fern.compare([x.filepath for x in new_candidates])

    example_result = """
{'crop': 0,
 'references': {'paths': ['/media/storage/camfinger/images/008A88BB-FE1E-4F49-A4BD-9695EB653FB9_0_0_2016-12-07_01-21-21.jpg',
   '/media/storage/camfinger/images/008A88BB-FE1E-4F49-A4BD-9695EB653FB9_15_3_2016-12-07_01-21-26.jpg',
   '/media/storage/camfinger/images/008A88BB-FE1E-4F49-A4BD-9695EB653FB9_18_2_2016-12-07_01-21-27.jpg']},
 'candidates': {'/media/storage/camfinger/images/008A88BB-FE1E-4F49-A4BD-9695EB653FB9_6_2_2016-12-07_01-21-22.jpg': {'pce': 11137.308512097023,
   'pvalue': 0.0,
   'pFA': 0.0,
   'pFALog10': -3863.7633488268243,
   'matchesReferenceDimensions': True,
   'width': 2448,
   'height': 3264}}}
    """

    for new_candidate in new_candidates:
        comparison_id = insert_comparison(fingerprint.id, new_candidate.id,
                                          **result_json["candidates"][new_candidate.filepath])

        new_candidate.fcache[fingerprint.id] = Comparison(comparison_id, fingerprint, new_candidate,
                                                          result_json["candidates"][new_candidate.filepath])

    comparisons = [x.fcache[fingerprint.id] for x in comparison_candidates]
    return {"fingerprint": fingerprint, "comparisons": comparisons}


def get_fingerprint_for_candidates(user, fingerprint_candidates, fingerprint_cache):
    img_ids = sorted([x.id for x in fingerprint_candidates])
    finger_key = json.dumps(img_ids)

    try:
        return fingerprint_cache[finger_key]
    except KeyError as ex:
        # TODO: Could look up in database if already exists (?)
        print("generating new reference_fingerprint for", finger_key)

    fingerprint_query = """
    SELECT id 
    FROM `references`
    WHERE user = {}
    AND count = {}
    AND images = JSON_ARRAY({})
    """.format(user, len(img_ids), ",".join([str(x) for x in img_ids]))

    cursor = get_cursor()
    cursor.execute(fingerprint_query)

    rows = cursor.fetchall()

    fern = magicfernalize.MagicFern([x.filepath for x in fingerprint_candidates])

    if len(rows):
        fingerprint_id = rows[0][0]
    else:
        fingerprint_id = insert_fingerprint(user, img_ids, len(img_ids))

    fingerprint_cache[finger_key] = fingerprint = Fingerprint(fingerprint_id, fingerprint_candidates, fern)

    return fingerprint


def images_for_user(user_id):  # -> List[Tuple[int, str]]:

    query = """
        SELECT id, filename
        FROM images
        WHERE user = {}
        """.format(user_id)

    mc = get_cursor()
    mc.execute(query)
    rows = mc.fetchall()

    filenames = [x[1] for x in rows]
    filenames_1024 = ["{}_1024{}".format(*os.path.splitext(x)) for x in filenames]
    paths = [os.path.join(IMAGES_CROPPED_DIR_PATH, x) for x in filenames_1024]

    return zip([x[0] for x in rows], paths)


def insert_fingerprint(user, images, count, filename="NULL"):
    query = """
    INSERT INTO `references`
    (user, images, filename, count)
    VALUES
    ({user}, "{images}", {filename}, {count})
    """.format(user=user, images=json.dumps(images), filename=filename, count=count)

    print("inserting fingerprint", user)

    cursor = get_cursor()
    cursor.execute(query)

    return cursor.lastrowid


def insert_comparison(reference, candidate, matchesReferenceDimensions,
                      pce, pvalue, pFA, pFALog10, width, height, **kwargs):
    pValue = pvalue  # TODO Vincent: Fix magicfern.py
    cropWidth = width
    cropHeight = height
    dimensionsMatch = matchesReferenceDimensions

    query = """
    INSERT INTO comparisonCropped
    (reference, candidate, dimensionsMatch, cropWidth, cropHeight, pce, pValue, pFA, pFALog10)
    VALUES
    ({reference}, {candidate}, {dimensionsMatch}, {cropWidth}, {cropHeight}, {pce}, {pValue}, {pFA}, {pFALog10})
    """.format(reference=reference, candidate=candidate, dimensionsMatch=dimensionsMatch, cropWidth=cropWidth,
               cropHeight=cropHeight, pce=pce, pValue=pValue, pFA=pFA, pFALog10=pFALog10)

    print("inserting comparison", reference, candidate)

    cursor = get_cursor()
    try:
        cursor.execute(query)
    except Exception as ex:
        print("Duplicate entry for comparisonCropped, return old key. Message: {}".format(ex))
        query = """
        SELECT id
        FROM comparisonCropped 
        WHERE `reference` = {} AND candidate = {} AND cropWidth = {} AND cropHeight = {}
        """.format(
            reference, candidate, cropWidth, cropHeight
        )
        cursor.execute(query)
        return [x[0] for x in cursor.fetchall()][0]
    else:
        cursor.close()

    return cursor.lastrowid


def insert_frequency_constraint(frequency: int, user: int, comparisonsCropped: List[int], pce_stats: PceStats,
                                referenceCount: int, rejectionRate: float, shuffleSeed: int) -> int:
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT IGNORE INTO constraintFrequency 
        (frequency, user, comparisonsCropped, minPce, maxPce, medianPce, meanPce, referenceCount, rejectionRate, shuffleSeed)
        VALUES 
        ({}, {}, "{}", {}, {}, {}, {}, {}, {}, {})
        """.format
            (
            frequency, user, json.dumps(comparisonsCropped), pce_stats.min, pce_stats.max, pce_stats.median,
            pce_stats.mean,
            referenceCount, rejectionRate,
            shuffleSeed)
    )

    return cursor.lastrowid


def insert_darkness_constraint(count_percentage: Tuple[int, float], user: int, comparisonsCropped: List[int],
                               pce_stats: PceStats, referenceCount: int, rejectionRate: float, shuffleSeed: int) -> int:
    count = count_percentage[0]  # type: int
    percentage = count_percentage[1]  # type: float

    cursor = get_cursor()
    cursor.execute(
        """
        INSERT IGNORE INTO constraintDarkness 
        (count, percentage, user, comparisonsCropped, minPce, maxPce, medianPce, meanPce, referenceCount, rejectionRate, shuffleSeed)
        VALUES
        ({}, {}, {}, "{}", {}, {}, {}, {}, {}, {}, {}) 
        """.format
        (count, percentage, user, json.dumps(comparisonsCropped), pce_stats.min, pce_stats.max, pce_stats.median,
         pce_stats.mean,
         referenceCount, rejectionRate,
         shuffleSeed)
    )

    return cursor.lastrowid


def insert_brightness_constraint(count_percentage: Tuple[int, float], user: int,
                                 comparisonsCropped: List[int],
                                 pce_stats: PceStats, referenceCount: int, rejectionRate: float,
                                 shuffleSeed: int) -> int:
    count = count_percentage[0]  # type: int
    percentage = count_percentage[1]  # type: float

    cursor = get_cursor()
    cursor.execute(
        """
        INSERT IGNORE INTO constraintBrightness 
        (count, percentage, user, comparisonsCropped, minPce, maxPce, medianPce, meanPce, referenceCount, rejectionRate, shuffleSeed)
        VALUES
        ({}, {}, {}, "{}", {}, {}, {}, {}, {}, {}, {}) 
        """.format
        (count, percentage, user, json.dumps(comparisonsCropped), pce_stats.min, pce_stats.max, pce_stats.median,
         pce_stats.mean,
         referenceCount, rejectionRate,
         shuffleSeed)
    )

    return cursor.lastrowid


def insert_local_std_constraint(localStd: float, user: int, comparisonsCropped: List[int], pce_stats: PceStats,
                                referenceCount: int, rejectionRate: float, shuffleSeed: int) -> int:
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT IGNORE INTO constraintLocalStd 
        (localStd, user, comparisonsCropped, minPce, maxPce, medianPce, meanPce, referenceCount, rejectionRate, shuffleSeed)
        VALUES
        ({}, {}, "{}", {}, {}, {}, {}, {}, {}, {}) 
        """.format
            (
            localStd, user, json.dumps(comparisonsCropped), pce_stats.min, pce_stats.max, pce_stats.median,
            pce_stats.mean,
            referenceCount,
            rejectionRate, shuffleSeed
        )
    )

    return cursor.lastrowid


def insert_bins_empty_constraint(count: int, user: int, comparisonsCropped: List[int], pce_stats: PceStats,
                                 referenceCount: int, rejectionRate: float, shuffleSeed: int) -> int:
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT INTO constraintBinsEmpty 
        (id, count, user, comparisonsCropped, minPce, maxPce, medianPce, meanPce, referenceCount, rejectionRate, shuffleSeed)
        VALUES
        ({}, {}, {}, "{}", {}, {}, {}, {}, {}, {}, {}) 
        """.format
        (id, count, user, json.dumps(comparisonsCropped), pce_stats.min, pce_stats.max, pce_stats.median,
         pce_stats.mean, referenceCount, rejectionRate, shuffleSeed)
    )

    return cursor.lastrowid


def insert_constraint_user_done(user: int, shuffleSeed: int = RANDOM_SEED, cropWidth: int = CROP_SIZE, cropHeight: int = CROP_SIZE) -> int:
    cursor = get_cursor()
    cursor.execute(
        """
        INSERT INTO constraintUserDone 
        (user, cropWidth, cropHeight, shuffleSeed)
        VALUES
        ({}, {}, {}, {}) 
        """.format
        (user, cropWidth, cropHeight, shuffleSeed)
    )
    commit_db()

    return cursor.lastrowid

def get_pce_stats(comparisons: List[Comparison]):
    if not comparisons:
        return PceStats(0, 0, 0, 0)

    pces = []
    minimum = sys.maxsize
    maximum = 0
    mean = .0

    for comparison in comparisons:
        pce = comparison.result["pce"]
        pces.append(pce)
        minimum = min(minimum, pce)
        maximum = max(maximum, pce)
        mean += pce

    mean /= len(comparisons)
    median = statistics.median(pces)

    return (PceStats(
        minimum,
        maximum,
        median,
        mean
    ))


def store_results(user: int, results: List[Comparison], seed: int, value, rejection_rate: float,
                  store_func: Callable[[Tuple[Any, Any], int, List[int], PceStats, int, float, int], int]):
    for (count, result) in results:
        if len(result["comparisons"]):
            pce_stats = get_pce_stats(result["comparisons"])
            store_func(
                value,
                user,
                sorted([x.id for x in result["comparisons"]]),
                pce_stats,
                count,
                rejection_rate,
                seed
            )

    commit_db()
    print("Stored result to database.")


def generate_lookup_table(image):
    darks = []
    brights = []
    empty = 0

    current = 0

    for bucket in image.vals.hist:
        if bucket == 0:
            empty += 1
        current += bucket
        darks.append(current)
        brights.append(1.0 - current)

    return {
        "image": image,
        "darks": darks,
        "brights": brights,
        "empty": empty
    }


def compute_constraints(user: int, images_randomized: iter, seed, constraint_iter: iter, constraint_func: callable,
                        reference_counts: List[int],
                        fingerprint_map: dict,
                        store_func: Callable[[Any, int, List[int], PceStats, int, float, int], int],
                        inner_constraint_iter: iter = None,
                        **kwargs) -> None:
    current_imgs = []
    last_results = []
    last_vals = None

    has_inner = inner_constraint_iter is not None
    inner_iter = inner_constraint_iter if has_inner else [True]

    first_round = True

    for constraint in constraint_iter:
        # print("Still working, current vals and results", last_vals, last_results)
        for inner_constraint in inner_iter:
            if first_round:
                # In the first round, we need to set all values up.
                last_vals = (constraint, inner_constraint) if has_inner else constraint
                current_imgs = sorted([x.id for x in images_randomized])
                first_round = False

            if has_inner:
                images_constrained = [x for x in images_randomized
                                      if constraint_func(x, constraint, inner_constraint, **kwargs)]
            else:
                images_constrained = [x for x in images_randomized if constraint_func(x, constraint, **kwargs)]

            next_imgs = sorted([x.id for x in images_constrained])

            if current_imgs == next_imgs:
                # we didn't find anything new for these values. Adapt boundaries.
                last_vals = (constraint, inner_constraint) if has_inner else constraint
                continue

            # we found a new set, so something has changed. persist last results with boundary.
            rejection_ratio = 1 - (len(current_imgs) / len(images_randomized))
            store_results(user, last_results, seed, last_vals, rejection_ratio, store_func)

            last_results = []
            # new set starts here.
            current_imgs = next_imgs
            last_vals = (constraint, inner_constraint) if has_inner else constraint

            # ref_count = how many of the remaining images should be in the fingerprint
            for ref_count in reference_counts:
                print("Calculating values for ", ref_count, last_vals)

                fingerprint_candidates = images_constrained[:ref_count]  # references
                comparison_candidates = images_constrained[ref_count:]  # candidates

                last_results.append(
                    (ref_count, compare_all(user, fingerprint_candidates, comparison_candidates, fingerprint_map)))

    # save one last time for the last iteration.
    rejection_ratio = 1 - (len(current_imgs) / len(images_randomized))
    store_results(user, last_results, seed, last_vals, rejection_ratio, store_func)


def test(user, crop_width=CROP_SIZE, crop_height=CROP_SIZE, seed=RANDOM_SEED):
    user_images = list(images_for_user(user))
    sorted(user_images, key=lambda x: x[0])

    darks = range(0, 100, 1)
    dark_percentiles = [x / 100 for x in range(100, 0, -1)]

    brights = range(255, 155, -1)
    bright_percentiles = [x / 100 for x in range(100, 0, -1)]

    reference_counts = [1, 3, 9, 15]

    empty_counts = range(255, 0, -1)

    dataset = {
        x[0]: Candidate(caco.query_or_calc_and_add(*x, crop_width=crop_width, crop_height=crop_height), x[0], x[1], {})
        for
        x in user_images}

    def freq(candidate):
        return candidate.vals.freq_comp_eucl_normalized

    def std(candidate):
        return candidate.vals.local_std

    frequencies = [1.0] + sorted(map(freq, dataset.values()), reverse=True)
    stds = [1.0] + sorted(map(std, dataset.values()), reverse=True)

    randomized = list(dataset.values())
    # We don't want real random, just 1337-pseudorandom.
    random.seed(seed)
    random.shuffle(randomized)
    # randomized = [id_to_elements[x] for x in shuffle(id_to_elements.keys())]
    hist_lookup_tables = {image.id: generate_lookup_table(image) for image in randomized}

    fingerprint_map = {}
<<<<<<< HEAD
    current_imgs = []  # sorted([x.id for x in randomized])

    last_results = []
    last_vals = None

    rejection_ratio = 0

    upper_bounds = {count: "NULL" for count in fimg_counts}

    for dark in darks:
        print("Still working, current vals and results", last_vals, last_results)
        # new, unconstrained run.
        upper_bounds = {count: "NULL" for count in fimg_counts}

        for dark_percentile in dark_percentiles:

            non_dark = [x for x in randomized if hist_lookup_tables[x.id]["darks"][dark] < dark_percentile]

            for bright in brights:


                for bright_percentile in bright_percentiles:

                    non_bright = [x for x in non_dark if
                                  hist_lookup_tables[x.id]["brights"][bright] < bright_percentile]

                    for upper_frequency in frequencies:
                        low_freqs = [x for x in non_bright if freq(x) < upper_frequency]

                        for upper_std in stds:
                            filtered = [x for x in low_freqs if std(x) < upper_std]

                            for empty_count in empty_counts:
                                non_empty = [x for x in filtered if hist_lookup_tables[x.id]["empty"] < empty_count]

                                next_imgs = sorted([x.id for x in non_empty])

                                if current_imgs == next_imgs:
                                    # we didn't find anything new for these values. Adapt boundaries.
                                    last_vals = Constraints(upper_std, dark, dark_percentile, bright, bright_percentile,
                                                            upper_frequency, empty_count)
                                    continue
=======

    """
    def compute_constraints(user: int, images_randomized: iter, seed:int, 
                            constraint_iter: iter, constraint_func: callable,
                            reference_counts: list[int],
                            fingerprint_map: dict,
                            store_func: Callable[[Tuple[Any, Any], int, List[int], PceStats, int, float, int], int]):
                            store_func: callable,
                            inner_constraint_iter: iter = none,
                            **kwargs) -> none:
    """
>>>>>>> 998f7be5127c1c189c13bd122d9ecc99217a3b52

    compute_constraints(user, randomized, seed,
                        darks,
                        lambda x, dark, dark_percentile: hist_lookup_tables[x.id]["darks"][dark] < dark_percentile,
                        reference_counts,
                        fingerprint_map,
                        insert_darkness_constraint,
                        inner_constraint_iter=dark_percentiles,
                        )

    compute_constraints(user, randomized, seed,
                        brights,
                        lambda x, bright, bright_percentile: hist_lookup_tables[x.id]["brights"][
                                                                 bright] < bright_percentile,
                        reference_counts,
                        fingerprint_map,
                        insert_brightness_constraint,
                        inner_constraint_iter=bright_percentiles
                        )

    compute_constraints(user, randomized, seed,
                        frequencies,
                        lambda x, upper_frequency: freq(x) < upper_frequency,
                        reference_counts,
                        fingerprint_map,
                        insert_frequency_constraint
                        )

    compute_constraints(user, randomized, seed,
                        stds,
                        lambda x, upper_std: std(x) < upper_std,
                        reference_counts,
                        fingerprint_map,
                        insert_local_std_constraint
                        )

    compute_constraints(user, randomized, seed,
                        empty_counts,
                        lambda x, empty_count: hist_lookup_tables[x.id]["empty"] < empty_count,
                        reference_counts,
                        fingerprint_map,
                        insert_bins_empty_constraint
                        )


def get_all_userids(reverse=False, divisor=1.0):
    conn = get_mysql_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT *
        FROM usersWithImages AS u
        LEFT JOIN constraintUserDone AS c ON c.user = u.id
        WHERE c.user IS NULL
        ORDER BY id
        """)
    res = [x[0] for x in cursor.fetchall()]
    conn.close()

    if reverse:
        res = res[::-1]

    if divisor != 1.0:
        start = int(len(res) / divisor)
        res = res[int(start):]

    return res


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", "-t", type=int, default=20, required=False)
    parser.add_argument("--reverse", "-r", action="store_true", required=False, default=False)
    parser.add_argument("--divisor", "-d", required=False, default=1.0, type=float,
                        help="Divide the amount of available users by this value and use it as a starting point for the user id.")
    args = parser.parse_args()

    if not os.path.exists(IMAGES_CROPPED_DIR_PATH):
        raise FileNotFoundError("{} does not exist!".format(IMAGES_CROPPED_DIR_PATH))

    futures = {}
    with ProcessPoolExecutor(max_workers=args.threads) as tpe:
        userids = get_all_userids(args.reverse, args.divisor)
        if not userids:
            print("Got no users, exiting.")
            sys.exit(0)

        print("Got {} users, starting at {}.".format(len(userids), userids[0]))

        for userid in userids:
            future = tpe.submit(test, userid)
            futures[future] = userid

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            userid = futures[future]

            try:
                r = future.result()
            except Exception as exc:
                print("{} generated an exception: {}".format(userid, exc))
            else:
                insert_constraint_user_done(userid)
                percent = i / len(futures) * 100
                print("Finished user {} ({:.2f}%, {} of {})".format(userid, percent, i, len(futures)))

    print("All done.")
