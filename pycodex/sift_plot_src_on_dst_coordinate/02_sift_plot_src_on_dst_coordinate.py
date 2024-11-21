import logging
import os
import pickle as pkl
import re

import cv2
import pandas as pd
import tifffile
from pycodex import align, io, metadata
from tqdm import tqdm

# TODO: pipeline for aligning two runs
# 1. do manual alignment for bridge marker (usually DAPI) using `01_sift_plot_src_on_dst_coordinate.ipynb`, where you
#    will get a `sift_parameter.pkl` file.
# 2. use this function to align the rest of the markers
#    - align source image on coordinates of destination image and apply blank mask on the aligned source images.
#    - apply blank mask to the destination images
# 3. pack the aligned images into an ome.tiff file


def load_tiff_files(directory: str) -> dict[str, str]:
    """
    Helper function to load image files from a directory.
    """
    tiff_files = {
        os.path.splitext(file)[0]: file
        for file in os.listdir(directory)
        if os.path.splitext(file)[1].lower() in [".tiff", ".tif"]
    }
    return tiff_files


def clean_marker_name(filename: str):
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


def align_2_runs(
    dir_dst: str,
    dir_src: str,
    path_parameter: str,
    dir_output: str,
    src_rot90cw: int = 0,
    src_hflip: bool = False,
    name_out_dst: str = "dst",
    name_out_src: str = "src",
):
    """
    Aligns and processes images from two separate runs (align source image on coordinates of destination image).

    Parameters
    ----------
    dir_dst : str
        Path to the directory containing destination images.
    dir_src : str
        Path to the directory containing source images.
    path_parameter : str
        Path to the file containing SIFT alignment parameters.
    dir_output : str
        Path to the directory where the aligned and processed images will be saved.
    src_rot90cw : int, optional
        Number of times to rotate the source images 90 degrees clockwise. Defaults to 0 (no rotation).
    src_hflip : bool, optional
        If True, horizontally flips the source images. Defaults to False.
    name_out_dst : str, optional
        Name of the destination images directory in the output directory. Defaults to "dst".
    name_out_src : str, optional
        Name of the source images directory in the output directory. Defaults to "src".

    Returns
    -------
    None
    """

    try:
        # Load SIFT parameters
        with open(path_parameter, "rb") as f:
            data = pkl.load(f)
        logging.info("SIFT parameters loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Parameter file not found: {path_parameter}")
        return

    # Load marker lists and metadata
    dst_metadata_dict = io.organize_metadata_fusion(dir_dst, subfolders=False)
    dst_unique_markers, _, _, _ = metadata.summary_markers(dst_metadata_dict)
    src_metadata_dict = io.organize_metadata_fusion(dir_src, subfolders=False)
    src_unique_markers, _, _, _ = metadata.summary_markers(src_metadata_dict)

    # Rename markers to avoid duplicates
    dst_unique_markers_renamed = io.rename_duplicate_markers(dst_unique_markers)
    src_unique_markers_renamed = io.rename_duplicate_markers(src_unique_markers)

    # Load source and destination image file information
    src_files_dict = load_tiff_files(dir_src)
    dst_files_dict = load_tiff_files(dir_dst)

    def process_image(marker, path_marker, output_path, transform=True):
        """
        Helper function to align and process images.
        """
        if os.path.exists(path_marker):
            im = tifffile.imread(path_marker)
            if transform:
                for _ in range(src_rot90cw):
                    im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
                if src_hflip:
                    im = cv2.flip(im, 1)
                logging.info(f"{marker}: image loaded and transformed")

                im_warped, _ = align.apply_affine_transformation(im, data["output_shape"], data["H_inverse"])
                logging.info(f"{marker}: affine transformation applied")

                im_masked = align.apply_blank_mask(im_warped, data["blank_mask"])
                logging.info(f"{marker}: blank mask applied")
            else:
                im_masked = align.apply_blank_mask(im, data["blank_mask"])
                logging.info(f"{marker}: blank mask applied without transformation")
            tifffile.imwrite(output_path, im_masked)
            logging.info(f"{marker}: saved successfully to {output_path}")
        else:
            logging.warning(f"File not found: {path_marker}")

    # Align source images
    dir_out_src = os.path.join(dir_output, name_out_src)
    os.makedirs(dir_out_src, exist_ok=True)
    for i, marker in tqdm(enumerate(src_unique_markers), desc="Source images", total=len(src_unique_markers)):
        path_marker = os.path.join(dir_src, src_files_dict.get(marker, ""))
        path_output = os.path.join(dir_out_src, f"{src_unique_markers_renamed[i]}.tiff")
        process_image(marker, path_marker, path_output, transform=True)

    # Process destination images
    dir_out_dst = os.path.join(dir_output, name_out_dst)
    os.makedirs(dir_out_dst, exist_ok=True)
    for i, marker in tqdm(enumerate(dst_unique_markers), desc="Destination images", total=len(dst_unique_markers)):
        path_marker = os.path.join(dir_dst, dst_files_dict.get(marker, ""))
        path_output = os.path.join(dir_out_dst, f"{dst_unique_markers_renamed[i]}.tiff")
        process_image(marker, path_marker, path_output, transform=False)
