###############################################################################
# Purpose:
# There are multiple DAPI images from the Keyence platform. Some of them are full
# of artifacts and some of them are clean.
#
# This script is used to pack the DAPI images into a OME-TIFF file to select the
# best DAPI image for each region, which will be packed into the final OME-TIFF
# file for following steps.

# Note:
# This script will generate a OME-TIFF file of DAPI images and a metadata file
# for each region.
#
# You need to:
# 1. Select the best DAPI image for each region manually
# 2. Edit the metadata file:
#    - Remove the rows of the DAPI images that are not selected
#    - Edit the `channel_name` column for each marker
#    - Modify the order of the rows, which will be the order of the markers in
#      the final OME-TIFF file
# 3. Save the edited metadata file as `metadata_ometiff.csv` in the region directory
###############################################################################

# conda activate cellSeg_test
import re
from pathlib import Path

from pycodex.cls import Marker
from pyqupath.ometiff import export_ometiff_pyramid
from tqdm import tqdm


def export_dapi_ometiff_and_metadata(dir_root, dir_output):
    """
    Export DAPI OME-TIFF and metadata for each region.

    Parameters
    ----------
    dir_root : str
        Root directory of the organized images of the Keyence data.
    dir_output : str
        Output directory of the OME-TIFF and metadata.
    """
    markers = Marker(dir_root)
    markers.organize_metadata(platform="keyence", subfolders=True)
    markers.summary_metadata()

    dir_output = Path(dir_output)
    dir_output.mkdir(exist_ok=True, parents=True)

    for region in tqdm(markers.regions):
        dir_region = dir_output / region
        dir_region.mkdir(exist_ok=True, parents=True)

        # Export DAPI OME-TIFF
        def is_dapi(x):
            """Check if the marker is DAPI"""
            return re.search(r"^Ch\d+Cy\d+$", x) is not None

        metadata_region = markers.metadata[region]
        idx = metadata_region["marker"].apply(is_dapi)
        paths_dapi = metadata_region["path"][idx].tolist()
        names_dapi = metadata_region["marker"][idx].tolist()

        path_ometiff = dir_region / "dapi.ome.tiff"
        if not path_ometiff.exists():
            export_ometiff_pyramid(
                paths_tiff=paths_dapi,
                path_ometiff=str(path_ometiff),
                channel_names=names_dapi,
            )
        else:
            print(f"DAPI OME-TIFF already exists for: {region}")

        # Export marker metadata
        metadata_region["channel_name"] = metadata_region["marker"]
        metadata_region.to_csv(dir_region / "metadata.csv", index=False)


# `dir_root`: directory of the organized images of the Keyence data
# `dir_output`: output directory of the OME-TIFF and metadata
dir_root = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA001-run1/reg_4x5/images/final/"
dir_output = "/mnt/nfs/storage/wenruiwu_temp/pipeline/keyence/01_data_preprocessing"
export_dapi_ometiff_and_metadata(dir_root, dir_output)
