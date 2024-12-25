# %%
import logging
import os
import shutil
import subprocess
import tempfile

import numpy as np

import tifffile


def export_ometiff_pyramid(
    paths_tiff: list[str],
    path_ometiff: str,
    channel_names: list[str],
    tile_size: int = 256,
    n_threads: int = 20,
    path_script: str = "/mnt/nfs/home/wenruiwu/tools/ome-tiff-pyramid-tools/pyramid_assemble.py",
):
    """
    Generate a pyramidal OME-TIFF file from multiple input TIFF files.

    This function combines multiple input TIFF files into a single multi-channel
    OME-TIFF file, adds channel metadata, and builds a multi-resolution pyramid
    for efficient visualization and processing.
    ( https://github.com/labsyspharm/ome-tiff-pyramid-tools)

    Parameters
    ----------
    paths_tiff : list of str
        A list of file paths to the input TIFF images. Each file corresponds
        to a specific channel in the final OME-TIFF.

    path_ometiff : str
        Path to the output OME-TIFF file. If the file already exists, the process
        will terminate to prevent overwriting.

    channel_names : list of str
        Names of the channels in the OME-TIFF file. Each name corresponds to a TIFF
        file in `input_tiff_paths`. The length of this list must match the number
        of files in `input_tiff_paths`.

    tile_size : int, optional, default=256
        The width and height of tiles in the pyramidal TIFF. Smaller tile sizes
        can improve performance in certain scenarios.

    n_threads : int, optional, default=20
        The number of threads to use for downsampling images and constructing the
        pyramid. Higher values can improve performance on multi-core systems.

    Notes
    -----
    - This function requires a Python script (`pyramid_assemble.py`) located at
      `/mnt/nfs/home/wenruiwu/tools/ome-tiff-pyramid-tools/`.
    - The tile size must be a multiple of 16 to ensure compatibility with most
      TIFF readers.
    - Ensure that the input TIFF files and output directory have the correct
      permissions.
    """
    command = [
        "python",
        path_script,
        *paths_tiff,
        path_ometiff,
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
        logging.info(f"DAPI OME-TIFF generated successfully: {path_ometiff}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during execution: {e}")


def export_ometiff_pyramid_from_dict(
    marker_dict: dict[str, np.ndarray],
    dir_output: str,
    name_output: str,
    **kwargs,
):
    """
    Generate a pyramidal OME-TIFF file from a dictionary of marker images.

    Parameters
    ----------
    marker_dict : dict of str to np.ndarray
        A dictionary where keys are channel names and values are 2D numpy arrays
        representing the marker images.
    dir_output : str
        The directory where the output OME-TIFF file will be saved.
    name_output : str
        The name of the output OME-TIFF file.
    """
    temp_dir = tempfile.mkdtemp(dir=dir_output)

    paths_im = []
    names_im = []
    for name, im in marker_dict.items():
        path_im = os.path.join(temp_dir, f"{name}.tiff")
        tifffile.imwrite(path_im, im)
        paths_im.append(path_im)
        names_im.append(name)
    path_output = os.path.join(dir_output, f"{name_output}.ome.tiff")
    export_ometiff_pyramid(
        paths_tiff=paths_im,
        path_ometiff=path_output,
        channel_names=names_im,
        **kwargs,
    )

    shutil.rmtree(temp_dir)
