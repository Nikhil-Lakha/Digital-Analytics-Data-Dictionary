from io import BytesIO
import pandas as pd
import streamlit as st

from utils.data_loader import load_dictionary, unique_values

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
    .detail-box {background:#fafafa; border:1px solid #ececec; border-radius:12px; padding:16px; margin-bottom:12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def get_data():
    return load_dictionary()

try:
    df = get_data()
except Exception as exc:
    st.error(f"Could not load the analytics dictionary: {exc}")
    st.stop()

st.markdown('<div class="app-kicker">ADOBE ANALYTICS REPLACEMENT</div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">Digital Analytics Data Dictionary</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Central reference for analytics variables, Tealium mappings, AWS fields and governance metadata.</div>',
    unsafe_allow_html=True,
)

# Summary metrics
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
    owner = st.multiselect("Owner", unique_values(df, "Owner"))
with f2:
    data_type = st.multiselect("Data type", unique_values(df, "Data Type"))
    journey = st.multiselect("Journey", unique_values(df, "Journey"))
with f3:
    status = st.multiselect("Status", unique_values(df, "Status"))
    pii = st.selectbox("Contains PII", ["All", "Yes", "No"])
with f4:
    send_aws = st.selectbox("Send to AWS", ["All", "Yes", "No"])

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
    ("Journey", journey),
]:
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]


def apply_boolean_filter(frame, column, selection):
    if selection == "All":
        return frame
    truthy = frame[column].astype(str).str.lower().isin(["true", "yes", "1"])
    return frame[truthy] if selection == "Yes" else frame[~truthy]

filtered = apply_boolean_filter(filtered, "Contains PII", pii)
filtered = apply_boolean_filter(filtered, "Send to AWS", send_aws)

st.markdown(f"### Variables ({len(filtered)})")
preferred_cols = [
    "Variable Name", "Friendly Name", "Category", "Definition", "Data Type",
    "Tealium Variable Name", "AWS Field Name", "Send to AWS", "Contains PII", "Status", "Journey"
]
display_cols = [c for c in preferred_cols if c in filtered.columns]
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True, height=430)

csv_data = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered list",
    data=csv_data,
    file_name="filtered_analytics_variables.csv",
    mime="text/csv",
)

st.divider()
st.markdown("### Variable details")

if filtered.empty:
    st.info("No variables match the current filters.")
else:
    labels = filtered.apply(
        lambda r: f"{r.get('Variable Name', '')} — {r.get('Friendly Name', '')}", axis=1
    ).tolist()
    selected_label = st.selectbox("Select a variable", labels)
    row = filtered.iloc[labels.index(selected_label)]

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Definition")
        st.markdown(
            f"""<div class="detail-box">
            <strong>{row.get('Friendly Name', '')}</strong><br><br>
            {row.get('Definition', '') or '<em>No definition provided</em>'}
            </div>""",
            unsafe_allow_html=True,
        )
        st.write("**Variable name:**", row.get("Variable Name", ""))
        st.write("**Category:**", row.get("Category", ""))
        st.write("**Subcategory:**", row.get("Subcategory", ""))
        st.write("**Data type:**", row.get("Data Type", ""))
        st.write("**Example value:**", row.get("Example Value", ""))
        st.write("**Allowed values:**", row.get("Allowed Values", ""))

    with right:
        st.markdown("#### Implementation")
        st.write("**Tealium variable type:**", row.get("Tealium Variable Type", ""))
        st.write("**Tealium variable name:**", row.get("Tealium Variable Name", ""))
        st.write("**AWS field name:**", row.get("AWS Field Name", ""))
        st.write("**Send to AWS:**", row.get("Send to AWS", ""))
        st.write("**Source system:**", row.get("Source System", ""))

        st.markdown("#### Governance")
        st.write("**Contains PII:**", row.get("Contains PII", ""))
        st.write("**PII classification:**", row.get("PII Classification", ""))
        st.write("**Owner:**", row.get("Owner", ""))
        st.write("**Status:**", row.get("Status", ""))
        st.write("**Business criticality:**", row.get("Business Criticality", ""))
        st.write("**Journey:**", row.get("Journey", ""))
        st.write("**Schema version:**", row.get("Schema Version", ""))

st.caption("Documentation layer only — Tealium controls which variables are mapped and sent to AWS.")
