
## 01_alignment_parameter.xlsx

This `xlsx` file is designed to store parameters for alignment between two runs and contains the following columns:

- `id`: A unique identifier for each pair of alignments. 
- `dir_dst`: Path to directory containing destination images.
- `dir_src`: Path to directory containing source images will be aligned to the coordinates of the destination images.
- `path_parameter`: Path to the `sift_parameter.pkl` file storing parameters for the SIFT alignment process, generated iteratively using the `01_sift_plot_src_on_dst_coordinate.ipynb` notebook. 
- `dir_output`: Path to directory where the alignment results are saved.
- `src_rot90cw`: A number indicating how many times the source images should be rotated 90 degrees clockwise before alignment.
- `src_hflip`: A flag (TRUE or FALSE) indicating whether the source images should be horizontally flipped before alignment.
- `name_output_dst`: The name of subfolder under `dir_output` for saving output of the processed destination images.
- `name_output_src`: The name of subfolder under `dir_output` for saving output of the aligned source images.

### Example Values

| Column | Example |
|--------|---------|
| `id` | TMA543_run1=reg001_run2=reg021 |
| `dir_dst` | /mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA543-run1/images/final/reg001/ |
| `dir_src` | /mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA543-run2/images/final/reg021/ |
| `path_parameter` | /mnt/nfs/home/shuliluo/Projects/codex_wenrui/alignment/output-formal/TMA543/run1-reg001_run2-reg021/sift_parameter.pkl |
| `dir_output` | /mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/01_alignment/ |
| `src_rot90cw` | 1 |
| `src_hflip` | FALSE |
| `name_output_dst` | run1 |
| `name_output_src` | run2 |

### File Structure 

#### Input
```
dir_dst
├── marker_1.tif
└── marker_2.tif

dir_src
├── marker_3.tif
└── marker_4.tif
```

#### Output
```
dir_output
├── id_1
│   ├── name_output_dst_1
│   │   ├── marker_1.tiff
│   │   └── marker_2.tiff
│   └── name_output_src_1
│       ├── marker_3.tiff
│       └── marker_4.tiff
└── id_2
    ├── name_output_dst_2
    │   ├── marker_1.tiff
    │   └── marker_2.tiff
    └── name_output_src_2
        ├── marker_3.tiff
        └── marker_4.tiff
```