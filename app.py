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
#     df = pd.read_csv(uploaded_file, encoding='ISO-8859-1') # Added encoding handling for common sales CSVs
# else:
#     # Ensure you have this file in your repo or handle the error gracefully
#     try:
#         df = pd.read_csv("data/sales_data_sample.csv", encoding='ISO-8859-1')
#     except FileNotFoundError:
#         st.error("Default data file not found. Please upload a CSV.")
#         st.stop()

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

# # Dynamic Years
# all_years = sorted(df["YEAR_ID"].unique())
# year = st.sidebar.multiselect(
#     "Select Year",
#     options=all_years,
#     default=all_years
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
# # ⚠️ DATA INTELLIGENCE WARNING (NEW FEATURE)
# # =====================================================
# # Automatically detect if 2005 is selected and warn about incomplete data
# if 2005 in year:
#     max_date_2005 = df[df["YEAR_ID"] == 2005]["ORDERDATE"].max()
#     st.warning(f"⚠️ **Analyst Note:** Data for 2005 is incomplete. It ends on {max_date_2005.strftime('%B %Y')}. Comparisons with full years (2003, 2004) may appear lower.")

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
# # DASHBOARD CHARTS (Optimized Sorting)
# # =====================================================
# st.subheader("📈 Monthly Sales Trend")
# monthly_sales = filtered_df.groupby("YearMonth")["SALES"].sum()
# st.line_chart(monthly_sales)

# # Row 2
# c1, c2 = st.columns(2)

# with c1:
#     st.subheader("📊 Sales by Product Line")
#     # Sort values descending for better readability
#     product_sales = filtered_df.groupby("PRODUCTLINE")["SALES"].sum().sort_values(ascending=False)
#     st.bar_chart(product_sales)

# with c2:
#     st.subheader("🌍 Sales by Country")
#     country_sales = filtered_df.groupby("COUNTRY")["SALES"].sum().sort_values(ascending=False)
#     st.bar_chart(country_sales)

# st.subheader("💼 Revenue by Deal Size")
# deal_sales = filtered_df.groupby("DEALSIZE")["SALES"].sum().sort_values(ascending=False)
# st.bar_chart(deal_sales)

# # =====================================================
# # RAW DATA
# # =====================================================
# with st.expander("View Raw Data"):
#     st.dataframe(filtered_df)

# # =====================================================
# # CHATBOT LOGIC (UPGRADED FOR "WHY" QUESTIONS)
# # =====================================================
# client = Groq(api_key=st.secrets["OPENAI_API_KEY"])

# # We create a "Summary" of the dataset to give the AI context
# # This lets it answer "Why" questions without needing to see all 10k rows
# data_context = f"""
# Dataset Summary:
# - Date Range: {df['ORDERDATE'].min().date()} to {df['ORDERDATE'].max().date()}
# - Total Years: {sorted(df['YEAR_ID'].unique())}
# - Note: 2005 data ends in May, making it a partial year.
# - Columns: ORDERDATE, SALES, PRODUCTLINE, COUNTRY, DEALSIZE.
# """

# def ask_data_question(question, context):
#     system_prompt = f"""
#     You are an expert Data Analyst.
#     {context}
    
#     If the user asks for specific numbers (e.g., "highest sales month"), reply in JSON format:
#     {{
#       "type": "data",
#       "metric": "SALES",
#       "groupby": "YearMonth", 
#       "operation": "sum",
#       "chart": "bar"
#     }}

#     If the user asks a "Why" or "Explain" question (e.g., "Why did sales drop in 2005?"), reply in JSON format with an explanation:
#     {{
#       "type": "text",
#       "answer": "Your explanation here based on the dataset summary provided."
#     }}
    
#     Return ONLY valid JSON.
#     """
    
#     completion = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": question}
#         ],
#         temperature=0
#     )

#     try:
#         response = json.loads(completion.choices[0].message.content)
#         return response
#     except json.JSONDecodeError:
#         return {"type": "error", "message": "Failed to process query."}

# # =====================================================
# # CHAT UI
# # =====================================================
# st.markdown("---")
# st.subheader("🤖 AI Analyst")

# user_question = st.text_input(
#     "Ask a question (e.g. 'Why are 2005 sales lower?' or 'Which product sells best?')"
# )

# if user_question:
#     response = ask_data_question(user_question, data_context)

#     if response["type"] == "text":
#         st.info(f"🤖 **Analysis:** {response['answer']}")
    
#     elif response["type"] == "data":
#         # Process data query logic here (similar to your previous code)
#         st.markdown("### 📊 Data Result")
        
#         # Simple dynamic grouping based on AI response
#         if response["groupby"] == "YearMonth":
#             data = filtered_df.groupby("YearMonth")[response["metric"]].sum()
#         else:
#             data = filtered_df.groupby(response["groupby"])[response["metric"]].sum().sort_values(ascending=False)
            
#         st.bar_chart(data)
#         st.write(f"Showing {response['metric']} by {response['groupby']}")
        
#     else:
#         st.error("Could not understand the question. Try being more specific.")


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

if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================================================
# CSV UPLOAD
# =====================================================
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
    col4.metric("Top Product", filtered_df.groupby("PRODUCTLINE")["SALES"].sum().idxmax())

# =====================================================
# CHARTS
# =====================================================
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

# =====================================================
# 🧠 HYBRID AI LOGIC (THE FIX)
# =====================================================
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
