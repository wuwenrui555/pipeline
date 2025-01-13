# %%
import logging
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
from pyqupath.ometiff import export_ometiff_pyramid_from_dict
from tqdm import tqdm
from valis import registration

TQDM_FORMAT = "{desc}: {percentage:3.0f}%|{bar:10}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"

# Reference
# https://github.com/MathOnco/valis/issues/154


def setup_logging(
    log_file=os.path.join(os.getcwd(), "output.log"),
    log_format="%(asctime)s - %(levelname)s - %(message)s",
    log_mode="w",
    logger_level=logging.INFO,
    file_handler_level=logging.INFO,
    stream_handler_level=logging.WARNING,
):
    """
    Configures logging to output messages to both a file and the console.

    Parameters
    ----------
    log_file : str, optional
        Path to the log file. Default is 'output.log' in the current working directory.
    log_format : str, optional
        Format for log messages. Default includes timestamp, log level, and message.
    log_mode : str, optional
        File mode for the log file. Default is 'w' (write mode, overwrites file).
    logger_level : int, optional
        Logging level for the root logger. Default is logging.WARNING.
    file_handler_level : int, optional
        Logging level for the FileHandler. Default is logging.INFO.
    stream_handler_level : int, optional
        Logging level for the StreamHandler (console output). Default is logging.WARNING.

    Returns
    -------
    None
        This function configures the logger and does not return any value.

    Notes
    -----
    - The logger level controls the global filtering of messages.
    - The FileHandler writes log messages to a file.
    - The StreamHandler displays log messages in the console.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logger_level)  # Set the logger's global logging level

    # Create a FileHandler for writing logs to a file
    file_handler = logging.FileHandler(log_file, mode=log_mode)
    file_handler.setLevel(file_handler_level)  # Set the level for the file handler
    file_handler.setFormatter(logging.Formatter(log_format))  # Apply the log format

    # Create a StreamHandler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(
        stream_handler_level
    )  # Set the level for the stream handler
    stream_handler.setFormatter(
        logging.Formatter(log_format)
    )  # Apply the same log format

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Optional: Print confirmation to the console
    print(
        f"\nLogging is configured. Logs are saved to: {log_file} and displayed in the console."
    )


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

    # TODO: wrap into valis initialization
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
                total=len(dst_apply_fl) + len(src_apply_fl),
                desc=f"Aligning images ({self.mode})",
                bar_format=self.parent.tqdm_format,
            ) as total_pbar:
                # Align destination images
                self._process_images(
                    slide=self.parent.registrar.get_slide("dst.tiff"),
                    input_files=dst_apply_fl,
                    prefix="dst",
                    total_pbar=total_pbar,
                )

                # Align source images
                self._process_images(
                    slide=self.parent.registrar.get_slide("src.tiff"),
                    input_files=src_apply_fl,
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
