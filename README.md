# SQL AI Demo — Talk to Your Database

Demo repo for the article **"SQL AI Database Solutions: Building a Safe Text-to-SQL App with Streamlit and Hugging Face"**.

Natural language → LLM → SQL → validated → executed on SQLite → results in a table.

- `app.py` — Streamlit UI + Hugging Face Inference API call
- `database.py` — demo e-commerce SQLite DB (customers, products, orders)
- `guardrails.py` — the safety layer: SELECT-only validation, fence stripping, single-statement rule
- `test_core.py` — 17 tests for everything deterministic (DB, prompt, guardrails)

## Run it

```bash
pip install -r requirements.txt
export HF_TOKEN=hf_xxx        # free token from https://huggingface.co/settings/tokens
streamlit run app.py
```

Then ask things like *"Which country has the highest total sales?"* or *"Top 3 products by revenue"*.

## Run the tests

```bash
pytest test_core.py -v        # 17 passed
```
