"""
Talk to your database in plain English.
Streamlit + Hugging Face Inference API + SQLite, with a safety layer.

Run:  HF_TOKEN=hf_xxx streamlit run app.py
"""
import os

import pandas as pd
import requests
import streamlit as st

from database import get_connection, get_schema_text
from guardrails import UnsafeSQLError, build_prompt, extract_sql, validate_sql

HF_MODEL = os.environ.get("HF_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
HF_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}/v1/chat/completions"


def ask_llm(prompt: str) -> str:
    """Send the schema-aware prompt to the Hugging Face Inference API."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("Set the HF_TOKEN environment variable (free at hf.co)")
    resp = requests.post(
        HF_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model": HF_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.1,  # low temperature: we want deterministic SQL
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ---------------- UI ----------------

st.set_page_config(page_title="SQL AI Demo", page_icon="🗃️")
st.title("🗃️ Talk to your database")
st.caption("Natural language → SQL → results. Powered by Hugging Face + SQLite.")

conn = get_connection("shop.db")
schema = get_schema_text(conn)

with st.expander("Database schema (what the AI sees)"):
    st.code(schema, language="sql")

question = st.text_input(
    "Ask a question about the data:",
    placeholder="e.g. Which country has the highest total sales?",
)

if question:
    with st.spinner("Thinking..."):
        try:
            raw = ask_llm(build_prompt(schema, question))
            sql = validate_sql(extract_sql(raw))
            st.subheader("Generated SQL")
            st.code(sql, language="sql")

            df = pd.read_sql_query(sql, conn)
            st.subheader("Results")
            st.dataframe(df, use_container_width=True)
        except UnsafeSQLError as e:
            st.error(f"🛡️ Blocked by guardrails: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
