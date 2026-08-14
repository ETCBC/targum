import os
from pathlib import Path
from typing import Optional, Final

from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Final[Path] = Path(__file__).resolve().parents[3]

XML_DIR: Final[Path] = BASE_DIR / "xml"
PROGRAMS_DIR: Final[Path] = BASE_DIR / "programs"

BASE_DIR.mkdir(parents=True, exist_ok=True)
XML_DIR.mkdir(parents=True, exist_ok=True)
PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME: Optional[str] = os.getenv("DB_NAME")
DB_USER: Optional[str] = os.getenv("DB_USER")
DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
DB_HOST: Optional[str] = os.getenv("DB_HOST")
DB_PORT: Optional[str] = os.getenv("DB_PORT")


if __name__ == "__main__":
    print(f"DEBUG: BASE_DIR is currently: {BASE_DIR}")
    print(f"DEBUG: XML_DIR is currently: {XML_DIR}")
    print(f"DEBUG: PROGRAMS_DIR is currently: {PROGRAMS_DIR}")
