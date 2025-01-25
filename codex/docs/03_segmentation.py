# conda activate cellSeg_test
import logging
from itertools import product
from pathlib import Path

from tqdm import tqdm

from pycodex.io import setup_gpu, setup_logging
from pycodex.segmentation import run_segmentation_mesmer

TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


def run_segmentation_batch(dir_root: str) -> None:
    """
    Run segmentation on a batch of regions.

    Parameters
    ----------
    dir_root : str
        Root directory of the regions, where each region is a subdirectory.
    """
    ############################################################################
    # Parameters
    boundary_markers = ["CD45", "CD3e", "CD163", "NaKATP"]
    internal_markers = ["DAPI"]
    pixel_size_um = 0.3775202  # Keyence
    # pixel_size_um = 0.5068164319979996  # Fusion
    scale = True
    q_min = 0
    q_max = 0.99
    maxima_threshold = 0.075  # larger for fewer cells. Defaults to 0.075.
    interior_threshold = 0.20  # larger for larger cells. Defaults to 0.20.
    compartment = "whole-cell"
    tag = "20250125_whole_cell"
    ###########################################################################

    dir_root = Path(dir_root)
    dirs_region = [
        dir
        for dir in list(Path(dir_root).glob("*"))
        if dir.is_dir() and dir.name not in ["logs", "params"]
    ]

    for dir_region in tqdm(dirs_region, total=len(dirs_region)):
        dir_region = Path(dir_region)
        try:
            run_segmentation_mesmer(
                output_dir=dir_region,
                boundary_markers=boundary_markers,
                internal_markers=internal_markers,
                pixel_size_um=pixel_size_um,
                q_min=q_min,
                q_max=q_max,
                scale=scale,
                maxima_threshold=maxima_threshold,
                interior_threshold=interior_threshold,
                compartment=compartment,
                tag=tag,
            )
            logging.info(f"Segmentation completed: {dir_region.name}")
        except Exception as e:
            logging.error(f"Segmentation Failed {dir_region.name}: {e}")


def run_segmentation_test_params() -> None:
    """
    Run segmentation on a test region.
    """
    ############################################################################
    # Parameters
    boundary_markers = ["NaKATP"]
    internal_markers = ["DAPI"]
    compartment = "whole-cell"
    pixel_size_um = 0.3775202  # Keyence
    # pixel_size_um = 0.5068164319979996  # Fusion
    scale = True
    q_min = 0
    q_max = 0.99
    ###########################################################################

    # Parameters to test
    maxima_thresholds = [0.001, 0.075, 0.2, 0.5, 1, 10, 100]
    interior_thresholds = [0.001, 0.10, 0.2, 0.5, 1, 10, 100]

    dir_root = Path(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/05_marker_ometiff"
    )
    regions = [
        "TMA544_run1=reg004_run2=reg006",
        "TMA544_run1=reg018_run2=reg014",
        "TMA544_run1=reg011_run2=reg023",
        "TMA544_run1=reg014_run2=reg008",
    ]

    parameters = list(product(regions, maxima_thresholds, interior_thresholds))
    for region, maxima_threshold, interior_threshold in tqdm(
        parameters,
        desc="Segmentation",
        bar_format=TQDM_FORMAT,
    ):
        dir_region = dir_root / region
        tag = f"20250105_maxima_{maxima_threshold}_interior_{interior_threshold}"
        try:
            run_segmentation_mesmer(
                output_dir=dir_region,
                boundary_markers=boundary_markers,
                internal_markers=internal_markers,
                pixel_size_um=pixel_size_um,
                q_min=q_min,
                q_max=q_max,
                scale=scale,
                maxima_threshold=maxima_threshold,
                interior_threshold=interior_threshold,
                compartment=compartment,
                tag=tag,
            )
            logging.info(f"Segmentation completed: {dir_region.name}")
        except Exception as e:
            logging.error(f"Segmentation Failed {dir_region.name}: {e}")


def run_segmentation_test() -> None:
    """
    Run segmentation on a test region.
    """
    ############################################################################
    # Parameters
    boundary_markers = ["CD45", "CD3e", "CD163", "NaKATP"]
    internal_markers = ["DAPI"]
    compartment = "whole-cell"
    pixel_size_um = 0.3775202  # Keyence
    # pixel_size_um = 0.5068164319979996  # Fusion
    scale = True
    q_min = 0
    q_max = 0.99
    tag = "20250115_run1"
    ###########################################################################

    # Parameters to test
    # maxima_thresholds = [0.001, 0.075, 0.2, 0.5, 1, 10, 100]
    # interior_thresholds = [0.001, 0.10, 0.2, 0.5, 1, 10, 100]
    maxima_thresholds = [0.075]
    interior_thresholds = [0.20]

    dir_root = Path(
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/05_marker_ometiff"
    )
    regions = [
        "TMA544_run1=reg004_run2=reg006",
        "TMA544_run1=reg018_run2=reg014",
        "TMA544_run1=reg011_run2=reg023",
        "TMA544_run1=reg014_run2=reg008",
    ]

    parameters = list(product(regions, maxima_thresholds, interior_thresholds))
    for region, maxima_threshold, interior_threshold in tqdm(
        parameters,
        desc="Segmentation",
        bar_format=TQDM_FORMAT,
    ):
        dir_region = dir_root / region
        try:
            run_segmentation_mesmer(
                output_dir=dir_region,
                boundary_markers=boundary_markers,
                internal_markers=internal_markers,
                pixel_size_um=pixel_size_um,
                q_min=q_min,
                q_max=q_max,
                scale=scale,
                maxima_threshold=maxima_threshold,
                interior_threshold=interior_threshold,
                compartment=compartment,
                tag=tag,
            )
            logging.info(f"Segmentation completed: {dir_region.name}")
        except Exception as e:
            logging.error(f"Segmentation Failed {dir_region.name}: {e}")


if False:
    path_log = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_rcc_test_params.log"
    setup_logging(path_log)
    setup_gpu("0,1,2,3")
    run_segmentation_test()
    run_segmentation_test_params()

if True:
    dir_root = (
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250116_ometiff/"
    )
    path_log = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250125_segmentation.log"
    setup_logging(path_log)
    setup_gpu("0,1,2,3")
    run_segmentation_batch(dir_root)

# TODO: output a mask label to show the segmenation geojson is ok
