import html
from datetime import date

import pandas as pd
import streamlit as st

from utils.data_loader import load_dictionary, unique_values
from utils.github_store import create_variable, delete_variable, update_variable

st.set_page_config(
    page_title="Digital Analytics Bible",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .app-kicker {font-size:0.85rem; font-weight:700; letter-spacing:.08em; color:#E60000;}
    .app-title {font-size:2.2rem; font-weight:800; margin-bottom:.25rem;}
    .app-subtitle {color:#666; margin-bottom:1.5rem;}
    .metric-card {background:#fff; border:1px solid #e6e6e6; border-radius:14px; padding:18px 20px; box-shadow:0 1px 2px rgba(0,0,0,.04);}
    .metric-label {font-size:.82rem; color:#666; margin-bottom:4px;}
    .metric-value {font-size:1.6rem; font-weight:800; color:#222;}
    .detail-box {background:#fafafa; border:1px solid #ececec; border-radius:12px; padding:16px 18px; margin-bottom:12px;}
    .table-header {font-size:.78rem; font-weight:750; color:#666; text-transform:uppercase; letter-spacing:.02em; padding:8px 4px;}
    .table-cell {font-size:.92rem; padding:8px 4px; overflow-wrap:anywhere;}
    .row-divider {border-top:1px solid #eeeeee; margin:3px 0 5px 0;}
    div[data-testid="stDialog"] div[role="dialog"] {max-width: 1050px; width: min(1050px, 95vw);}
    </style>
    """,
    unsafe_allow_html=True,
)


def get_token() -> str:
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return ""


def get_admin_password() -> str:
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return ""


def require_admin(prefix: str) -> bool:
    """Allow localhost testing without secrets; require password when GitHub write-back is enabled."""
    if not get_token() and not get_admin_password():
        return True

    if st.session_state.get("admin_authenticated", False):
        return True

    configured_password = get_admin_password()
    if not configured_password:
        st.warning("Editing is locked until ADMIN_PASSWORD is added to Streamlit Secrets.")
        return False

    st.info("Enter the administrator password to continue.")
    entered = st.text_input("Administrator password", type="password", key=f"{prefix}_admin_password")
    if st.button("Unlock", key=f"{prefix}_unlock", type="primary"):
        if entered == configured_password:
            st.session_state["admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect administrator password.")
    return False


def esc(value) -> str:
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def get_data():
    return load_dictionary(get_token() or None)


def find_row(frame: pd.DataFrame, variable_name: str):
    matches = frame[frame["Variable Name"].astype(str) == str(variable_name)]
    return None if matches.empty else matches.iloc[0]


def header():
    st.markdown('<div class="app-kicker">ADOBE ANALYTICS REPLACEMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">Digital Analytics Data Dictionary</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Central reference for analytics variables, Tealium mappings, AWS fields and governance metadata.</div>',
        unsafe_allow_html=True,
    )


def build_variable_form(frame: pd.DataFrame, row=None, prefix="form") -> dict:
    values = {}
    current = {} if row is None else row.to_dict()

    st.markdown("### Main information")
    c1, c2 = st.columns(2)
    with c1:
        values["Variable Name"] = st.text_input(
            "Variable name *",
            value=str(current.get("Variable Name", "")),
            key=f"{prefix}_variable_name",
        )
        values["Friendly Name"] = st.text_input(
            "Friendly name *",
            value=str(current.get("Friendly Name", "")),
            key=f"{prefix}_friendly_name",
        )
        values["Category"] = st.text_input(
            "Category *",
            value=str(current.get("Category", "")),
            key=f"{prefix}_category",
        )
    with c2:
        values["Data Type"] = st.text_input(
            "Data type *",
            value=str(current.get("Data Type", "")),
            key=f"{prefix}_data_type",
        )
        values["Tealium Variable Name"] = st.text_input(
            "Tealium variable name",
            value=str(current.get("Tealium Variable Name", "")),
            key=f"{prefix}_tealium_name",
        )
        values["AWS Field Name"] = st.text_input(
            "AWS field name",
            value=str(current.get("AWS Field Name", "")),
            key=f"{prefix}_aws_name",
        )

    st.markdown("### Detailed information")
    already_rendered = {
        "Variable Name", "Friendly Name", "Category", "Data Type",
        "Tealium Variable Name", "AWS Field Name"
    }
    bool_fields = {"Required", "Send to AWS", "Contains PII"}
    text_area_fields = {"Definition", "Allowed Values", "Notes"}
    detail_fields = [column for column in frame.columns if column not in already_rendered]
    cols = st.columns(2)

    for idx, field in enumerate(detail_fields):
        default = current.get(field, "")
        if row is None:
            if field == "Status":
                default = "Draft"
            elif field == "Schema Version":
                default = "1.0"
            elif field in {"Date Added", "Last Updated"}:
                default = date.today().isoformat()

        with cols[idx % 2]:
            if field in bool_fields:
                values[field] = st.selectbox(
                    field,
                    [False, True],
                    index=1 if truthy(default) else 0,
                    key=f"{prefix}_{field}",
                )
            elif field == "Status":
                status_options = unique_values(frame, "Status")
                for option in ["Draft", "Active", "Deprecated"]:
                    if option not in status_options:
                        status_options.append(option)
                status_options = sorted(set(status_options))
                default_text = str(default) if str(default) in status_options else "Draft"
                values[field] = st.selectbox(
                    field,
                    status_options,
                    index=status_options.index(default_text),
                    key=f"{prefix}_{field}",
                )
            elif field in text_area_fields:
                values[field] = st.text_area(
                    field,
                    value=str(default),
                    key=f"{prefix}_{field}",
                )
            else:
                values[field] = st.text_input(
                    field,
                    value=str(default),
                    key=f"{prefix}_{field}",
                )

    return values


try:
    df = get_data()
except Exception as exc:
    st.error(f"Could not load the analytics dictionary: {exc}")
    st.stop()


@st.dialog("Add new variable")
def add_variable_dialog():
    st.caption("Create a new record in the Digital Analytics Data Dictionary.")
    if not require_admin("add"):
        return

    if not get_token():
        st.info("Local test mode: Save will update your local Excel workbook only. GitHub is unchanged until GITHUB_TOKEN is configured.")

    with st.form("add_variable_form"):
        values = build_variable_form(df, row=None, prefix="add")
        submitted = st.form_submit_button("Add variable", type="primary", use_container_width=True)

    if submitted:
        required = ["Variable Name", "Friendly Name", "Category", "Data Type"]
        missing = [field for field in required if not str(values.get(field, "")).strip()]
        if missing:
            st.error(f"Please complete: {', '.join(missing)}")
            return
        try:
            create_variable(get_token() or None, values)
            st.success("Variable added successfully.")
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add the variable: {exc}")


@st.dialog("Variable information")
def information_dialog(variable_name: str):
    row = find_row(df, variable_name)
    if row is None:
        st.error("That variable could not be found.")
        return

    st.markdown(f"## {esc(row.get('Friendly Name', variable_name))}", unsafe_allow_html=True)
    st.caption(str(row.get("Variable Name", "")))

    left, right = st.columns(2)
    with left:
        st.markdown("### Main information")
        for field in ["Variable Name", "Friendly Name", "Category", "Data Type"]:
            st.markdown(
                f'<div class="detail-box"><strong>{html.escape(field)}</strong><br>{esc(row.get(field, "")) or "—"}</div>',
                unsafe_allow_html=True,
            )
    with right:
        st.markdown("### Implementation")
        for field in ["Tealium Variable Name", "AWS Field Name", "Tealium Variable Type", "Send to AWS"]:
            if field in df.columns:
                st.markdown(
                    f'<div class="detail-box"><strong>{html.escape(field)}</strong><br>{esc(row.get(field, "")) or "—"}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("### Additional details")
    main_fields = {
        "Variable Name", "Friendly Name", "Category", "Data Type",
        "Tealium Variable Name", "AWS Field Name", "Tealium Variable Type", "Send to AWS"
    }
    detail_fields = [column for column in df.columns if column not in main_fields]
    d1, d2 = st.columns(2)
    for idx, field in enumerate(detail_fields):
        with (d1 if idx % 2 == 0 else d2):
            st.markdown(
                f'<div class="detail-box"><strong>{html.escape(field)}</strong><br>{esc(row.get(field, "")) or "—"}</div>',
                unsafe_allow_html=True,
            )


@st.dialog("Edit variable")
def edit_variable_dialog(variable_name: str):
    row = find_row(df, variable_name)
    if row is None:
        st.error("That variable could not be found.")
        return

    st.caption(f"Update main and detailed information for {variable_name}.")
    if not require_admin(f"edit_{variable_name}"):
        return

    if not get_token():
        st.info("Local test mode: Save will update your local Excel workbook only. GitHub is unchanged until GITHUB_TOKEN is configured.")

    with st.form(f"edit_variable_form_{variable_name}"):
        values = build_variable_form(df, row=row, prefix=f"edit_{variable_name}")
        submitted = st.form_submit_button("Save changes", type="primary", use_container_width=True)

    if submitted:
        required = ["Variable Name", "Friendly Name", "Category", "Data Type"]
        missing = [field for field in required if not str(values.get(field, "")).strip()]
        if missing:
            st.error(f"Please complete: {', '.join(missing)}")
            return
        try:
            update_variable(get_token() or None, variable_name, values)
            st.success("Changes saved successfully.")
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save the changes: {exc}")


@st.dialog("Delete variable")
def delete_variable_dialog(variable_name: str):
    row = find_row(df, variable_name)
    if row is None:
        st.error("That variable could not be found.")
        return

    if not require_admin(f"delete_{variable_name}"):
        return

    st.warning(
        f"You are about to delete **{variable_name} — {row.get('Friendly Name', '')}** from the dictionary."
    )
    if not get_token():
        st.info("Local test mode: Delete will affect your local Excel workbook only. GitHub is unchanged until GITHUB_TOKEN is configured.")

    confirm = st.checkbox("I understand that this action removes the full variable record.", key=f"confirm_{variable_name}")
    if st.button(
        "Delete variable",
        type="primary",
        disabled=not confirm,
        use_container_width=True,
        key=f"delete_confirm_{variable_name}",
    ):
        try:
            delete_variable(get_token() or None, variable_name)
            st.success("Variable deleted successfully.")
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not delete the variable: {exc}")


header()

missing_definitions = int(df["Definition"].fillna("").astype(str).str.strip().eq("").sum())
aws_count = int(df["Send to AWS"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
pii_count = int(df["Contains PII"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
active_count = int(df["Status"].astype(str).str.lower().eq("active").sum())

metrics = [
    ("Total variables", len(df)),
    ("Sent to AWS", aws_count),
    ("PII variables", pii_count),
    ("Missing definitions", missing_definitions),
    ("Active variables", active_count),
]
cols = st.columns(5)
for col, (label, value) in zip(cols, metrics):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("### Search & filter")
search = st.text_input(
    "Search",
    placeholder="Search variable name, friendly name or definition...",
    label_visibility="collapsed",
)

f1, f2, f3, f4 = st.columns(4)
with f1:
    category = st.multiselect("Category", unique_values(df, "Category"))
with f2:
    data_type = st.multiselect("Data type", unique_values(df, "Data Type"))
with f3:
    status = st.multiselect("Status", unique_values(df, "Status"))
with f4:
    owner = st.multiselect("Owner", unique_values(df, "Owner"))

filtered = df.copy()
if search.strip():
    term = search.strip().lower()
    search_cols = [column for column in ["Variable Name", "Friendly Name", "Definition"] if column in filtered.columns]
    mask = pd.Series(False, index=filtered.index)
    for column in search_cols:
        mask = mask | filtered[column].fillna("").astype(str).str.lower().str.contains(term, regex=False)
    filtered = filtered[mask]

for column, selected in [
    ("Category", category),
    ("Data Type", data_type),
    ("Status", status),
    ("Owner", owner),
]:
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]

heading_col, add_col = st.columns([5, 1.25])
with heading_col:
    st.markdown(f"### Variables ({len(filtered)})")
with add_col:
    if st.button("＋ Add New Variable", type="primary", use_container_width=True):
        add_variable_dialog()

if filtered.empty:
    st.info("No variables match the current filters.")
else:
    widths = [1.35, 1.45, 1.05, 1.35, 1.35, 1.05, 0.65, 0.65]
    headers = [
        "Variable Name", "Friendly Name", "Category", "Tealium Variable Name",
        "AWS Field Name", "More Information", "Edit", "Delete"
    ]
    header_cols = st.columns(widths)
    for col, label in zip(header_cols, headers):
        with col:
            st.markdown(f'<div class="table-header">{html.escape(label)}</div>', unsafe_allow_html=True)

    for idx, (_, row) in enumerate(filtered.iterrows()):
        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)
        variable_name = str(row.get("Variable Name", ""))
        row_cols = st.columns(widths, vertical_alignment="center")

        with row_cols[0]:
            st.markdown(f'<div class="table-cell"><strong>{esc(variable_name)}</strong></div>', unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f'<div class="table-cell">{esc(row.get("Friendly Name", ""))}</div>', unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f'<div class="table-cell">{esc(row.get("Category", ""))}</div>', unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f'<div class="table-cell">{esc(row.get("Tealium Variable Name", ""))}</div>', unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(f'<div class="table-cell">{esc(row.get("AWS Field Name", ""))}</div>', unsafe_allow_html=True)
        with row_cols[5]:
            if st.button("More info", key=f"more_{idx}_{variable_name}", use_container_width=True):
                information_dialog(variable_name)
        with row_cols[6]:
            if st.button("Edit", key=f"edit_{idx}_{variable_name}", use_container_width=True):
                edit_variable_dialog(variable_name)
        with row_cols[7]:
            if st.button("Delete", key=f"delete_{idx}_{variable_name}", use_container_width=True):
                delete_variable_dialog(variable_name)

st.divider()
st.caption(
    "Documentation layer only — Tealium controls which variables are mapped and sent to AWS. "
    "On localhost, changes are written to the local Excel workbook. With GITHUB_TOKEN configured, changes are committed to GitHub."
)
