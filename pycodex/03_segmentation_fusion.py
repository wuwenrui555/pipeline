import logging
import os

import tensorflow as tf
from pycodex import io, utils

# parameter ^ #####
marker_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/data/output/periodontal"
output_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/output/data/segmentation_20241022_run2"

boundary_markers = ["HLA-1", "CD31", "E-cadherin", "CD68", "CD3e", "HLA-DR", "CD15", "Vimentin"]
internal_markers = ["DAPI", "a-SMA"]
pixel_size_um = 0.5068164319979996
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20

os.environ["CUDA_VISIBLE_DEVICES"] = "1"  # GPU setup: Specify visible GPU(s) and allow memory growth
# parameter $ #####

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logging.info(f"Using GPU(s): {[gpu.name for gpu in gpus]}")
    else:
        logging.info("No GPU detected, using CPU.")
except RuntimeError as e:
    logging.info(f"GPU setup failed: {e}")

segmentation_dir = os.path.join(output_dir, "segmentation")
cropped_dir = os.path.join(output_dir, "cropped")

metadata_dict = io.organize_metadata_fusion(marker_dir)
all_regions = list(metadata_dict.keys())

utils.segmentation_mesmer(
    output_dir=segmentation_dir,
    metadata_dict=metadata_dict,
    regions=all_regions,
    boundary_markers=boundary_markers,
    internal_markers=internal_markers,
    pixel_size_um=pixel_size_um,
    scale=scale,
    maxima_threshold=maxima_threshold,
    interior_threshold=interior_threshold,
)

utils.crop_image_into_blocks(
    marker_dir=marker_dir, segmentation_dir=segmentation_dir, output_dir=cropped_dir, regions=all_regions
)
