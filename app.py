import html
import math
from datetime import date

import pandas as pd
import streamlit as st

from utils.data_loader import load_dictionary, unique_values
from utils.github_store import (
    bulk_delete_variables, bulk_update_sent_to_aws, create_variable,
    delete_variable, update_variable,
)

st.set_page_config(
    page_title="Digital Analytics Data Dictionary",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --vodafone-red:#E60000;
        --ink:#111827;
        --muted:#667085;
        --line:rgba(148,163,184,.24);
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 12%, rgba(197,224,255,.68), transparent 31%),
            radial-gradient(circle at 88% 10%, rgba(255,197,214,.56), transparent 27%),
            radial-gradient(circle at 68% 78%, rgba(219,236,255,.62), transparent 34%),
            linear-gradient(135deg, #f7fbff 0%, #f5f8fc 48%, #fff7fa 100%);
        color:var(--ink);
    }

    .block-container {
        max-width:1560px;
        padding-top:1.55rem;
        padding-bottom:2.4rem;
    }

    [data-testid="stSidebar"] {
        background:rgba(248,251,255,.78);
        backdrop-filter:blur(18px);
        -webkit-backdrop-filter:blur(18px);
        border-right:1px solid rgba(148,163,184,.20);
    }
    [data-testid="stSidebar"] .block-container {padding-top:1.4rem;}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background:rgba(255,255,255,.72) !important;
        border-color:rgba(148,163,184,.30) !important;
        border-radius:10px !important;
    }

    .brand-row {display:flex; align-items:center; gap:10px; margin-bottom:1.2rem;}
    .brand-mark {
        width:34px; height:34px; border-radius:50%;
        background:var(--vodafone-red); color:#fff;
        display:flex; align-items:center; justify-content:center;
        font-size:19px; font-weight:900;
        box-shadow:0 8px 20px rgba(230,0,0,.18);
    }
    .brand-name {font-size:1.18rem; font-weight:850; color:var(--vodafone-red); letter-spacing:-.02em;}

    .sidebar-kicker {font-size:.68rem; font-weight:800; letter-spacing:.12em; color:#475467; margin-bottom:.2rem;}
    .sidebar-title {font-size:1.08rem; font-weight:800; color:#101828; margin-bottom:.2rem;}
    .sidebar-copy {font-size:.8rem; color:#667085; line-height:1.45; margin-bottom:1rem;}
    .sidebar-footer {
        margin-top:1rem; padding:12px 13px;
        background:rgba(255,255,255,.58); border:1px solid var(--line);
        border-radius:12px; font-size:.76rem; color:#667085; line-height:1.45;
    }

    .app-kicker {font-size:.72rem; font-weight:850; letter-spacing:.16em; color:#344054; margin-bottom:.18rem;}
    .app-title {font-size:2.35rem; line-height:1.05; font-weight:850; letter-spacing:-.035em; color:#0f172a; margin-bottom:.35rem;}
    .app-subtitle {font-size:.96rem; color:#667085; margin-bottom:0;}

    .metric-card {
        background:rgba(255,255,255,.72);
        border:1px solid rgba(255,255,255,.82);
        box-shadow:0 10px 28px rgba(31,41,55,.055);
        backdrop-filter:blur(16px);
        -webkit-backdrop-filter:blur(16px);
        border-radius:14px;
        padding:16px 17px;
        min-height:82px;
        display:flex;
        flex-direction:column;
        justify-content:center;
    }
    .metric-value {font-size:1.55rem; font-weight:850; color:#101828; line-height:1.05;}
    .metric-label {font-size:.76rem; color:#667085; margin-top:5px;}

    .search-label {
        font-size:.78rem;
        color:#667085;
        font-weight:700;
        margin-top:1rem;
        margin-bottom:.25rem;
    }

    .registry-shell {
        margin-top:.9rem;
        background:rgba(255,255,255,.72);
        border:1px solid rgba(255,255,255,.84);
        border-radius:16px;
        box-shadow:0 14px 38px rgba(31,41,55,.06);
        backdrop-filter:blur(18px);
        -webkit-backdrop-filter:blur(18px);
        padding:15px 17px 12px;
    }
    .registry-title {font-size:1.22rem; font-weight:850; color:#101828; margin-bottom:2px;}
    .registry-copy {font-size:.8rem; color:#667085;}
    .result-pill {
        display:inline-block; padding:5px 10px; border-radius:999px;
        background:#eef4fb; color:#475467; font-size:.72rem; font-weight:700;
    }
    .table-header {
        font-size:.68rem; font-weight:800; color:#475467;
        text-transform:uppercase; letter-spacing:.045em; padding:8px 2px;
    }
    .row-spacer {height:7px;}
    .row-card-marker {
        height:1px;
        background:rgba(148,163,184,.12);
        border-radius:999px;
        margin:0 4px;
    }

    .friendly-primary {font-size:.86rem; font-weight:700; color:#25324a; padding-top:5px; line-height:1.25;}
    .friendly-secondary {font-size:.72rem; color:#8a94a6; margin-top:2px; line-height:1.25;}
    .cell-text {font-size:.82rem; color:#475467; padding-top:9px; line-height:1.3;}
    .owner-wrap {display:flex; align-items:center; gap:8px; padding-top:5px;}
    .owner-avatar {
        width:27px; height:27px; border-radius:50%; background:#e8edf3;
        color:#344054; font-size:.65rem; font-weight:850;
        display:flex; align-items:center; justify-content:center;
    }
    .owner-name {font-size:.78rem; color:#344054; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
    .pill {display:inline-flex; align-items:center; border-radius:999px; padding:4px 9px; margin-top:5px; font-size:.7rem; font-weight:750; white-space:nowrap;}
    .pill-green {background:#d9f8e8; color:#087443;}
    .pill-amber {background:#fff0c7; color:#9a6700;}
    .pill-red {background:#fee4e2; color:#b42318;}
    .pill-gray {background:#eef2f6; color:#475467;}
    .pill-blue {background:#e8f1ff; color:#315b9b;}

    .detail-box {
        background:rgba(248,250,252,.88);
        border:1px solid rgba(148,163,184,.18);
        border-radius:11px; padding:12px 14px; margin-bottom:10px; min-height:68px;
    }
    .detail-box strong {font-size:.7rem; color:#667085; text-transform:uppercase; letter-spacing:.04em;}
    .detail-box div {margin-top:5px; color:#25324a; font-size:.88rem; line-height:1.42;}
    .footer-note {font-size:.74rem; color:#7b8494; padding-top:1rem;}

    div[data-testid="stDialog"] div[role="dialog"] {
        max-width:1080px; width:min(1080px,95vw);
        border-radius:18px;
        background:rgba(255,255,255,.94);
        backdrop-filter:blur(20px);
        -webkit-backdrop-filter:blur(20px);
        border:1px solid rgba(255,255,255,.9);
        box-shadow:0 24px 80px rgba(15,23,42,.18);
    }
    div[data-testid="stDialog"] [data-testid="stForm"] {border:0; padding:0;}

    /* Make Add/Edit form controls visibly editable against the glass background. */
    div[data-testid="stDialog"] [data-testid="stTextInput"] input,
    div[data-testid="stDialog"] [data-testid="stTextArea"] textarea {
        border:1px solid #111827 !important;
        border-radius:8px !important;
        background:#ffffff !important;
        box-shadow:none !important;
    }
    div[data-testid="stDialog"] [data-testid="stTextInput"] > div > div,
    div[data-testid="stDialog"] [data-testid="stTextArea"] > div > div {
        border-color:#111827 !important;
        border-radius:8px !important;
    }
    div[data-testid="stDialog"] [data-baseweb="select"] > div {
        border:1px solid #111827 !important;
        border-radius:8px !important;
        background:#ffffff !important;
        box-shadow:none !important;
    }
    div[data-testid="stDialog"] [data-testid="stTextInput"] input:focus,
    div[data-testid="stDialog"] [data-testid="stTextArea"] textarea:focus,
    div[data-testid="stDialog"] [data-baseweb="select"] > div:focus-within {
        border-color:#111827 !important;
        box-shadow:0 0 0 1px #111827 !important;
    }
    div[data-testid="stDialog"] input:disabled {
        border-color:#667085 !important;
        background:#f2f4f7 !important;
    }

    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        border-radius:10px;
        min-height:40px;
        width:100%;
    }
    div[data-testid="stButton"] button p,
    div[data-testid="stDownloadButton"] button p {
        white-space:nowrap !important;
    }
    div[data-testid="stTabs"] button {font-weight:700;}

    div[data-testid="stButton"] button[kind="tertiary"] {
        justify-content:flex-start; padding:4px 0; min-height:0;
        border:0; background:transparent; color:#075bd8;
        font-weight:800; font-size:.84rem; text-decoration:none;
    }
    div[data-testid="stButton"] button[kind="tertiary"] p {
        white-space:normal !important;
        overflow-wrap:anywhere;
        word-break:break-word;
        text-align:left;
        line-height:1.25;
    }
    div[data-testid="stButton"] button[kind="tertiary"]:hover {
        color:var(--vodafone-red); background:transparent; text-decoration:underline;
    }

    @media (max-width: 900px) {
        .app-title {font-size:1.9rem;}
        .metric-card {min-height:74px;}
        .block-container {padding-left:1rem; padding-right:1rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DROPDOWN_OPTIONS = {
    "Tealium Variable Type": [
        "Data Layer Variable", "JavaScript Variable", "DOM Variable", "Cookie",
        "Query String Parameter", "Meta Data Element", "UDO Variable", "Other",
    ],
    "Category": [
        "Core / Technical", "Page", "Journey", "Event", "Visitor", "Customer",
        "Product", "Transaction", "Marketing", "Campaign", "Device", "Search",
        "Personalisation", "Consent / Permissions", "Errors", "Video",
        "Experimentation / A/B Testing",
    ],
    "Data Type": ["String", "Integer", "Decimal", "Boolean", "Date", "Datetime", "Array", "Object"],
    "Sent to AWS": ["Yes", "No"],
    "Contains PII": ["Yes", "No"],
    "Source System": [
        "Website", "Mobile App", "WebView", "Tealium", "Backend / API", "CRM",
        "AWS", "Third Party", "Calculated / Derived",
    ],
    "Owner": [
        "Digital Analytics", "Marketing Analytics", "CRO / Optimisation", "Product",
        "Engineering", "Data Engineering", "Data Science", "Marketing", "Other",
    ],
    "Status": ["Draft", "Active", "Deprecated", "Retired"],
    "Business Criticality": ["Low", "Medium", "High", "Critical"],
    "Journey": [
        "Global / All Journeys", "Vouchers", "Vodapay Club", "Airtime Advance",
        "Cash Advance", "Funeral Cover", "Compare / Quick Quote", "Business Term Advance",
        "POS / Buy POS", "Tap on Phone", "Other",
    ],
}

AUTO_FIELDS = {"Date Added", "Last Updated"}
REMOVED_FIELDS = {"PII Classification", "Deprecated Replacement", "Required", "Subcategory"}
REQUIRED_FIELDS = [
    "Variable Name", "Friendly Name", "Category", "Definition", "Data Type",
    "Tealium Variable Name", "Sent to AWS", "Tealium Variable Type", "AWS Field Name",
    "Owner", "Status",
]
MAIN_FIELDS = ["Variable Name", "Friendly Name", "Category", "Definition", "Data Type", "Example Value"]
DETAIL_FIELDS = [
    "Allowed Values", "Tealium Variable Type", "Tealium Variable Name", "AWS Field Name",
    "Sent to AWS", "Source System", "Journey",
]
GOVERNANCE_FIELDS = ["Contains PII", "Owner", "Status", "Business Criticality", "Schema Version", "Notes"]


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
            st.rerun(scope="fragment")
        else:
            st.error("Incorrect administrator password.")
    return False


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def esc(value):
    return html.escape(clean_text(value))


def get_data():
    return load_dictionary(get_token() or None)


def find_row(frame, variable_name):
    matches = frame[frame["Variable Name"].astype(str) == str(variable_name)]
    return None if matches.empty else matches.iloc[0]


def dropdown(field, current, key, required=False):
    options = [""] + list(DROPDOWN_OPTIONS[field])
    current_text = clean_text(current)
    if current_text and current_text not in options:
        options.append(current_text)
    index = options.index(current_text) if current_text in options else 0
    return st.selectbox(
        field + (" *" if required else ""),
        options,
        index=index,
        key=key,
        format_func=lambda value: "Select an option..." if value == "" else value,
    )


def render_field(field, current, values, prefix, required=False):
    default = clean_text(current)
    label = field + (" *" if required else "")
    if field in DROPDOWN_OPTIONS:
        values[field] = dropdown(field, current, f"{prefix}_{field}", required)
    elif field in {"Definition", "Allowed Values", "Notes"}:
        values[field] = st.text_area(
            label,
            value=default,
            key=f"{prefix}_{field}",
            height=110 if field == "Definition" else 90,
        )
    else:
        values[field] = st.text_input(label, value=default, key=f"{prefix}_{field}")


def render_form_section(fields, frame, current, values, prefix):
    available = [field for field in fields if field in frame.columns]
    left, right = st.columns(2, gap="large")
    for idx, field in enumerate(available):
        with (left if idx % 2 == 0 else right):
            render_field(field, current.get(field, ""), values, prefix, field in REQUIRED_FIELDS)


def build_variable_form(frame, row=None, prefix="form"):
    values = {}
    current = {} if row is None else row.to_dict()
    main_tab, technical_tab, governance_tab = st.tabs(
        ["Main Information", "Technical Details", "Governance"]
    )

    with main_tab:
        st.caption("Core naming, definition and data structure for this analytics variable.")
        render_form_section(MAIN_FIELDS, frame, current, values, prefix)
    with technical_tab:
        st.caption("Tealium implementation, AWS mapping and source-system information.")
        render_form_section(DETAIL_FIELDS, frame, current, values, prefix)
    with governance_tab:
        st.caption("Ownership, lifecycle, privacy and governance metadata.")
        render_form_section(GOVERNANCE_FIELDS, frame, current, values, prefix)
        if row is not None:
            st.markdown("---")
            audit_left, audit_right = st.columns(2)
            with audit_left:
                st.text_input(
                    "Date Added",
                    value=clean_text(current.get("Date Added", "")),
                    disabled=True,
                    key=f"{prefix}_date_added",
                )
            with audit_right:
                st.text_input(
                    "Last Updated",
                    value=clean_text(current.get("Last Updated", "")),
                    disabled=True,
                    key=f"{prefix}_last_updated",
                )

    displayed = set(MAIN_FIELDS + DETAIL_FIELDS + GOVERNANCE_FIELDS) | AUTO_FIELDS | REMOVED_FIELDS
    for field in frame.columns:
        if field not in displayed:
            values[field] = current.get(field, "")
    for field in REMOVED_FIELDS:
        if field in frame.columns:
            values[field] = current.get(field, "") if row is not None else ""

    today = date.today().isoformat()
    values["Date Added"] = today if row is None else clean_text(current.get("Date Added", "")) or today
    values["Last Updated"] = today
    return values


def missing_required_fields(values):
    return [field for field in REQUIRED_FIELDS if not clean_text(values.get(field, ""))]


def detail_card(field, value):
    st.markdown(
        f'<div class="detail-box"><strong>{html.escape(field)}</strong><div>{esc(value) or "—"}</div></div>',
        unsafe_allow_html=True,
    )


def render_info_section(row, fields, frame):
    available = [field for field in fields if field in frame.columns]
    left, right = st.columns(2, gap="large")
    for idx, field in enumerate(available):
        with (left if idx % 2 == 0 else right):
            detail_card(field, row.get(field, ""))


def status_pill(value):
    label = clean_text(value) or "Not set"
    css = "pill-gray"
    if label.lower() == "active":
        css = "pill-green"
    elif label.lower() == "draft":
        css = "pill-amber"
    elif label.lower() in {"deprecated", "retired"}:
        css = "pill-red"
    return f'<span class="pill {css}">{html.escape(label)}</span>'


def aws_pill(value):
    yes = clean_text(value).lower() in {"yes", "true", "1"}
    css = "pill-green" if yes else "pill-gray"
    label = "Yes" if yes else "No"
    return f'<span class="pill {css}">{label}</span>'


def type_pill(value):
    label = clean_text(value) or "—"
    return f'<span class="pill pill-blue">{html.escape(label)}</span>'


def initials(name):
    parts = [p for p in clean_text(name).replace("/", " ").split() if p]
    if not parts:
        return "—"
    return "".join(part[0].upper() for part in parts[:2])


def clear_filters():
    for key in ["filter_category", "filter_data_type", "filter_status", "filter_owner", "filter_sent_to_aws"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["registry_page"] = 1


try:
    df = get_data()
except Exception as exc:
    st.error(f"Could not load the analytics dictionary: {exc}")
    st.stop()


@st.dialog("Add Variable")
def add_variable_dialog():
    st.caption("Create a governed analytics variable. Fields marked * are required.")
    if not require_admin("add"):
        return
    if not get_token():
        st.info("Local test mode: Save updates your local CSV file only.")
    with st.form("add_variable_form"):
        values = build_variable_form(df, prefix="add")
        _, action = st.columns([3.4, 1])
        with action:
            submitted = st.form_submit_button("Add Variable", type="primary", use_container_width=True)
    if submitted:
        missing = missing_required_fields(values)
        if missing:
            st.error(f"Please complete all required fields: {', '.join(missing)}")
            return
        try:
            create_variable(get_token() or None, values)
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add the variable: {exc}")


@st.dialog("Variable")
def variable_dialog(variable_name):
    row = find_row(df, variable_name)
    if row is None:
        st.error("That variable could not be found.")
        return

    mode_key = f"variable_dialog_mode_{variable_name}"
    mode = st.session_state.get(mode_key, "view")

    if mode == "edit":
        st.markdown(f"### Edit {esc(row.get('Friendly Name', variable_name))}", unsafe_allow_html=True)
        st.caption(f"{variable_name} · Fields marked * are required.")
        if not require_admin(f"edit_{variable_name}"):
            return
        with st.form(f"edit_form_{variable_name}"):
            values = build_variable_form(df, row, f"edit_{variable_name}")
            _, save_col = st.columns([3.4, 1])
            with save_col:
                submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
        if st.button("← Back to variable", key=f"back_edit_{variable_name}"):
            st.session_state[mode_key] = "view"
            st.rerun(scope="fragment")
        if submitted:
            missing = missing_required_fields(values)
            if missing:
                st.error(f"Please complete all required fields: {', '.join(missing)}")
                return
            try:
                update_variable(get_token() or None, variable_name, values)
                st.cache_data.clear()
                st.session_state[mode_key] = "view"
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save changes: {exc}")
        return

    if mode == "delete":
        st.markdown("### Delete Variable")
        st.warning(
            f"You are about to permanently delete **{variable_name} — {clean_text(row.get('Friendly Name', ''))}**."
        )
        if not require_admin(f"delete_{variable_name}"):
            return
        confirm = st.checkbox("I understand this removes the full record.", key=f"confirm_{variable_name}")
        back_col, delete_col = st.columns([3.4, 1])
        with back_col:
            if st.button("← Back", key=f"back_delete_{variable_name}"):
                st.session_state[mode_key] = "view"
                st.rerun(scope="fragment")
        with delete_col:
            if st.button(
                "Delete Variable",
                type="primary",
                disabled=not confirm,
                use_container_width=True,
                key=f"confirm_delete_{variable_name}",
            ):
                try:
                    delete_variable(get_token() or None, variable_name)
                    st.cache_data.clear()
                    st.session_state.pop(mode_key, None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete variable: {exc}")
        return

    st.markdown(f"### {esc(row.get('Friendly Name', variable_name))}", unsafe_allow_html=True)
    st.caption(f"{variable_name}  ·  {clean_text(row.get('Status', '')) or 'Status not set'}")
    main_tab, technical_tab, governance_tab = st.tabs(["Main Information", "Technical Details", "Governance"])
    with main_tab:
        render_info_section(row, MAIN_FIELDS, df)
    with technical_tab:
        render_info_section(row, DETAIL_FIELDS, df)
    with governance_tab:
        render_info_section(row, GOVERNANCE_FIELDS + ["Date Added", "Last Updated"], df)

    st.markdown("---")
    _, edit_col, delete_col = st.columns([3, 1, 1])
    with edit_col:
        if st.button("Edit Variable", type="primary", use_container_width=True, key=f"modal_edit_{variable_name}"):
            st.session_state[mode_key] = "edit"
            st.rerun(scope="fragment")
    with delete_col:
        if st.button("Delete", use_container_width=True, key=f"modal_delete_{variable_name}"):
            st.session_state[mode_key] = "delete"
            st.rerun(scope="fragment")


@st.dialog("Change Sent to AWS")
def bulk_aws_dialog(variable_names):
    st.markdown(f"### Update {len(variable_names)} selected variable{'s' if len(variable_names) != 1 else ''}")
    st.caption("Choose whether the selected variables should be marked as sent to AWS.")
    if not require_admin("bulk_aws"):
        return

    target_value = st.radio(
        "Sent to AWS",
        ["Yes", "No"],
        horizontal=True,
        key="bulk_aws_target",
    )
    st.caption("Selected variables: " + ", ".join(variable_names))

    if st.button("Apply to selected variables", type="primary", use_container_width=True, key="bulk_aws_apply"):
        try:
            bulk_update_sent_to_aws(get_token() or None, variable_names, target_value)
            st.cache_data.clear()
            st.session_state["bulk_variable_selection"] = []
            st.rerun()
        except Exception as exc:
            st.error(f"Could not update selected variables: {exc}")


@st.dialog("Delete Selected Variables")
def bulk_delete_dialog(variable_names):
    st.markdown(f"### Delete {len(variable_names)} selected variable{'s' if len(variable_names) != 1 else ''}")
    st.warning("This action permanently removes all selected variable records.")
    st.caption("Selected variables: " + ", ".join(variable_names))
    if not require_admin("bulk_delete"):
        return

    confirm = st.checkbox(
        "I understand that all selected variables will be permanently deleted.",
        key="bulk_delete_confirm",
    )
    if st.button(
        "Delete selected variables",
        type="primary",
        use_container_width=True,
        disabled=not confirm,
        key="bulk_delete_apply",
    ):
        try:
            bulk_delete_variables(get_token() or None, variable_names)
            st.cache_data.clear()
            st.session_state["bulk_variable_selection"] = []
            st.rerun()
        except Exception as exc:
            st.error(f"Could not delete selected variables: {exc}")


with st.sidebar:
    st.markdown(
        '<div class="brand-row"><div class="brand-mark">V</div><div class="brand-name">vodafone</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-kicker">DIGITAL ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Filters</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-copy">Refine the data dictionary using the fields below.</div>',
        unsafe_allow_html=True,
    )
    category = st.multiselect("Category", unique_values(df, "Category"), key="filter_category")
    data_type = st.multiselect("Data Type", unique_values(df, "Data Type"), key="filter_data_type")
    status = st.multiselect("Status", unique_values(df, "Status"), key="filter_status")
    owner = st.multiselect("Owner", unique_values(df, "Owner"), key="filter_owner")
    sent_to_aws = st.multiselect("Sent to AWS", unique_values(df, "Sent to AWS"), key="filter_sent_to_aws")
    st.button("Reset all", use_container_width=True, on_click=clear_filters)
    st.markdown(
        '<div class="sidebar-footer"><strong>Schema v1.0</strong><br>Documentation layer only.<br>Tealium controls which variables are mapped and sent to AWS.</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="app-kicker">DIGITAL ANALYTICS</div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">Data Dictionary</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">A central registry of digital analytics variables, definitions and mappings.</div>',
    unsafe_allow_html=True,
)

st.write("")
missing_definitions = int(df["Definition"].fillna("").astype(str).str.strip().eq("").sum())
aws_count = int(df["Sent to AWS"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
pii_count = int(df["Contains PII"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
active_count = int(df["Status"].astype(str).str.lower().eq("active").sum())
metrics = [
    ("Total Variables", len(df)),
    ("Active", active_count),
    ("Sent to AWS", aws_count),
    ("PII Variables", pii_count),
    ("Missing Definitions", missing_definitions),
]
for col, (label, value) in zip(st.columns(5, gap="medium"), metrics):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="search-label">Search variables</div>', unsafe_allow_html=True)
search = st.text_input(
    "Search variables",
    placeholder="Search by variable name, friendly name or definition...",
    key="main_search",
    label_visibility="collapsed",
)

filtered = df.copy()
if search.strip():
    term = search.strip().lower()
    mask = pd.Series(False, index=filtered.index)
    for column in ["Variable Name", "Friendly Name", "Definition"]:
        mask |= filtered[column].fillna("").astype(str).str.lower().str.contains(term, regex=False)
    filtered = filtered[mask]
for column, selected in [
    ("Category", category),
    ("Data Type", data_type),
    ("Status", status),
    ("Owner", owner),
    ("Sent to AWS", sent_to_aws),
]:
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]
filtered = filtered.sort_values(by="Variable Name", key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)

button_left, export_col, add_col = st.columns([4.2, 1.15, 1.35], gap="small")
with export_col:
    st.download_button(
        "⇩ Export",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="digital_analytics_dictionary_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )
with add_col:
    if st.button("＋ Add Variable", type="primary", use_container_width=True):
        add_variable_dialog()


st.markdown('<div class="search-label">Bulk actions</div>', unsafe_allow_html=True)
bulk_options = filtered["Variable Name"].astype(str).tolist()
selected_variables = st.multiselect(
    "Select variables",
    options=bulk_options,
    key="bulk_variable_selection",
    placeholder="Select one or more variables...",
    label_visibility="collapsed",
)
bulk_left, bulk_aws_col, bulk_delete_col = st.columns([3.6, 1.4, 1.35], gap="small")
with bulk_left:
    if selected_variables:
        st.caption(f"{len(selected_variables)} variable{'s' if len(selected_variables) != 1 else ''} selected")
    else:
        st.caption("Select multiple variables to update Sent to AWS or delete them.")
with bulk_aws_col:
    if st.button(
        "Change Sent to AWS",
        use_container_width=True,
        disabled=not selected_variables,
        key="bulk_aws_button",
    ):
        bulk_aws_dialog(selected_variables)
with bulk_delete_col:
    if st.button(
        "Delete Selected",
        use_container_width=True,
        disabled=not selected_variables,
        key="bulk_delete_button",
    ):
        bulk_delete_dialog(selected_variables)

st.markdown('<div class="registry-shell">', unsafe_allow_html=True)
reg_left, reg_right = st.columns([5, 1])
with reg_left:
    st.markdown('<div class="registry-title">Variables</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="registry-copy">Click a variable name to view its full definition and manage the record.</div>',
        unsafe_allow_html=True,
    )
with reg_right:
    st.markdown(
        f'<div style="text-align:right;padding-top:6px;"><span class="result-pill">{len(filtered)} results</span></div>',
        unsafe_allow_html=True,
    )

page_size = 10
total_pages = max(1, math.ceil(len(filtered) / page_size))
if "registry_page" not in st.session_state:
    st.session_state["registry_page"] = 1
st.session_state["registry_page"] = min(max(1, st.session_state["registry_page"]), total_pages)
page = st.session_state["registry_page"]
start = (page - 1) * page_size
end = min(start + page_size, len(filtered))
page_frame = filtered.iloc[start:end]

widths = [1.35, 1.8, 1.15, .85, .85, .8, 1.15, 1.0]
headers = [
    "Variable Name", "Friendly Name", "Category", "Data Type",
    "Status", "Sent to AWS", "Owner", "Last Updated",
]
for col, label in zip(st.columns(widths), headers):
    with col:
        st.markdown(f'<div class="table-header">{label}</div>', unsafe_allow_html=True)

if page_frame.empty:
    st.info("No variables match the current search or filters.")
else:
    for display_idx, (idx, row) in enumerate(page_frame.iterrows()):
        if display_idx > 0:
            st.markdown(
                '<div class="row-spacer"></div><div class="row-card-marker"></div><div class="row-spacer"></div>',
                unsafe_allow_html=True,
            )
        variable_name = clean_text(row.get("Variable Name", ""))
        row_key = f"{idx}_{variable_name}"
        cols = st.columns(widths)
        with cols[0]:
            if st.button(variable_name or "Unnamed", key=f"open_{row_key}", type="tertiary"):
                st.session_state[f"variable_dialog_mode_{variable_name}"] = "view"
                variable_dialog(variable_name)
        with cols[1]:
            friendly = esc(row.get("Friendly Name", "")) or "—"
            definition = clean_text(row.get("Definition", ""))
            short_def = html.escape(definition[:62] + ("…" if len(definition) > 62 else "")) if definition else "No definition"
            st.markdown(
                f'<div class="friendly-primary">{friendly}</div><div class="friendly-secondary">{short_def}</div>',
                unsafe_allow_html=True,
            )
        with cols[2]:
            st.markdown(f'<div class="cell-text">{esc(row.get("Category", "")) or "—"}</div>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown(type_pill(row.get("Data Type", "")), unsafe_allow_html=True)
        with cols[4]:
            st.markdown(status_pill(row.get("Status", "")), unsafe_allow_html=True)
        with cols[5]:
            st.markdown(aws_pill(row.get("Sent to AWS", "")), unsafe_allow_html=True)
        with cols[6]:
            owner_name = clean_text(row.get("Owner", "")) or "Unassigned"
            st.markdown(
                f'<div class="owner-wrap"><div class="owner-avatar">{html.escape(initials(owner_name))}</div><div class="owner-name">{html.escape(owner_name)}</div></div>',
                unsafe_allow_html=True,
            )
        with cols[7]:
            st.markdown(f'<div class="cell-text">{esc(row.get("Last Updated", "")) or "—"}</div>', unsafe_allow_html=True)

st.write("")
page_info, prev_col, next_col = st.columns([5.5, 1.35, 1.05], gap="small")
with page_info:
    if len(filtered):
        st.caption(f"Showing {start + 1}–{end} of {len(filtered)} variables · Page {page} of {total_pages}")
    else:
        st.caption("Showing 0 variables")
with prev_col:
    if st.button("‹ Previous", use_container_width=True, disabled=page <= 1):
        st.session_state["registry_page"] = page - 1
        st.rerun()
with next_col:
    if st.button("Next ›", use_container_width=True, disabled=page >= total_pages):
        st.session_state["registry_page"] = page + 1
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
st.markdown(
    '<div class="footer-note">Better Data. Smarter Decisions. A More Connected Tomorrow.</div>',
    unsafe_allow_html=True,
)