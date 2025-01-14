# %%
import logging
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from IPython.core.interactiveshell import InteractiveShell
from tqdm import tqdm

sys.path.append("/mnt/nfs/home/wenruiwu/pipeline/alignment")
from src.valisaligner import ValisAligner, setup_logging

InteractiveShell.ast_node_interactivity = "all"
TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:10}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


###############################################################################
# Valis alignment
###############################################################################


def run_valis_register(row):
    """
    Run Valis to register destination and source images.
    """
    id = row["id"]
    dst_dir = Path(row["dst_dir"])
    src_dir = Path(row["src_dir"])
    output_dir = Path(row["output_dir"])

    dst_register_f = dst_dir / row["dst_register"]
    src_register_f = src_dir / row["src_register"]

    valis_aligner = ValisAligner(
        dst_register_f=dst_register_f,
        src_register_f=src_register_f,
        output_dir=output_dir,
    )

    overlap_dir = output_dir / "overlap"
    overlap_dir.mkdir(exist_ok=True, parents=True)
    fig, axs = valis_aligner.plot_overlap()
    fig.savefig(overlap_dir / f"{id}.png")

    error_df_dir = output_dir / "error_df"
    error_df_dir.mkdir(exist_ok=True, parents=True)
    valis_aligner.error_df.assign(id=id).to_csv(error_df_dir / f"{id}.csv", index=False)


def run_valis_apply(row):
    """
    Run Valis to apply registration on destination and source images.
    """
    output_dir = Path(row["output_dir"])

    valis_aligner_f = output_dir / "valis" / "intermediate" / "valis_aligner.pkl"
    with open(valis_aligner_f, "rb") as f:
        valis_aligner = pickle.load(f)

    dst_dir = Path(row["dst_dir"])
    src_dir = Path(row["src_dir"])
    dst_apply_fl = list(dst_dir.glob("*.tif"))
    src_apply_fl = list(src_dir.glob("*.tif"))

    valis_aligner.rigid.apply(dst_apply_fl=dst_apply_fl, src_apply_fl=src_apply_fl)
    valis_aligner.non_rigid.apply(dst_apply_fl=dst_apply_fl, src_apply_fl=src_apply_fl)


params_df = pd.read_csv(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/alignment_parameter.csv"
)

if False:
    setup_logging(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/valis_register.log"
    )
    for i, row in tqdm(
        params_df.iterrows(),
        desc="Register",
        bar_format=TQDM_FORMAT,
        total=params_df.shape[0],
    ):
        id = row["id"]
        try:
            run_valis_register(row)
            logging.info(f"Succeed: {id}.")
        except Exception as e:
            logging.error(f"Failed: {id} ({e}).")

if False:
    setup_logging(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/valis_apply.log"
    )
    run_df = params_df[params_df["tma"] == "TMA003"]
    for i, row in tqdm(
        run_df.iterrows(),
        desc="Apply",
        bar_format=TQDM_FORMAT,
        total=run_df.shape[0],
    ):
        id = row["id"]
        try:
            run_valis_apply(row)
            logging.info(f"Succeed: {id}.")
        except Exception as e:
            logging.error(f"Failed: {id} ({e}).")


###############################################################################
# OME-TIFF construction: Markers
###############################################################################


def parse_metadata_keyence(output_dir, non_rigid=True):
    id = Path(output_dir).name
    tag = "non_rigid" if non_rigid else "rigid"
    ometiff_dir = Path(output_dir) / f"registered_{tag}" / "ometiff"

    # Marker metadata
    img_fl = list(ometiff_dir.glob("*.ome.tiff"))
    filenames, extensions = zip(
        *[re.match(r"([^.]+)(.*)", img_f.name).groups() for img_f in img_fl]
    )

    metadata_file = pd.DataFrame(
        {
            "id": id,
            "img_f": img_fl,
            "filename": filenames,
            "extension": extensions,
        }
    )

    ## Marker type
    idx_dapi = metadata_file.filename.apply(
        lambda x: re.search(r"Ch\dCy\d", x) is not None
    )
    idx_blank = metadata_file.filename.apply(
        lambda x: re.search(r"blank", x, re.IGNORECASE) is not None
    )
    marker_type = np.full(metadata_file.shape[0], "marker")
    marker_type[idx_dapi] = "dapi"
    marker_type[idx_blank] = "blank"
    metadata_file["marker_type"] = marker_type

    metadata_marker = pd.DataFrame(
        metadata_file.filename.str.split("_", n=4).tolist(),
        columns=["prefix", "region", "cycle", "channel", "marker"],
    )
    metadata_marker["marker_label"] = metadata_marker.apply(
        lambda row: f"{row['prefix']}_{row['cycle']}_{row['channel']}_{row['marker']}",
        axis=1,
    )

    metadata = pd.concat([metadata_file, metadata_marker], axis=1)
    return metadata


def review_markerlist_pattern(params_df, excel_dir):
    # Find distinct markerlist patterns
    markerlist_dict = defaultdict(list)
    for i, row in params_df.iterrows():
        metadata = parse_metadata_keyence(row["output_dir"], non_rigid=False)
        markerlist = tuple(
            metadata[metadata.marker_type == "marker"].marker_label.sort_values()
        )
        markerlist_dict[markerlist].append(row["id"])
    markerlists, ids = zip(*markerlist_dict.items())
    labels = [f"type_{i}" for i in range(len(markerlists))]

    label_markerlist = {
        labels: markerlist for labels, markerlist in zip(labels, markerlists)
    }
    label_id = {labels: id for labels, id in zip(labels, ids)}

    # Write to Excel
    with pd.ExcelWriter(Path(excel_dir, "label_markerlist.xlsx")) as writer:
        for label, markerlist in label_markerlist.items():
            markerlist_df = pd.DataFrame(
                {"marker_label": markerlist, "marker_name": ""}
            ).sort_values("marker_label")
            markerlist_df.to_excel(writer, sheet_name=label, index=False)

    with pd.ExcelWriter(Path(excel_dir, "label_id.xlsx")) as writer:
        for label, id in label_id.items():
            id_df = pd.DataFrame({"id": id}).sort_values("id")
            id_df.to_excel(writer, sheet_name=label, index=False)

    return label_markerlist, label_id


if False:
    excel_dir = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/metadata"
    label_markerlist, label_id = review_markerlist_pattern(params_df, excel_dir)


###############################################################################
# OME-TIFF construction: DAPI selection
###############################################################################
