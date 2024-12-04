# %%
# cargo install proseg@1.1.9
import logging
import os

import pandas as pd
from pycodex import io
from tqdm import tqdm

from src.proseg import run_proseg_fov

io.setup_logging(
    file_handler_level=logging.INFO, stream_handler_level=logging.INFO
)


def proseg_tma_z_as_voxel_layer(path_tx, dir_output):
    """
    Run proseg on TMA for each FOV with the z-layer as the voxel layer.
    """
    df_tx = pd.read_csv(path_tx)
    for fov in tqdm(df_tx["fov"].unique()):
        # Create a directory for the FOV
        dir_fov = os.path.join(dir_output, f"{fov:03d}")
        os.makedirs(dir_fov, exist_ok=True)

        # Save the transcript file for the FOV
        path_tx_fov = os.path.join(dir_fov, "tx_file.csv")
        df_tx_fov = df_tx[df_tx["fov"] == fov].reset_index(drop=True)
        df_tx_fov.to_csv(path_tx_fov, index=False)

        # Get the z-layer
        z = sorted(df_tx_fov["z"].unique())
        z_layer = len(z)

        # Run proseg
        run_proseg_fov(
            dir_output_fov=dir_fov,
            path_tx_fov=path_tx_fov,
            n_voxel_layer=z_layer,
        )
        logging.info(f"Proseg executed successfully for FOV {fov:03d}.")


def proseg_fov_with_different_voxel_layers(
    path_tx_fov, dir_output, voxel_layers
):
    """
    Run proseg on FOV with different voxel layers.
    """
    for voxel_layer in voxel_layers:
        # Create a directory for results
        dir_fov = os.path.join(dir_output, f"voxel_layers={voxel_layer:02d}")
        os.makedirs(dir_fov, exist_ok=True)

        # Run proseg
        run_proseg_fov(
            dir_output_fov=dir_fov,
            path_tx_fov=path_tx_fov,
            n_voxel_layer=voxel_layer,
        )
        logging.info(
            f"Proseg executed successfully with voxel_layers={voxel_layer:02d}."
        )


# %%

if __name__ == "__main__":
    # path_tx = "/mnt/nfs/storage/CosMX/Indepth_TMA971_section01_v132/AtoMx/flatFiles/Indepth_EBV971_CosMx/Indepth_EBV971_CosMx_tx_file.csv.gz"
    # dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_fov_cosmx_only_Indepth_TMA971_section01_v132"
    # proseg_z_as_voxel_layer(path_tx, dir_output)

    path_tx_fov = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_fov_cosmx_only_Indepth_TMA971_section01_v132/001/tx_file.csv"
    dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_test_voxel_layer/"
    voxel_layers = [1, 5, 9, 20]
    proseg_fov_with_different_voxel_layers(
        path_tx_fov,
        dir_output,
        voxel_layers,
    )
