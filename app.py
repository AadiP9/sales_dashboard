# Import Libraries
import pandas as pd
import streamlit as st
from groq import Groq
import json

# PAGE CONFIG
st.set_page_config(page_title="Sales Dashboard", layout="wide")

# TITLE & SESSION STATE
st.title("📊 Sales Performance Dashboard")
st.caption("Upload your sales data, explore insights, and ask questions in plain English")

if "messages" not in st.session_state:
    st.session_state.messages = []

# CSV UPLOAD
uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

if uploaded_file is not None:
    # 'errors="replace"' prevents crashes from bad characters
    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1', errors='replace') 
else:
    # Fallback / Demo mode
    try:
        df = pd.read_csv("data/sales_data_sample.csv", encoding='ISO-8859-1')
    except:
        st.warning("Please upload a CSV file to begin.")
        st.stop()

# FEATURE ENGINEERING
df["ORDERDATE"] = pd.to_datetime(df["ORDERDATE"])
df["YearMonth"] = df["ORDERDATE"].dt.to_period("M").astype(str)
df["MonthName"] = df["ORDERDATE"].dt.month_name()

# SIDEBAR FILTERS
st.sidebar.header("Filters")
year = st.sidebar.multiselect("Select Year", options=sorted(df["YEAR_ID"].unique()), default=sorted(df["YEAR_ID"].unique()))
product_line = st.sidebar.multiselect("Product Line", options=df["PRODUCTLINE"].unique(), default=df["PRODUCTLINE"].unique())
country = st.sidebar.multiselect("Country", options=df["COUNTRY"].unique(), default=df["COUNTRY"].unique())

filtered_df = df[
    (df["YEAR_ID"].isin(year)) &
    (df["PRODUCTLINE"].isin(product_line)) &
    (df["COUNTRY"].isin(country))
]

# KPI SECTION
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered_df['SALES'].sum():,.0f}")
col2.metric("Total Orders", filtered_df["ORDERNUMBER"].nunique())
col3.metric("Units Sold", filtered_df["QUANTITYORDERED"].sum())
if not filtered_df.empty:
    col4.metric("Top Product", filtered_df.groupby("PRODUCTLINE")["SALES"].sum().idxmax())

# Charts
st.subheader("📈 Business Overview")
c1, c2 = st.columns(2)
with c1:
    st.markdown("### Monthly Sales")
    if not filtered_df.empty:
        st.line_chart(filtered_df.groupby("YearMonth")["SALES"].sum())
with c2:
    st.markdown("### Sales by Product")
    if not filtered_df.empty:
        st.bar_chart(filtered_df.groupby("PRODUCTLINE")["SALES"].sum().sort_values(ascending=False))

# Hybrid AI Logic
client = Groq(api_key=st.secrets["OPENAI_API_KEY"])

# Create a textual summary of the data so the AI "knows" what it's looking at
data_summary = f"""
DATA CONTEXT:
- Total Revenue: ${filtered_df['SALES'].sum():,.2f}
- Top Selling Product: {filtered_df.groupby('PRODUCTLINE')['SALES'].sum().idxmax() if not filtered_df.empty else 'N/A'}
- Top Country: {filtered_df.groupby('COUNTRY')['SALES'].sum().idxmax() if not filtered_df.empty else 'N/A'}
- Date Range: {filtered_df['ORDERDATE'].min().date()} to {filtered_df['ORDERDATE'].max().date()}
"""

def ask_ai(question, context):
    # This prompt forces the AI to choose: "Am I calculating a number?" OR "Am I giving advice?"
    system_prompt = f"""
    You are an expert Business Intelligence Consultant.
    {context}
    
    If the user asks a DATA question (e.g., "Total sales in 2004", "Show me a bar chart of sales by country"), return JSON with "type": "plot".
    
    If the user asks a STRATEGY or WHY question (e.g., "How to increase sales?", "Why did sales drop?", "Give me a roadmap"), return JSON with "type": "text".

    RESPONSE FORMATS (Return ONLY valid JSON):

    OPTION 1 (For Plot/Data):
    {{
      "type": "plot",
      "metric": "SALES | QUANTITYORDERED",
      "groupby": "YearMonth | PRODUCTLINE | COUNTRY | DEALSIZE",
      "operation": "sum | mean | count"
    }}

    OPTION 2 (For Advice/Explanation):
    {{
      "type": "text",
      "response": "Your professional advice here based on the data summary. Keep it strictly under 50 words."
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )
        response_content = completion.choices[0].message.content
        return json.loads(response_content)
    
    except json.JSONDecodeError:
        # FALLBACK: If AI fails to give JSON, just return the raw text
        return {"type": "text", "response": "I couldn't format the data exactly, but here is my thought: " + completion.choices[0].message.content[:100]}
    except Exception as e:
        return {"type": "error", "response": f"Error: {str(e)}"}

# CHAT INTERFACE
st.markdown("---")
st.subheader("🤖 AI Business Consultant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input
if prompt := st.chat_input("Ask: 'Sales in 2004?' OR 'How to improve sales?'"):
    
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 2. Get AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            result = ask_ai(prompt, data_summary)
            
            # CASE A: It's just text/advice
            if result["type"] == "text":
                st.write(result["response"])
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            
            # CASE B: It's a chart/data query
            elif result["type"] == "plot":
                try:
                    # Compute the data
                    grouped_data = filtered_df.groupby(result["groupby"])[result["metric"]].agg(result["operation"]).sort_values(ascending=False)
                    
                    # Display the Chart
                    st.bar_chart(grouped_data)
                    
                    # Add a text summary
                    summary_text = f"Here is the {result['metric']} grouped by {result['groupby']}."
                    st.write(summary_text)
                    st.session_state.messages.append({"role": "assistant", "content": summary_text})
                    
                except Exception as e:
                    st.error(f"Could not generate chart. Error: {e}")
            
            # CASE C: Error
            else:
                st.error("I couldn't process that request.")
