import sys
from io import StringIO
from pathlib import Path

import pandas as pd

dir_src = Path(__file__).resolve().parent.parent
sys.path.append(str(dir_src))
from src.preprocess import KeyencePreprocessor

################################################################################
# input directory
dir_root = "/mnt/nfs/storage/RCC/RCC_formal_CODEX/RCC_TMA001-run1/reg_4x5/images/final/"

# output directory for DAPI OME-TIFF and metadata
dir_output_review = "/mnt/nfs/storage/wenruiwu_temp/pipeline/keyence/01_preprocess"

# output directory for final OME-TIFF
dir_output_ometiff = "/mnt/nfs/storage/wenruiwu_temp/pipeline/keyence/02_ometiff"

# metadata string (copy from Excel)
string_metadata_dapi = """
region	dapi
reg001	Ch1Cy1
reg002	Ch1Cy2
reg003	Ch1Cy3
reg004	Ch1Cy1
reg005	Ch1Cy2
reg006	Ch1Cy3
reg007	Ch1Cy1
reg008	Ch1Cy2
reg009	Ch1Cy3
reg010	Ch1Cy1
reg011	Ch1Cy2
reg012	Ch1Cy3
reg013	Ch1Cy1
reg014	Ch1Cy2
"""

string_metadata_marker = """
marker	channel_name
CD45	CD45
CD3e	CD3e
CD8	CD8
CD4	CD4
CD45RO	CD45RO
CD45RA	CD45RA
CD69	CD69
CD57	CD57
CD56	CD56
FoxP3	FoxP3
CD28	CD28
CD86	CD86
T-bet	T-bet
TCF1_7	TCF1_7
IFN-y	IFN-y
GranzymeB	GranzymeB
Tox_Tox2	Tox_Tox2
Tim-3	Tim-3
PD-1	PD-1
LAG-3	LAG-3
CD20	CD20
CD138	CD138
CD68	CD68
DIG_TREM2	TREM2
CD163	CD163
CD16	CD16
CD11b	CD11b
CD11c	CD11c
MPO	MPO
IDO-1	IDO-1
PDL1_100_500ms	PD-L1
CA9	CA9
Cytokeratin	Cytokeratin
HLA1	HLA1
Ki-67	Ki-67
P53	P53
CD31	CD31
Podoplanin	Podoplanin
aSMA	aSMA
NaKATP	NaKATP
VDAC1	VDAC1
ATP5A	ATP5A
GLUT1	GLUT1
G6PD	G6PD
C1Q	C1Q
"""
################################################################################

keyence = KeyencePreprocessor(dir_root)

# Step 1: Generate DAPI OME-TIFF and metadata
if False:
    keyence.export_dapi_ometiff_and_metadata(dir_output_review)

# Step 2: Generate final OME-TIFF
if True:
    df_metadata_dapi = pd.read_csv(StringIO(string_metadata_dapi), sep="\t")
    df_metadata_marker = pd.read_csv(StringIO(string_metadata_marker), sep="\t")
    keyence.export_ometiff(dir_output_ometiff, df_metadata_dapi, df_metadata_marker)
