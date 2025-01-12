# %%
import os
import pickle as pkl
import shutil
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tifffile
from matplotlib.patches import Patch
from pyqupath.ometiff import export_ometiff_pyramid_from_dict, load_tiff_to_dict
from tqdm import tqdm
from valis import registration

TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:10}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"

# Reference
# https://github.com/MathOnco/valis/issues/154


class ValisAligner:
    def __init__(
        self,
        dst_register_f: Union[str, Path],
        src_register_f: Union[str, Path],
        output_dir: Union[str, Path],
        tqdm_format: str = "{desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    ):
        """
        Initialize ValisAligner

        Parameters
        ----------

        dst_register_f : Union[str, Path]
            Path to the destination image file for registration.
        src_register_f : Union[str, Path]
            Path to the source image file for registration.
        output_dir : Union[str, Path]
            Path to the output directory.
        tqdm_format : str, optional
            Format for tqdm progress bar.
        """
        self.dst_register_f = Path(dst_register_f)
        self.src_register_f = Path(src_register_f)
        self.output_dir = Path(output_dir)
        self.tqdm_format = tqdm_format

        # Register the source image to the destination image
        ## Initialize directories
        self.valis_dir = self.output_dir / "valis"
        self._setup_directories()

        ## Copy input files
        shutil.copy(self.dst_register_f, self.valis_dir / "input" / "dst.tiff")
        shutil.copy(self.src_register_f, self.valis_dir / "input" / "src.tiff")

        ## Initialize registrar
        self.registrar = registration.Valis(
            src_dir=str(self.valis_dir / "input"),
            dst_dir=str(self.valis_dir / "output"),
            reference_img_f=str(self.valis_dir / "input" / "dst.tiff"),
            align_to_reference=True,
        )
        _, _, self.error_df = self.registrar.register()
        registration.kill_jvm()

        ## Initialize aligners
        self.rigid = self.AlignBase(self, non_rigid=False)
        self.non_rigid = self.AlignBase(self, non_rigid=True)

        # Save the instance
        with open(self.valis_dir / "intermediate" / "valis_aligner.pkl", "wb") as f:
            pkl.dump(self, f)

    def _setup_directories(self):
        """Create required directories"""
        valis_dir_input = self.valis_dir / "input"
        valis_dir_output = self.valis_dir / "output"
        valis_dir_inter = self.valis_dir / "intermediate"
        for d in [valis_dir_input, valis_dir_output, valis_dir_inter]:
            d.mkdir(parents=True, exist_ok=True)

    def plot_overlap(
        self,
        original: bool = True,
        rigid: bool = True,
        non_rigid: bool = True,
        w_sub: float = 5,
        h_sub: float = 5,
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Plot the overlap images

        Parameters
        ----------
        original : bool, optional
            Whether to plot the original overlap image, by default True.
        rigid : bool, optional
            Whether to plot the rigid overlap image, by default True.
        non_rigid : bool, optional
            Whether to plot the non-rigid overlap image, by default True.
        w_sub : int, optional
            Figure width for each subplot, by default 5.
        h_sub : int, optional
            Figure height for each subplot, by default 5.

        Returns
        -------
        tuple[plt.Figure, plt.Axes]
            Figure and Axes objects
        """
        # Image to plot
        idx = [original, rigid, non_rigid]
        title_l = ["Original overlap", "Rigid overlap", "Non-rigid overlap"]
        img_l = [
            self.registrar.original_overlap_img,
            self.registrar.rigid_overlap_img,
            self.registrar.non_rigid_overlap_img,
        ]
        p_img_l = [img for img, include in zip(img_l, idx) if include]
        p_title_l = [title for title, include in zip(title_l, idx) if include]

        # Plot
        n_axs = sum(idx)
        fig, axs = plt.subplots(1, n_axs, figsize=(n_axs * w_sub, h_sub))
        axs = axs.flatten()
        for i, img, title in zip(range(n_axs), p_img_l, p_title_l):
            axs[i].imshow(img)
            axs[i].set_title(title)
            axs[i].axis("off")

        ## Add color legend
        legend_elements = [
            Patch(facecolor="#FF3EBC", label="Destination", edgecolor="black"),
            Patch(facecolor="#0EF64E", label="Source", edgecolor="black"),
        ]
        fig.legend(
            handles=legend_elements,
            loc="upper center",
            ncol=2,
            bbox_to_anchor=(0.5, 0),
        )

        plt.tight_layout()

        return fig, axs

    class AlignBase:
        def __init__(self, parent, non_rigid: bool):
            self.parent = parent
            self.non_rigid = non_rigid
            self.mode = "non_rigid" if non_rigid else "rigid"
            self.output_dir = parent.output_dir / f"registered_{self.mode}"
            self._setup_directories()

            self.registered_fl = []

        def _setup_directories(self):
            """Create required directories"""
            self.ometiff_dir = self.output_dir / "ometiff"
            self.temp_dir = self.output_dir / "temp"
            for d in [self.ometiff_dir, self.temp_dir]:
                d.mkdir(parents=True, exist_ok=True)

        def apply(
            self,
            dst_apply_fl: list[Union[str, Path]],
            src_apply_fl: list[Union[str, Path]],
        ):
            """
            Apply the registration to the source and destination images

            Parameters
            ----------
            dst_apply_fl : list[Union[str, Path]]
                Path to the destination image files for applying registration0
            src_apply_fl : list[Union[str, Path]]
                Path to the source image files for applying registration.
            """
            dst_apply_fl = [Path(f) for f in dst_apply_fl]
            src_apply_fl = [Path(f) for f in src_apply_fl]

            with tqdm(
                total=len(dst_apply_fl) + len(src_apply_fl) + 2,
                desc=f"Aligning images ({self.mode})",
                bar_format=self.parent.tqdm_format,
            ) as total_pbar:
                # Align destination images
                self._process_images(
                    slide=self.parent.registrar.get_slide("dst.tiff"),
                    input_files=[self.parent.dst_register_f] + dst_apply_fl,
                    prefix="dst",
                    total_pbar=total_pbar,
                )

                # Align source images
                self._process_images(
                    slide=self.parent.registrar.get_slide("src.tiff"),
                    input_files=[self.parent.src_register_f] + src_apply_fl,
                    prefix="src",
                    total_pbar=total_pbar,
                )

                # Create overlap mask
                self._create_overlap_mask()

        def _process_images(self, slide, input_files, prefix, total_pbar):
            """
            Process and register images
            """
            for f in input_files:
                registered_f = self.ometiff_dir / f"{prefix}_{f.stem}.ome.tiff"
                if registered_f.exists():
                    print(f"File exists and skip: {registered_f}")
                else:
                    slide.warp_and_save_slide(
                        src_f=str(f),
                        dst_f=str(registered_f),
                        crop="reference",
                        non_rigid=self.non_rigid,
                    )
                if registered_f not in self.registered_fl:
                    self.registered_fl.append(registered_f)
                total_pbar.update(1)
            # ValisAligner.AlignBase._process_images = _process_images

        def _create_overlap_mask(self):
            """
            Create overlap mask for the region after registration
            """
            src_mask_f = self.temp_dir / "src_mask.tiff"
            src_mask_aligned_f = self.temp_dir / "src_mask_aligned.ome.tiff"
            if src_mask_aligned_f.exists():
                print(f"File exists and skip: {src_mask_aligned_f}")
            else:
                with tifffile.TiffFile(self.parent.src_register_f) as tif:
                    src_mask = np.ones(tif.pages[0].shape, dtype=np.uint16)
                    tifffile.imwrite(src_mask_f, src_mask)

                    src_slide = self.parent.registrar.get_slide("src.tiff")
                    src_slide.warp_and_save_slide(
                        src_f=str(src_mask_f),
                        dst_f=str(src_mask_aligned_f),
                        crop="reference",
                        non_rigid=self.non_rigid,
                    )
            self.mask_overlap = tifffile.imread(src_mask_aligned_f)
            # ValisAligner.AlignBase._create_overlap_mask = _create_overlap_mask

        def get_metadata(self) -> pd.DataFrame:
            """
            Get metadata of registered images
            """
            metadata_df = pd.DataFrame(
                {
                    "registered_f": self.registered_fl,
                    "f_name": [
                        f.name.replace(".ome.tiff", "") for f in self.registered_fl
                    ],
                    "channel_name": "",
                }
            )
            return metadata_df

        def write_metadata(self, output_f: Union[str, Path]):
            """
            Write the metadata to a CSV file

            Parameters
            ----------
            output_f : Union[str, Path]
                Path to the output CSV file
            """
            metadata_df = self.get_metadata()
            metadata_df.to_csv(str(output_f), index=False)

        def write_ometiff(
            self,
            output_f: Union[str, Path],
            f_names: list[str],
            channel_names: list[str],
        ):
            """
            Write the registered images to an OME-TIFF file

            Parameters
            ----------
            output_f : Union[str, Path]
                Path to the output OME-TIFF file. If the file already exists, the
                process will terminate to prevent overwriting.
            f_names : list[str]
                List of file names in the metadata you want embed in the OME-TIFF.
            channel_names : list[str]
                List of channel names
            """
            metadata_df = self.get_metadata().set_index("f_name")
            if sum(metadata_df.index.duplicated()) > 0:
                raise ValueError("Duplicated file names in the metadata")

            img_fl = metadata_df.loc[f_names]["registered_f"].tolist()
            img_dict = {
                channel_name: tifffile.imread(img_f) * self.mask_overlap
                for img_f, channel_name in zip(img_fl, channel_names)
            }
            export_ometiff_pyramid_from_dict(img_dict, str(output_f), channel_names)


id = "RCC_TMA544_run1=reg014_run2=reg008"

dst_register_f = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA544-run1/images/final/reg014/reg014_cyc001_ch001_Ch1Cy1.tif"
src_register_f = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA544-run2/images/final/reg008/reg008_cyc001_ch001_Ch1Cy1.tif"

dst_apply_fl = [
    "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA544-run1/images/final/reg014/reg014_cyc002_ch001_Ch1Cy2.tif",
    "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA544-run1/images/final/reg014/reg014_cyc020_ch003_CD45.tif",
]
src_apply_fl = [
    "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA544-run2/images/final/reg008/reg008_cyc002_ch003_CD3e.tif",
]

output_dir = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/999_test"

f_names = [
    "dst_reg014_cyc002_ch001_Ch1Cy2",
    "dst_reg014_cyc020_ch003_CD45",
    "src_reg008_cyc001_ch001_Ch1Cy1",
    "src_reg008_cyc002_ch003_CD3e",
]
channel_names = ["DAPI_dst", "CD45", "DAPI_src", "CD3e"]
# %%
valis_aligner = ValisAligner(
    dst_register_f=dst_register_f,
    src_register_f=src_register_f,
    output_dir=output_dir,
)
# %%
valis_aligner_f = "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/999_test/valis/intermediate/valis_aligner.pkl"
with open(valis_aligner_f, "rb") as f:
    valis_aligner = pkl.load(f)

# %%
valis_aligner.rigid.apply(dst_apply_fl=dst_apply_fl, src_apply_fl=src_apply_fl)
output_f = valis_aligner.rigid.output_dir / f"{id}.ome.tiff"
if output_f.exists():
    os.remove(output_f)
valis_aligner.rigid.write_ometiff(output_f, f_names, channel_names)


valis_aligner.non_rigid.apply(dst_apply_fl=dst_apply_fl, src_apply_fl=src_apply_fl)
output_f = valis_aligner.non_rigid.output_dir / f"{id}.ome.tiff"
if output_f.exists():
    os.remove(output_f)
valis_aligner.non_rigid.write_ometiff(output_f, f_names, channel_names)


# %%
fig, axs = valis_aligner.plot_overlap()

# %%
img_dict_valis_non_rigid = load_tiff_to_dict(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/999_test/registered_non_rigid/RCC_TMA544_run1=reg014_run2=reg008.ome.tiff",
    filetype="ome.tiff",
)
img_dict_valis_rigid = load_tiff_to_dict(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/999_test/registered_rigid/RCC_TMA544_run1=reg014_run2=reg008.ome.tiff",
    filetype="ome.tiff",
)
img_dict_sift = load_tiff_to_dict(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/03_dapi/TMA544_run1=reg014_run2=reg008.ome.tiff",
    filetype="ome.tiff",
)

y_min = 5225
x_min = 1835
length = 50


def rgb_ndarray(img_dst, img_src, y_min, x_min, length):
    # Define the region of interest
    roi_dst = img_dst[y_min : (y_min + length), x_min : (x_min + length)]
    roi_src = img_src[y_min : (y_min + length), x_min : (x_min + length)]

    # Normalize the images to [0, 1] for visualization
    roi_dst_norm = roi_dst / roi_dst.max() if roi_dst.max() != 0 else roi_dst
    roi_src_norm = roi_src / roi_src.max() if roi_src.max() != 0 else roi_src

    # Create an RGB overlay
    overlay = np.zeros((*roi_dst.shape, 3))  # Initialize an RGB image
    overlay[..., 0] = roi_dst_norm  # Red channel for `DAPI_dst`
    overlay[..., 1] = roi_src_norm  # Green channel for `DAPI_src`

    return overlay


overlay_valis_non_rigid = rgb_ndarray(
    img_dict_valis_non_rigid["DAPI_dst"],
    img_dict_valis_non_rigid["DAPI_src"],
    y_min,
    x_min,
    length,
)
overlay_valis_rigid = rgb_ndarray(
    img_dict_valis_rigid["DAPI_dst"],
    img_dict_valis_rigid["DAPI_src"],
    y_min,
    x_min,
    length,
)
overlay_sift = rgb_ndarray(
    img_dict_sift["run1-Ch1Cy2"],
    img_dict_sift["run2-Ch1Cy1"],
    y_min,
    x_min,
    length,
)


fig, axs = plt.subplots(1, 3, figsize=(15, 5))
axs[0].imshow(overlay_valis_non_rigid)
axs[0].set_title("Valis Alignment (non-rigid)")
axs[1].imshow(overlay_valis_rigid)
axs[1].set_title("Valis Alignment (rigid)")
axs[2].imshow(overlay_sift)
axs[2].set_title("SIFT Alignment")

## Add color legend
legend_elements = [
    Patch(facecolor="#FF0000", label="Destination", edgecolor="black"),
    Patch(facecolor="#00FF00", label="Source", edgecolor="black"),
]
fig.legend(
    handles=legend_elements,
    loc="upper center",
    ncol=2,
    bbox_to_anchor=(0.5, 0),
)

plt.tight_layout()

# %%
mask = tifffile.imread(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/999_test/registered_non_rigid/temp/src_mask.tiff"
)
mask_aligned = tifffile.imread(
    "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/999_test/registered_non_rigid/temp/src_mask_aligned.ome.tiff"
)
mask[0, 0] = 0
fig, axs = plt.subplots(1, 2, figsize=(10, 5))
axs[0].imshow(mask)
axs[0].set_title("Mask with same size")
axs[1].imshow(mask_aligned)
axs[1].set_title("Mask after alignment")

# %%
error_df = pd.concat(
    [
        valis_aligner.error_df.iloc[[1]].assign(id=id),
        # valis_aligner.error_df.iloc[[1]].assign(id="id1"),
        # valis_aligner.error_df.iloc[[1]].assign(id="id2"),
    ]
)


# %%
def plot_dodge_points(
    error_df,
    metrics=["original_D", "rigid_D", "non_rigid_D"],
    x_col="id",
    colors=None,
    markers=None,
    bar_width=0.1,
    figsize=(10, 6),
    y_label="Distance (D)",
    ax=None,
):
    """
    Generate a dodge point plot for the given DataFrame.

    Parameters:
    ----------
    error_df : pd.DataFrame
        DataFrame containing the data to plot.
    metrics : list[str]
        List of column names representing the metrics to plot.
    x_col : str, optional
        Column name for the x-axis labels (default is "id").
    colors : list[str], optional
        List of colors for the metrics (default is None, will use default colors).
    markers : list[str], optional
        List of marker styles for the metrics (default is None, will use ["o", "s", "D"]).
    bar_width : float, optional
        Dodge distance between points (default is 0.1).
    figsize : tuple, optional
        Figure size (default is (10, 6)).
    y_label : str, optional
        Label for the y-axis (default is "Distance (D)").

    Returns:
    -------
    fig, ax : tuple or AxesSubplot
        If `ax` is None, returns (fig, ax). Otherwise, returns ax.
    """
    error_df = error_df.copy().reset_index(drop=True)

    x = np.arange(len(error_df))  # Numeric positions for x-axis
    if colors is None:
        colors = ["green", "green", "green"]
    if markers is None:
        markers = ["o", "s", "D"]

    # Create the figure and axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        return_ax = False
    else:
        return_ax = True

    for i, metric in enumerate(metrics):
        for j in x:
            # Determine color based on whether this is the minimum value
            color = colors[i]
            if error_df.loc[j, metric] == min(error_df.loc[j, metrics]):
                color = "red"  # Highlight the minimum value

            # Plot each point
            ax.scatter(
                j + (i - 1) * bar_width,  # Dodge position
                error_df.loc[j, metric],
                color=color,
                marker=markers[i],
                label=metric if j == 0 else "",  # Only add label once
                s=80,
            )

    # Customize the plot
    ax.set_xticks(x)
    ax.set_xticklabels(error_df[x_col], rotation=90)
    ax.set_ylabel(y_label)
    ax.legend(
        loc="center left",  # Position relative to the bounding box
        bbox_to_anchor=(1.02, 0.5),
    )
    # Add padding to x-axis limits
    x_padding = 0.5  # Adjust this value to control the padding
    ax.set_xlim(
        -x_padding, len(x) - 1 + x_padding
    )  # Add padding to both sides of the x-axis

    ax.grid(axis="y", linestyle="--", alpha=0.7)

    if return_ax:
        return ax
    else:
        plt.tight_layout()
        return fig, ax


# Example usage

fig, axs = plt.subplots(1, 2, figsize=(8, 10))
axs[0] = plot_dodge_points(
    error_df,
    metrics=["original_D", "rigid_D", "non_rigid_D"],
    bar_width=0.3,
    figsize=(3, 6),
    y_label="Distance (D)",
    ax=axs[0],
)
axs[1] = plot_dodge_points(
    error_df,
    metrics=["original_rTRE", "rigid_rTRE", "non_rigid_rTRE"],
    bar_width=0.3,
    figsize=(3, 6),
    y_label="Relative Target Registration Error (rTRE)",
    ax=axs[1],
)
plt.tight_layout()
# %%
