# =====================================================
# IMPORT LIBRARIES
# =====================================================
import pandas as pd
import streamlit as st
from groq import Groq
import json
import io

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# =====================================================
# TITLE
# =====================================================
st.title("📊 Sales Performance Dashboard")
st.caption("Upload your sales data, explore insights, and ask questions in plain English")

# =====================================================
# CSV UPLOAD (CLIENT FEATURE)
# =====================================================
def load_sales_data(file_source):
    if isinstance(file_source, str):
        return pd.read_csv(file_source)

    file_bytes = file_source.getvalue()
    encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "ISO-8859-1"]

    for encoding in encodings_to_try:
        try:
            return pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
        except UnicodeDecodeError:
            pass

    decoded_text = file_bytes.decode("utf-8", errors="replace")
    return pd.read_csv(io.StringIO(decoded_text))


uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    df = load_sales_data(uploaded_file)
    data_signature = f"upload:{uploaded_file.name}:{uploaded_file.size}"
else:
    df = load_sales_data("data/sales_data_sample.csv")
    data_signature = "sample"

# =====================================================
# FEATURE ENGINEERING
# =====================================================
df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)
df["MonthName"] = df["ORDERDATE"].dt.month_name()

# Normalize common string columns to avoid hidden whitespace issues
string_cols = [
    "COUNTRY",
    "PRODUCTLINE",
    "DEALSIZE",
    "STATUS",
    "CITY",
    "STATE",
    "TERRITORY",
]
for col in string_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# =====================================================
# CLEAN DATA
# =====================================================
df.dropna(
    subset=["ORDERDATE", "YEAR_ID", "PRODUCTLINE", "COUNTRY", "SALES"],
    inplace=True
)

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("Filters")

if st.session_state.get("data_signature") != data_signature:
    st.session_state["data_signature"] = data_signature
    st.session_state["year_filter"] = sorted(df["YEAR_ID"].unique())
    st.session_state["product_line_filter"] = sorted(df["PRODUCTLINE"].unique())
    st.session_state["country_filter"] = sorted(df["COUNTRY"].unique())

country_values = sorted(df["COUNTRY"].unique())
if len(country_values) <= 1:
    st.sidebar.warning(
        "Only one country found in the data. If this is unexpected, check the "
        "uploaded CSV for extra spaces or missing country values."
    )

year = st.sidebar.multiselect(
    "Select Year",
    options=sorted(df["YEAR_ID"].unique()),
    default=sorted(df["YEAR_ID"].unique()),
    key="year_filter"
)

product_line = st.sidebar.multiselect(
    "Product Line",
    options=sorted(df["PRODUCTLINE"].unique()),
    default=sorted(df["PRODUCTLINE"].unique()),
    key="product_line_filter"
)

country = st.sidebar.multiselect(
    "Country",
    options=country_values,
    default=country_values,
    key="country_filter"
)

filtered_df = df[
    (df["YEAR_ID"].isin(year)) &
    (df["PRODUCTLINE"].isin(product_line)) &
    (df["COUNTRY"].isin(country))
]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# =====================================================
# KPI SECTION
# =====================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"${filtered_df['SALES'].sum():,.0f}")
col2.metric("Total Orders", filtered_df["ORDERNUMBER"].nunique())
col3.metric("Units Sold", filtered_df["QUANTITYORDERED"].sum())
col4.metric(
    "Top Product Line",
    filtered_df.groupby("PRODUCTLINE")["SALES"].sum().idxmax()
)

# =====================================================
# DASHBOARD CHARTS
# =====================================================
st.subheader("📈 Monthly Sales Trend")
monthly_sales = filtered_df.groupby("YearMonth")["SALES"].sum()
st.line_chart(monthly_sales)

st.subheader("📊 Sales by Product Line")
st.bar_chart(filtered_df.groupby("PRODUCTLINE")["SALES"].sum())

st.subheader("🌍 Sales by Country")
st.bar_chart(filtered_df.groupby("COUNTRY")["SALES"].sum())

st.subheader("💼 Revenue by Deal Size")
st.bar_chart(filtered_df.groupby("DEALSIZE")["SALES"].sum())

# =====================================================
# RAW DATA
# =====================================================
with st.expander("View Raw Data"):
    st.dataframe(filtered_df)

# =====================================================
# CHATBOT CONFIG (SECURE)
# =====================================================
ALLOWED_METRICS = ["SALES", "QUANTITYORDERED", "PRICEEACH"]
ALLOWED_GROUPBY = ["YearMonth", "MonthName", "YEAR_ID", "PRODUCTLINE", "COUNTRY", "DEALSIZE"]
ALLOWED_OPERATIONS = ["sum", "mean", "min", "max"]
ALLOWED_CHARTS = ["bar", "line", "none"]

client = Groq(api_key=st.secrets["OPENAI_API_KEY"])

data_schema = """
You are an analytics assistant.

Respond ONLY in valid JSON.
Do NOT explain anything.

Columns:
- ORDERDATE
- YearMonth
- MonthName
- SALES
- QUANTITYORDERED
- PRICEEACH
- PRODUCTLINE
- COUNTRY
- DEALSIZE
- YEAR_ID

JSON format:
{
  "metric": "SALES | QUANTITYORDERED | PRICEEACH",
  "groupby": "YearMonth | MonthName | YEAR_ID | PRODUCTLINE | COUNTRY | DEALSIZE",
  "year": 2005 or null,
  "operation": "sum | mean | min | max",
  "chart": "bar | line | none"
}
"""

# =====================================================
# CHATBOT LOGIC (NO EXEC)
# =====================================================
def ask_data_question(question, df):
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"{data_schema}\nQuestion:\n{question}"}],
        temperature=0
    )

    try:
        query = json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError:
        return None, "Invalid response from model."

    # Validate
    if (
        query["metric"] not in ALLOWED_METRICS or
        query["groupby"] not in ALLOWED_GROUPBY or
        query["operation"] not in ALLOWED_OPERATIONS or
        query["chart"] not in ALLOWED_CHARTS
    ):
        return None, "Unsupported query."

    data = df.copy()

    if query["year"] is not None:
        data = data[data["YEAR_ID"] == query["year"]]

    grouped = data.groupby(query["groupby"])[query["metric"]]

    if query["operation"] == "sum":
        result_series = grouped.sum()
    elif query["operation"] == "mean":
        result_series = grouped.mean()
    elif query["operation"] == "min":
        result_series = grouped.min()
    else:
        result_series = grouped.max()

    return result_series, query

# =====================================================
# CHAT UI
# =====================================================
st.subheader("🤖 Ask Questions About the Data")

user_question = st.text_input(
    "Ask a question (e.g. Which was the lowest sales month in 2005?)"
)

if user_question:
    result, query = ask_data_question(user_question, filtered_df)

    if isinstance(result, str):
        st.error(result)
    else:
        st.markdown("### ✅ Answer")

        if query["operation"] in ["min", "max"]:
            st.write(result.idxmin() if query["operation"] == "min" else result.idxmax())
        else:
            st.write(result)

        if query["chart"] == "bar":
            st.bar_chart(result)
        elif query["chart"] == "line":
            st.line_chart(result)

        with st.expander("How this was computed"):
            st.json(query)
