# 📊 AI-Powered Sales Intelligence Dashboard

> **Live Demo:** [Click Here to View App](https://salesdashboard-rfwrmeplbeqgk44gns8e9p.streamlit.app/)

## 💼 Business Value
Most dashboards are static. This project introduces **"Hybrid Intelligence"**—combining hard data analytics with AI-driven business strategy.
* **For Executives:** Instant access to high-level KPIs (Revenue, Churn, Growth).
* **For Managers:** "Ask the Data" feature allows natural language queries (e.g., *"Why did sales drop in 2005?"*) without needing SQL knowledge.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Python)
* **Data Engine:** Pandas, NumPy
* **AI Integration:** Groq API (Llama-3.1-8b)
* **Visualization:** Altair & Streamlit Native Charts

## 🤖 Features
1.  **Dynamic Filtering:** Real-time data slicing by Year, Country, and Product Line.
2.  **AI Consultant:** A custom-built RAG (Retrieval-Augmented Generation) system that switches context between:
    * *Data Mode:* Generates charts for quantitative questions.
    * *Strategy Mode:* Provides business advice for qualitative questions.
3.  **Data Safety:** Secure API key handling via Streamlit Secrets.

## 🚀 How to Run Locally
1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/sales-dashboard.git](https://github.com/yourusername/sales-dashboard.git)
