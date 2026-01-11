# # =====================================================
# # IMPORT LIBRARIES
# # =====================================================
# import pandas as pd
# import streamlit as st
# from groq import Groq
# import json

# # =====================================================
# # PAGE CONFIG
# # =====================================================
# st.set_page_config(page_title="Sales Dashboard", layout="wide")

# # =====================================================
# # TITLE
# # =====================================================
# st.title("📊 Sales Performance Dashboard")
# st.caption("Upload your sales data, explore insights, and ask questions in plain English")

# # =====================================================
# # CSV UPLOAD (CLIENT FEATURE)
# # =====================================================
# uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

# if uploaded_file is not None:
#     df = pd.read_csv(uploaded_file)
# else:
#     df = pd.read_csv("data/sales_data_sample.csv")

# # =====================================================
# # FEATURE ENGINEERING
# # =====================================================
# df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
# df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)
# df["MonthName"] = df["ORDERDATE"].dt.month_name()

# # =====================================================
# # CLEAN DATA
# # =====================================================
# df.dropna(inplace=True)

# # =====================================================
# # SIDEBAR FILTERS
# # =====================================================
# st.sidebar.header("Filters")

# year = st.sidebar.multiselect(
#     "Select Year",
#     options=sorted(df["YEAR_ID"].unique()),
#     default=sorted(df["YEAR_ID"].unique())
# )

# product_line = st.sidebar.multiselect(
#     "Product Line",
#     options=df["PRODUCTLINE"].unique(),
#     default=df["PRODUCTLINE"].unique()
# )

# country = st.sidebar.multiselect(
#     "Country",
#     options=df["COUNTRY"].unique(),
#     default=df["COUNTRY"].unique()
# )

# filtered_df = df[
#     (df["YEAR_ID"].isin(year)) &
#     (df["PRODUCTLINE"].isin(product_line)) &
#     (df["COUNTRY"].isin(country))
# ]

# if filtered_df.empty:
#     st.warning("No data available for selected filters.")
#     st.stop()

# # =====================================================
# # KPI SECTION
# # =====================================================
# col1, col2, col3, col4 = st.columns(4)

# col1.metric("Total Revenue", f"${filtered_df['SALES'].sum():,.0f}")
# col2.metric("Total Orders", filtered_df["ORDERNUMBER"].nunique())
# col3.metric("Units Sold", filtered_df["QUANTITYORDERED"].sum())
# col4.metric(
#     "Top Product Line",
#     filtered_df.groupby("PRODUCTLINE")["SALES"].sum().idxmax()
# )

# # =====================================================
# # DASHBOARD CHARTS
# # =====================================================
# st.subheader("📈 Monthly Sales Trend")
# monthly_sales = filtered_df.groupby("YearMonth")["SALES"].sum()
# st.line_chart(monthly_sales)

# st.subheader("📊 Sales by Product Line")
# st.bar_chart(filtered_df.groupby("PRODUCTLINE")["SALES"].sum())

# st.subheader("🌍 Sales by Country")
# st.bar_chart(filtered_df.groupby("COUNTRY")["SALES"].sum())

# st.subheader("💼 Revenue by Deal Size")
# st.bar_chart(filtered_df.groupby("DEALSIZE")["SALES"].sum())

# # =====================================================
# # RAW DATA
# # =====================================================
# with st.expander("View Raw Data"):
#     st.dataframe(filtered_df)

# # =====================================================
# # CHATBOT CONFIG (SECURE)
# # =====================================================
# ALLOWED_METRICS = ["SALES", "QUANTITYORDERED", "PRICEEACH"]
# ALLOWED_GROUPBY = ["YearMonth", "MonthName", "YEAR_ID", "PRODUCTLINE", "COUNTRY", "DEALSIZE"]
# ALLOWED_OPERATIONS = ["sum", "mean", "min", "max"]
# ALLOWED_CHARTS = ["bar", "line", "none"]

# client = Groq(api_key=st.secrets["OPENAI_API_KEY"])

# data_schema = """
# You are an analytics assistant.

