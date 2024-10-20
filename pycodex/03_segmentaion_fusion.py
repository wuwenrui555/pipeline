import os
import pickle as pkl

from pycodex.segmentation import io_fusion as io
from pycodex.segmentation import mobject as mo

# parameter ^ #####
final_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/data/output"
output_dir = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/data/output/segmentation"

boundary_markers = ["HLA-1", "CD31", "E-cadherin", "CD68", "CD3e", "HLA-DR", "CD15"]
internal_markers = ["DAPI", "a-SMA", "Vimentin"]
pixel_size_um = 0.5068164319979996
scale = True
maxima_threshold = 0.075
interior_threshold = 0.20
# parameter $ #####

metadata_dict = io.organize_metadata(final_dir)

marker_list = boundary_markers + internal_markers
marker_object = mo.organize_marker_object(metadata_dict, marker_list)
mask_object = mo.marker_object_segmentation_mesmer(
    marker_object,
    boundary_markers,
    internal_markers,
    pixel_size_um,
    scale,
    maxima_threshold,
    interior_threshold,
)

os.makedirs(output_dir, exist_ok=True)
with open(f"{output_dir}/mask_object.pkl", "wb") as file:
    pkl.dump(mask_object, file)
