import streamlit as st
import pandas as pd

# 🌱 App Title
st.set_page_config(page_title="Plantation Data Viewer", page_icon="🌿", layout="wide")
st.title("🌿 Plantation Data Viewer")
st.markdown("### Monthly plantation and cut analysis")

# 📂 Load CSV Data
@st.cache_data
def load_data():
    df = pd.read_csv("plantation_data.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ plantation_data.csv not found. Please upload the file to the same folder.")
    st.stop()

# 🧮 Data Processing
df["month"] = df["date"].dt.to_period("M").astype(str)
monthly_data = df.groupby("month")[["planted", "cut"]].sum().reset_index()

# 📈 Line Chart
st.subheader("📈 Monthly Plantation vs Cut")
st.line_chart(
    monthly_data.set_index("month"),
    use_container_width=True
)

# 📋 Data Table
st.subheader("📋 Full Data")
st.dataframe(df, use_container_width=True)

# ℹ️ Footer
st.markdown("---")
st.caption("Developed with ❤️ in Streamlit & Pandas by Mohan Sharma")

