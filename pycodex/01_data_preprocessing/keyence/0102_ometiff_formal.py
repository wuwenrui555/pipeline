###############################################################################
# Purpose:
# Using the organized `metadata_ometiff.csv` to generate a OME-TIFF with the best
# DAPI and other markers for each region which will be used in following steps.
###############################################################################

# conda activate cellSeg_test
from pathlib import Path

import pandas as pd
from pyqupath.ometiff import export_ometiff_pyramid
from tqdm import tqdm


def export_marker_ometiff(dir_metadata, dir_output):
    """
    Export marker OME-TIFF for each region.

    Parameters
    ----------
    dir_metadata : str
        Directory of the organized metadata of each region.
    dir_output : str
        Output directory of the marker OME-TIFF files.
    """
    dirs_region = [dir for dir in Path(dir_metadata).glob("*") if dir.is_dir()]
    for dir_region in tqdm(dirs_region):
        region = dir_region.name

        path_metadata = dir_region / "metadata_ometiff.csv"
        if path_metadata.exists():
            metadata = pd.read_csv(path_metadata)
            paths_marker = metadata["path"].tolist()
            names_marker = metadata["channel_name"].tolist()

            path_ometiff = Path(dir_output) / region / f"{region}.ome.tiff"
            path_ometiff.parent.mkdir(exist_ok=True, parents=True)
            if not path_ometiff.exists():
                export_ometiff_pyramid(
                    paths_tiff=paths_marker,
                    path_ometiff=str(path_ometiff),
                    channel_names=names_marker,
                )
            else:
                print(f"DAPI OME-TIFF already exists for: {region}")
        else:
            print(f"Metadata not found for: {region}")


# `dir_metadata`: directory for `metadata_ometiff.csv` of each region
# `dir_output`: output directory of the final OME-TIFF file
dir_metadata = "/mnt/nfs/storage/wenruiwu_temp/pipeline/keyence/01_data_preprocessing"
dir_output = "/mnt/nfs/storage/wenruiwu_temp/pipeline/keyence/02_ometiff"
export_marker_ometiff(dir_metadata, dir_output)
