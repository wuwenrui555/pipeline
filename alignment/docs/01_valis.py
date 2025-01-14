# %%
import logging
import re
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from IPython.core.interactiveshell import InteractiveShell
from tqdm import tqdm

sys.path.append("..")
from src.valisaligner import ValisAligner, setup_logging

InteractiveShell.ast_node_interactivity = "all"
TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:10}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


# %%
def get_id(row):
    tma_id = re.sub(r"-formal", "", row["sheet"])
    id = f"RCC-{tma_id}-dst={row['dst_id']}-src={row['src_id']}"
    id = re.sub(r"\s+", "", id)
    return id


# Load alignment parameters
params_f = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/data/raw/20250114_alignment_parameter.xlsx"
sheets = pd.ExcelFile(params_f).sheet_names
sheet_l = [
    sheet
    for sheet in sheets
    if re.search(r"formal", sheet) and not re.search(r"not-formal", sheet)
]

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
params_df = pd.concat(
    [
        pd.read_excel(params_f, sheet_name=sheet)
        .assign(sheet=sheet)
        .assign(tma=re.search(r"TMA\d+", sheet).group(0))
        for sheet in sheet_l
    ]
).rename(columns=cols_rename)
params_df["id"] = params_df.apply(get_id, axis=1)

output_root = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/"
params_df["output_dir"] = [
    str(Path(output_root) / "valis" / id) for id in params_df["id"]
]

dapi = np.full(params_df.shape[0], fill_value="").astype(object)
idx_na_dst = ~params_df["dapi_dst"].isna()
idx_na_src = ~params_df["dapi_src"].isna()
dapi[idx_na_dst] = params_df["dapi_dst"][idx_na_dst].str.replace(
    "^run1-", "dst_", regex=True
)
dapi[idx_na_src] = params_df["dapi_src"][idx_na_src].str.replace(
    "^run2-", "src_", regex=True
)
params_df["dapi"] = dapi

params_df = (
    params_df[
        [
            "id",
            "tma",
            "dst_id",
            "src_id",
            "dst_dir",
            "src_dir",
            "output_dir",
            "dst_register",
            "src_register",
            "dapi",
        ]
    ]
    .sort_values("id")
    .reset_index(drop=True)
)

params_df.to_csv(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/alignment_parameter.csv",
    index=False,
)

# %%

# %%
params_df


def run_valis_alignment(output_root, row):
    id = row["id"]

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


if False:
    setup_logging(Path(output_root) / "valis_alignment.log")
    for i, row in tqdm(
        params_df.iterrows(),
        desc="Processing",
        bar_format=TQDM_FORMAT,
        total=params_df.shape[0],
    ):
        id = row["id"]
        try:
            run_valis_alignment(output_root, row)
            logging.info(f"Succeed: {id}.")
        except Exception as e:
            logging.error(f"Failed: {id} ({e}).")

if False:
    setup_logging(Path(output_root) / "valis_alignment_tma003.log")
    run_df = params_df[params_df["tma"] == "TMA003"]
    for i, row in tqdm(
        run_df.iterrows(),
        desc="Processing",
        bar_format=TQDM_FORMAT,
        total=run_df.shape[0],
    ):
        id = row["id"]
        try:
            run_valis_alignment(output_root, row)
            logging.info(f"Succeed: {id}.")
        except Exception as e:
            logging.error(f"Failed: {id} ({e}).")

if False:
    setup_logging(Path(output_root) / "valis_alignment_tma001.log")
    run_df = params_df[params_df["id"] == "RCC-TMA001(reg3x4)-dst=reg001-src=reg001"]
    for i, row in tqdm(
        run_df.iterrows(),
        desc="Processing",
        bar_format=TQDM_FORMAT,
        total=run_df.shape[0],
    ):
        id = row["id"]
        try:
            run_valis_alignment(output_root, row)
            logging.info(f"Succeed: {id}.")
        except Exception as e:
            logging.error(f"Failed: {id} ({e}).")


# %%
