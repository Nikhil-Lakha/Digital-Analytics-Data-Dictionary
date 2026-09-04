import html
from datetime import date

import pandas as pd
import streamlit as st

from utils.data_loader import load_dictionary, unique_values
from utils.github_store import create_variable, delete_variable, update_variable

st.set_page_config(page_title="Digital Analytics Bible", page_icon="📊", layout="wide")

st.markdown("""
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
.row-divider {border-top:1px solid #eeeeee; margin:3px 0 5px 0;}
div[data-testid="stDialog"] div[role="dialog"] {max-width: 1050px; width: min(1050px, 95vw);}
</style>
""", unsafe_allow_html=True)

DROPDOWN_OPTIONS = {
    "Tealium Variable Type": ["Data Layer Variable", "JavaScript Variable", "DOM Variable", "Cookie", "Query String Parameter", "Meta Data Element", "UDO Variable", "Other"],
    "Category": ["Core / Technical", "Page", "Journey", "Event", "Visitor", "Customer", "Product", "Transaction", "Marketing", "Campaign", "Device", "Search", "Personalisation", "Consent / Permissions", "Errors", "Video", "Experimentation / A/B Testing"],
    "Subcategory": ["Identity", "Navigation", "Interaction", "Funnel", "Product Detail", "Purchase", "Attribution", "Campaign Tracking", "Device Information", "Search Behaviour", "Consent", "Error Detail", "Experiment", "Other", "Not Applicable"],
    "Data Type": ["String", "Integer", "Decimal", "Boolean", "Date", "Datetime", "Array", "Object"],
    "Send to AWS": ["Yes", "No"],
    "Required": ["Yes", "No"],
    "Contains PII": ["Yes", "No"],
    "Source System": ["Website", "Mobile App", "WebView", "Tealium", "Backend / API", "CRM", "AWS", "Third Party", "Calculated / Derived"],
    "Owner": ["Digital Analytics", "Marketing Analytics", "CRO / Optimisation", "Product", "Engineering", "Data Engineering", "Data Science", "Marketing", "Other"],
    "Status": ["Draft", "Active", "Deprecated", "Retired"],
    "Business Criticality": ["Low", "Medium", "High", "Critical"],
    "Journey": ["Global / All Journeys", "Vouchers", "Vodapay Club", "Airtime Advance", "Cash Advance", "Funeral Cover", "Compare / Quick Quote", "Business Term Advance", "POS / Buy POS", "Tap on Phone", "Other"],
}

AUTO_FIELDS = {"Date Added", "Last Updated"}


def get_token():
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return ""


def get_admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return ""


def require_admin(prefix):
    if not get_token() and not get_admin_password():
        return True
    if st.session_state.get("admin_authenticated", False):
        return True
    password = get_admin_password()
    if not password:
        st.warning("Editing is locked until ADMIN_PASSWORD is added to Streamlit Secrets.")
        return False
    entered = st.text_input("Administrator password", type="password", key=f"{prefix}_admin_password")
    if st.button("Unlock", key=f"{prefix}_unlock", type="primary"):
        if entered == password:
            st.session_state["admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect administrator password.")
    return False


def esc(value):
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def get_data():
    return load_dictionary(get_token() or None)


def find_row(frame, variable_name):
    matches = frame[frame["Variable Name"].astype(str) == str(variable_name)]
    return None if matches.empty else matches.iloc[0]


def header():
    st.markdown('<div class="app-kicker">ADOBE ANALYTICS REPLACEMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">Digital Analytics Data Dictionary</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Central reference for analytics variables, Tealium mappings, AWS fields and governance metadata.</div>', unsafe_allow_html=True)


def dropdown(field, current, key):
    options = list(DROPDOWN_OPTIONS[field])
    current_text = str(current).strip()

    # Preserve existing custom/legacy values when editing.
    if current_text and current_text not in options:
        options.append(current_text)

    defaults = {
        "Category": "Core / Technical",
        "Subcategory": "Not Applicable",
        "Data Type": "String",
        "Tealium Variable Type": "Data Layer Variable",
        "Send to AWS": "Yes",
        "Required": "No",
        "Contains PII": "No",
        "Source System": "Website",
        "Owner": "Digital Analytics",
        "Status": "Draft",
        "Business Criticality": "Medium",
        "Journey": "Global / All Journeys",
    }

    if not current_text:
        current_text = defaults[field]

    return st.selectbox(
        field + (" *" if field in {"Category", "Data Type"} else ""),
        options,
        index=options.index(current_text),
        key=key,
    )


