import base64
from io import BytesIO

import requests
from openpyxl import load_workbook

REPO = "Nikhil-Lakha/Digital-Analytics-Data-Dictionary"
FILE_PATH = "data/analytics_data_dictionary.xlsx"
BRANCH = "main"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{FILE_PATH}"


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
    """Fetch the latest workbook from GitHub, falling back to the public raw URL."""
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


def _commit_workbook(token: str, workbook_bytes: bytes, message: str) -> None:
    sha, _ = _get_file_metadata(token)
    payload = {
        "message": message,
        "content": base64.b64encode(workbook_bytes).decode("utf-8"),
        "sha": sha,
        "branch": BRANCH,
    }
    response = requests.put(API_URL, headers=_headers(token), json=payload, timeout=30)
    response.raise_for_status()


def _find_variable_row(ws, variable_name: str) -> tuple[int, dict[str, int]]:
    headers = {str(cell.value).strip(): idx for idx, cell in enumerate(ws[1], start=1) if cell.value is not None}
    variable_col = headers.get("Variable Name")
    if not variable_col:
        raise ValueError("Variable Name column is missing from the workbook.")

    for row_idx in range(2, ws.max_row + 1):
        value = ws.cell(row=row_idx, column=variable_col).value
        if str(value).strip() == str(variable_name).strip():
            return row_idx, headers

    raise ValueError(f"Variable '{variable_name}' was not found in the workbook.")


def update_variable(token: str, original_variable_name: str, values: dict) -> None:
    _, workbook_bytes = _get_file_metadata(token)
    wb = load_workbook(BytesIO(workbook_bytes))
    ws = wb["Variables"]
    row_idx, headers = _find_variable_row(ws, original_variable_name)

    for field, value in values.items():
        col_idx = headers.get(field)
        if col_idx:
            ws.cell(row=row_idx, column=col_idx).value = value

    output = BytesIO()
    wb.save(output)
    _commit_workbook(token, output.getvalue(), f"Update analytics variable: {original_variable_name}")


def delete_variable(token: str, variable_name: str) -> None:
    _, workbook_bytes = _get_file_metadata(token)
    wb = load_workbook(BytesIO(workbook_bytes))
    ws = wb["Variables"]
    row_idx, _ = _find_variable_row(ws, variable_name)
    ws.delete_rows(row_idx, 1)

    output = BytesIO()
    wb.save(output)
    _commit_workbook(token, output.getvalue(), f"Delete analytics variable: {variable_name}")
