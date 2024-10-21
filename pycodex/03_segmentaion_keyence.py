import logging

from pycodex.segmentation import io_fusion as io
from pycodex.segmentation import mobject as mo

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# parameter ^ #####
boundary_markers = ["CD45", "NaKATP", "HLA1", "G6PD", "CD45RO", "CD45RA", "CD8", "CD20", "CD31", "CD9_500ms"]
internal_markers = ["Ch1Cy1", "VDAC1", "ATP5A", "aSMA"]
pixel_size_um = 377.5202 / 1000
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20
# parameter $ #####

marker_list = boundary_markers + internal_markers

marker_dir = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA543/images/final"
metadata_dict = io.organize_metadata(marker_dir)
marker_object = mo.organize_marker_object(metadata_dict, marker_list)

segmentation_dir = "/mnt/nfs/home/wenruiwu/projects/shuli_rcc/data/output/segmentation_20241221"
mo.marker_object_segmentation_mesmer(
    segmentation_dir,
    marker_object,
    boundary_markers,
    internal_markers,
    pixel_size_um,
    scale,
    maxima_threshold,
    interior_threshold,
)
mo.extract_cell_features(marker_dir, segmentation_dir)
