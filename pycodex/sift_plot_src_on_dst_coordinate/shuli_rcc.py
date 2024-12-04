# %%
########################################################################################################################
# Setup
########################################################################################################################
import importlib
import logging
import os
import re

import numpy as np
import pandas as pd
import tifffile
from pycodex import io
from tqdm import tqdm

# Load the module from the given file path
spec = importlib.util.spec_from_file_location(
    "align",
    "/mnt/nfs/home/wenruiwu/pipeline/pycodex/sift_plot_src_on_dst_coordinate/align.py",
)
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)

# Setup GPU
io.setup_gpu("0,1,2,3")


# %%
########################################################################################################################
# Align Source Images on Coordinates of Destination Images
########################################################################################################################
if False:
    path_parameter = (
        "/mnt/nfs/home/wenruiwu/pipeline/pycodex/sift_plot_src_on_dst_coordinate/data/01_alignment_parameter.xlsx"
    )
    df_parameter = pd.read_excel(path_parameter)

    def align_row(row):
        align.sift_align_src_on_dst_coordinate(
            row["id"],
            row["dir_dst"],
            row["dir_src"],
            row["path_parameter"],
            row["dir_output"],
            row["src_rot90cw"],
            row["src_hflip"],
            row["name_output_dst"],
            row["name_output_src"],
        )

    dir_root = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/01_alignment/"
    os.makedirs(dir_root, exist_ok=True)
    io.setup_logging(os.path.join(dir_root, "01_alignment.log"), stream_handler_level=logging.WARNING)

    tqdm.pandas(desc="Aligning images")
    df_parameter.progress_apply(align_row, axis=1)


# %%
dir_id = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/01_alignment/TMA543_run1=reg001_run2=reg021"
align.display_aligned_markers(dir_id)

########################################################################################################################
# Output DAPI ome.tiff
########################################################################################################################

########################################################################################################################
# Output Marker Metadata
########################################################################################################################

########################################################################################################################
# Input Selected Markers
########################################################################################################################



