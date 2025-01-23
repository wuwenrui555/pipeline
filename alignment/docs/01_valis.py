# %%
import logging
import os
import pickle
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from chalign.io import setup_logging
from chalign.valisaligner import ValisAligner
from IPython.core.interactiveshell import InteractiveShell
from pyqupath.ometiff import export_ometiff_pyramid, export_ometiff_pyramid_from_dict
from tqdm import tqdm

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


###############################################################################
# OME-TIFF construction: Markers
###############################################################################


def parse_metadata_keyence(output_dir, non_rigid=True):
    """
    Parse metadata from output directory for Keyence data.
    """
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
    """
    Export markerlist patterns and corresponding IDs.
    """
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


###############################################################################
# OME-TIFF construction: DAPI selection
###############################################################################


def export_dapi_ometiff(row, dapi_dir, non_rigid=True):
    """
    Export DAPI OME-TIFF.
    """
    id = row.id
    ometiff_f = Path(dapi_dir) / f"{id}.ome.tiff"

    metadata = parse_metadata_keyence(row.output_dir, non_rigid=non_rigid)
    metadata_dapi = metadata[metadata.marker_type == "dapi"].sort_values("filename")
    img_fl = metadata_dapi.img_f.astype(str).tolist()
    channel_names = metadata_dapi.filename.astype(str).tolist()

    if not ometiff_f.exists():
        export_ometiff_pyramid(
            paths_tiff=img_fl,
            path_ometiff=str(ometiff_f),
            channel_names=channel_names,
        )
    else:
        logging.info(f"OME-TIFF exists and skip: {id}.")


###############################################################################
# OME-TIFF construction: Final OME-TIFF with DAPI and markers
###############################################################################


def run_export_ometiff():
    dapi_df = pd.read_excel(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_ometiff/params/dapi_selection.xlsx",
        sheet_name="alignment_parameter",
    )
    marker_dict = pd.read_excel(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_ometiff/params/label_markerlist.xlsx",
        sheet_name=None,
    )
    label_df = pd.read_excel(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_ometiff/params/label_id.xlsx",
        sheet_name=None,
    )
    label_dict = {id: label for label, id_df in label_df.items() for id in id_df.id}
    input_dir = Path(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/valis"
    )
    output_dir = Path(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_ometiff/"
    )

    dapi_index = get_max_dst_dapi_index()
    dapi = f"Ch1Cy{dapi_index}"
    for id, label in tqdm(
        label_dict.items(), desc="Marker Dict", bar_format=TQDM_FORMAT
    ):
        marker_df = marker_dict[label].reset_index(drop=True)
        marker_df = marker_df.iloc[: np.where(marker_df.marker_label.isna())[0][0]]
        mask_f = (
            input_dir
            / id
            / "registered_non_rigid"
            / "temp"
            / "src_mask_aligned.ome.tiff"
        )
        mask = tifffile.imread(mask_f)

        im_dict = {}
        for i, row in tqdm(
            marker_df.iterrows(),
            desc="Marker",
            bar_format=TQDM_FORMAT,
            total=marker_df.shape[0],
        ):
            tiff_f = list(
                (input_dir / id / "registered_non_rigid" / "ometiff").glob(
                    f"{row.marker_label}"[:4] + "*" + f"{row.marker_label}"[4:] + "*"
                )
            )[0]
            im = tifffile.imread(tiff_f)
            im_dict[row.marker_name] = im * mask

        dapi_df_id = dapi_df[dapi_df.id == id]
        dapi_f = [
            f
            for f in (input_dir / id / "registered_non_rigid" / "ometiff").glob("*")
            if re.search(f"dst.+{dapi}", f.name)
        ][0]
        dst_dapi_f = (
            input_dir
            / id
            / "registered_non_rigid"
            / "ometiff"
            / f"dst_{dapi_df_id.dst_register.str.replace('tif', 'ome.tiff').values[0]}"
        )
        src_dapi_f = (
            input_dir
            / id
            / "registered_non_rigid"
            / "ometiff"
            / f"src_{dapi_df_id.src_register.str.replace('tif', 'ome.tiff').values[0]}"
        )
        im_dict["DAPI"] = tifffile.imread(dapi_f) * mask
        im_dict["dst_register"] = tifffile.imread(dst_dapi_f) * mask
        im_dict["src_register"] = tifffile.imread(src_dapi_f) * mask

        output_f = output_dir / id / f"{id}.ome.tiff"
        output_f.parent.mkdir(parents=True, exist_ok=True)
        if output_f.exists():
            os.remove(output_f)
        export_ometiff_pyramid_from_dict(
            im_dict,
            str(output_f),
            ["dst_register", "src_register", "DAPI"] + marker_df.marker_name.tolist(),
        )


def get_max_dst_dapi_index():
    """
    Get the maximum index of dst DAPI channel.
    """
    valis_dir = Path(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/valis"
    )
    all_index = []
    all_dir = list(valis_dir.glob("*/"))
    for region_dir in tqdm(
        all_dir,
        desc="Get max dst dapi index",
        bar_format=TQDM_FORMAT,
    ):
        file_names = [
            f.name
            for f in (region_dir / "registered_non_rigid/ometiff").glob("*.ome.tiff")
        ]
        dapi_index = [
            re.search(r"dst_.+Ch1Cy(\d+)", name).group(1)
            for name in file_names
            if re.search(r"dst_.+Ch1Cy(\d+)", name)
        ]
        dapi_index = [int(i) for i in dapi_index]
        all_index += dapi_index
    dapi_index, n = np.unique(all_index, return_counts=True)
    max_dapi = dapi_index[n == len(all_dir)].max()
    return max_dapi


###############################################################################
# Main
###############################################################################


def main_valis_register():
    setup_logging(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/log/valis_register.log"
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


def main_valis_apply():
    setup_logging(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/log/valis_apply.log"
    )
    run_df = params_df
    for i, row in tqdm(
        params_df.iterrows(),
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


def main_valis_markerlist():
    excel_dir = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/metadata"
    label_markerlist, label_id = review_markerlist_pattern(params_df, excel_dir)


def main_dapi_ometiff():
    setup_logging(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/log/dapi_ometiff.log"
    )
    dapi_dir = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250114_dapi_selection/"
    for i, row in tqdm(
        params_df.iterrows(),
        desc="DAPI OME-TIFF",
        bar_format=TQDM_FORMAT,
        total=params_df.shape[0],
    ):
        id = row["id"]
        try:
            export_dapi_ometiff(row, dapi_dir, non_rigid=True)
            logging.info(f"Succeed: {id}.")
        except Exception as e:
            logging.error(f"Failed: {id} ({e}).")


def main_export_ometiff():
    setup_logging(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_ometiff/logs/export_ometiff.log"
    )
    run_export_ometiff()


# %%
params_df = pd.read_csv(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/metadata/alignment_parameter.csv"
)

# main_valis_register()
# main_valis_apply()
# main_valis_markerlist()
# main_dapi_ometiff()
main_export_ometiff()
