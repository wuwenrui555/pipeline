import os
import pickle as pkl
import cv2

import tifffile
from pycodex import align, io, metadata
from tqdm import tqdm
import logging


def align_2_runs(dir_dst: str, dir_src: str, dir_output: str, src_rot90cw: int = 0, src_hflip: bool = False):
    """
    Aligns and processes images from two separate runs (align source image on coordinates of destination image)

    Parameters:
    ----------
    dir_dst : str
        Path to the directory containing destination images.
    dir_src : str
        Path to the directory containing source images.
    dir_output : str
        Path to the directory where the aligned and processed images will be saved. There should be a `sift_parameter.pkl` 
        in this directory, which is generated from `01_sift_plot_src_on_dst_coordinate.ipynb`.
    src_rot90cw : int, optional
        Number of times to rotate the source images 90 degrees clockwise. Defaults to 0 (no rotation).
    src_hflip : bool, optional
        If True, horizontally flips the source images. Defaults to False.

    Returns:
    ----------
    None
    """
    # load sift parameters
    with open(os.path.join(dir_output, "sift_parameter.pkl"), "rb") as f:
        data = pkl.load(f)
    logging.info("Parameters loaded")

    # get marker list
    dst_metadata_dict = io.organize_metadata_fusion(dir_dst, subfolders=False)
    dst_unique_markers, _, _, _ = metadata.summary_markers(dst_metadata_dict)
    src_metadata_dict = io.organize_metadata_fusion(dir_src, subfolders=False)
    src_unique_markers, _, _, _ = metadata.summary_markers(src_metadata_dict)

    all_markers = dst_unique_markers + src_unique_markers
    all_markers_renamed = io.rename_duplicate_markers(all_markers)
    dst_unique_markers_renamed = all_markers_renamed[: len(dst_unique_markers)]
    src_unique_markers_renamed = all_markers_renamed[len(dst_unique_markers) :]

    src_files = os.listdir(dir_src)
    src_files_dict = {}
    for file in src_files:
        name, extension = os.path.splitext(file)
        if extension in [".tiff", ".tif"]:
            src_files_dict[name] = file
    dst_files = os.listdir(dir_dst)
    dst_files_dict = {}
    for file in dst_files:
        name, extension = os.path.splitext(file)
        if extension in [".tiff", ".tif"]:
            dst_files_dict[name] = file

    # align images
    for i, marker in tqdm(enumerate(src_unique_markers), desc="im_src", total=len(src_unique_markers)):
        path_marker = os.path.join(dir_src, src_files_dict[marker])
        path_output = os.path.join(dir_output, f"{src_unique_markers_renamed[i]}.tiff")
        if os.path.exists(path_marker):
            im = tifffile.imread(path_marker)
            for i in range(src_rot90cw):
                im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
            if src_hflip:
                im = cv2.flip(im, 1)
            logging.info(f"{marker}: loaded")

            im_warped, _ = align.apply_affine_transformation(im, data["output_shape"], data["H_inverse"])
            logging.info(f"{marker}: transformed")

            im_masked = align.apply_blank_mask(im_warped, data["blank_mask"])
            logging.info(f"{marker}: masked")

            tifffile.imwrite(path_output, im_masked)
            logging.info(f"{marker}: completed")
        else:
            logging.info(f"File not exist: {path_marker}")

    for i, marker in tqdm(enumerate(dst_unique_markers), desc="im_dst", total=len(dst_unique_markers)):
        path_marker = os.path.join(dir_dst, dst_files_dict[marker])
        path_output = os.path.join(dir_output, f"{dst_unique_markers_renamed[i]}.tiff")
        if os.path.exists(path_marker):
            im = tifffile.imread(path_marker)
            logging.info(f"{marker}: loaded")

            im_masked = align.apply_blank_mask(im, data["blank_mask"])
            logging.info(f"{marker}: masked")

            tifffile.imwrite(path_output, im_masked)
            logging.info(f"{marker} completed")
        else:
            logging.info(f"File not exist: {path_marker}")
