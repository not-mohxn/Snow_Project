# public_app.py
import streamlit as st
import pandas as pd
from datetime import date

# --- Page config ---
st.set_page_config(page_title="Plantation Data Viewer", page_icon="🌿", layout="wide")
st.title("🌿 Plantation Data Viewer")
st.markdown("### Monthly plantation vs cut (line) — and search by a specific date")

# --- Load CSV with caching ---
@st.cache_data
def load_data(csv_path="plantation_data.csv"):
    df = pd.read_csv(csv_path)
    # Ensure date column is datetime
    df["date"] = pd.to_datetime(df["date"])
    return df

# Try to load data; show friendly error if missing
try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ `plantation_data.csv` not found. Please place the CSV in the same folder as this app.")
    st.stop()

# --- Sidebar: date selector for users ---
st.sidebar.header("Search / Filter")
st.sidebar.write("Select a date to view only records for that date (optional).")
# default: no selection — use an empty checkbox to control whether date filtering is active
use_date_filter = st.sidebar.checkbox("Filter by specific date", value=False)

selected_date = None
if use_date_filter:
    # show date input; default to today
    selected_date = st.sidebar.date_input("Choose date", value=date.today())
    st.sidebar.write("Showing records for:", selected_date.strftime("%Y-%m-%d"))

# --- Data processing for monthly chart (always from full dataset) ---
df["month"] = df["date"].dt.to_period("M").astype(str)
monthly_data = df.groupby("month")[["planted", "cut"]].sum().reset_index()

# --- Chart: monthly line chart ---
st.subheader("📈 Monthly Plantation vs Cut (All available data)")
st.line_chart(
    monthly_data.set_index("month"),
    use_container_width=True
)

st.markdown("---")

# --- If user selected a date, filter and show only that date's rows & summary ---
if use_date_filter and selected_date is not None:
    # Convert timestamp column to date for exact match
    df["date_only"] = df["date"].dt.date
    # Filter rows matching the selected date
    filtered = df[df["date_only"] == selected_date]

    st.subheader(f"📅 Records for {selected_date.strftime('%Y-%m-%d')}")
    if filtered.empty:
        st.info("No records found for this date.")
    else:
        # Show the filtered rows (drop helper column)
        st.dataframe(filtered.drop(columns=["date_only"]), use_container_width=True)

        # Show summary numbers
        total_planted = int(filtered["planted"].sum())
        total_cut = int(filtered["cut"].sum())
        st.metric(label="Total planted on this date", value=total_planted)
        st.metric(label="Total cut on this date", value=total_cut)

    st.markdown("---")
    st.caption("Tip: Uncheck 'Filter by specific date' in the sidebar to see full data & monthly chart again.")

# --- Show full data table (if not filtering by date) ---
if not (use_date_filter and selected_date is not None):
    st.subheader("📋 Full Data")
    st.dataframe(df.drop(columns=["month"]), use_container_width=True)

st.markdown("---")
st.caption("Developed with ❤️ in Streamlit & Pandas — by Mohan Sharma")

