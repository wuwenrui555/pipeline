# cargo install proseg@1.1.9
import os
import subprocess

import pandas as pd
from tqdm import tqdm


def run_proseg_fov(
    dir_output_fov,
    path_tx_fov,
    z_layer,
    n_threads=20,
    x_column="x_global_px",
    y_column="y_global_px",
):
    """
    Executes the 'proseg' command with the specified parameters.

    Parameters:
    ----------
    dir_output_fov : str
        Directory where the output files will be saved.
    path_tx_fov : str
        Path to the transcript file for the field of view.
    z_layer : str
        Voxel layers (z-layer).
    n_threads : int, optional
        Number of threads to use (default is 20).
    x_column : str, optional
        Name of the X column in the data (default is "x_global_px").
    y_column : str, optional
        Name of the Y column in the data (default is "y_global_px").

    Returns:
    -------
    None
    """
    # Define the command
    command = f"""
    proseg --cosmx \
        --nthreads {n_threads} \
        --x-column {x_column} --y-column {y_column} \
        --output-expected-counts "{dir_output_fov}/cell-expected-counts.csv.gz" \
        --output-cell-metadata "{dir_output_fov}/cell-metadata.csv.gz" \
        --output-transcript-metadata "{dir_output_fov}/transcript-metadata.csv.gz" \
        --output-gene-metadata "{dir_output_fov}/gene-metadata.csv.gz" \
        --output-cell-polygons "{dir_output_fov}/cell-polygons.geojson.gz" \
        --output-cell-polygon-layers "{dir_output_fov}/cell-polygons-layers.geojson.gz" \
        --output-cell-hulls "{dir_output_fov}/cell-hulls.geojson.gz" \
        --output-cell-voxels "{dir_output_fov}/cell-voxels.csv.gz" \
        --voxel-layers "{z_layer}" \
        "{path_tx_fov}"
    """

    try:
        # Execute the command in the terminal
        subprocess.run(command, shell=True, check=True)
        print("Command executed successfully!")
    except subprocess.CalledProcessError as e:
        print("An error occurred while running the command.")
        print(e)


########################################################################################################################
path_tx = "/mnt/nfs/storage/CosMX/Indepth_TMA971_section01_v132/AtoMx/flatFiles/Indepth_EBV971_CosMx/Indepth_EBV971_CosMx_tx_file.csv.gz"
dir_output_proseg = (
    "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg"
)
########################################################################################################################


df_tx = pd.read_csv(path_tx)
for fov in tqdm(df_tx["fov"].unique()):
    dir_fov = os.path.join(dir_output_proseg, f"{fov:03d}")
    os.makedirs(dir_fov, exist_ok=True)

    path_tx_fov = os.path.join(dir_fov, "tx_file.csv")
    df_tx_fov = df_tx[df_tx["fov"] == fov].reset_index(drop=True)
    df_tx_fov.to_csv(path_tx_fov, index=False)

    z = sorted(df_tx_fov["z"].unique())
    z_layer = len(z)

    run_proseg_fov(dir_fov, path_tx_fov, z_layer)
