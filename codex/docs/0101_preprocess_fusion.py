import os
from pathlib import Path

from pyqupath.geojson import crop_dict_by_geojson
from pyqupath.ometiff import export_ometiff_pyramid_from_dict, load_tiff_to_dict

################################################################################
# input directory
dir_root = "/mnt/nfs/storage/wenruiwu_temp/pipeline/fusion/00_raw_data/"

# output directory
dir_output = "/mnt/nfs/storage/wenruiwu_temp/pipeline/fusion/01_preprocess/"

# selcet the channels that are needed (e.g., exclude the Blank channels)")
channels_order = [
    "DAPI",
    "CD45",
    "CD3e",
    "CD4",
    "CD8",
    "CD56",
    "CD11b",
    "CD11c",
    "CD138",
    "Pax5",
    "CD68",
    "CD15",
    "CD31",
    "HLA-E",
    "HLA-DR",
    "E-cadherin",
    "MUC5AC",
    "MUC5B",
    "COLA1",
    "KRT14",
    "a-SMA",
    "Vimentin",
    "ICOS",
    "CD44",
    "Ki67",
    "HLA-1",
]
channels_rename = None  # If None, the channels will not be renamed
################################################################################


def preprocess_fusion(
    dir_root,
    dir_output,
    channels_order,
    channels_rename,
):
    dir_root = Path(dir_root)
    dir_output = Path(dir_output)

    # parse the dir_root
    path_markerlist = dir_root / "MarkerList.txt"
    path_geojson = dir_root / "cropping_regions.geojson"
    paths_qptiff = list(dir_root.glob("*.qptiff"))
    if len(paths_qptiff) == 1:
        path_qptiff = paths_qptiff[0]
    else:
        raise ValueError("There should be only one qptiff file in the directory")

    # load QPTIFF file
    im_dict = load_tiff_to_dict(
        path_qptiff,
        filetype="qptiff",
        channels_order=channels_order,
        channels_rename=channels_rename,
        path_markerlist=path_markerlist,
    )

    # crop QPTIFF file into multiple OME-TIFF files
    for name, crop_im_dict in crop_dict_by_geojson(im_dict, path_geojson):
        path_ometiff = dir_output / name / f"{name}.ome.tiff"
        path_ometiff.parent.mkdir(parents=True, exist_ok=True)
        if path_ometiff.exists():
            os.remove(path_ometiff)
        export_ometiff_pyramid_from_dict(crop_im_dict, str(path_ometiff))


preprocess_fusion(dir_root, dir_output, channels_order, channels_rename)
