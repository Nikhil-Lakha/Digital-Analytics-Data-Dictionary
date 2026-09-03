import html
from urllib.parse import quote

import pandas as pd
import streamlit as st

from utils.data_loader import load_dictionary, unique_values
from utils.github_store import delete_variable, update_variable

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
    .detail-box {background:#fafafa; border:1px solid #ececec; border-radius:12px; padding:18px; margin-bottom:16px;}
    .dict-table {width:100%; border-collapse:collapse; margin-top:8px; font-size:.92rem;}
    .dict-table th {text-align:left; padding:12px 10px; border-bottom:2px solid #e5e5e5; color:#555; font-size:.82rem;}
    .dict-table td {padding:13px 10px; border-bottom:1px solid #eeeeee; vertical-align:top;}
    .dict-table tr:hover {background:#fafafa;}
    .action-link {text-decoration:none; font-weight:650; margin-right:12px; white-space:nowrap;}
    .more-link {color:#E60000;}
    .edit-link {color:#333;}
    .delete-link {color:#a40000;}
    .back-link {display:inline-block; margin-bottom:16px; text-decoration:none; font-weight:650; color:#E60000;}
    </style>
    """,
    unsafe_allow_html=True,
)


def get_token() -> str:
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return ""


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


def header(title="Digital Analytics Data Dictionary", subtitle=None):
    st.markdown('<div class="app-kicker">ADOBE ANALYTICS REPLACEMENT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="app-subtitle">{html.escape(subtitle or "Central reference for analytics variables, Tealium mappings, AWS fields and governance metadata.")}</div>',
        unsafe_allow_html=True,
    )


try:
    df = get_data()
except Exception as exc:
    st.error(f"Could not load the analytics dictionary: {exc}")
    st.stop()

view = st.query_params.get("view", "list")
variable = st.query_params.get("variable", "")

# -----------------------------
# DETAIL VIEW
# -----------------------------
if view == "detail":
    row = find_row(df, variable)
    if row is None:
        st.error("That variable could not be found.")
        st.link_button("Back to dictionary", "./")
        st.stop()

    header(str(row.get("Friendly Name", variable)), f"Full details for {row.get('Variable Name', '')}")
    st.markdown('<a class="back-link" href="./">← Back to dictionary</a>', unsafe_allow_html=True)

    main_left, main_right = st.columns(2)
    with main_left:
        st.markdown("### Main information")
        st.markdown(
            f"""<div class="detail-box">
            <strong>Variable name</strong><br>{esc(row.get('Variable Name', ''))}<br><br>
            <strong>Friendly name</strong><br>{esc(row.get('Friendly Name', ''))}<br><br>
            <strong>Category</strong><br>{esc(row.get('Category', ''))}
            </div>""",
            unsafe_allow_html=True,
        )
    with main_right:
        st.markdown("### Implementation")
        st.markdown(
            f"""<div class="detail-box">
            <strong>Tealium variable name</strong><br>{esc(row.get('Tealium Variable Name', ''))}<br><br>
            <strong>AWS field name</strong><br>{esc(row.get('AWS Field Name', ''))}<br><br>
            <strong>Data type</strong><br>{esc(row.get('Data Type', ''))}
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("### Additional details")
    hidden_main = {"Variable Name", "Friendly Name", "Category", "Tealium Variable Name", "AWS Field Name"}
    detail_fields = [c for c in df.columns if c not in hidden_main]
    left, right = st.columns(2)
    for idx, field in enumerate(detail_fields):
        target = left if idx % 2 == 0 else right
        with target:
            st.markdown(
                f'<div class="detail-box"><strong>{html.escape(field)}</strong><br>{esc(row.get(field, "")) or "—"}</div>',
                unsafe_allow_html=True,
            )

    e1, e2 = st.columns([1, 5])
    with e1:
        st.link_button("Edit variable", f"?view=edit&variable={quote(str(variable))}", use_container_width=True)
    with e2:
        st.link_button("Delete variable", f"?view=delete&variable={quote(str(variable))}")
    st.stop()

# -----------------------------
# EDIT VIEW
# -----------------------------
if view == "edit":
    row = find_row(df, variable)
    if row is None:
        st.error("That variable could not be found.")
        st.stop()

    header("Edit variable", f"Update both main and detailed information for {variable}")
    st.markdown('<a class="back-link" href="./">← Back to dictionary</a>', unsafe_allow_html=True)

    if not get_token():
        st.warning("Editing is not enabled yet. Add GITHUB_TOKEN to this app's Streamlit Secrets to allow write-back to GitHub.")

    with st.form("edit_variable"):
        st.markdown("### Main information")
        c1, c2 = st.columns(2)
        values = {}
        with c1:
            values["Variable Name"] = st.text_input("Variable name", value=str(row.get("Variable Name", "")))
            values["Friendly Name"] = st.text_input("Friendly name", value=str(row.get("Friendly Name", "")))
            values["Category"] = st.selectbox(
                "Category",
                options=unique_values(df, "Category"),
                index=max(0, unique_values(df, "Category").index(str(row.get("Category", ""))) if str(row.get("Category", "")) in unique_values(df, "Category") else 0),
            )
        with c2:
            values["Tealium Variable Name"] = st.text_input("Tealium variable name", value=str(row.get("Tealium Variable Name", "")))
            values["AWS Field Name"] = st.text_input("AWS field name", value=str(row.get("AWS Field Name", "")))
            values["Data Type"] = st.selectbox(
                "Data type",
                options=unique_values(df, "Data Type"),
                index=max(0, unique_values(df, "Data Type").index(str(row.get("Data Type", ""))) if str(row.get("Data Type", "")) in unique_values(df, "Data Type") else 0),
            )

        st.markdown("### Detailed information")
        text_area_fields = {"Definition", "Notes", "Allowed Values"}
        bool_fields = {"Required", "Send to AWS", "Contains PII"}
        already_rendered = {"Variable Name", "Friendly Name", "Category", "Tealium Variable Name", "AWS Field Name", "Data Type"}

        cols = st.columns(2)
        for idx, field in enumerate([c for c in df.columns if c not in already_rendered]):
            with cols[idx % 2]:
                current = row.get(field, "")
                if field in bool_fields:
                    values[field] = st.selectbox(field, [True, False], index=0 if truthy(current) else 1, key=f"field_{field}")
                elif field == "Status":
                    options = unique_values(df, "Status")
                    current_text = str(current)
                    values[field] = st.selectbox(field, options, index=options.index(current_text) if current_text in options else 0, key=f"field_{field}")
                elif field in text_area_fields:
                    values[field] = st.text_area(field, value=str(current), key=f"field_{field}")
                else:
                    values[field] = st.text_input(field, value=str(current), key=f"field_{field}")

        submitted = st.form_submit_button("Save changes", type="primary", use_container_width=True, disabled=not bool(get_token()))

    if submitted:
        try:
            update_variable(get_token(), variable, values)
            st.success("Changes saved to the Excel file in GitHub.")
            st.cache_data.clear()
            st.query_params.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save the changes: {exc}")
    st.stop()

# -----------------------------
# DELETE VIEW
# -----------------------------
if view == "delete":
    row = find_row(df, variable)
    if row is None:
        st.error("That variable could not be found.")
        st.stop()

    header("Delete variable", f"Remove {variable} from the analytics dictionary")
    st.markdown('<a class="back-link" href="./">← Back to dictionary</a>', unsafe_allow_html=True)
    st.warning(f"You are about to permanently delete **{variable} — {row.get('Friendly Name', '')}** from the Excel dictionary in GitHub.")

    if not get_token():
        st.info("Deletion is disabled until GITHUB_TOKEN is added to Streamlit Secrets.")

    confirm = st.checkbox("I understand that this removes the row from the master Excel file.")
    if st.button("Delete variable", type="primary", disabled=not (confirm and bool(get_token()))):
        try:
            delete_variable(get_token(), variable)
            st.success("Variable deleted from the Excel file in GitHub.")
            st.cache_data.clear()
            st.query_params.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Could not delete the variable: {exc}")
    st.stop()

# -----------------------------
# MAIN LIST VIEW
# -----------------------------
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
    search_cols = [c for c in ["Variable Name", "Friendly Name", "Definition"] if c in filtered.columns]
    mask = pd.Series(False, index=filtered.index)
    for col in search_cols:
        mask = mask | filtered[col].fillna("").astype(str).str.lower().str.contains(term, regex=False)
    filtered = filtered[mask]

for column, selected in [
    ("Category", category),
    ("Data Type", data_type),
    ("Status", status),
    ("Owner", owner),
]:
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]

st.markdown(f"### Variables ({len(filtered)})")

if filtered.empty:
    st.info("No variables match the current filters.")
else:
    rows = []
    for _, row in filtered.iterrows():
        variable_name = str(row.get("Variable Name", ""))
        encoded = quote(variable_name)
        rows.append(
            "<tr>"
            f"<td><strong>{esc(row.get('Variable Name', ''))}</strong></td>"
            f"<td>{esc(row.get('Friendly Name', ''))}</td>"
            f"<td>{esc(row.get('Category', ''))}</td>"
            f"<td>{esc(row.get('Tealium Variable Name', ''))}</td>"
            f"<td>{esc(row.get('AWS Field Name', ''))}</td>"
            f'<td><a class="action-link more-link" href="?view=detail&variable={encoded}" target="_blank">More information ↗</a></td>'
            f'<td><a class="action-link edit-link" href="?view=edit&variable={encoded}">Edit</a>'
            f'<a class="action-link delete-link" href="?view=delete&variable={encoded}">Delete</a></td>'
            "</tr>"
        )

    table_html = f"""
    <table class="dict-table">
      <thead>
        <tr>
          <th>Variable name</th>
          <th>Friendly name</th>
          <th>Category</th>
          <th>Tealium variable name</th>
          <th>AWS field name</th>
          <th>More information</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

st.caption("Documentation layer only — Tealium controls which variables are mapped and sent to AWS.")