def build_variable_form(frame, row=None, prefix="form"):
    values = {}
    current = {} if row is None else row.to_dict()

    st.markdown("### Main information")
    c1, c2 = st.columns(2)
    with c1:
        values["Variable Name"] = st.text_input("Variable name *", value=str(current.get("Variable Name", "")), key=f"{prefix}_variable_name")
        values["Friendly Name"] = st.text_input("Friendly name *", value=str(current.get("Friendly Name", "")), key=f"{prefix}_friendly_name")
        values["Category"] = dropdown("Category", current.get("Category", ""), f"{prefix}_category")
        if "Subcategory" in frame.columns:
            values["Subcategory"] = dropdown("Subcategory", current.get("Subcategory", ""), f"{prefix}_subcategory")
    with c2:
        values["Data Type"] = dropdown("Data Type", current.get("Data Type", ""), f"{prefix}_data_type")
        if "Tealium Variable Type" in frame.columns:
            values["Tealium Variable Type"] = dropdown("Tealium Variable Type", current.get("Tealium Variable Type", ""), f"{prefix}_tealium_type")
        values["Tealium Variable Name"] = st.text_input("Tealium variable name", value=str(current.get("Tealium Variable Name", "")), key=f"{prefix}_tealium_name")
        values["AWS Field Name"] = st.text_input("AWS field name", value=str(current.get("AWS Field Name", "")), key=f"{prefix}_aws_name")

    st.markdown("### Detailed information")
    already_rendered = {
        "Variable Name", "Friendly Name", "Category", "Subcategory", "Data Type",
        "Tealium Variable Type", "Tealium Variable Name", "AWS Field Name"
    }
    text_area_fields = {"Definition", "Allowed Values", "Notes"}
    detail_fields = [c for c in frame.columns if c not in already_rendered and c not in AUTO_FIELDS]
    cols = st.columns(2)

    for idx, field in enumerate(detail_fields):
        default = current.get(field, "")
        if row is None and field == "Schema Version":
            default = "1.0"

        with cols[idx % 2]:
            if field in DROPDOWN_OPTIONS:
                values[field] = dropdown(field, default, f"{prefix}_{field}")
            elif field in text_area_fields:
                values[field] = st.text_area(field, value=str(default), key=f"{prefix}_{field}")
            else:
                values[field] = st.text_input(field, value=str(default), key=f"{prefix}_{field}")

    # Audit dates are controlled by the application, not the user.
    today = date.today().isoformat()
    if row is None:
        values["Date Added"] = today
    else:
        existing_date_added = str(current.get("Date Added", "")).strip()
        values["Date Added"] = existing_date_added or today
    values["Last Updated"] = today

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
        st.info("Local test mode: Save will update your local Excel workbook only.")
    with st.form("add_variable_form"):
        values = build_variable_form(df, prefix="add")
        submitted = st.form_submit_button("Add variable", type="primary", use_container_width=True)
    if submitted:
        missing = [f for f in ["Variable Name", "Friendly Name", "Category", "Data Type"] if not str(values.get(f, "")).strip()]
        if missing:
            st.error(f"Please complete: {', '.join(missing)}")
            return
        try:
            create_variable(get_token() or None, values)
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add the variable: {exc}")


@st.dialog("Variable information")
def information_dialog(variable_name):
    row = find_row(df, variable_name)
    if row is None:
        st.error("That variable could not be found.")
        return
    st.markdown(f"## {esc(row.get('Friendly Name', variable_name))}", unsafe_allow_html=True)
    st.caption(str(row.get("Variable Name", "")))
    d1, d2 = st.columns(2)
    for idx, field in enumerate(df.columns):
        with (d1 if idx % 2 == 0 else d2):
            st.markdown(f'<div class="detail-box"><strong>{html.escape(field)}</strong><br>{esc(row.get(field, "")) or "—"}</div>', unsafe_allow_html=True)


