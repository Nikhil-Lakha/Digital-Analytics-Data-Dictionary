import html
from datetime import date

import pandas as pd
import streamlit as st

from utils.data_loader import load_dictionary, unique_values
from utils.github_store import create_variable, delete_variable, update_variable

st.set_page_config(
    page_title="Digital Analytics Data Dictionary",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top:1.35rem; padding-bottom:2.5rem; max-width:1500px;}
    [data-testid="stSidebar"] {background:#f7f7f8; border-right:1px solid #e9e9eb;}
    [data-testid="stSidebar"] .block-container {padding-top:1.5rem;}

    .sidebar-kicker {font-size:.72rem; font-weight:800; letter-spacing:.1em; color:#E60000; margin-bottom:.25rem;}
    .sidebar-title {font-size:1.15rem; font-weight:800; color:#1f1f1f; margin-bottom:.2rem;}
    .sidebar-copy {font-size:.84rem; color:#747474; margin-bottom:1.2rem; line-height:1.45;}

    .app-kicker {font-size:.76rem; font-weight:800; letter-spacing:.1em; color:#E60000; margin-bottom:.2rem;}
    .app-title {font-size:2rem; line-height:1.1; font-weight:800; color:#171717; margin-bottom:.35rem;}
    .app-subtitle {font-size:.95rem; color:#6b6b6b; margin-bottom:.45rem;}
    .schema-badge {display:inline-block; font-size:.72rem; font-weight:700; color:#555; background:#f4f4f5; border:1px solid #e4e4e7; border-radius:999px; padding:4px 9px; margin-top:2px;}

    .metric-card {background:#fff; border:1px solid #e7e7e9; border-radius:10px; padding:12px 14px; box-shadow:0 1px 2px rgba(0,0,0,.025);}
    .metric-label {font-size:.76rem; color:#777; margin-bottom:2px;}
    .metric-value {font-size:1.35rem; font-weight:800; color:#202020; line-height:1.2;}

    .section-title {font-size:1.12rem; font-weight:800; color:#1f1f1f; margin-top:.3rem; margin-bottom:.1rem;}
    .section-copy {font-size:.82rem; color:#777; margin-bottom:.65rem;}
    .toolbar-note {font-size:.8rem; color:#777; padding-top:.5rem;}

    .registry-header {background:#f6f6f7; border:1px solid #e7e7e9; border-radius:10px; padding:3px 12px; margin-top:.25rem; margin-bottom:2px;}
    .table-header {font-size:.7rem; font-weight:800; color:#6f6f73; text-transform:uppercase; letter-spacing:.045em; padding:8px 3px;}
    .registry-row {border-bottom:1px solid #ededee; padding:5px 12px 6px 12px;}
    .cell-text {color:#454549; font-size:.88rem; padding-top:8px; line-height:1.35;}
    .cell-muted {color:#737378; font-size:.82rem; padding-top:8px; line-height:1.35;}
    .mapping-value {font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color:#4d4d52; font-size:.82rem; padding-top:8px; overflow-wrap:anywhere;}
    .status-badge {display:inline-flex; align-items:center; gap:6px; border:1px solid #e1e1e4; background:#f7f7f8; border-radius:999px; padding:4px 9px; margin-top:5px; font-size:.74rem; font-weight:700; color:#444; white-space:nowrap;}
    .status-dot {width:7px; height:7px; background:#777; border-radius:50%; display:inline-block;}

    .detail-box {background:#fbfbfc; border:1px solid #e9e9eb; border-radius:9px; padding:12px 14px; margin-bottom:9px; min-height:68px;}
    .detail-box strong {font-size:.75rem; color:#686868; text-transform:uppercase; letter-spacing:.025em;}
    .modal-heading {font-size:1.35rem; font-weight:800; color:#1d1d1f; margin-bottom:2px;}
    .modal-meta {font-size:.82rem; color:#777; margin-bottom:.7rem;}
    .modal-actions {border-top:1px solid #ececee; margin-top:.8rem; padding-top:.9rem;}

    div[data-testid="stDialog"] div[role="dialog"] {max-width:1080px; width:min(1080px, 95vw); border-radius:16px;}
    div[data-testid="stDialog"] [data-testid="stForm"] {border:0; padding:0;}
    div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button {border-radius:8px;}
    div[data-testid="stTabs"] button {font-weight:650;}

    /* Variable-name buttons behave like clean table links. */
    div[data-testid="stButton"] button[kind="tertiary"] {
        justify-content:flex-start;
        padding:5px 0;
        min-height:0;
        border:0;
        background:transparent;
        color:#202024;
        font-weight:750;
        font-size:.9rem;
        text-decoration:none;
    }
    div[data-testid="stButton"] button[kind="tertiary"]:hover {
        color:#E60000;
        background:transparent;
        text-decoration:underline;
    }
    hr {margin:.8rem 0 1rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

DROPDOWN_OPTIONS = {
    "Tealium Variable Type": [
        "Data Layer Variable",
        "JavaScript Variable",
        "DOM Variable",
        "Cookie",
        "Query String Parameter",
        "Meta Data Element",
        "UDO Variable",
        "Other",
    ],
    "Category": [
        "Core / Technical",
        "Page",
        "Journey",
        "Event",
        "Visitor",
        "Customer",
        "Product",
        "Transaction",
        "Marketing",
        "Campaign",
        "Device",
        "Search",
        "Personalisation",
        "Consent / Permissions",
        "Errors",
        "Video",
        "Experimentation / A/B Testing",
    ],
    "Data Type": ["String", "Integer", "Decimal", "Boolean", "Date", "Datetime", "Array", "Object"],
    "Send to AWS": ["Yes", "No"],
    "Contains PII": ["Yes", "No"],
    "Source System": [
        "Website",
        "Mobile App",
        "WebView",
        "Tealium",
        "Backend / API",
        "CRM",
        "AWS",
        "Third Party",
        "Calculated / Derived",
    ],
    "Owner": [
        "Digital Analytics",
        "Marketing Analytics",
        "CRO / Optimisation",
        "Product",
        "Engineering",
        "Data Engineering",
        "Data Science",
        "Marketing",
        "Other",
    ],
    "Status": ["Draft", "Active", "Deprecated", "Retired"],
    "Business Criticality": ["Low", "Medium", "High", "Critical"],
    "Journey": [
        "Global / All Journeys",
        "Vouchers",
        "Vodapay Club",
        "Airtime Advance",
        "Cash Advance",
        "Funeral Cover",
        "Compare / Quick Quote",
        "Business Term Advance",
        "POS / Buy POS",
        "Tap on Phone",
        "Other",
    ],
}

AUTO_FIELDS = {"Date Added", "Last Updated"}
REMOVED_FIELDS = {"PII Classification", "Deprecated Replacement", "Required", "Subcategory"}

REQUIRED_FIELDS = [
    "Variable Name",
    "Friendly Name",
    "Category",
    "Definition",
    "Data Type",
    "Tealium Variable Name",
    "Send to AWS",
    "Tealium Variable Type",
    "AWS Field Name",
    "Owner",
    "Status",
]

MAIN_FIELDS = [
    "Variable Name",
    "Friendly Name",
    "Category",
    "Definition",
    "Data Type",
    "Example Value",
]

DETAIL_FIELDS = [
    "Allowed Values",
    "Tealium Variable Type",
    "Tealium Variable Name",
    "AWS Field Name",
    "Send to AWS",
    "Source System",
    "Journey",
]

GOVERNANCE_FIELDS = [
    "Contains PII",
    "Owner",
    "Status",
    "Business Criticality",
    "Schema Version",
    "Notes",
]


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


def esc(value):
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def clean_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


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
    if field in DROPDOWN_OPTIONS:
        values[field] = dropdown(field, current, f"{prefix}_{field}", required=required)
    elif field in {"Definition", "Allowed Values", "Notes"}:
        values[field] = st.text_area(
            field + (" *" if required else ""),
            value=default,
            key=f"{prefix}_{field}",
            height=110 if field == "Definition" else 90,
        )
    else:
        values[field] = st.text_input(
            field + (" *" if required else ""),
            value=default,
            key=f"{prefix}_{field}",
        )


def render_form_section(fields, frame, current, values, prefix):
    available_fields = [field for field in fields if field in frame.columns]
    left, right = st.columns(2, gap="large")
    for idx, field in enumerate(available_fields):
        required = field in REQUIRED_FIELDS
        with (left if idx % 2 == 0 else right):
            render_field(field, current.get(field, ""), values, prefix, required=required)


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
            st.caption("Audit dates are managed automatically by the application.")
            audit_left, audit_right = st.columns(2)
            with audit_left:
                st.text_input(
                    "Date Added",
                    value=clean_text(current.get("Date Added", "")),
                    disabled=True,
                    key=f"{prefix}_date_added_display",
                )
            with audit_right:
                st.text_input(
                    "Last Updated",
                    value=clean_text(current.get("Last Updated", "")),
                    disabled=True,
                    key=f"{prefix}_last_updated_display",
                )

    displayed = set(MAIN_FIELDS + DETAIL_FIELDS + GOVERNANCE_FIELDS) | AUTO_FIELDS | REMOVED_FIELDS
    for field in frame.columns:
        if field not in displayed:
            values[field] = current.get(field, "")

    for field in REMOVED_FIELDS:
        if field in frame.columns:
            values[field] = current.get(field, "") if row is not None else ""

    today = date.today().isoformat()
    if row is None:
        values["Date Added"] = today
    else:
        existing_date_added = clean_text(current.get("Date Added", ""))
        values["Date Added"] = existing_date_added or today
    values["Last Updated"] = today
    return values


def detail_card(field, value):
    st.markdown(
        f'<div class="detail-box"><strong>{html.escape(field)}</strong><br>{esc(value) or "—"}</div>',
        unsafe_allow_html=True,
    )


def render_info_section(row, fields):
    available = [field for field in fields if field in df.columns]
    left, right = st.columns(2, gap="large")
    for idx, field in enumerate(available):
        with (left if idx % 2 == 0 else right):
            detail_card(field, row.get(field, ""))


def missing_required_fields(values):
    return [field for field in REQUIRED_FIELDS if not clean_text(values.get(field, ""))]


def status_badge(status):
    label = clean_text(status) or "Not set"
    return f'<span class="status-badge"><span class="status-dot"></span>{html.escape(label)}</span>'


def clear_filters():
    for key in ["filter_search", "filter_category", "filter_data_type", "filter_status", "filter_owner"]:
        if key in st.session_state:
            del st.session_state[key]


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
        st.info("Local test mode: Save updates your local Excel workbook only.")

    with st.form("add_variable_form"):
        values = build_variable_form(df, prefix="add")
        _, submit_col = st.columns([3.2, 1])
        with submit_col:
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

    mode_key = f"variable_modal_mode_{variable_name}"
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "view"
    mode = st.session_state[mode_key]

    friendly_name = clean_text(row.get("Friendly Name", "")) or variable_name
    status = clean_text(row.get("Status", "")) or "Status not set"

    st.markdown(f'<div class="modal-heading">{html.escape(friendly_name)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="modal-meta">{html.escape(variable_name)} &nbsp;•&nbsp; {html.escape(status)}</div>',
        unsafe_allow_html=True,
    )

    if mode == "view":
        main_tab, technical_tab, governance_tab = st.tabs(
            ["Main Information", "Technical Details", "Governance"]
        )
        with main_tab:
            render_info_section(row, MAIN_FIELDS)
        with technical_tab:
            render_info_section(row, DETAIL_FIELDS)
        with governance_tab:
            render_info_section(row, GOVERNANCE_FIELDS + ["Date Added", "Last Updated"])

        st.markdown('<div class="modal-actions"></div>', unsafe_allow_html=True)
        spacer, edit_col, delete_col = st.columns([3, 1, 1])
        with edit_col:
            if st.button("Edit Variable", key=f"modal_edit_{variable_name}", use_container_width=True):
                st.session_state[mode_key] = "edit"
                st.rerun(scope="fragment")
        with delete_col:
            if st.button("Delete", key=f"modal_delete_{variable_name}", use_container_width=True):
                st.session_state[mode_key] = "delete"
                st.rerun(scope="fragment")

    elif mode == "edit":
        if not require_admin(f"edit_{variable_name}"):
            return

        st.caption("Fields marked * are required before changes can be saved.")
        with st.form(f"edit_{variable_name}"):
            values = build_variable_form(df, row, f"edit_{variable_name}")
            cancel_col, spacer, save_col = st.columns([1, 2.2, 1])
            with cancel_col:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            with save_col:
                submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

        if cancelled:
            st.session_state[mode_key] = "view"
            st.rerun(scope="fragment")

        if submitted:
            missing = missing_required_fields(values)
            if missing:
                st.error(f"Please complete all required fields: {', '.join(missing)}")
                return
            try:
                new_variable_name = clean_text(values.get("Variable Name", "")) or variable_name
                update_variable(get_token() or None, variable_name, values)
                st.cache_data.clear()
                st.session_state.pop(mode_key, None)
                if new_variable_name != variable_name:
                    st.session_state[f"variable_modal_mode_{new_variable_name}"] = "view"
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save changes: {exc}")

    elif mode == "delete":
        if not require_admin(f"delete_{variable_name}"):
            return

        st.warning(f"You are about to permanently delete **{variable_name} — {friendly_name}**.")
        st.caption("This removes the complete variable record from the data dictionary.")
        confirm = st.checkbox(
            "I understand that this action cannot be undone.",
            key=f"confirm_{variable_name}",
        )
        cancel_col, spacer, delete_col = st.columns([1, 2.2, 1])
        with cancel_col:
            if st.button("Cancel", key=f"cancel_delete_{variable_name}", use_container_width=True):
                st.session_state[mode_key] = "view"
                st.rerun(scope="fragment")
        with delete_col:
            if st.button(
                "Delete Variable",
                type="primary",
                disabled=not confirm,
                key=f"confirm_delete_{variable_name}",
                use_container_width=True,
            ):
                try:
                    delete_variable(get_token() or None, variable_name)
                    st.cache_data.clear()
                    st.session_state.pop(mode_key, None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete variable: {exc}")


with st.sidebar:
    st.markdown('<div class="sidebar-kicker">DIGITAL ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Filters</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-copy">Refine the variable registry without taking space away from the main workspace.</div>',
        unsafe_allow_html=True,
    )
    search = st.text_input(
        "Search",
        placeholder="Search variables...",
        key="filter_search",
    )
    category = st.multiselect(
        "Category",
        unique_values(df, "Category"),
        key="filter_category",
    )
    data_type = st.multiselect(
        "Data Type",
        unique_values(df, "Data Type"),
        key="filter_data_type",
    )
    status = st.multiselect(
        "Status",
        unique_values(df, "Status"),
        key="filter_status",
    )
    owner = st.multiselect(
        "Owner",
        unique_values(df, "Owner"),
        key="filter_owner",
    )
    st.button("Clear Filters", use_container_width=True, on_click=clear_filters)
    st.markdown("---")
    st.caption("Documentation layer only. Tealium controls which variables are mapped and sent to AWS.")

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
]:
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]

header_left, header_actions = st.columns([4.8, 1.8], gap="large")
with header_left:
    st.markdown('<div class="app-kicker">ADOBE ANALYTICS REPLACEMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">Digital Analytics Data Dictionary</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">A governed registry for analytics variables, Tealium mappings, AWS fields and ownership.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<span class="schema-badge">Schema v1.0</span>', unsafe_allow_html=True)
with header_actions:
    export_col, add_col = st.columns(2)
    with export_col:
        st.download_button(
            "Export ↓",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="digital_analytics_dictionary_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with add_col:
        if st.button("＋ Add Variable", type="primary", use_container_width=True):
            add_variable_dialog()

st.write("")
missing_definitions = int(df["Definition"].fillna("").astype(str).str.strip().eq("").sum())
aws_count = int(df["Send to AWS"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
pii_count = int(df["Contains PII"].astype(str).str.lower().isin(["true", "yes", "1"]).sum())
active_count = int(df["Status"].astype(str).str.lower().eq("active").sum())

metrics = [
    ("Total Variables", len(df)),
    ("Active", active_count),
    ("Sent to AWS", aws_count),
    ("PII Variables", pii_count),
    ("Missing Definitions", missing_definitions),
]
for col, (label, value) in zip(st.columns(5), metrics):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

st.write("")
registry_left, registry_right = st.columns([4, 1])
with registry_left:
    st.markdown('<div class="section-title">Variable Registry</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Click a variable name to view its complete definition, edit it or delete it.</div>',
        unsafe_allow_html=True,
    )
with registry_right:
    st.markdown(
        f'<div class="toolbar-note" style="text-align:right;"><strong>{len(filtered)}</strong> of {len(df)} variables shown</div>',
        unsafe_allow_html=True,
    )

widths = [1.55, 1.55, 1.1, 1.55, 1.4, .9]
headers = [
    "Variable Name",
    "Friendly Name",
    "Category",
    "Tealium Variable",
    "AWS Field",
    "Status",
]

header_container = st.container()
with header_container:
    st.markdown('<div class="registry-header">', unsafe_allow_html=True)
    for col, label in zip(st.columns(widths), headers):
        with col:
            st.markdown(f'<div class="table-header">{label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if filtered.empty:
    st.info("No variables match the current filters. Try clearing one or more filters from the sidebar.")
else:
    for idx, row in filtered.reset_index(drop=True).iterrows():
        variable_name = clean_text(row.get("Variable Name", ""))
        with st.container():
            cols = st.columns(widths, gap="small")
            with cols[0]:
                if st.button(
                    variable_name or "Unnamed variable",
                    key=f"open_variable_{idx}_{variable_name}",
                    type="tertiary",
                    help="Open variable details",
                ):
                    st.session_state[f"variable_modal_mode_{variable_name}"] = "view"
                    variable_dialog(variable_name)
            with cols[1]:
                st.markdown(
                    f'<div class="cell-text">{esc(row.get("Friendly Name", "")) or "—"}</div>',
                    unsafe_allow_html=True,
                )
            with cols[2]:
                st.markdown(
                    f'<div class="cell-muted">{esc(row.get("Category", "")) or "—"}</div>',
                    unsafe_allow_html=True,
                )
            with cols[3]:
                st.markdown(
                    f'<div class="mapping-value">{esc(row.get("Tealium Variable Name", "")) or "—"}</div>',
                    unsafe_allow_html=True,
                )
            with cols[4]:
                st.markdown(
                    f'<div class="mapping-value">{esc(row.get("AWS Field Name", "")) or "—"}</div>',
                    unsafe_allow_html=True,
                )
            with cols[5]:
                st.markdown(status_badge(row.get("Status", "")), unsafe_allow_html=True)
            st.markdown('<div style="border-bottom:1px solid #ededee; margin-top:4px;"></div>', unsafe_allow_html=True)
