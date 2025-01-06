# %%
# cargo install proseg@1.1.9
import logging
import os

from pycodex import io

import src.proseg as proseg

io.setup_logging(
    file_handler_level=logging.INFO, stream_handler_level=logging.INFO
)


# %%
if __name__ == "__main__":
    path_tx = "/mnt/nfs/storage/CosMX/Indepth_TMA971_section01_v132/AtoMx/flatFiles/Indepth_EBV971_CosMx/Indepth_EBV971_CosMx_tx_file.csv.gz"
    
    dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_voxel-layer=5_cosmx_only_Indepth_TMA971_section01_v132"
    os.makedirs(dir_output, exist_ok=True)
    proseg.proseg(path_tx, dir_output, n_voxel_layer=5, n_threads=20)

    dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_voxel-layer=4_cosmx_only_Indepth_TMA971_section01_v132"
    os.makedirs(dir_output, exist_ok=True)
    proseg.proseg(path_tx, dir_output, n_voxel_layer=4, n_threads=20)

    dir_output = "/mnt/nfs/home/wenruiwu/projects/indepth_cosmx_dlbcl/data/output/proseg_voxel-layer=10_cosmx_only_Indepth_TMA971_section01_v132"
    os.makedirs(dir_output, exist_ok=True)
    proseg.proseg(path_tx, dir_output, n_voxel_layer=10, n_threads=20)