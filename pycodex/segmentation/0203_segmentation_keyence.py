import os

from pycodex import io, utils

########################################################################################################################

marker_dir = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA543/images/final"
output_dir = "/mnt/nfs/home/wenruiwu/projects/shuli_rcc/output/data/segmentation_20241022_run1"

boundary_markers = ["CD45", "NaKATP", "HLA1", "G6PD", "CD8", "CD20", "CD31"]
internal_markers = ["Ch1Cy1", "aSMA"]
pixel_size_um = 377.5202 / 1000
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20

########################################################################################################################

io.setup_gpu("0,1,2,3")

segmentation_dir = os.path.join(output_dir, "segmentation")
cropped_dir = os.path.join(output_dir, "cropped")

metadata_dict = io.organize_metadata_keyence(marker_dir)
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
