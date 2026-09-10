from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "analytics_data_dictionary.csv"
APP_PATH = ROOT / "app.py"
LOADER_PATH = ROOT / "utils" / "data_loader.py"


def migrate_csv():
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError("CSV has no header row")

        old_fieldnames = list(reader.fieldnames)
        if "Send to AWS" in old_fieldnames:
            fieldnames = ["Sent to AWS" if name == "Send to AWS" else name for name in old_fieldnames]
        elif "Sent to AWS" in old_fieldnames:
            fieldnames = old_fieldnames
        else:
            raise RuntimeError("Neither 'Send to AWS' nor 'Sent to AWS' exists in the CSV")

        rows = []
        for row in reader:
            if "Send to AWS" in row:
                row["Sent to AWS"] = row.pop("Send to AWS")
            row["Sent to AWS"] = "No"
            rows.append(row)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def migrate_loader():
    text = LOADER_PATH.read_text(encoding="utf-8")
    text = text.replace('"Send to AWS"', '"Sent to AWS"')
    LOADER_PATH.write_text(text, encoding="utf-8")


def migrate_app():
    text = APP_PATH.read_text(encoding="utf-8")
    text = text.replace('"Send to AWS"', '"Sent to AWS"')

    old_clear = 'for key in ["filter_category", "filter_data_type", "filter_status", "filter_owner"]:'
    new_clear = 'for key in ["filter_category", "filter_data_type", "filter_status", "filter_owner", "filter_sent_to_aws"]:'
    text = text.replace(old_clear, new_clear)

    old_sidebar = '    owner = st.multiselect("Owner", unique_values(df, "Owner"), key="filter_owner")\n    st.button("Reset all", use_container_width=True, on_click=clear_filters)'
    new_sidebar = '    owner = st.multiselect("Owner", unique_values(df, "Owner"), key="filter_owner")\n    sent_to_aws = st.multiselect("Sent to AWS", unique_values(df, "Sent to AWS"), key="filter_sent_to_aws")\n    st.button("Reset all", use_container_width=True, on_click=clear_filters)'
    if old_sidebar not in text:
        raise RuntimeError("Could not find sidebar filter insertion point in app.py")
    text = text.replace(old_sidebar, new_sidebar)

    old_filter = '    ("Status", status),\n    ("Owner", owner),\n]:'
    new_filter = '    ("Status", status),\n    ("Owner", owner),\n    ("Sent to AWS", sent_to_aws),\n]:'
    if old_filter not in text:
        raise RuntimeError("Could not find dataframe filter insertion point in app.py")
    text = text.replace(old_filter, new_filter)

    APP_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    migrate_csv()
    migrate_loader()
    migrate_app()
    print("Migrated Send to AWS -> Sent to AWS, set all values to No, and added sidebar filter.")
