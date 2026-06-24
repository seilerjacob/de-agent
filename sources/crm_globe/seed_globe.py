"""
Seed script for the Globe CRM SQLite database.

Creates and populates three tables with intentionally different naming/schema
conventions compared to the Acme CRM, demonstrating the need for schema
unification in the curated layer.

Tables:
    customers — Customer records (different column names/structure vs Acme contacts)
    products  — Product catalog (different column names/structure vs Acme inventory)
    quotes    — Quote line items (line-item grain; multiple rows share a quote_id)
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "globe_crm.db"


def _surrogate_key(source_system: str, source_id: str) -> str:
    """Reproduce dbt's generate_surrogate_key for seeding FK values."""
    return hashlib.md5(f"{source_system}-{source_id}".encode()).hexdigest()


# Surrogate keys matching unified_customers / unified_products after dbt runs.
_CUST_ACME_1  = _surrogate_key("acme",  "1")
_CUST_ACME_2  = _surrogate_key("acme",  "2")
_CUST_GLOBE_1 = _surrogate_key("globe", "1")
_CUST_GLOBE_2 = _surrogate_key("globe", "2")
_PROD_ACME_1  = _surrogate_key("acme",  "1")
_PROD_ACME_2  = _surrogate_key("acme",  "2")
_PROD_GLOBE_1 = _surrogate_key("globe", "1")
_PROD_GLOBE_2 = _surrogate_key("globe", "2")

CUSTOMERS_DDL = """
CREATE TABLE IF NOT EXISTS customers (
    cust_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT,
    mobile_phone  TEXT,
    organization  TEXT,
    signup_date   TEXT    NOT NULL,  -- ISO 8601 datetime string
    status        TEXT    NOT NULL DEFAULT 'active'  -- active, inactive, churned
);
"""

PRODUCTS_DDL = """
CREATE TABLE IF NOT EXISTS products (
    prod_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_title   TEXT    NOT NULL,
    product_desc    TEXT,
    product_type    TEXT,
    unit_cost       REAL    NOT NULL,
    retail_price    REAL    NOT NULL,
    available       INTEGER NOT NULL DEFAULT 1,  -- 1 = available, 0 = discontinued
    created_at      TEXT    NOT NULL  -- ISO 8601 datetime string
);
"""

QUOTES_DDL = """
CREATE TABLE IF NOT EXISTS quotes (
    quote_line_id  TEXT    PRIMARY KEY,
    quote_id       TEXT    NOT NULL,
    customer_id    TEXT    NOT NULL,
    product_id     TEXT    NOT NULL,
    quoted_price   REAL    NOT NULL,
    quantity       INTEGER NOT NULL,
    status         TEXT    NOT NULL,  -- draft, sent, accepted, expired
    expiry_date    TEXT,              -- ISO 8601 date string
    created_at     TEXT    NOT NULL   -- ISO 8601 datetime string
);
"""

CUSTOMERS_DATA = [
    ("Alice Johnson", "a.johnson@acmecorp.com", "555-100-0001", "Acme Corp", "2024-01-20 09:30:00", "active"),
    ("Robert Smith", "rsmith@globex.com", "555-100-0002", "Globex Inc", "2024-02-25 14:15:00", "active"),
    ("Carol Williams", "cwilliams@initech.com", None, "Initech", "2024-03-15 11:00:00", "active"),
    ("Diana Prince", "diana.p@themyscira.org", "555-100-0004", "Themyscira Ltd", "2024-04-10 08:45:00", "active"),
    ("Eva Martinez", "eva.martinez@piedpiper.com", "555-100-0005", "Pied Piper", "2024-05-18 16:30:00", "inactive"),
    ("George Harris", "gharris@wayneent.com", "555-100-0006", "Wayne Enterprises", "2024-06-22 10:00:00", "active"),
    ("Hank Davis", "hdavis@stark.com", "555-100-0007", "Stark Industries", "2024-07-25 13:20:00", "active"),
    ("Isabella Rossi", "irossi@umbrella.com", "555-100-0008", "Umbrella Corp", "2024-08-05 09:15:00", "churned"),
    ("Jack Wilson", "jwilson@globex.com", "555-100-0009", "Globex Inc", "2024-09-20 11:45:00", "active"),
    ("Kenji Tanaka", "ktanaka@capsule.co", "555-100-0010", "Capsule Corp", "2024-10-08 15:00:00", "active"),
]

