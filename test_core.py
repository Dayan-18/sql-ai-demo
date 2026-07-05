"""Tests for everything deterministic: database, prompt, and guardrails.

The LLM call is intentionally NOT tested here — network calls don't belong
in unit tests. The guardrails exist precisely so we don't have to trust it.
"""
import pytest

from database import get_connection, get_schema_text
from guardrails import (
    UnsafeSQLError,
    build_prompt,
    extract_sql,
    validate_sql,
)

# ---------- database ----------

@pytest.fixture()
def conn():
    return get_connection(":memory:")


def test_schema_has_three_tables(conn):
    schema = get_schema_text(conn)
    for table in ("customers", "products", "orders"):
        assert table in schema


def test_seed_data_loaded(conn):
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 8


def test_analytical_query_runs(conn):
    # the kind of query the LLM is expected to produce
    row = conn.execute("""
        SELECT c.country, SUM(p.price * o.quantity) AS total
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        JOIN products p ON p.id = o.product_id
        GROUP BY c.country ORDER BY total DESC LIMIT 1
    """).fetchone()
    # Peru: Ana (1200 + 2x25.50) + Luis (349.99 + 45) = 1645.99, the highest
    assert row[0] == "Peru"


# ---------- extract_sql ----------

def test_extracts_sql_from_markdown_fence():
    raw = "Here is your query:\n```sql\nSELECT * FROM customers\n```\nHope it helps!"
    assert extract_sql(raw) == "SELECT * FROM customers"


def test_extracts_plain_sql_without_fence():
    assert extract_sql("SELECT id FROM orders;") == "SELECT id FROM orders"


def test_keeps_only_first_statement():
    raw = "```sql\nSELECT 1; DROP TABLE customers\n```"
    assert extract_sql(raw) == "SELECT 1"


# ---------- validate_sql (the security layer) ----------

def test_accepts_select():
    assert validate_sql("SELECT name FROM products") == "SELECT name FROM products"


def test_accepts_cte():
    sql = "WITH t AS (SELECT 1 AS x) SELECT x FROM t"
    assert validate_sql(sql) == sql


@pytest.mark.parametrize("evil", [
    "DROP TABLE customers",
    "DELETE FROM orders",
    "INSERT INTO customers VALUES (9,'x','y','z')",
    "UPDATE products SET price = 0",
    "PRAGMA writable_schema = ON",
    "ATTACH DATABASE '/etc/passwd' AS pwn",
    "SELECT * FROM customers; DROP TABLE customers",
])
def test_rejects_dangerous_sql(evil):
    with pytest.raises(UnsafeSQLError):
        validate_sql(evil)


def test_rejects_empty():
    with pytest.raises(UnsafeSQLError):
        validate_sql("   ")


# ---------- prompt ----------

def test_prompt_contains_schema_and_question(conn):
    schema = get_schema_text(conn)
    prompt = build_prompt(schema, "How many customers are from Peru?")
    assert "CREATE TABLE customers" in prompt
    assert "How many customers are from Peru?" in prompt
    assert "SELECT" in prompt  # instructs read-only
