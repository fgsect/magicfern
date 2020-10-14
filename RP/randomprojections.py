import numpy as np
import random
import json
import time
from ImageUtils import Image
from signalprocessing.correlation import correlate
from numpy.fft import ifft2, fft2



class CirculantMatrixRNG:
    """
    This is simply a template for both auto-completion and reference for the rng implementation the get_circulant_matrix
    function expects
    """

    def __init__(self, params):
        self.params = params
        pass

    def reset(self):
        pass

    def next(self):
        pass

    def get_params(self):
        return self.params


class GaussianDistributedRNG(CirculantMatrixRNG):
    def __init__(self, params):
        super().__init__(params)

        random.seed(self.params['seed'])
        self.mu = params['mean']
        self.sigma = params['standard_deviation']

    def reset(self):
        random.seed(self.params['seed'])

    def next(self):
        return random.gauss(self.mu, self.sigma)


def get_rng(rng_params):
    assert(rng_params['type'] == GaussianDistributedRNG.__name__)
    return GaussianDistributedRNG(rng_params)








def get_circulant_random_matrix(dimensions, rng, rotate_left=True):
    """

        Returns a circulant random sensing matrix as described in

        "Compressed Fingerprint Matching and Camera Identiﬁcation via Random Projections"
        by Diego Valsesia et al.


        :type rotate_left: bool
        :param rotate_left: Whether the circulant random sensing matrix should create rows by shifting left or right

        :type rng: CirculantMatrixRNG
        :param rng: An RNG implementation to use for generating the sensing matrix

        :type dimensions: tuple
        :param dimensions:  A 3-dimensional tuple containing the height, the width and the number of channels to
                            generate in that exact order. This should be compatible with the internal storage of the
                            ImageUtils.Image class

        :rtype: np.ndarray
        :returns:   A multi-dimensional numpy array that contains a random circulant sensing matrix with the dimensions
                    as defined in the 'dimensions' argument
    """
    start = time.time()
    assert(len(dimensions) == 2)

    def rotate_array_left(arr):
        assert (len(arr) > 0)
        return arr[1:] + [arr[0]]

    def rotate_array_right(arr):
        assert (len(arr) > 0)
        return [arr[-1]] + arr[:-1]

    height = dimensions[0]
    width = dimensions[1]

    rng.reset()
    channel_data = [[rng.next() for _ in range(width)]]
    for i in range(height - 1):
        if rotate_left:
            channel_data.append(rotate_array_left(channel_data[i]))
        else:
            channel_data.append(rotate_array_right(channel_data[i]))

    result = np.array(channel_data)
    assert(result.shape == dimensions)
    end = time.time()
    print("Calculating circulant matrix took {}".format(end - start))
    return result

class CompressedFingerprint:

    def __init__(self, rng_params, original_dimensions, data, original_path='unknown'):
        """

        :param rng_params: a dictionary with the information about the rng to use. This needs to have a 'type' entry
        :param original_dimensions: The dimensions the image had before compression
        :param data: the compressed fingerprints, array of arrays, one for each channel
        :param original_path: the path of the
        """
        self.rng = get_rng(rng_params)
        self.original_dimensions = original_dimensions
        self.data = data
        self.original_path = original_path

    def get_rng_params(self):
        return self.rng.get_params()

    def store_to_file(self, path):

        serializable = {
            'rng': self.rng.get_params(),
            'original_dimensions': self.original_dimensions,
            'compressed_data': self.data,
            'original_path': self.original_path
        }

        with open(path, 'w') as file:
            json.dump(serializable, file, sort_keys=True, indent=4, separators=(',', ': '))

    @staticmethod
    def load_from_file(path):
        with open(path, 'r') as file:
            p = json.load(file)

        return CompressedFingerprint(p['rng'], p['original_dimensions'], p['compressed_data'],
                                     p['original_path'])

    @staticmethod
    def extract_from_noise_fingerprint(noise_fingerprint, rng_params, target_dimensions, num_kept_entries,
                                       original_path='unknown'):
        """

        :param noise_fingerprint: the fingerprint image to create a compressed projection fingerprint for
        :type noise_fingerprint: Image
        :param target_dimensions: The dimensions the fingerprint should be zero-padded to before compression
        :type rng_params: dict
        :param rng_params: parameters for a random number generator (see CirculantMatrixRNG class as schematic)
        :type target_dimensions: tuple
        :param num_kept_entries: to how many entries to reduce the image to
        :type num_kept_entries: int
        :param original_path: an optional parameter that can be used to associate fingerprints with their original path
        :type original_path: str

        :return: a CompressedFingerprint object
        """
        start = time.time()
        if noise_fingerprint.dimensions() != target_dimensions:
            noise_fingerprint = noise_fingerprint.zero_pad(target_dimensions)

        num_pixels = noise_fingerprint.dimensions()[0] * noise_fingerprint.dimensions()[1]
        assert(num_kept_entries <= num_pixels)

        rng = get_rng(rng_params)

        random_matrix = get_circulant_random_matrix(noise_fingerprint.dimensions(), rng)

        t1 = time.time()
        frequency_original = [fft2(noise_fingerprint.get_channel(i)) for i in range(noise_fingerprint.num_channels())]
        t2 = time.time()
        print("FFT took {}".format(t2 - t1))
        frequency_random = [chan * random_matrix for chan in frequency_original]
        t3 = time.time()
        print("Multiplication took {}".format(t3 - t2))
        image_random = [np.real(ifft2(chan)) for chan in frequency_random]
        t4 = time.time()
        print("iFFT took {}".format(t4 - t3))

        reduced_fingerprint = []
        for channel in image_random:
            flattened = channel.flatten()
            valid = list(flattened[: num_kept_entries])
            reduced_fingerprint.append(valid)

        t5 = time.time()
        print("Keeping relevant entries and transforming back took took {}".format(t5 - t4))

        end = time.time()
        print("Extracted compressed noise from fingerprint in {}".format(end - start))
        return CompressedFingerprint(rng_params, target_dimensions, reduced_fingerprint, original_path)


def calc_random_projection_similarity(compressed_fingerprints, other_noise, rng_params, original_dimensions, num_kept_entries):
    """

    :type compressed_fingerprints: list(CompressedFingerprint)
    :type other_noise: Image
    :type rng_params: dict
    :type original_dimensions: tuple
    :type num_kept_entries: int
    :return:
    """

    compressed_other = CompressedFingerprint.extract_from_noise_fingerprint(other_noise, rng_params,
                                                                            original_dimensions,
                                                                            num_kept_entries)

    max_similarity_list = []
    for i in range(len(compressed_fingerprints)):
        similarity = []

        for channel_idx in range(len(compressed_fingerprints[i].data)):
            comp_fp_array = np.array(compressed_fingerprints[i].data[channel_idx])
            comp_other_array = np.array(compressed_other.data[channel_idx])
            channel_similarity = correlate(comp_fp_array, comp_other_array)
            similarity.append(channel_similarity)

        max_similarity_list.append(similarity)

    return max_similarity_list


if __name__ == "__main__":
    pass

