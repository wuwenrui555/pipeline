###############################################################################
# Purpose:
# This script is used to convert a QPTIFF file for whole slide to multiple
# OME-TIFF files for each region.

# Note:
# You need to generate a GeoJSON file for cropping regions using the QPTIFF file
# before running this script.
###############################################################################


from pathlib import Path

from pyqupath.geojson import crop_dict_by_geojson
from pyqupath.ometiff import export_ometiff_pyramid_from_dict, export_ometiff_pyramid_from_qptiff, load_tiff_to_dict

###############################################################################
# Convert a QPTIFF file to an OME-TIFF file
###############################################################################

# `path_qptiff`: path to the input QPTIFF file
# `path_ometiff`: path to the output OME-TIFF file
# `path_markerlist`: path to the marker list file. If not provided, the marker
#      list will be extracted from the QPTIFF file
path_qptiff = "/mnt/nfs/home/stephanieyiu/Periodontal/qptif_HnE/Periodontal_CODEX-S8_Scan1.er.qptiff"
path_ometiff = "/mnt/nfs/storage/wenruiwu_temp/pipeline/fusion/01_preprocessing/Periodontal_CODEX-S8_Scan1.er.ome.tiff"
path_markerlist = "/mnt/nfs/home/wenruiwu/projects/steph_periodontal/20241022_segmentation/data/raw/MarkerList.txt"
export_ometiff_pyramid_from_qptiff(path_qptiff, path_ometiff, path_markerlist)


###############################################################################
# Cropping into multiple OME-TIFF files
###############################################################################

# `path_qptiff`: path to the input QPTIFF file
# `path_ometiff`: path to the output directory for OME-TIFF files
dir_ometiff = "/mnt/nfs/storage/wenruiwu_temp/pipeline/fusion/02_ometiff/"
path_geojson = "/mnt/nfs/storage/wenruiwu_temp/pipeline/fusion/01_preprocessing/cropping_regions.geojson"

# `channels_order`: the order of channels in the QPTIFF file to load
# `channels_rename`: the new names for the channels
channels_order = ["DAPI", "CD45", "CD3e", "CD4", "CD8"]
channels_rename = ["DAPI", "CD45", "CD3", "CD4", "CD8"]

# Load the QPTIFF file
im_dict = load_tiff_to_dict(
    path_qptiff,
    filetype="qptiff",
    path_markerlist=path_markerlist,
    channels_order=channels_order,
    channels_rename=channels_rename,
)

# Crop the QPTIFF file into multiple OME-TIFF files
for name, crop_im_dict in crop_dict_by_geojson(im_dict, path_geojson):
    path_ometiff = Path(dir_ometiff) / name / f"{name}.ome.tiff"
    path_ometiff.parent.mkdir(parents=True, exist_ok=True)
    export_ometiff_pyramid_from_dict(crop_im_dict, str(path_ometiff))
