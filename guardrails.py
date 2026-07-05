"""Safety layer: never execute whatever an LLM returns without validation."""
import re

# statements that must never reach the database
FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|"
    r"ATTACH|DETACH|PRAGMA|VACUUM|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(Exception):
    pass


def extract_sql(llm_output: str) -> str:
    """LLMs love wrapping SQL in markdown fences and prose. Strip all of it."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", llm_output, re.DOTALL)
    sql = match.group(1) if match else llm_output
    # keep only the first statement
    sql = sql.split(";")[0].strip()
    return sql


def validate_sql(sql: str) -> str:
    """Allow exactly one read-only SELECT statement. Raise otherwise."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        raise UnsafeSQLError("Empty SQL")
    if not re.match(r"^\s*(SELECT|WITH)\b", stripped, re.IGNORECASE):
        raise UnsafeSQLError(f"Only SELECT queries are allowed, got: {stripped[:40]}")
    if FORBIDDEN.search(stripped):
        raise UnsafeSQLError("Query contains a forbidden keyword")
    if ";" in stripped:
        raise UnsafeSQLError("Multiple statements are not allowed")
    return stripped


def build_prompt(schema: str, question: str) -> str:
    """Schema-aware prompt: the single biggest accuracy factor in text-to-SQL."""
    return f"""You are an expert SQLite analyst. Given this database schema:

{schema}

Write ONE SQLite SELECT query that answers this question:
"{question}"

Rules:
- Return ONLY the SQL, inside a ```sql code block.
- Read-only: SELECT statements only.
- Use exact table and column names from the schema.
"""
