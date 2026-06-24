"""
Seed script for the Acme CRM SQLite database.

Creates and populates three tables with intentionally different naming/schema
conventions compared to the Globe CRM, demonstrating the need for schema
unification in the curated layer.

Tables:
    contacts  — Customer/contact records
    inventory — Product catalog
    sales     — Sales line items (line-item grain; multiple rows share a sale_id)
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "acme_crm.db"


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

CONTACTS_DDL = """
CREATE TABLE IF NOT EXISTS contacts (
    contact_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email_address   TEXT,
    phone           TEXT,
    company_name    TEXT,
    created_date    TEXT    NOT NULL  -- ISO 8601 date string
);
"""

INVENTORY_DDL = """
CREATE TABLE IF NOT EXISTS inventory (
    item_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name        TEXT    NOT NULL,
    item_description TEXT,
    category         TEXT,
    price            REAL    NOT NULL,
    stock_qty        INTEGER NOT NULL DEFAULT 0,
    added_date       TEXT    NOT NULL  -- ISO 8601 date string
);
"""

CONTACTS_DATA = [
    ("Alice", "Johnson", "alice.johnson@acmecorp.com", "555-0101", "Acme Corp", "2024-01-15"),
    ("Bob", "Smith", "bob.smith@globex.com", "555-0102", "Globex Inc", "2024-02-20"),
    ("Carol", "Williams", "carol.w@initech.com", "555-0103", "Initech", "2024-03-10"),
    ("David", "Brown", "d.brown@hooli.com", "555-0104", "Hooli", "2024-04-05"),
    ("Eva", "Martinez", "eva.m@piedpiper.com", "555-0105", "Pied Piper", "2024-05-12"),
    ("Frank", "Lee", "frank.lee@acmecorp.com", "555-0106", "Acme Corp", "2024-06-01"),
    ("Grace", "Kim", "grace.kim@wayneent.com", None, "Wayne Enterprises", "2024-06-15"),
    ("Hank", "Davis", "hank.d@stark.com", "555-0108", "Stark Industries", "2024-07-20"),
    ("Irene", "Chen", "irene.chen@umbrella.com", "555-0109", "Umbrella Corp", "2024-08-03"),
    ("Jack", "Wilson", "jack.w@globex.com", "555-0110", "Globex Inc", "2024-09-18"),
    ("Karen", "Taylor", "karen.t@initech.com", "555-0111", "Initech", "2024-10-01"),
    ("Leo", "Garcia", "leo.garcia@hooli.com", "555-0112", None, "2024-10-15"),
]

SALES_DDL = """
CREATE TABLE IF NOT EXISTS sales (
    sale_line_id  TEXT    PRIMARY KEY,
    sale_id       TEXT    NOT NULL,
    customer_id   TEXT    NOT NULL,
    product_id    TEXT    NOT NULL,
    amount        REAL    NOT NULL,
    stage         TEXT    NOT NULL,  -- closed_won, closed_lost, pending
    close_date    TEXT,              -- ISO 8601 date string, null when pending
    created_at    TEXT    NOT NULL   -- ISO 8601 datetime string
);
"""

INVENTORY_DATA = [
    ("Widget Alpha", "Standard widget, blue finish", "Widgets", 9.99, 150, "2024-01-01"),
    ("Widget Beta", "Premium widget, chrome finish", "Widgets", 14.99, 85, "2024-01-15"),
    ("Gadget Pro", "Multi-function gadget", "Gadgets", 29.99, 60, "2024-02-01"),
    ("Gadget Elite", "Top-tier gadget with extras", "Gadgets", 49.99, 30, "2024-02-15"),
    ("Connector Basic", "Standard connector cable", "Accessories", 4.99, 500, "2024-03-01"),
    ("Connector Pro", "Shielded connector cable", "Accessories", 12.99, 200, "2024-03-15"),
    ("Adapter Universal", "Universal power adapter", "Accessories", 19.99, 120, "2024-04-01"),
    ("Sensor Module", "Temperature and humidity sensor", "Sensors", 34.99, 45, "2024-05-01"),
    ("Sensor Array", "Multi-point sensor array", "Sensors", 79.99, 20, "2024-06-01"),
    ("Mount Kit", "Universal mounting hardware", "Accessories", 7.99, 300, "2024-07-01"),
]


SALES_DATA = [
    # sale_line_id, sale_id, customer_id, product_id, amount, stage, close_date, created_at
    ("SL-0001", "SALE-001", _CUST_ACME_1,  _PROD_ACME_1,   99.90, "closed_won",  "2025-01-15", "2025-01-10 09:30:00"),
    ("SL-0002", "SALE-001", _CUST_ACME_1,  _PROD_ACME_2,  149.90, "closed_won",  "2025-01-15", "2025-01-10 09:30:00"),
    ("SL-0003", "SALE-001", _CUST_ACME_1,  _PROD_GLOBE_1,  29.97, "closed_won",  "2025-01-15", "2025-01-10 09:30:00"),
    ("SL-0004", "SALE-002", _CUST_GLOBE_1, _PROD_GLOBE_2,  77.45, "closed_lost", "2025-02-03", "2025-01-28 14:05:00"),
    ("SL-0005", "SALE-002", _CUST_GLOBE_1, _PROD_ACME_1,    9.99, "closed_lost", "2025-02-03", "2025-01-28 14:05:00"),
    ("SL-0006", "SALE-003", _CUST_GLOBE_2, _PROD_GLOBE_1,  59.94, "closed_won",  "2025-02-20", "2025-02-18 11:15:00"),
    ("SL-0007", "SALE-003", _CUST_GLOBE_2, _PROD_ACME_2,   14.99, "closed_won",  "2025-02-20", "2025-02-18 11:15:00"),
    ("SL-0008", "SALE-004", _CUST_ACME_2,  _PROD_ACME_1,   19.98, "pending",     None,         "2025-03-05 16:45:00"),
    ("SL-0009", "SALE-004", _CUST_ACME_2,  _PROD_GLOBE_2,  52.99, "pending",     None,         "2025-03-05 16:45:00"),
    ("SL-0010", "SALE-004", _CUST_ACME_2,  _PROD_GLOBE_1,   6.99, "pending",     None,         "2025-03-05 16:45:00"),
]


def seed() -> Path:
    """Create and populate the Acme CRM database.

    Returns:
        Path to the created database file.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Create tables
    cur.execute("DROP TABLE IF EXISTS contacts")
    cur.execute("DROP TABLE IF EXISTS inventory")
    cur.execute("DROP TABLE IF EXISTS sales")
    cur.execute(CONTACTS_DDL)
    cur.execute(INVENTORY_DDL)
    cur.execute(SALES_DDL)

    # Populate
    cur.executemany(
        "INSERT INTO contacts (first_name, last_name, email_address, phone, company_name, created_date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        CONTACTS_DATA,
    )
    cur.executemany(
        "INSERT INTO inventory (item_name, item_description, category, price, stock_qty, added_date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        INVENTORY_DATA,
    )
    cur.executemany(
        "INSERT INTO sales (sale_line_id, sale_id, customer_id, product_id, amount, stage, close_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SALES_DATA,
    )

    con.commit()
    contact_count = cur.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    inventory_count = cur.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
    sales_count = cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    con.close()

    logger.info(
        "Acme CRM seeded — %d contacts, %d inventory items, %d sales → %s",
        contact_count, inventory_count, sales_count, DB_PATH,
    )
    return DB_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    path = seed()
    print(f"Acme CRM database created at {path}")
