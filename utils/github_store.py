import base64
import csv
from io import StringIO
from pathlib import Path

import requests

REPO = "Nikhil-Lakha/Digital-Analytics-Data-Dictionary"
FILE_PATH = "data/analytics_data_dictionary.csv"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{FILE_PATH}"
LOCAL_CSV_PATH = Path(__file__).resolve().parents[1] / FILE_PATH


def _headers(token: str | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "digital-analytics-data-dictionary",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_workbook_bytes(token: str | None = None) -> bytes:
    """Fetch the latest CSV dictionary from GitHub."""
    if token:
        response = requests.get(API_URL, headers=_headers(token), params={"ref": BRANCH}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        return base64.b64decode(payload["content"])

    response = requests.get(RAW_URL, headers=_headers(), timeout=20)
    response.raise_for_status()
    return response.content


def _get_file_metadata(token: str) -> tuple[str, bytes]:
    response = requests.get(API_URL, headers=_headers(token), params={"ref": BRANCH}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    return payload["sha"], base64.b64decode(payload["content"])


def _commit_csv(token: str, csv_bytes: bytes, message: str) -> None:
    sha, _ = _get_file_metadata(token)
    payload = {
        "message": message,
        "content": base64.b64encode(csv_bytes).decode("utf-8"),
        "sha": sha,
        "branch": BRANCH,
    }
    response = requests.put(API_URL, headers=_headers(token), json=payload, timeout=30)
    response.raise_for_status()


def _load_rows(token: str | None):
    """Load CSV rows from GitHub when a token is supplied; otherwise use the local CSV."""
    if token:
        _, csv_bytes = _get_file_metadata(token)
        text = csv_bytes.decode("utf-8-sig")
    else:
        if not LOCAL_CSV_PATH.exists():
            raise FileNotFoundError(f"Local CSV was not found at {LOCAL_CSV_PATH}")
        text = LOCAL_CSV_PATH.read_text(encoding="utf-8-sig")

    reader = csv.DictReader(StringIO(text))
    fieldnames = reader.fieldnames or []
    rows = list(reader)
    return fieldnames, rows


def _save_rows(token: str | None, fieldnames: list[str], rows: list[dict], message: str) -> None:
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = output.getvalue().encode("utf-8")

    if token:
        _commit_csv(token, csv_bytes, message)
    else:
        LOCAL_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_CSV_PATH.write_bytes(csv_bytes)


def _find_variable_index(rows: list[dict], variable_name: str) -> int:
    target = str(variable_name).strip()
    for idx, row in enumerate(rows):
        if str(row.get("Variable Name", "")).strip() == target:
            return idx
    raise ValueError(f"Variable '{variable_name}' was not found in the CSV.")


def create_variable(token: str | None, values: dict) -> None:
    fieldnames, rows = _load_rows(token)

    variable_name = str(values.get("Variable Name", "")).strip()
    if not variable_name:
        raise ValueError("Variable Name is required.")

    for row in rows:
        existing = str(row.get("Variable Name", "")).strip()
        if existing.lower() == variable_name.lower():
            raise ValueError(f"Variable '{variable_name}' already exists.")

    new_row = {field: values.get(field, "") for field in fieldnames}
    rows.append(new_row)
    _save_rows(token, fieldnames, rows, f"Add analytics variable: {variable_name}")


def update_variable(token: str | None, original_variable_name: str, values: dict) -> None:
    fieldnames, rows = _load_rows(token)
    row_idx = _find_variable_index(rows, original_variable_name)

    new_variable_name = str(values.get("Variable Name", original_variable_name)).strip()
    if new_variable_name.lower() != str(original_variable_name).strip().lower():
        for idx, row in enumerate(rows):
            if idx == row_idx:
                continue
            existing = str(row.get("Variable Name", "")).strip()
            if existing.lower() == new_variable_name.lower():
                raise ValueError(f"Variable '{new_variable_name}' already exists.")

    for field in fieldnames:
        if field in values:
            rows[row_idx][field] = values[field]

    _save_rows(token, fieldnames, rows, f"Update analytics variable: {original_variable_name}")


def delete_variable(token: str | None, variable_name: str) -> None:
    fieldnames, rows = _load_rows(token)
    row_idx = _find_variable_index(rows, variable_name)
    rows.pop(row_idx)
    _save_rows(token, fieldnames, rows, f"Delete analytics variable: {variable_name}")
