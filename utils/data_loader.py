from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "analytics_data_dictionary.xlsx"

REQUIRED_COLUMNS = [
    "Variable Name", "Friendly Name", "Category", "Definition", "Data Type",
    "Tealium Variable Name", "AWS Field Name", "Send to AWS", "Contains PII",
    "Owner", "Status", "Journey"
]


def load_dictionary(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and lightly validate the Variables sheet from the analytics dictionary."""
    df = pd.read_excel(path, sheet_name="Variables", engine="openpyxl")
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
