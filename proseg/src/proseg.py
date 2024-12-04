# cargo install proseg@1.1.9
import logging
import os
import subprocess

import pandas as pd
from tqdm import tqdm


def proseg(
    path_tx: str,
    dir_output: str,
    n_voxel_layer: int,
    n_threads: int = 20,
    x_column: str = "x_global_px",
    y_column: str = "y_global_px",
):
    """
    Executes the 'proseg' command with the specified parameters.

    Parameters:
    ----------
    path_tx : str
        Path to the transcript file.
    dir_output : str
        Directory where the output files will be saved.
    n_voxel_layer : int
        Voxel layers.
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
    command = [
        "proseg",
        "--cosmx",
        f"--nthreads={n_threads}",
        f"--x-column={x_column}",
        f"--y-column={y_column}",
        f"--output-expected-counts={os.path.join(dir_output, 'cell-expected-counts.csv.gz')}",
        f"--output-cell-metadata={os.path.join(dir_output, 'cell-metadata.csv.gz')}",
        f"--output-transcript-metadata={os.path.join(dir_output, 'transcript-metadata.csv.gz')}",
        f"--output-gene-metadata={os.path.join(dir_output, 'gene-metadata.csv.gz')}",
        f"--output-cell-polygons={os.path.join(dir_output, 'cell-polygons.geojson.gz')}",
        f"--output-cell-polygon-layers={os.path.join(dir_output, 'cell-polygons-layers.geojson.gz')}",
        f"--output-cell-hulls={os.path.join(dir_output, 'cell-hulls.geojson.gz')}",
        f"--output-cell-voxels={os.path.join(dir_output, 'cell-voxels.csv.gz')}",
        f"--voxel-layers={n_voxel_layer}",
        path_tx,
    ]

    try:
        subprocess.run(command, check=True)
        logging.info("Proseg executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during proseg execution: {e}")
    except FileNotFoundError:
        logging.error("Proseg command not found.")


def proseg_tma_z_as_voxel_layer(path_tx, dir_output, fovs=None):
    """
    Run proseg on TMA for each FOV with the z-layer as the voxel layer.

    Parameters:
    ----------
    path_tx : str
        Path to the transcript CSV file containing data for all FOVs.
    dir_output : str
        Directory where the output for each FOV will be saved.
    fovs : list, optional
        List of FOVs to process. If None, all FOVs in the transcript file will be processed.

    Returns:
    -------
    None
    """
    # Load the transcript file
    df_tx = pd.read_csv(path_tx)
    logging.info(f"Loaded transcript file with {len(df_tx)} records.")

    # Filter by specified FOVs if provided
    if fovs is not None:
        df_tx = df_tx[df_tx["fov"].isin(fovs)].reset_index(drop=True)
        logging.info(f"Filtered transcript data for specified FOVs: {fovs}.")

    # Run proseg for each FOV
    for fov in tqdm(df_tx["fov"].unique(), desc="Processing FOVs"):
        # Create a directory for the current FOV
        dir_fov = os.path.join(dir_output, f"{fov:03d}")
        os.makedirs(dir_fov, exist_ok=True)

        # Save the transcript file for the current FOV
        path_tx_fov = os.path.join(dir_fov, "tx_file.csv")
        df_tx_fov = df_tx[df_tx["fov"] == fov].reset_index(drop=True)
        df_tx_fov.to_csv(path_tx_fov, index=False)
        logging.info(
            f"Saved transcript file for FOV {fov:03d} at {path_tx_fov}."
        )

        # Get the z-layer
        z = sorted(df_tx_fov["z"].unique())
        z_layer = len(z)
        logging.info(f"FOV {fov:03d}: Detected {z_layer} unique z-layers.")

        # Run proseg
        try:
            proseg(path_tx_fov, dir_fov, z_layer)
            logging.info(f"Proseg executed successfully for FOV {fov:03d}.")
        except Exception as e:
            logging.error(f"Error executing proseg for FOV {fov:03d}: {e}")


def proseg_with_different_voxel_layers(path_tx, dir_output, voxel_layers):
    """
    Run proseg with different voxel layers.

    Parameters:
    ----------
    path_tx : str
        Path to the transcript file.
    dir_output : str
        Directory where the output for each voxel layer configuration will be saved.
    voxel_layers : list of int
        List of voxel layer configurations to process.

    Returns:
    -------
    None
    """
    for voxel_layer in voxel_layers:
        # Create a directory for the current voxel layer
        dir_fov = os.path.join(dir_output, f"voxel_layers={voxel_layer:02d}")
        os.makedirs(dir_fov, exist_ok=True)

        # Run proseg with the specified voxel layer
        try:
            proseg(path_tx, dir_fov, voxel_layer)
            logging.info(
                f"Proseg executed successfully with voxel_layers={voxel_layer:02d}."
            )
        except Exception as e:
            logging.error(
                f"Error executing proseg for voxel_layers={voxel_layer:02d}: {e}"
            )
