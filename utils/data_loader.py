from io import StringIO
from pathlib import Path

import pandas as pd

from utils.github_store import fetch_workbook_bytes

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATH = DATA_DIR / "analytics_data_dictionary.csv"

REQUIRED_COLUMNS = [
    "Variable Name", "Friendly Name", "Category", "Definition", "Data Type",
    "Tealium Variable Name", "AWS Field Name", "Sent to AWS", "Contains PII",
    "Owner", "Status", "Journey"
]


def load_dictionary(token: str | None = None) -> pd.DataFrame:
    """Load the analytics dictionary from GitHub CSV when a token is configured, otherwise use the local CSV."""
    df = None

    if token:
        try:
            csv_bytes = fetch_workbook_bytes(token)
            df = pd.read_csv(StringIO(csv_bytes.decode("utf-8-sig")))
        except Exception:
            df = None

    if df is None:
        if not CSV_PATH.exists():
            raise FileNotFoundError("No analytics dictionary CSV source file was found.")
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
