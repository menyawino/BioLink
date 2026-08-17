from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
REFERENCE_DIR = DATA_DIR / "reference"

# Datasets definition
DATASETS = {
    "EHVol": RAW_DIR / "EHVol_Full.csv",
    "BHS": RAW_DIR / "BHS_Full.csv",
}
