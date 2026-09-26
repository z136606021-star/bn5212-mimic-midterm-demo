from __future__ import annotations
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT.parent / "data" / "extracted" / "MIMIC_IV" / "physionet.org" / "files" / "mimiciv" / "3.1"
DATA_ROOT = Path(os.getenv("MIMIC_DATA_ROOT", DEFAULT_DATA_ROOT)).resolve()
ARTIFACT_ROOT = Path(os.getenv("DEMO_ARTIFACT_ROOT", PROJECT_ROOT / "artifacts")).resolve()
RANDOM_SEED = 5212
