import importlib
import logging
import os

import pandas as pd
from pycodex import io
from tqdm import tqdm

align = importlib.import_module("02_sift_plot_src_on_dst_coordinate")

# logging
log_format = "%(asctime)s - %(levelname)s - %(message)s"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.log"), mode="w")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(file_handler)

# formal run
io.setup_gpu("0,1,2,3")

excel_parameter = pd.read_excel(
    "/mnt/nfs/home/wenruiwu/pipeline/pycodex/sift_plot_src_on_dst_coordinate/alignment parameter.xlsx", sheet_name=None
)
sheets = ["TMA543-formal", "TMA544-formal", "TMA609 (reg_3x5)-formal", "TMA609 (reg_4x5)-formal"]
df_parameter = pd.concat([excel_parameter[sheet] for sheet in sheets], axis=0)

for i, row in tqdm(df_parameter.iterrows(), total=df_parameter.shape[0], desc="Aligning RCC cores"):
    dir_dst, dir_src, dir_output = row[
        ["path of run1 (dst_dir)", "path of run2 (src_dir)", "output path of run1-run2 (output_dir)"]
    ]
    align.align_2_runs(dir_dst=dir_dst, dir_src=dir_src, dir_output=dir_output, src_rot90cw=1, src_hflip=False)