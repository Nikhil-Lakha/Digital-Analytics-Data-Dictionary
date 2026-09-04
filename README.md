# Digital Analytics Data Dictionary

Central documentation application for the Adobe Analytics Replacement project.

This repository contains a Streamlit application and analytics dictionary source data. The application is a documentation and governance layer only; it is **not** part of the live Tealium-to-AWS event flow.

## Architecture

Live analytics flow:

`Website / App -> Tealium -> AWS ingestion -> S3 / Glue / Athena / QuickSight`

Documentation flow:

`GitHub -> analytics_data_dictionary.xlsx -> Streamlit`

## Current features

- Search variable name, friendly name, and definition
- Four filters only: Category, Data Type, Status, and Owner
- Simplified main table showing:
  - Variable Name
  - Friendly Name
  - Category
  - Tealium Variable Name
  - AWS Field Name
- **Add New Variable** opens an in-page modal and captures both main and detailed metadata
- **More Information** opens the complete variable record in a wide in-page modal — no new browser tab
- **Edit** opens an in-page modal and supports both the main fields and all detailed metadata
- **Delete** opens an in-page confirmation modal before removing the record
- Add, Edit, and Delete write back to `data/analytics_data_dictionary.xlsx`
- On localhost, changes update the local Excel workbook so the workflow can be tested without GitHub credentials
- When `GITHUB_TOKEN` is configured, changes are committed directly back to the Excel workbook in GitHub
- Duplicate Variable Name validation is included for both Add and Edit
- Production editing can be protected with an administrator password

## Repository structure

```text
.
├── app.py
├── data/
│   └── analytics_data_dictionary.xlsx
├── utils/
│   ├── __init__.py
│   ├── data_loader.py
│   └── github_store.py
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── requirements.txt
├── .gitignore
└── README.md
```

## Local testing

When neither `GITHUB_TOKEN` nor `ADMIN_PASSWORD` is configured, the app runs in local test mode. Add, Edit, and Delete update the local file at:

`data/analytics_data_dictionary.xlsx`

This makes it possible to test the full workflow in VS Code before enabling GitHub write-back.

Run locally on Windows:

```powershell
.venv\Scripts\activate
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## GitHub write-back setup

The deployed app needs two secrets. Do **not** commit real secret values to this repository.

```toml
GITHUB_TOKEN = "your-fine-grained-github-token"
ADMIN_PASSWORD = "your-admin-password"
```

Create a fine-grained GitHub Personal Access Token that is restricted to this repository and has repository **Contents: Read and write** permission. Then add both values to the Streamlit Community Cloud app's Secrets settings.

The app uses the GitHub Contents API to download the latest workbook, add/update/delete the matching row, and commit the modified `.xlsx` file back to the `main` branch.

## Deploy to Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with GitHub.
2. Choose this repository.
3. Branch: `main`.
4. Main file path: `app.py`.
5. Add `GITHUB_TOKEN` and `ADMIN_PASSWORD` under the app's Secrets settings.
6. Deploy or reboot the app.

## Future roadmap

- Change history / audit log
- Schema versioning
- Compare dictionary with Tealium mapped variables
- Compare dictionary with AWS / Glue / Athena schemas
- Tealium API integration
- Role-based authentication
- Approval workflow
