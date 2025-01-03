# %%
from collections import OrderedDict

import numpy as np
import pandas as pd
from pyqupath.ometiff import export_ometiff_pyramid_from_dict
from pathlib import Path
from pyqupath.ometiff import load_tiff_to_dict
import os
from tqdm import tqdm
from pycodex.segmentation import scale_marker_sum, cut_quantile


def combine_markers(
    marker_dict: dict[str, np.ndarray],
    markers_list: list[list[str]],
) -> OrderedDict:
    """
    Combine markers from different channels into one channel.

    Parameters
    ----------
    marker_dict : dict[str, np.ndarray]
        Dictionary of markers, with keys as marker names and values as marker arrays.
    markers_list : list[list[str]]
        List of markers to be combined.

    Returns
    -------
    OrderedDict
        Dictionary of combined markers.
    """
    marker_sum_dict = OrderedDict()
    for markers in tqdm(markers_list, desc="Combining markers"):
        tag = ",".join(markers)

        # raw markers
        q_min = 0.00
        q_max = 1.00
        marker_name = f"({q_min:.2f},{q_max:.2f}) {tag}"
        marker_sum_dict[marker_name] = (
            scale_marker_sum(
                markers,
                {
                    key: cut_quantile(value, q_min=q_min, q_max=q_max)
                    for key, value in marker_dict.items()
                },
                True,
            )
            * 65535
        ).astype(np.uint16)

        # cut quantile: 0.00-0.99
        q_min = 0.00
        q_max = 0.99
        marker_name = f"({q_min:.2f},{q_max:.2f}) {tag}"
        marker_sum_dict[marker_name] = (
            scale_marker_sum(
                markers,
                {
                    key: cut_quantile(value, q_min=q_min, q_max=q_max)
                    for key, value in marker_dict.items()
                },
                True,
            )
            * 65535
        ).astype(np.uint16)

        # cut quantile: 0.00-0.90
        q_min = 0.00
        q_max = 0.90
        marker_name = f"({q_min:.2f},{q_max:.2f}) {tag}"
        marker_sum_dict[marker_name] = (
            scale_marker_sum(
                markers,
                {
                    key: cut_quantile(value, q_min=q_min, q_max=q_max)
                    for key, value in marker_dict.items()
                },
                True,
            )
            * 65535
        ).astype(np.uint16)

    return marker_sum_dict


# %%

# id = "TMA544_run1=reg008_run2=reg012"
# path_ometiff = f"/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/05_marker_ometiff/{id}/{id}.ome.tiff"

markers_list = [
    ["DAPI"],
    ["DAPI", "Ki-67"],
    ["CD45", "CD3e", "CD163", "NaKATP"],
    ["CD45", "CD3e", "CD163", "CD45RO", "NaKATP"],
    ["CD45", "CD3e", "CD163", "CD45RO", "NaKATP", "HLA1"],
]
all_markers = [marker for markers in markers_list for marker in markers]
all_markers = pd.Series(all_markers).unique()

id_list = [
    "TMA544_run1=reg008_run2=reg012",
    "TMA544_run1=reg004_run2=reg006",
    "TMA544_run1=reg018_run2=reg014",
    "TMA544_run1=reg011_run2=reg023",
    "TMA544_run1=reg014_run2=reg008",
]
dir_id = Path(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/05_marker_ometiff"
)
dir_output = Path(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/05_marker_ometiff_combination"
)
dir_output.mkdir(parents=True, exist_ok=True)

for id in tqdm(id_list, desc="Generating ome.tiff"):
    # Load markers dictionary
    path_ometiff = dir_id / f"{id}/{id}.ome.tiff"
    marker_dict = load_tiff_to_dict(
        path_ometiff,
        "ome.tiff",
        channels_order=all_markers,
    )

    # Combine markers and update markers dictionary
    marker_sum_dict = combine_markers(marker_dict, markers_list)
    marker_dict.update(marker_sum_dict)

    # Export ome.tiff
    path_output = dir_output / f"{id}.ome.tiff"
    if path_output.exists():
        os.remove(path_output)
    export_ometiff_pyramid_from_dict(marker_dict, str(path_output))


# %%