# Respond ONLY in valid JSON.
# Do NOT explain anything.

# Columns:
# - ORDERDATE
# - YearMonth
# - MonthName
# - SALES
# - QUANTITYORDERED
# - PRICEEACH
# - PRODUCTLINE
# - COUNTRY
# - DEALSIZE
# - YEAR_ID

# JSON format:
# {
#   "metric": "SALES | QUANTITYORDERED | PRICEEACH",
#   "groupby": "YearMonth | MonthName | YEAR_ID | PRODUCTLINE | COUNTRY | DEALSIZE",
#   "year": 2005 or null,
#   "operation": "sum | mean | min | max",
#   "chart": "bar | line | none"
# }
# """

# # =====================================================
# # CHATBOT LOGIC (NO EXEC)
# # =====================================================
# def ask_data_question(question, df):
#     completion = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[{"role": "user", "content": f"{data_schema}\nQuestion:\n{question}"}],
#         temperature=0
#     )

#     try:
#         query = json.loads(completion.choices[0].message.content)
#     except json.JSONDecodeError:
#         return None, "Invalid response from model."

#     # Validate
#     if (
#         query["metric"] not in ALLOWED_METRICS or
#         query["groupby"] not in ALLOWED_GROUPBY or
#         query["operation"] not in ALLOWED_OPERATIONS or
#         query["chart"] not in ALLOWED_CHARTS
#     ):
#         return None, "Unsupported query."

#     data = df.copy()

#     if query["year"] is not None:
#         data = data[data["YEAR_ID"] == query["year"]]

#     grouped = data.groupby(query["groupby"])[query["metric"]]

#     if query["operation"] == "sum":
#         result_series = grouped.sum()
#     elif query["operation"] == "mean":
#         result_series = grouped.mean()
#     elif query["operation"] == "min":
#         result_series = grouped.min()
#     else:
#         result_series = grouped.max()

#     return result_series, query

# # =====================================================
# # CHAT UI
# # =====================================================
# st.subheader("🤖 Ask Questions About the Data")

# user_question = st.text_input(
#     "Ask a question (e.g. Which was the lowest sales month in 2005?)"
# )

# if user_question:
#     result, query = ask_data_question(user_question, filtered_df)

#     if isinstance(result, str):
#         st.error(result)
#     else:
#         st.markdown("### ✅ Answer")

#         if query["operation"] in ["min", "max"]:
#             st.write(result.idxmin() if query["operation"] == "min" else result.idxmax())
#         else:
#             st.write(result)

#         if query["chart"] == "bar":
#             st.bar_chart(result)
#         elif query["chart"] == "line":
#             st.line_chart(result)

#         with st.expander("How this was computed"):
#             st.json(query)


# =====================================================
# IMPORT LIBRARIES
# =====================================================
import pandas as pd
import streamlit as st
from groq import Groq
import json

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
uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1') # Added encoding handling for common sales CSVs
else:
    # Ensure you have this file in your repo or handle the error gracefully
    try:
        df = pd.read_csv("data/sales_data_sample.csv", encoding='ISO-8859-1')
    except FileNotFoundError:
        st.error("Default data file not found. Please upload a CSV.")
        st.stop()

# =====================================================
# FEATURE ENGINEERING
# =====================================================
df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)
df["MonthName"] = df["ORDERDATE"].dt.month_name()

# =====================================================
# CLEAN DATA
# =====================================================
df.dropna(inplace=True)

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("Filters")

# Dynamic Years
all_years = sorted(df["YEAR_ID"].unique())
year = st.sidebar.multiselect(
    "Select Year",
    options=all_years,
    default=all_years
)

product_line = st.sidebar.multiselect(
    "Product Line",
    options=df["PRODUCTLINE"].unique(),
    default=df["PRODUCTLINE"].unique()
)

