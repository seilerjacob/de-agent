"""
Seed script for the Globe CRM SQLite database.

Creates and populates two tables with intentionally different naming/schema
conventions compared to the Acme CRM, demonstrating the need for schema
unification in the curated layer.

Tables:
    customers — Customer records (different column names/structure vs Acme contacts)
    products  — Product catalog (different column names/structure vs Acme inventory)
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "globe_crm.db"

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
    cur.execute(CUSTOMERS_DDL)
    cur.execute(PRODUCTS_DDL)

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

    con.commit()
    cust_count = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    prod_count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    con.close()

    logger.info("Globe CRM seeded — %d customers, %d products → %s", cust_count, prod_count, DB_PATH)
    return DB_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    path = seed()
    print(f"Globe CRM database created at {path}")
