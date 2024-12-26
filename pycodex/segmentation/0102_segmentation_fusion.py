import os
from pycodex.cls import Marker
from pycodex.io import setup_gpu
from pycodex import utils

################################################################################

marker_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/20241022_segmentation/data/output/periodontal/"
output_dir = (
    "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/20241022_segmentation/output/data/segmentation_20241022_run2"
)

boundary_markers = ["HLA-1", "CD31", "E-cadherin", "CD68", "CD3e", "HLA-DR", "CD15", "Vimentin"]
internal_markers = ["DAPI", "a-SMA"]
pixel_size_um = 0.5068164319979996
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20

################################################################################


setup_gpu("0,1,2,3")

segmentation_dir = os.path.join(output_dir, "segmentation")
cropped_dir = os.path.join(output_dir, "cropped")

markers = Marker(marker_dir)
markers.organize_metadata(platform="fusion", subfolders=True)
metadata_dict = markers.metadata
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
