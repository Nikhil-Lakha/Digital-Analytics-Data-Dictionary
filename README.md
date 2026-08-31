# Digital Analytics Data Dictionary

Central documentation application for the Adobe Analytics Replacement project.

This repository contains a Streamlit application and an Excel-based analytics data dictionary. The application is a documentation and governance layer only; it is **not** part of the live Tealium-to-AWS event flow.

## Architecture

Live analytics flow:

`Website / App -> Tealium -> AWS ingestion -> S3 / Glue / Athena / QuickSight`

Documentation flow:

`GitHub -> analytics_data_dictionary.xlsx -> Streamlit`

## Repository structure

```text
.
├── app.py
├── data/
│   └── analytics_data_dictionary.xlsx
├── utils/
│   ├── __init__.py
│   └── data_loader.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── .gitignore
└── README.md
```

## V1 features

- Search variable name, friendly name, and definition
- Filters for category, data type, status, PII, Send to AWS, owner, and journey
- Summary cards for total variables, AWS variables, PII variables, missing definitions, and active variables
- Variable detail view
- Download filtered results as CSV
- Excel file remains the source of truth

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Update the dictionary

1. Edit `data/analytics_data_dictionary.xlsx`.
2. Commit and push the updated file to GitHub.
3. Streamlit reloads the workbook from the repository on the next app run/reload.

## Deploy to Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with GitHub.
2. Choose this repository.
3. Branch: `main`.
4. Main file path: `app.py`.
5. Deploy.

## Future roadmap

- Add/edit variables through the app
- Duplicate validation
- Missing-definition warnings
- Change history
- Schema versioning
- Compare dictionary with Tealium mapped variables
- Compare dictionary with AWS / Glue / Athena schemas
- Tealium API integration
- Authentication and roles
- Approval workflow
