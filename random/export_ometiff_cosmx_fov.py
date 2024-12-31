from collections import OrderedDict

import numpy as np
import tifffile
from pyqupath.ometiff import export_ometiff_pyramid_from_dict
from pathlib import Path


dir_cosmx_fov = "/mnt/nfs/home/wenruiwu/projects/valis/RCC_TMA542_section05_v132_1104_morphology2d_dapi_500/fov/output_morphology2d/output/FOV000012/"
path_ometiff = "/mnt/nfs//home/wenruiwu/TMA542_FOV012_annotation.ome.tiff"


def export_ometiff_cosmx_fov(dir_cosmx_fov: str, path_ometiff: str) -> None:
    """
    Export an OME-TIFF for CosMx FOV.

    Parameters
    ----------
    dir_cosmx_fov : str
        Directory containing CoSMx FOV images, including H&E staining and CosMx
        markers (DAPI, CD45, CD298_B2M, CD68, and PanCK).
    path_ometiff : str
        Path to save the OME-TIFF.
    """
    dir_cosmx_fov = Path(dir_cosmx_fov)

    marker_dict = OrderedDict()

    # RGB of H&E
    im_he = tifffile.imread(dir_cosmx_fov / "HE.tiff")
    for i in range(3):
        marker_dict[["HE_R", "HE_G", "HE_B"][i]] = im_he[:, :, i].astype(np.uint16)

    # CosMx markers
    marker_dict["DAPI"] = tifffile.imread(dir_cosmx_fov / "DAPI.tiff")
    marker_dict["CD45"] = tifffile.imread(dir_cosmx_fov / "CD45.tiff")
    marker_dict["CD298_B2M"] = tifffile.imread(dir_cosmx_fov / "CD298_B2M.tiff")
    marker_dict["CD68"] = tifffile.imread(dir_cosmx_fov / "CD68.tiff")
    marker_dict["PanCK"] = tifffile.imread(dir_cosmx_fov / "PanCK.tiff")

    export_ometiff_pyramid_from_dict(marker_dict, path_ometiff)


export_ometiff_cosmx_fov(dir_cosmx_fov, path_ometiff)
