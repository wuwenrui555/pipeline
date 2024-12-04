import logging
import os
import pickle as pkl
import re

import cv2
import pandas as pd
import tifffile
from IPython.display import display
from pycodex import align, io, metadata
from tqdm import tqdm

# TODO: pipeline for aligning two runs
# 1. do manual alignment for bridge marker (usually DAPI) using `01_sift_plot_src_on_dst_coordinate.ipynb`, where you
#    will get a `sift_parameter.pkl` file.
# 2. use this function to align the rest of the markers
#    - align source image on coordinates of destination image and apply blank mask on the aligned source images.
#    - apply blank mask to the destination images
# 3. pack the aligned images into an ome.tiff file


def clean_marker_name(filename: str) -> str:
    """
    Helper function to clean marker names of Keyence platform.

    Parameters
    ----------
    filename : str
        The name of the marker file.

    Returns
    -------
    str
        The cleaned marker name.
    """
    marker_name = re.sub(r"reg\d+_cyc\d+_ch\d+_", "", os.path.splitext(filename)[0])
    marker_name = "DAPI" if re.search(r"Ch\d+Cy\d+", marker_name, re.IGNORECASE) else marker_name
    return marker_name


