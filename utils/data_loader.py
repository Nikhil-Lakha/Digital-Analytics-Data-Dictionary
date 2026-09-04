from io import BytesIO
from pathlib import Path

import pandas as pd

from utils.github_store import fetch_workbook_bytes

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
XLSX_PATH = DATA_DIR / "analytics_data_dictionary.xlsx"
CSV_PATH = DATA_DIR / "analytics_data_dictionary.csv"

REQUIRED_COLUMNS = [
    "Variable Name", "Friendly Name", "Category", "Definition", "Data Type",
    "Tealium Variable Name", "AWS Field Name", "Send to AWS", "Contains PII",
    "Owner", "Status", "Journey"
]


def load_dictionary(token: str | None = None) -> pd.DataFrame:
    """Load local Excel during localhost testing; use GitHub as the source when a token is configured."""
    df = None

    if not token and XLSX_PATH.exists():
        try:
            df = pd.read_excel(XLSX_PATH, sheet_name="Variables", engine="openpyxl")
        except Exception:
            df = None

    if df is None:
        try:
            workbook_bytes = fetch_workbook_bytes(token)
            df = pd.read_excel(BytesIO(workbook_bytes), sheet_name="Variables", engine="openpyxl")
        except Exception:
            if XLSX_PATH.exists():
                try:
                    df = pd.read_excel(XLSX_PATH, sheet_name="Variables", engine="openpyxl")
                except Exception:
                    df = None

    if df is None:
        if not CSV_PATH.exists():
            raise FileNotFoundError("No analytics dictionary source file was found.")
        df = pd.read_csv(CSV_PATH)

    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Dictionary is missing required columns: {', '.join(missing)}")

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("")

    return df


def unique_values(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    values = [str(v).strip() for v in df[column].dropna().tolist() if str(v).strip()]
    return sorted(set(values))
