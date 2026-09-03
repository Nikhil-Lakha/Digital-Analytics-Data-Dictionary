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
- More Information link opens the complete variable record in a separate browser tab
- Edit workflow supports both the main fields and all detailed metadata
- Delete workflow removes the variable from the master Excel workbook
- Edit and Delete actions commit directly back to `data/analytics_data_dictionary.xlsx` in GitHub
- Edit/Delete access is protected by an administrator password

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

## GitHub write-back setup

The deployed app needs two secrets. Do **not** commit real secret values to this repository.

```toml
GITHUB_TOKEN = "your-fine-grained-github-token"
ADMIN_PASSWORD = "your-admin-password"
```

Create a fine-grained GitHub Personal Access Token that is restricted to this repository and has repository **Contents: Read and write** permission. Then add both values to the Streamlit Community Cloud app's Secrets settings.

The app uses the GitHub Contents API to download the latest workbook, update or delete the matching row, and commit the modified `.xlsx` file back to the `main` branch.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

For local editing, create `.streamlit/secrets.toml` using the same two values shown above. The real `secrets.toml` must never be committed.

## Deploy to Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with GitHub.
2. Choose this repository.
3. Branch: `main`.
4. Main file path: `app.py`.
5. Add `GITHUB_TOKEN` and `ADMIN_PASSWORD` under the app's Secrets settings.
6. Deploy or reboot the app.

## Future roadmap

- Add new variables through the app
- Duplicate validation
- Missing-definition warnings
- Change history / audit log
- Schema versioning
- Compare dictionary with Tealium mapped variables
- Compare dictionary with AWS / Glue / Athena schemas
- Tealium API integration
- Role-based authentication
- Approval workflow