country = st.sidebar.multiselect(
    "Country",
    options=df["COUNTRY"].unique(),
    default=df["COUNTRY"].unique()
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
# ⚠️ DATA INTELLIGENCE WARNING (NEW FEATURE)
# =====================================================
# Automatically detect if 2005 is selected and warn about incomplete data
if 2005 in year:
    max_date_2005 = df[df["YEAR_ID"] == 2005]["ORDERDATE"].max()
    st.warning(f"⚠️ **Analyst Note:** Data for 2005 is incomplete. It ends on {max_date_2005.strftime('%B %Y')}. Comparisons with full years (2003, 2004) may appear lower.")

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
# DASHBOARD CHARTS (Optimized Sorting)
# =====================================================
st.subheader("📈 Monthly Sales Trend")
monthly_sales = filtered_df.groupby("YearMonth")["SALES"].sum()
st.line_chart(monthly_sales)

# Row 2
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Sales by Product Line")
    # Sort values descending for better readability
    product_sales = filtered_df.groupby("PRODUCTLINE")["SALES"].sum().sort_values(ascending=False)
    st.bar_chart(product_sales)

with c2:
    st.subheader("🌍 Sales by Country")
    country_sales = filtered_df.groupby("COUNTRY")["SALES"].sum().sort_values(ascending=False)
    st.bar_chart(country_sales)

st.subheader("💼 Revenue by Deal Size")
deal_sales = filtered_df.groupby("DEALSIZE")["SALES"].sum().sort_values(ascending=False)
st.bar_chart(deal_sales)

# =====================================================
# RAW DATA
# =====================================================
with st.expander("View Raw Data"):
    st.dataframe(filtered_df)

# =====================================================
# CHATBOT LOGIC (UPGRADED FOR "WHY" QUESTIONS)
# =====================================================
client = Groq(api_key=st.secrets["OPENAI_API_KEY"])

# We create a "Summary" of the dataset to give the AI context
# This lets it answer "Why" questions without needing to see all 10k rows
data_context = f"""
Dataset Summary:
- Date Range: {df['ORDERDATE'].min().date()} to {df['ORDERDATE'].max().date()}
- Total Years: {sorted(df['YEAR_ID'].unique())}
- Note: 2005 data ends in May, making it a partial year.
- Columns: ORDERDATE, SALES, PRODUCTLINE, COUNTRY, DEALSIZE.
"""

def ask_data_question(question, context):
    system_prompt = f"""
    You are an expert Data Analyst.
    {context}
    
    If the user asks for specific numbers (e.g., "highest sales month"), reply in JSON format:
    {{
      "type": "data",
      "metric": "SALES",
      "groupby": "YearMonth", 
      "operation": "sum",
      "chart": "bar"
    }}

    If the user asks a "Why" or "Explain" question (e.g., "Why did sales drop in 2005?"), reply in JSON format with an explanation:
    {{
      "type": "text",
      "answer": "Your explanation here based on the dataset summary provided."
    }}
    
    Return ONLY valid JSON.
    """
    
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0
    )

    try:
        response = json.loads(completion.choices[0].message.content)
        return response
    except json.JSONDecodeError:
        return {"type": "error", "message": "Failed to process query."}

# =====================================================
# CHAT UI
# =====================================================
st.markdown("---")
st.subheader("🤖 AI Analyst (Ask 'Why')")

user_question = st.text_input(
    "Ask a question (e.g. 'Why are 2005 sales lower?' or 'Which product sells best?')"
)

if user_question:
    response = ask_data_question(user_question, data_context)

    if response["type"] == "text":
        st.info(f"🤖 **Analysis:** {response['answer']}")
    
    elif response["type"] == "data":
        # Process data query logic here (similar to your previous code)
        st.markdown("### 📊 Data Result")
        
        # Simple dynamic grouping based on AI response
        if response["groupby"] == "YearMonth":
            data = filtered_df.groupby("YearMonth")[response["metric"]].sum()
        else:
            data = filtered_df.groupby(response["groupby"])[response["metric"]].sum().sort_values(ascending=False)
            
        st.bar_chart(data)
        st.write(f"Showing {response['metric']} by {response['groupby']}")
        
    else:
        st.error("Could not understand the question. Try being more specific.")
