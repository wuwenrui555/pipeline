# conda activate cellSeg_test
import logging
from itertools import product
from pathlib import Path

from tqdm import tqdm

from pycodex.io import setup_gpu, setup_logging
from pycodex.segmentation import run_segmentation_mesmer


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
    tag = "20250103_run1"
    ###########################################################################

    dir_root = Path(dir_root)
    dirs_region = [dir for dir in list(Path(dir_root).glob("*")) if dir.is_dir()]

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
    boundary_markers = ["NaKATP"]
    internal_markers = ["DAPI"]
    pixel_size_um = 0.3775202  # Keyence
    # pixel_size_um = 0.5068164319979996  # Fusion
    scale = True
    q_min = 0
    q_max = 0.99
    tag = "20250103_run1"
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

    for region in regions:
        dir_region = dir_root / region
        generator_parameter = product(maxima_thresholds, interior_thresholds)
        for maxima_threshold, interior_threshold in generator_parameter:
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
                    tag=tag,
                )
                logging.info(f"Segmentation completed: {dir_region.name}")
            except Exception as e:
                logging.error(f"Segmentation Failed {dir_region.name}: {e}")


if False:
    dir_root = (
        "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/05_marker_ometiff"
    )
    path_log = "/mnt/nfs/home/wenruiwu/pipeline/pycodex/segmentation/practice/20250103_shuli_rcc.log"

    setup_gpu("0,1,2,3")
    setup_logging(path_log)
    run_segmentation_batch(dir_root)

if True:
    setup_gpu("0,1,2,3")
    run_segmentation_test()
