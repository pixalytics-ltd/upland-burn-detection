from scipy.ndimage import gaussian_filter
import scipy.ndimage as ndi
from scipy.stats import median_absolute_deviation
import numpy as np

def plot_comparison(arr, vmax=1, vmin=0):
    cols = int(len(arr) / 4)
    rows = int(len(arr) / cols) +1
    fig, ax = plt.subplots(nrows = rows, ncols = cols)
    plt_num = 0
    for row in ax:
        for col in row:
            if (len(arr)-1) < plt_num:
                continue
            col.imshow(arr[plt_num], vmax=np.max(arr), vmin=np.min(arr))
            plt_num += 1
            
def gauss(arr, sigma=10):
    return gaussian_filter(arr, sigma=sigma)

def denormalise(arr):
    perc = get_true_perc(arr, perc=50)
    arr = arr / np.percentile(arr, perc)
    return arr
    
def threshold(arr, perc=25, threshtype=None):
    arr = arr.flatten()
    arr = arr[arr != 0]
    if threshtype == "median":
        median, mad = get_median_and_mad(arr)
        return median + (mad*3)
    if threshtype == "mean":
        mean, std = np.mean(arr), np.std(arr)
        return mean + (std * 3)
    return np.percentile(arr, perc)

def get_median_and_mad(arr):
    median = np.median(arr)
    mad = np.median(np.abs(arr-median))
    return median, mad

def get_true_perc(arr, perc=50):
    ### Median may be skewed by zeros so get the median of non zero
    num_zeros = len(arr[arr==0])
    total_size = len(arr.flatten())
    real_mid_point = num_zeros + ((total_size - num_zeros) / (100/perc))
    perc = (real_mid_point / total_size) * 100
    return perc 

def size_filter(arr, size=50):
    label, num_label = ndi.label(arr == 1)
    label_sizes = np.bincount(label.ravel())
    arr2 = np.zeros(arr.shape)
    for n, s in enumerate(label_sizes, start=1):
        if s > size:
            arr2[label==n] = 1
    return arr2

def dilation(arr, iterations=10):
    arr = ndi.binary_dilation(arr, iterations=iterations)
    return arr

def erode(arr, iterations=10):
    arr = ndi.binary_erosion(arr, iterations=iterations)
    return arr

def fill_holes(arr):
    arr = ndi.binary_fill_holes(arr)
    return arr

def close_arr(arr):
    arr = ndi.binary_closing(arr)
    return arr

def determine_difference(all_arr):
    new_arr = np.zeros(all_arr.shape)
    for n, arr in enumerate(all_arr):
        if n == 0:
            continue 
        arr = arr - all_arr[n-1]
        new_arr[n] = arr
    return new_arr

def run_analysis(analysed_array, analysis, pol="VV"):

    if "diff" in analysis:
        analysed_array = determine_difference(analysed_array)
    for n, arr in enumerate(analysed_array):
        if "thresh" in analysis:
            thresh_info = analysis.split("-")[1]
            if "median" in thresh_info:
                perc = None
            elif "mean" in thresh_info:
                perc = None
            else:
                perc = int(thresh_info)
                thresh_info=None
            thresh = threshold(arr, perc=perc, threshtype=thresh_info)
            arr[arr < thresh] = 0
            arr[arr > thresh] = 1
            arr = 1 - arr
        if analysis == "denorm":
            arr = denormalise(arr)
        if "gauss" in analysis:
            sigma = int(analysis.split("-")[1])
            arr = gauss(arr, sigma=sigma)
        if "size" in analysis:
            size = int(analysis.split("-")[1])
            arr = size_filter(arr, size=size)
        if "dilate" in analysis:
            iter1 = int(analysis.split("-")[1])
            arr = dilation(arr, iterations=iter1)
        if "erode" in analysis:
            iter1 = int(analysis.split("-")[1])
            arr = erode(arr, iterations=iter1)
        if "fill" in analysis:
            arr = fill_holes(arr)
        if "close" in analysis:
            arr = close_arr(arr)


        analysed_array[n] = arr
    return analysed_array