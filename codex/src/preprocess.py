import os
import re
from pathlib import Path

import pandas as pd
from pyqupath.ometiff import export_ometiff_pyramid
from tqdm import tqdm

from pycodex.cls import MarkerMetadata


class KeyencePreprocessor:
    def __init__(self, dir_root):
        """
        Initialize the Keyence data preprocessing.

        Parameters
        ----------
        dir_root : str
            Root directory of the organized images of the Keyence data.
        """
        self.dir_root = Path(dir_root)

        metadatas = MarkerMetadata(dir_root)
        metadatas.organize_metadata(platform="keyence", subfolders=True)
        metadatas.summary_metadata()
        self.metadatas = metadatas

    def export_dapi_ometiff_and_metadata(self, dir_output):
        """
        Export DAPI OME-TIFF and metadata for each region.

        Parameters
        ----------
        dir_output : str
            Output directory for the DAPI OME-TIFF and metadata.
        """
        dir_output = Path(dir_output)
        dir_output.mkdir(exist_ok=True, parents=True)

        dir_output_ometiff = dir_output / "ometiff"
        dir_output_ometiff.mkdir(exist_ok=True, parents=True)
        for region in tqdm(self.metadatas.regions):
            print(f"Exporting DAPI OME-TIFF for: {region}")

            def is_dapi(x):
                """Check if the marker is DAPI"""
                return re.search(r"^Ch\d+Cy\d+$", x) is not None

            metadata_region = self.metadatas.metadata[region]
            idx = metadata_region["marker"].apply(is_dapi)
            paths_dapi = metadata_region["path"][idx].tolist()
            names_dapi = metadata_region["marker"][idx].tolist()

            path_ometiff = dir_output_ometiff / f"{region}_dapi.ome.tiff"
            if path_ometiff.exists():
                os.remove(path_ometiff)
            export_ometiff_pyramid(
                paths_tiff=paths_dapi,
                path_ometiff=str(path_ometiff),
                channel_names=names_dapi,
            )

        # Export metadata
        df_dapi = pd.DataFrame({"region": self.metadatas.regions, "dapi": ""})
        df_dapi.to_csv(dir_output / "metadata_dapi.csv", index=False)

        valid_markers = [
            marker for marker in self.metadatas.unique_markers if not is_dapi(marker)
        ]
        df_marker = pd.DataFrame({"marker": valid_markers, "channel_name": ""})
        df_marker.to_csv(dir_output / "metadata_marker.csv", index=False)

    def export_ometiff(
        self,
        dir_output: str,
        df_metadata_dapi: pd.DataFrame,
        df_metadata_marker: pd.DataFrame,
    ):
        """
        Export OME-TIFF files for each region based on metadata.

        Parameters
        ----------
        dir_output : str
            Directory where the output OME-TIFF files will be saved.
        df_metadata_dapi : pd.DataFrame
            DataFrame containing selected DAPI channel for each region.
            - Columns: ["region", "dapi"]
        df_metadata_marker : pd.DataFrame
            DataFrame containing marker order and corresponding names.
            - Columns: ["marker", "channel_name"]
        """
        dir_output = Path(dir_output)

        # Channel order and names
        channels_name = df_metadata_marker["marker"].str.strip()
        channels_rename = df_metadata_marker["channel_name"].str.strip()

        ## Validate unique markers in metadata
        if channels_name.duplicated().any():
            duplicated_markers = channels_name[channels_name.duplicated()].tolist()
            raise ValueError(f"Duplicated markers metadata: {duplicated_markers}")

        # Construct a dictionary of channels for each region
        channels_dict = {
            row["region"]: {
                "channels_name": [row["dapi"]] + channels_name.tolist(),
                "channels_rename": ["DAPI"] + channels_rename.tolist(),
            }
            for _, row in df_metadata_dapi.iterrows()
        }

        # Iterate through each region and export OME-TIFF
        for region, channel_info in tqdm(channels_dict.items()):
            print(f"Exporting OME-TIFF for: {region}")

            dir_region = dir_output / region
            dir_region.mkdir(parents=True, exist_ok=True)

            # Extract channel names and renames
            channels_name = channel_info["channels_name"]
            channels_rename = channel_info["channels_rename"]

            # Parameters for exporting OME-TIFF
            region_metadata = self.metadatas.metadata[region]
            paths_tiff = [
                region_metadata["path"][
                    region_metadata["marker"].tolist().index(marker)
                ]
                for marker in channels_name
            ]
            path_region_ometiff = dir_region / f"{region}.ome.tiff"

            # Export OME-TIFF
            if path_region_ometiff.exists():
                os.remove(path_region_ometiff)
            export_ometiff_pyramid(
                paths_tiff=paths_tiff,
                path_ometiff=str(path_region_ometiff),
                channel_names=channels_rename,
            )
