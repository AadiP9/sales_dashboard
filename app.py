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
# TITLE & SESSION STATE
# =====================================================
st.title("📊 Sales Performance Dashboard")
st.caption("Upload your sales data, explore insights, and ask questions in plain English")

# Initialize chat history to keep the conversation alive
if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================================================
# CSV UPLOAD
# =====================================================
uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
else:
    # Fallback to local file if available, or create dummy data for testing
    try:
        df = pd.read_csv("data/sales_data_sample.csv", encoding='ISO-8859-1')
    except:
        st.warning("Please upload a CSV file to begin.")
        st.stop()

# =====================================================
# FEATURE ENGINEERING
# =====================================================
df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)
df["MonthName"] = df["ORDERDATE"].dt.month_name()

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("Filters")
year = st.sidebar.multiselect("Select Year", options=sorted(df["YEAR_ID"].unique()), default=sorted(df["YEAR_ID"].unique()))
product_line = st.sidebar.multiselect("Product Line", options=df["PRODUCTLINE"].unique(), default=df["PRODUCTLINE"].unique())
country = st.sidebar.multiselect("Country", options=df["COUNTRY"].unique(), default=df["COUNTRY"].unique())

filtered_df = df[
    (df["YEAR_ID"].isin(year)) &
    (df["PRODUCTLINE"].isin(product_line)) &
    (df["COUNTRY"].isin(country))
]

# =====================================================
# KPI SECTION
# =====================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered_df['SALES'].sum():,.0f}")
col2.metric("Total Orders", filtered_df["ORDERNUMBER"].nunique())
col3.metric("Units Sold", filtered_df["QUANTITYORDERED"].sum())
if not filtered_df.empty:
    col4.metric("Top Product Line", filtered_df.groupby("PRODUCTLINE")["SALES"].sum().idxmax())

# =====================================================
# CHARTS
# =====================================================
st.subheader("📈 Business Overview")
c1, c2 = st.columns(2)
with c1:
    st.markdown("### Monthly Sales")
    st.line_chart(filtered_df.groupby("YearMonth")["SALES"].sum())
with c2:
    st.markdown("### Sales by Product")
    st.bar_chart(filtered_df.groupby("PRODUCTLINE")["SALES"].sum().sort_values(ascending=False))

# =====================================================
# ADVANCED AI LOGIC (THE FIX)
# =====================================================
client = Groq(api_key=st.secrets["OPENAI_API_KEY"])

# We feed the AI a summary of the CURRENT filtered data
data_summary = f"""
Current Data Context:
- Total Revenue: ${filtered_df['SALES'].sum():,.2f}
- Top Selling Product: {filtered_df.groupby('PRODUCTLINE')['SALES'].sum().idxmax() if not filtered_df.empty else 'N/A'}
- Top Country: {filtered_df.groupby('COUNTRY')['SALES'].sum().idxmax() if not filtered_df.empty else 'N/A'}
- Active Years: {sorted(filtered_df['YEAR_ID'].unique())}
"""

def ask_ai(question, context):
    # This prompt now allows 3 types of answers: DATA, REASONING, and STRATEGY
    system_prompt = f"""
    You are an expert Business Intelligence Consultant. 
    {context}
    
    Categorize the user's question into one of three types and return valid JSON ONLY.

    TYPE 1: DATA QUERY (The user asks for a specific number or chart)
    Format:
    {{
      "type": "data",
      "metric": "SALES | QUANTITYORDERED | PRICEEACH",
      "groupby": "YearMonth | PRODUCTLINE | COUNTRY | DEALSIZE",
      "operation": "sum | mean | count"
    }}

    TYPE 2: EXPLANATION (The user asks "Why" something happened)
    Format:
    {{
      "type": "text",
      "response": "Explain the insight using the provided data summary. Keep it professional and short."
    }}

    TYPE 3: STRATEGY (The user asks "How" to improve or specific business advice)
    Format:
    {{
      "type": "strategy",
      "response": "Provide 3 actionable business tips based on the data context (e.g., if sales are low in France, suggest marketing there)."
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.3
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"type": "error", "response": f"Error: {str(e)}"}

# =====================================================
# CHAT INTERFACE
# =====================================================
st.markdown("---")
st.subheader("🤖 AI Business Consultant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input
if prompt := st.chat_input("Ask about data (e.g., 'Total sales in 2004') or strategy (e.g., 'How can we sell more cars?')"):
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get AI Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = ask_ai(prompt, data_summary)
            
            if result["type"] == "text" or result["type"] == "strategy":
                st.write(result["response"])
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            
            elif result["type"] == "data":
                # Compute the data locally
                try:
                    grouped_data = filtered_df.groupby(result["groupby"])[result["metric"]].agg(result["operation"]).sort_values(ascending=False)
                    st.bar_chart(grouped_data)
                    response_text = f"Here is the {result['metric']} grouped by {result['groupby']}."
                    st.write(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Could not generate chart: {e}")
            
            else:
                st.error("I couldn't process that request.")
