# Import libraries
import pandas as pd
import streamlit as st

# Page config
st.set__page_config(page_title="Sales Dashboard", layout="wide")

# Load data
df = pd.read_csv("data/sales_data_sample.csv")

# Feature engineering
df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)

# Clean data
df.dropna(inplace=True)

# Sidebar filters
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

filtered_df = df[
    (df["YEAR_ID"].isin(year)) &
    (df["PRODUCTLINE"].isin(product_line)) &
    (df["COUNTRY"].isin(country))
]

# KPI Calculations
total_revenue = filtered_df["SALES"].sum()
total_orders = filtered_df["ORDERNUMBER"].nunique()
total_units = filtered_df["QUANTITYORDERED"].sum()

best_product_line = (
    filtered_df.groupby("PRODUCTLINE")["SALES"]
    .sum()
    .idxmax()
)

# Display KPIs
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Total Orders", total_orders)
col3.metric("Units Sold", total_units)
col4.metric("Top Product Line", best_product_line)

# Monthly revenue trend
monthly_sales = (
    filtered_df
    .groupby("YearMonth")["SALES"]
    .sum()
)

st.subheader("📈 Monthly Sales Trend")
st.line_chart(monthly_sales)

# Product line performance
product_sales = (
    filtered_df
    .groupby("PRODUCTLINE")["SALES"]
    .sum()
    .sort_values(ascending=False)
)

st.subheader("📊 Sales by Product Line")
st.bar_chart(product_sales)

# Country-wise sales
country_sales = (
    filtered_df
    .groupby("COUNTRY")["SALES"]
    .sum()
    .sort_values(ascending=False)
)

st.subheader("🌍 Sales by Country")
st.bar_chart(country_sales)

# Deal size analysis
deal_sales = (
    filtered_df
    .groupby("DEALSIZE")["SALES"]
    .sum()
)

st.subheader("💼 Revenue by Deal Size")
st.bar_chart(deal_sales)

# Raw data toggle
with st.expander("View Raw Data"):
    st.dataframe(filtered_df)

# Page title
st.title("📊 Sales Performance Dashboard")
st.caption("Turning raw sales data into clear business insights")