@st.dialog("Edit variable")
def edit_variable_dialog(variable_name):
    row = find_row(df, variable_name)
    if row is None:
        st.error("That variable could not be found.")
        return
    if not require_admin(f"edit_{variable_name}"):
        return
    with st.form(f"edit_{variable_name}"):
        values = build_variable_form(df, row, f"edit_{variable_name}")
        submitted = st.form_submit_button("Save changes", type="primary", use_container_width=True)
    if submitted:
        try:
            update_variable(get_token() or None, variable_name, values)
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save changes: {exc}")


@st.dialog("Delete variable")
def delete_variable_dialog(variable_name):
    row = find_row(df, variable_name)
    if row is None:
        return
    if not require_admin(f"delete_{variable_name}"):
        return
    st.warning(f"Delete **{variable_name} — {row.get('Friendly Name','')}**?")
    confirm = st.checkbox("I understand this removes the full record.", key=f"confirm_{variable_name}")
    if st.button("Delete variable", type="primary", disabled=not confirm, use_container_width=True):
        try:
            delete_variable(get_token() or None, variable_name)
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not delete variable: {exc}")


header()
missing_definitions = int(df["Definition"].fillna("").astype(str).str.strip().eq("").sum())
aws_count = int(df["Send to AWS"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
pii_count = int(df["Contains PII"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
active_count = int(df["Status"].astype(str).str.lower().eq("active").sum())
metrics = [("Total variables", len(df)), ("Sent to AWS", aws_count), ("PII variables", pii_count), ("Missing definitions", missing_definitions), ("Active variables", active_count)]
for col, (label, value) in zip(st.columns(5), metrics):
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown("### Search & filter")
search = st.text_input("Search", placeholder="Search variable name, friendly name or definition...", label_visibility="collapsed")
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
    mask = pd.Series(False, index=filtered.index)
    for column in ["Variable Name", "Friendly Name", "Definition"]:
        mask |= filtered[column].fillna("").astype(str).str.lower().str.contains(term, regex=False)
    filtered = filtered[mask]
for column, selected in [("Category", category), ("Data Type", data_type), ("Status", status), ("Owner", owner)]:
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]

heading_col, add_col = st.columns([5, 1.25])
with heading_col:
    st.markdown(f"### Variables ({len(filtered)})")
with add_col:
    if st.button("＋ Add new variable", type="primary", use_container_width=True):
        add_variable_dialog()

widths = [1.4, 1.5, 1.15, 1.5, 1.35, .75, .55, .55]
headers = ["Variable name", "Friendly name", "Category", "Tealium variable name", "AWS field name", "More", "Edit", "Delete"]
for col, label in zip(st.columns(widths), headers):
    with col:
        st.markdown(f'<div class="table-header">{label}</div>', unsafe_allow_html=True)
st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

if filtered.empty:
    st.info("No variables match the current filters.")
else:
    for idx, row in filtered.reset_index(drop=True).iterrows():
        variable_name = str(row.get("Variable Name", ""))
        cols = st.columns(widths)
        for col, value in zip(cols[:5], [f"**{variable_name}**", str(row.get("Friendly Name", "")), str(row.get("Category", "")), str(row.get("Tealium Variable Name", "")), str(row.get("AWS Field Name", ""))]):
            with col:
                st.markdown(value)
        with cols[5]:
            if st.button("Info", key=f"info_{idx}_{variable_name}", use_container_width=True):
                information_dialog(variable_name)
        with cols[6]:
            if st.button("Edit", key=f"edit_{idx}_{variable_name}", use_container_width=True):
                edit_variable_dialog(variable_name)
        with cols[7]:
            if st.button("Delete", key=f"delete_{idx}_{variable_name}", use_container_width=True):
                delete_variable_dialog(variable_name)
        st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)

st.download_button("Download filtered list", data=filtered.to_csv(index=False).encode("utf-8"), file_name="digital_analytics_dictionary_filtered.csv", mime="text/csv")
st.caption("Documentation layer only — Tealium controls which variables are mapped and sent to AWS.")
