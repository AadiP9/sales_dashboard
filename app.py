# =====================================================
# IMPORT LIBRARIES
# =====================================================
import pandas as pd
import streamlit as st
from groq import Groq

# =====================================================
# PAGE CONFIG (MUST BE FIRST)
# =====================================================
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# =====================================================
# PAGE TITLE
# =====================================================
st.title("📊 Sales Performance Dashboard")
st.caption("Turning raw sales data into clear business insights")

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_csv("data/sales_data_sample.csv")

# =====================================================
# FEATURE ENGINEERING
# =====================================================
df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)
# Convert numeric month to readable month name
df["MonthName"] = df["ORDERDATE"].dt.month_name()


# =====================================================
# CLEAN DATA
# =====================================================
df.dropna(inplace=True)

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("Filters")

year = st.sidebar.multiselect(
    "Select Year",
    options=sorted(df["YEAR_ID"].unique()),
    default=sorted(df["YEAR_ID"].unique())
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

# Apply filters
filtered_df = df[
    (df["YEAR_ID"].isin(year)) &
    (df["PRODUCTLINE"].isin(product_line)) &
    (df["COUNTRY"].isin(country))
]

# =====================================================
# HANDLE EMPTY DATA AFTER FILTERS
# =====================================================
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# =====================================================
# KPI CALCULATIONS
# =====================================================
total_revenue = filtered_df["SALES"].sum()
total_orders = filtered_df["ORDERNUMBER"].nunique()
total_units = filtered_df["QUANTITYORDERED"].sum()

best_product_line = (
    filtered_df.groupby("PRODUCTLINE")["SALES"]
    .sum()
    .idxmax()
)

# =====================================================
# DISPLAY KPIs
# =====================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Total Orders", total_orders)
col3.metric("Units Sold", total_units)
col4.metric("Top Product Line", best_product_line)

# =====================================================
# MONTHLY SALES TREND
# =====================================================
monthly_sales = (
    filtered_df
    .groupby("YearMonth")["SALES"]
    .sum()
)

st.subheader("📈 Monthly Sales Trend")
st.line_chart(monthly_sales)

st.caption(
    f"Sales peaked in {monthly_sales.idxmax()} and were lowest in "
    f"{monthly_sales.idxmin()}, indicating seasonality in demand."
)

# =====================================================
# PRODUCT LINE PERFORMANCE
# =====================================================
product_sales = (
    filtered_df
    .groupby("PRODUCTLINE")["SALES"]
    .sum()
    .sort_values(ascending=False)
)

st.subheader("📊 Sales by Product Line")
st.bar_chart(product_sales)

st.caption(
    f"{product_sales.idxmax()} is the top-performing product line, while "
    f"{product_sales.idxmin()} contributes the least revenue."
)

# =====================================================
# COUNTRY-WISE SALES
# =====================================================
country_sales = (
    filtered_df
    .groupby("COUNTRY")["SALES"]
    .sum()
    .sort_values(ascending=False)
)

st.subheader("🌍 Sales by Country")
st.bar_chart(country_sales)

st.caption(
    f"{country_sales.idxmax()} is the strongest market by revenue, suggesting "
    "higher customer demand or better market penetration."
)

# =====================================================
# DEAL SIZE ANALYSIS
# =====================================================
deal_sales = (
    filtered_df
    .groupby("DEALSIZE")["SALES"]
    .sum()
)

st.subheader("💼 Revenue by Deal Size")
st.bar_chart(deal_sales)

st.caption(
    f"{deal_sales.idxmax()} deals generate the highest revenue share, indicating "
    "the importance of deal size in sales performance."
)

# =====================================================
# RAW DATA VIEW
# =====================================================
with st.expander("View Raw Data"):
    st.dataframe(filtered_df)

# =====================================================
# CHATBOT (NATURAL LANGUAGE DATA Q&A)
# =====================================================
st.subheader("🤖 Ask Questions About the Sales Data")

# Initialize Groq client
client = Groq(api_key=st.secrets["OPENAI_API_KEY"])


data_schema = """
You are working with a pandas dataframe named df.

Columns:
- ORDERDATE (datetime)
- SALES (float)
- QUANTITYORDERED (int)
- PRICEEACH (float)
- PRODUCTLINE (category)
- COUNTRY (category)
- DEALSIZE (category)
- YEAR_ID (int)
- MONTH_ID (int)
- MonthName (string, e.g. January, February, ...)


Notes:
- SALES represents revenue
- There is NO profit column
"""

def ask_data_question(question, df):
    """
    Uses Groq LLM to convert a natural language question
    into pandas code, executes it, and returns the result.
    """

    prompt = f"""
You are a senior data analyst.

{data_schema}

Rules:
- Use ONLY pandas
- Assume dataframe name is df
- Store final answer in a variable named `result`
- Do NOT print anything
- Do NOT import libraries
- When returning a month, prefer MonthName over numeric MONTH_ID

Question:
{question}
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # ✅ VALID FREE MODEL
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    generated_code = completion.choices[0].message.content
    local_vars = {"df": df}

    try:
        exec(generated_code, {}, local_vars)
        return local_vars["result"], generated_code
    except Exception as e:
        return f"Error: {e}", generated_code

# Chat UI
user_question = st.text_input(
    "Ask a question (e.g. Which was the lowest sales month in 2005?)"
)

if user_question:
    answer, code_used = ask_data_question(user_question, filtered_df)

    st.markdown("### ✅ Answer")
    st.write(answer)

    with st.expander("How this was computed"):
        st.code(code_used, language="python")
