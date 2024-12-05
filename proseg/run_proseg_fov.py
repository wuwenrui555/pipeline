# %%
# cargo install proseg@1.1.9
import logging

from pycodex import io

import src.proseg as proseg

io.setup_logging(
    file_handler_level=logging.INFO, stream_handler_level=logging.INFO
)


# %%
if __name__ == "__main__":
    if False:
        path_tx = "/mnt/nfs/storage/CosMX/Indepth_TMA971_section01_v132/AtoMx/flatFiles/Indepth_EBV971_CosMx/Indepth_EBV971_CosMx_tx_file.csv.gz"
        dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_fov_cosmx_only_Indepth_TMA971_section01_v132"
        proseg.proseg_tma_z_as_voxel_layer(path_tx, dir_output)

    if False:
        path_tx_fov = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_fov_cosmx_only_Indepth_TMA971_section01_v132/001/tx_file.csv"
        dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_test_voxel_layer/"
        voxel_layers = [1, 5, 9, 20]
        proseg.proseg_with_different_voxel_layers(
            path_tx_fov,
            dir_output,
            voxel_layers,
        )

    if True:
        path_tx = "/mnt/nfs/storage/CosMX/AIH_TMA001_section05_v132/AtoMx/flatFiles/AIH_TMA001_section05_v132/AIH_TMA001_section05_v132_tx_file.csv.gz"
        dir_output = "/mnt/nfs/home/wenruiwu/projects/guanrui_aih/data/output/proseg_fov_AIH_TMA001_section05_v132"
        proseg.proseg_tma_z_as_voxel_layer(
            path_tx, dir_output, fovs=[3, 4, 5, 9, 10, 11, 13, 16, 19]
        )
