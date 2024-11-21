import importlib
import os
import re
import logging
import numpy as np
import pandas as pd
import tifffile
from pycodex import io
from tqdm import tqdm

# Load the module from the given file path
spec = importlib.util.spec_from_file_location(
    "align",
    "/mnt/nfs/home/wenruiwu/pipeline/pycodex/sift_plot_src_on_dst_coordinate/02_sift_plot_src_on_dst_coordinate.py",
)
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)

# Setup GPU
io.setup_gpu("0,1,2,3")

# parameter
excel_parameter = pd.read_excel(
    "/mnt/nfs/home/wenruiwu/pipeline/pycodex/sift_plot_src_on_dst_coordinate/alignment parameter.xlsx",
    sheet_name=None,
)
sheets = ["TMA543-formal", "TMA544-formal", "TMA609 (reg_3x5)-formal", "TMA609 (reg_4x5)-formal"]
df_parameter = pd.concat([excel_parameter[sheet] for sheet in sheets], axis=0)


# formal run
if True:
    dir_root = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/01_alignment/"
    os.makedirs(dir_root, exist_ok=True)

    io.setup_logging(os.path.join(dir_root, "01_alignment.log"), stream_handler_level=logging.WARNING) 

    for i, row in tqdm(df_parameter.iterrows(), total=df_parameter.shape[0], desc="Aligning RCC cores"):
        dir_dst, dir_src, dir_output = row[
            ["path of run1 (dst_dir)", "path of run2 (src_dir)", "output path of run1-run2 (output_dir)"]
        ]

        path_parameter = os.path.join(dir_output, "sift_parameter.pkl")

        tma = re.search(r"(TMA\d{3})", dir_output).group(0)
        tag = os.path.basename(dir_output).replace("-", "=")
        id = f"{tma}_{tag}"

        align.align_2_runs(
            dir_dst=dir_dst,
            dir_src=dir_src,
            path_parameter=path_parameter,
            dir_output=os.path.join(dir_root, id),
            src_rot90cw=1,
            src_hflip=False,
            name_out_dst="run1",
            name_out_src="run2",
        )
