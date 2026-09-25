import os
from pathlib import Path
from typing import Optional, Final

from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Final[Path] = Path(__file__).resolve().parents[3]

DATA_DIR: Final[Path] = BASE_DIR / "data" / "processed"
RAW_DIR: Final[Path] = BASE_DIR / "data" / "raw"
OUTPUT_DIR: Final[Path] = BASE_DIR / "data" / "out"
GLOSS_DIR: Final[Path] = BASE_DIR / "data" / "gloss"
XML_DIR: Final[Path] = BASE_DIR / "xml"
PROGRAMS_DIR: Final[Path] = BASE_DIR / "programs"

BASE_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
XML_DIR.mkdir(parents=True, exist_ok=True)
PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
GLOSS_DIR.mkdir(parents=True, exist_ok=True)

CSET_E_QUERY_PARAM: Optional[str] = os.getenv("CSET_E_QUERY_PARAM")
CSET_H_QUERY_PARAM: Optional[str] = os.getenv("CSET_H_QUERY_PARAM")
USE_JLA_ENTRY_FOR_DEFINITIONS: Optional[str] = os.getenv(
    "USE_JLA_ENTRY_FOR_DEFINITIONS"
)
DB_NAME: Optional[str] = os.getenv("DB_NAME")
DB_USER: Optional[str] = os.getenv("DB_USER")
DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
DB_HOST: Optional[str] = os.getenv("DB_HOST")
DB_PORT: Optional[str] = os.getenv("DB_PORT")
TF_BACKEND: Optional[str] = os.getenv("TF_BACKEND")
TF_ORG: Optional[str] = os.getenv("TF_ORG")
TF_REPO: Optional[str] = os.getenv("TF_REPO")

GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# Boolean flags evaluated from environment strings
SHOULD_FETCH_ARAMAIC: bool = os.getenv("SHOULD_FETCH_ARAMAIC") == "True"
SHOULD_TRANSFORM_LINE_WITH_REGEX: bool = (
    os.getenv("SHOULD_TRANSFORM_LINE_WITH_REGEX") == "True"
)
SHOULD_CREATE_CSV: bool = os.getenv("SHOULD_CREATE_CSV") == "True"
SHOULD_SAVE_LINES: bool = os.getenv("SHOULD_SAVE_LINES") == "True"


if __name__ == "__main__":
    print(f"DEBUG: BASE_DIR is currently: {BASE_DIR}")
    print(f"DEBUG: DATA_DIR is currently: {DATA_DIR}")
    print(f"DEBUG: OUTPUT_DIR is currently: {OUTPUT_DIR}")
    print(f"DEBUG: RAW_DIR is currently: {RAW_DIR}")
    print(f"DEBUG: GLOSS_DIR is currently: {GLOSS_DIR}")
    print(f"DEBUG: TF_BACKEND is currently: {TF_BACKEND}")
    print(f"DEBUG: TF_ORG is currently: {TF_ORG}")
    print(f"DEBUG: TF_REPO is currently: {TF_REPO}")
