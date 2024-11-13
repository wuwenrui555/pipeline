import os
import pickle as pkl
import cv2

import tifffile
from pycodex import align, io, metadata
from tqdm import tqdm
import logging


def align_2_runs(dst_dir: str, src_dir: str, output_dir: str, src_rot90cw: int = 0, src_hflip: bool = False):
    """
    Aligns and processes images from two separate runs (align source image on coordinates of destination image)

    Parameters:
    ----------
    dst_dir : str
        Path to the directory containing destination images.
    src_dir : str
        Path to the directory containing source images.
    output_dir : str
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
    with open(os.path.join(output_dir, "sift_parameter.pkl"), "rb") as f:
        data = pkl.load(f)
    logging.info("Parameters loaded")

    # get marker list
    dst_metadata_dict = io.organize_metadata_fusion(dst_dir, subfolders=False)
    dst_unique_markers, _, _, _ = metadata.summary_markers(dst_metadata_dict)
    src_metadata_dict = io.organize_metadata_fusion(src_dir, subfolders=False)
    src_unique_markers, _, _, _ = metadata.summary_markers(src_metadata_dict)

    all_markers = dst_unique_markers + src_unique_markers
    all_markers_renamed = io.rename_duplicate_markers(all_markers)
    dst_unique_markers_renamed = all_markers_renamed[: len(dst_unique_markers)]
    src_unique_markers_renamed = all_markers_renamed[len(dst_unique_markers) :]

    # align images
    for i, marker in tqdm(enumerate(src_unique_markers), desc="im_src", total=len(src_unique_markers)):
        marker_path = os.path.join(src_dir, f"{marker}.tiff")
        output_path = os.path.join(output_dir, f"{src_unique_markers_renamed[i]}.tiff")
        if os.path.exists(marker_path):
            im = tifffile.imread(marker_path)
            for i in range(src_rot90cw):
                im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
            if src_hflip:
                im = cv2.flip(im, 1)
            logging.info(f"{marker}: loaded")

            im_warped, _ = align.apply_affine_transformation(im, data["output_shape"], data["H_inverse"])
            logging.info(f"{marker}: transformed")

            im_masked = align.apply_blank_mask(im_warped, data["blank_mask"])
            logging.info(f"{marker}: masked")

            tifffile.imwrite(output_path, im_masked)
            logging.info(f"{marker}: completed")
        else:
            logging.info(f"File not exist: {marker_path}")

    for i, marker in tqdm(enumerate(dst_unique_markers), desc="im_dst", total=len(dst_unique_markers)):
        marker_path = os.path.join(dst_dir, f"{marker}.tiff")
        output_path = os.path.join(output_dir, f"{dst_unique_markers_renamed[i]}.tiff")
        if os.path.exists(marker_path):
            im = tifffile.imread(marker_path)
            logging.info(f"{marker}: loaded")

            im_masked = align.apply_blank_mask(im, data["blank_mask"])
            logging.info(f"{marker}: masked")

            tifffile.imwrite(output_path, im_masked)
            logging.info(f"{marker} completed")
        else:
            logging.info(f"File not exist: {marker_path}")
