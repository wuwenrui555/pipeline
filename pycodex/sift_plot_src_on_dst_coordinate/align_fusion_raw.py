# %%
########################################################################################################################
# Import
########################################################################################################################
import logging
import os
import subprocess

import pandas as pd
from pycodex import align, io
from tqdm import tqdm

# %%
########################################################################################################################
# Setup
########################################################################################################################
# Setup logging
dir_log = "/mnt/nfs/home/wenruiwu/pipeline/pycodex/sift_plot_src_on_dst_coordinate/data/test"
os.makedirs(dir_log, exist_ok=True)
io.setup_logging(
    os.path.join(dir_log, "alignment.log"),
    logger_level=logging.INFO,
    file_handler_level=logging.INFO,
    stream_handler_level=logging.WARNING,
)

# Setup GPU
io.setup_gpu("0,1,2,3")

# parameter
df_parameter = pd.read_excel(
    "/mnt/nfs/home/wenruiwu/projects/alignment_dlbcl/02_sift_parameter/alignment_parameter.xlsx"
)
df_parameter = df_parameter.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# path
dir_alignment = "/mnt/nfs/home/wenruiwu/projects/alignment_dlbcl/03_alignment/"
dir_metadata = "/mnt/nfs/home/wenruiwu/projects/alignment_dlbcl/04_metadata/"
dir_ometiff_dapi = "/mnt/nfs/home/wenruiwu/projects/alignment_dlbcl/05_dapi/"
dir_ometiff_marker = "/mnt/nfs/home/wenruiwu/projects/alignment_dlbcl/06_marker/"
for dir in [dir_alignment, dir_metadata, dir_ometiff_dapi, dir_ometiff_marker]:
    os.makedirs(dir, exist_ok=True)
# with pd.ExcelWriter(os.path.join(dir_ometiff_marker, "marker_selection.xlsx")) as writer:
#     pd.DataFrame(columns=["marker", "marker_name"]).to_excel(writer, sheet_name="marker_order", index=False)


# %%
########################################################################################################################
# Step 1: Align Source Images on Coordinates of Destination Images
########################################################################################################################
def step1_align_src_on_dst(df_parameter, dir_alignment):
    def row_align(row, dir_output):
        align.sift_align_src_on_dst_coordinate(
            row["id"],
            row["dir_dst"],
            row["dir_src"],
            row["path_parameter"],
            dir_output,
            row["src_rot90cw"],
            row["src_hflip"],
            row["name_output_dst"],
            row["name_output_src"],
        )

    tqdm.pandas(desc="Aligning images")
    df_parameter.progress_apply(lambda x: row_align(x, dir_alignment), axis=1)


# %%
########################################################################################################################
# Step 2: Export Marker Metadata
########################################################################################################################
def step2_export_metadata(dir_alignment, dir_metadata):
    for file in tqdm(os.listdir(dir_alignment), desc="Exporting metadata"):
        dir_region = os.path.join(dir_alignment, file)
        if os.path.isdir(dir_region):
            align.export_marker_metadata_fusion(dir_region, dir_metadata)

    df_metadata_dict = {}
    for file in os.listdir(dir_metadata):
        path_metadata = os.path.join(dir_metadata, file)
        if os.path.splitext(path_metadata)[1] == ".xlsx":
            df_metadata_dict.update(pd.read_excel(path_metadata, sheet_name=None))
    df_metadata = pd.concat(df_metadata_dict).reset_index(drop=True)
    df_metadata = df_metadata.drop_duplicates(subset=["marker"])
    df_metadata.to_excel(os.path.join(dir_metadata, "metadata.xlsx"), index=False)


# %%
########################################################################################################################
# Step 3: Export DAPI OME-TIFF
########################################################################################################################
def step3_export_dapi_ometiff(dir_metadata, dir_ometiff_dapi):
    df_metadata = pd.read_excel(os.path.join(dir_metadata, "metadata.xlsx"))
    df_dapi = df_metadata[df_metadata["is_dapi"]]
    dapi_names = df_dapi["marker"].tolist()
    dapi_paths = df_dapi["path"].tolist()
    path_ometiff = os.path.join(dir_ometiff_dapi, "DAPI.ome.tiff")

    path_script = "/mnt/nfs/home/wenruiwu/tools/ome-tiff-pyramid-tools/pyramid_assemble.py"
    tile_size = 256
    n_threads = 20
    input_tiff_paths = dapi_paths
    output_ometiff_path = path_ometiff
    channel_names = dapi_names
    command = [
        "python",
        path_script,
        *input_tiff_paths,
        output_ometiff_path,
        "--channel-names",
        *channel_names,
        "--tile-size",
        str(tile_size),
        "--num-threads",
        str(n_threads),
    ]
    command = [str(x) for x in command]
    logging.info(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        logging.info(f"DAPI OME-TIFF generated successfully: {output_ometiff_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during execution: {e}")


# %%
########################################################################################################################
# Step 4: Export Marker OME-TIFF
########################################################################################################################
def step4_export_marker_ometiff(dir_metadata, dir_ometiff_marker):
    df_selection_dict = pd.read_excel(os.path.join(dir_ometiff_marker, "marker_selection.xlsx"), sheet_name=None)
    # df_selection_dapi = df_selection_dict["dapi"]
    df_selection_marker = df_selection_dict["marker_order"]
    df_metadata = pd.read_excel(os.path.join(dir_metadata, "metadata.xlsx"))
    path_ometiff_marker = os.path.join(dir_ometiff_marker, "marker.ome.tiff")

    marker_names = []
    marker_paths = []
    for i, row in df_selection_marker.iterrows():
        marker, marker_name = row[["marker", "marker_name"]]
        marker_path = df_metadata["path"][df_metadata["marker"] == marker].item()
        marker_names.append(marker_name)
        marker_paths.append(marker_path)

    path_script = "/mnt/nfs/home/wenruiwu/tools/ome-tiff-pyramid-tools/pyramid_assemble.py"
    tile_size = 256
    n_threads = 20
    input_tiff_paths = marker_paths
    output_ometiff_path = path_ometiff_marker
    channel_names = marker_names
    command = [
        "python",
        path_script,
        *input_tiff_paths,
        output_ometiff_path,
        "--channel-names",
        *channel_names,
        "--tile-size",
        str(tile_size),
        "--num-threads",
        str(n_threads),
    ]
    command = [str(x) for x in command]
    logging.info(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        logging.info(f"Marker OME-TIFF generated successfully: {output_ometiff_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during execution: {e}")


# %%
if __name__ == "__main__":
    step1_align_src_on_dst(df_parameter, dir_alignment)
    step2_export_metadata(dir_alignment, dir_metadata)
    step3_export_dapi_ometiff(dir_metadata, dir_ometiff_dapi)
    step4_export_marker_ometiff(dir_metadata, dir_ometiff_marker)
