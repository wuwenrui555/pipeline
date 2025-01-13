# %%
import logging
import re
import sys
from pathlib import Path

import pandas as pd
from IPython.core.interactiveshell import InteractiveShell
from tqdm import tqdm

sys.path.append("..")
from src.valisaligner import ValisAligner, setup_logging

InteractiveShell.ast_node_interactivity = "all"
TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:10}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"

# %%
# Load alignment parameters
params_f = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/data/raw/20250110_alignment_parameter.xlsx"
sheets = pd.ExcelFile(params_f).sheet_names
sheet_l = [sheet for sheet in sheets if sheet.endswith("-formal")]

cols_rename = {
    "run1 (destination)": "dst_id",
    "run2": "src_id",
    "path of run1 (dst_dir)": "dst_dir",
    "path of run2 (src_dir)": "src_dir",
    "output path of run1-run2 (output_dir)": "output_dir",
    "marker_dst": "dst_register",
    "marker_src": "src_register",
    "tma": "tma",
}
params_df = (
    pd.concat(
        [
            pd.read_excel(params_f, sheet_name=sheet)
            .assign(sheet=sheet)
            .assign(tma=re.search(r"TMA\d+", sheet).group(0))
            for sheet in sheet_l
        ]
    )
    .reset_index(drop=True)
    .rename(columns=cols_rename)
)

# %%
output_root = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/"


def run_valis_alignment(output_root, row):
    tma_id = re.sub(r"-formal", "", row["sheet"])
    id = f"RCC-{tma_id}-dst={row['dst_id']}-src={row['src_id']}"
    id = re.sub(r"\s+", "", id)

    dst_dir = Path(row["dst_dir"])
    src_dir = Path(row["src_dir"])

    dst_register_f = dst_dir / row["dst_register"]
    src_register_f = src_dir / row["src_register"]

    dst_apply_fl = list(dst_dir.glob("*.tif"))
    src_apply_fl = list(src_dir.glob("*.tif"))

    output_dir = Path(output_root) / "valis" / id
    valis_aligner = ValisAligner(
        dst_register_f=dst_register_f,
        src_register_f=src_register_f,
        output_dir=output_dir,
    )

    overlap_dir = Path(output_root) / "overlap"
    overlap_dir.mkdir(exist_ok=True, parents=True)
    fig, axs = valis_aligner.plot_overlap()
    fig.savefig(overlap_dir / f"{id}.png")

    error_df_dir = Path(output_root) / "error_df"
    error_df_dir.mkdir(exist_ok=True, parents=True)
    valis_aligner.error_df.assign(id=id).to_csv(error_df_dir / f"{id}.csv", index=False)

    valis_aligner.rigid.apply(dst_apply_fl=dst_apply_fl, src_apply_fl=src_apply_fl)


setup_logging(Path(output_root) / "valis_alignment.log")
for i, row in tqdm(
    params_df.iterrows(),
    desc="Processing",
    bar_format=TQDM_FORMAT,
    total=params_df.shape[0],
):
    tma_id = re.sub(r"-formal", "", row["sheet"])
    id = f"RCC-{tma_id}-dst={row['dst_id']}-src={row['src_id']}"
    id = re.sub(r"\s+", "", id)
    try:
        run_valis_alignment(output_root, row)
        logging.info(f"Succeed: {id}.")
    except Exception as e:
        logging.error(f"Failed: {id} ({e}).")
# %%
