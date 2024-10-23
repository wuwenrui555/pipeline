import logging

from pycodex import io, utils

# parameter ^ #####
marker_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/data/output/periodontal"
output_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/data/output/segmentation_v3"

boundary_markers = ["HLA-1", "CD31", "E-cadherin", "CD68", "CD3e", "HLA-DR", "CD15"]
internal_markers = ["DAPI", "a-SMA", "Vimentin"]
pixel_size_um = 0.5068164319979996
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20
# parameter $ #####

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

metadata_dict = io.organize_metadata_fusion(marker_dir)
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
