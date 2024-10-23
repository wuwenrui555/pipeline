import logging

from pycodex import io, utils

# parameter ^ #####
marker_dir = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA543/images/final"
output_dir = "/mnt/nfs/home/wenruiwu/projects/shuli_rcc/data/output/segmentation_20241022"

boundary_markers = ["CD45", "NaKATP", "HLA1", "G6PD", "CD8", "CD20", "CD31"]
internal_markers = ["Ch1Cy1", "aSMA"]
pixel_size_um = 377.5202 / 1000
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20
# parameter $ #####

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

metadata_dict = io.organize_metadata_keyence(marker_dir)
utils.segmentation_mesmer(
    output_dir=output_dir,
    metadata_dict=metadata_dict,
    regions=list(metadata_dict.keys()),
    boundary_markers=boundary_markers,
    internal_markers=internal_markers,
    pixel_size_um=pixel_size_um,
    scale=scale,
    maxima_threshold=maxima_threshold,
    interior_threshold=interior_threshold,
)
