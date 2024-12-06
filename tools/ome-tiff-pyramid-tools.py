# %%
import logging
import subprocess


def export_ometiff_pyramid(
    input_tiff_paths: list[str],
    output_ometiff_path: str,
    channel_names: list[str],
    tile_size: int = 256,
    n_threads: int = 20,
):
    """
    Generate a pyramidal OME-TIFF file from multiple input TIFF files.

    This function combines multiple input TIFF files into a single multi-channel
    OME-TIFF file, adds channel metadata, and builds a multi-resolution pyramid
    for efficient visualization and processing.
    ( https://github.com/labsyspharm/ome-tiff-pyramid-tools)

    Parameters
    ----------
    input_tiff_paths : list of str
        A list of file paths to the input TIFF images. Each file corresponds
        to a specific channel in the final OME-TIFF.

    output_ometiff_path : str
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
    path_script = (
        "/mnt/nfs/home/wenruiwu/tools/ome-tiff-pyramid-tools/pyramid_assemble.py"
    )
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
