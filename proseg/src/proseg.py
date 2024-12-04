# cargo install proseg@1.1.9
import logging
import os
import subprocess


def run_proseg_fov(
    dir_output_fov: str,
    path_tx_fov: str,
    n_voxel_layer: int,
    n_threads: int = 20,
    x_column: str = "x_global_px",
    y_column: str = "y_global_px",
):
    """
    Executes the 'proseg' command with the specified parameters.

    Parameters:
    ----------
    dir_output_fov : str
        Directory where the output files will be saved.
    path_tx_fov : str
        Path to the transcript file for the field of view.
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
        f"--output-expected-counts={os.path.join(dir_output_fov, 'cell-expected-counts.csv.gz')}",
        f"--output-cell-metadata={os.path.join(dir_output_fov, 'cell-metadata.csv.gz')}",
        f"--output-transcript-metadata={os.path.join(dir_output_fov, 'transcript-metadata.csv.gz')}",
        f"--output-gene-metadata={os.path.join(dir_output_fov, 'gene-metadata.csv.gz')}",
        f"--output-cell-polygons={os.path.join(dir_output_fov, 'cell-polygons.geojson.gz')}",
        f"--output-cell-polygon-layers={os.path.join(dir_output_fov, 'cell-polygons-layers.geojson.gz')}",
        f"--output-cell-hulls={os.path.join(dir_output_fov, 'cell-hulls.geojson.gz')}",
        f"--output-cell-voxels={os.path.join(dir_output_fov, 'cell-voxels.csv.gz')}",
        f"--voxel-layers={n_voxel_layer}",
        path_tx_fov,
    ]

    try:
        subprocess.run(command, check=True)
        logging.info("Proseg executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during proseg execution: {e}")
    except FileNotFoundError:
        logging.error("Proseg command not found.")