PRODUCTS_DATA = [
    ("Alpha Widget", "Entry-level widget with blue finish", "Widget", 5.00, 9.99, 1, "2024-01-05 08:00:00"),
    ("Beta Widget", "Premium widget with chrome plating", "Widget", 8.50, 15.49, 1, "2024-01-20 08:00:00"),
    ("Pro Gadget", "Multi-purpose gadget for professionals", "Gadget", 15.00, 29.99, 1, "2024-02-10 08:00:00"),
    ("Elite Gadget", "Flagship gadget with all accessories", "Gadget", 25.00, 52.99, 1, "2024-02-28 08:00:00"),
    ("Basic Cable", "Standard connector cable, 3ft", "Accessory", 1.50, 4.99, 1, "2024-03-05 08:00:00"),
    ("Shielded Cable", "EMI-shielded connector cable, 6ft", "Accessory", 5.00, 13.49, 1, "2024-03-20 08:00:00"),
    ("Power Adapter", "Universal 100-240V adapter", "Accessory", 8.00, 19.99, 1, "2024-04-10 08:00:00"),
    ("Temp Sensor", "High-precision temperature sensor", "Sensor", 18.00, 36.99, 1, "2024-05-15 08:00:00"),
    ("Sensor Pack", "Multi-sensor array (temp, humidity, pressure)", "Sensor", 40.00, 82.99, 1, "2024-06-10 08:00:00"),
    ("Mounting Kit", "Universal wall/desk mount", "Accessory", 3.00, 8.49, 0, "2024-07-05 08:00:00"),
    ("Widget Nano", "Ultra-compact micro widget", "Widget", 3.00, 6.99, 1, "2024-08-01 08:00:00"),
]


QUOTES_DATA = [
    # quote_line_id, quote_id, customer_id, product_id, quoted_price, quantity, status, expiry_date, created_at
    ("QL-0001", "QUOTE-001", _CUST_ACME_1,  _PROD_ACME_1,    9.99,  5, "accepted", "2025-01-31", "2025-01-05 10:00:00"),
    ("QL-0002", "QUOTE-001", _CUST_ACME_1,  _PROD_ACME_2,   14.99,  2, "accepted", "2025-01-31", "2025-01-05 10:00:00"),
    ("QL-0003", "QUOTE-001", _CUST_ACME_1,  _PROD_GLOBE_1,   9.99, 10, "accepted", "2025-01-31", "2025-01-05 10:00:00"),
    ("QL-0004", "QUOTE-002", _CUST_GLOBE_1, _PROD_GLOBE_2,  52.99,  1, "sent",     "2025-02-28", "2025-02-01 13:20:00"),
    ("QL-0005", "QUOTE-003", _CUST_GLOBE_2, _PROD_ACME_1,    9.99,  3, "draft",    "2025-03-15", "2025-02-25 09:10:00"),
    ("QL-0006", "QUOTE-003", _CUST_GLOBE_2, _PROD_GLOBE_1,   6.99,  8, "draft",    "2025-03-15", "2025-02-25 09:10:00"),
    ("QL-0007", "QUOTE-004", _CUST_ACME_2,  _PROD_ACME_2,   14.99,  4, "expired",  "2025-02-10", "2025-01-20 15:30:00"),
    ("QL-0008", "QUOTE-004", _CUST_ACME_2,  _PROD_GLOBE_2,  52.99,  1, "expired",  "2025-02-10", "2025-01-20 15:30:00"),
    ("QL-0009", "QUOTE-005", _CUST_GLOBE_1, _PROD_ACME_1,    9.99,  6, "sent",     "2025-04-01", "2025-03-10 11:45:00"),
    ("QL-0010", "QUOTE-006", _CUST_ACME_1,  _PROD_GLOBE_1,   6.99, 12, "accepted", "2025-03-20", "2025-03-08 08:25:00"),
]


def seed() -> Path:
    """Create and populate the Globe CRM database.

    Returns:
        Path to the created database file.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Create tables
    cur.execute("DROP TABLE IF EXISTS customers")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS quotes")
    cur.execute(CUSTOMERS_DDL)
    cur.execute(PRODUCTS_DDL)
    cur.execute(QUOTES_DDL)

    # Populate
    cur.executemany(
        "INSERT INTO customers (full_name, email, mobile_phone, organization, signup_date, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        CUSTOMERS_DATA,
    )
    cur.executemany(
        "INSERT INTO products (product_title, product_desc, product_type, unit_cost, retail_price, available, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        PRODUCTS_DATA,
    )
    cur.executemany(
        "INSERT INTO quotes (quote_line_id, quote_id, customer_id, product_id, quoted_price, quantity, status, expiry_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        QUOTES_DATA,
    )

    con.commit()
    cust_count = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    prod_count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    quotes_count = cur.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    con.close()

    logger.info(
        "Globe CRM seeded — %d customers, %d products, %d quotes → %s",
        cust_count, prod_count, quotes_count, DB_PATH,
    )
    return DB_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    path = seed()
    print(f"Globe CRM database created at {path}")
