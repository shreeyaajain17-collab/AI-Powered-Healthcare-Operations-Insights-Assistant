"""
Streamlit front end for the AI-Powered Healthcare Operations Assistant.

Run with:  streamlit run app.py
Requires Azure OpenAI environment variables set (or entered in the sidebar):
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT
"""
import os
import pandas as pd
import streamlit as st

from azure_nl_to_sql import NLToSQLAssistant

st.set_page_config(page_title="Hospital Ops AI Assistant", page_icon="🏥", layout="wide")

st.title("🏥 AI-Powered Healthcare Operations & Insights Assistant")
st.caption("Built on Azure OpenAI Service. Ask a business question in plain English — "
           "the assistant converts it to SQL, runs it against the hospital operations "
           "database, and explains the result.")

with st.sidebar:
    st.header("Azure OpenAI Setup")
    azure_endpoint = st.text_input("Azure OpenAI Endpoint",
                                    value=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
                                    placeholder="https://your-resource.openai.azure.com/")
    api_key = st.text_input("Azure OpenAI API Key", type="password",
                             value=os.environ.get("AZURE_OPENAI_API_KEY", ""))
    deployment = st.text_input("Deployment name",
                                value=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"))
    st.markdown("---")
    st.subheader("Try one of these")
    examples = [
        "Which cities have the most patients but seem underserved by doctors?",
        "What's our total outstanding revenue and which payment status is driving it?",
        "Show me the top 3 doctors by completed appointment count.",
        "Which treatment types cost the most on average?",
        "What percentage of appointments end up cancelled or no-show?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["question"] = ex

if "question" not in st.session_state:
    st.session_state["question"] = ""

question = st.text_input("Your question", value=st.session_state["question"],
                          placeholder="e.g. Which department has the highest unpaid billing?")

if st.button("Ask", type="primary") and question:
    if not (azure_endpoint and api_key):
        st.error("Enter your Azure OpenAI endpoint and API key in the sidebar first.")
    else:
        with st.spinner("Generating SQL and running it against the database..."):
            assistant = NLToSQLAssistant(azure_endpoint=azure_endpoint, api_key=api_key, deployment=deployment)
            result = assistant.ask(question)

        if result["error"]:
            st.error(result["error"])
            with st.expander("Generated SQL (blocked / failed)"):
                st.code(result["sql"], language="sql")
        else:
            st.success(result["answer"])

            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("Generated SQL")
                st.code(result["sql"], language="sql")
            with col2:
                st.subheader("Result")
                if result["rows"]:
                    st.dataframe(pd.DataFrame(result["rows"]), use_container_width=True)
                else:
                    st.write("No rows returned.")
