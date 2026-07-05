"""Demo database: a small e-commerce SQLite DB the AI will query."""
import sqlite3

SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL
);
"""

SEED = """
INSERT INTO customers VALUES
 (1,'Ana Torres','Peru','2025-01-15'),
 (2,'Luis Quispe','Peru','2025-02-20'),
 (3,'Marie Dubois','France','2025-03-05'),
 (4,'John Smith','USA','2025-03-18'),
 (5,'Kenji Sato','Japan','2025-04-02');

INSERT INTO products VALUES
 (1,'Laptop Pro 14','electronics',1200.00),
 (2,'Wireless Mouse','electronics',25.50),
 (3,'Standing Desk','furniture',349.99),
 (4,'Office Chair','furniture',189.00),
 (5,'USB-C Hub','electronics',45.00);

INSERT INTO orders VALUES
 (1,1,1,1,'2025-05-01'),
 (2,1,2,2,'2025-05-01'),
 (3,2,3,1,'2025-05-10'),
 (4,3,1,1,'2025-05-12'),
 (5,3,5,3,'2025-05-12'),
 (6,4,4,2,'2025-06-01'),
 (7,5,2,1,'2025-06-15'),
 (8,2,5,1,'2025-06-20');
"""


def get_connection(path=":memory:"):
    """Create (or open) the demo database, seeding it if empty."""
    conn = sqlite3.connect(path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    if not tables:
        conn.executescript(SCHEMA)
        conn.executescript(SEED)
        conn.commit()
    return conn


def get_schema_text(conn):
    """Return the CREATE TABLE statements — this is what the LLM sees."""
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    ).fetchall()
    return "\n\n".join(r[0] for r in rows)
