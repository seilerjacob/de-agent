"""
Seed script for the shared transactions SQLite database.

Unlike the CRM sources (Acme, Globe), transactions are not source-system
specific — sales and quotes reference customers and products by their
*unified* surrogate keys. Those keys are produced downstream by dbt's
``generate_surrogate_key`` macro:

    md5(coalesce(cast(source_system as varchar), '') || '-'
        || coalesce(cast(source_id as varchar), ''))

To keep this seed self-documenting and free of magic hex strings, the
surrogate keys are computed here from the same (source_system, source_id)
inputs the CRM seeds use, via the ``surrogate_key`` helper below. The
inputs map to existing CRM seed rows (the SQLite integer autoincrement PK
is cast to varchar by staging, so the input is e.g. ``'acme-1'``):

    Customers:
      acme-1  → Alice Johnson   (acme_crm.contacts row 1)
      acme-2  → Bob Smith       (acme_crm.contacts row 2)
      globe-1 → Alice Johnson   (globe_crm.customers row 1)
      globe-2 → Robert Smith    (globe_crm.customers row 2)

    Products:
      acme-1  → Widget Alpha    (acme_crm.inventory row 1)
      acme-2  → Widget Beta     (acme_crm.inventory row 2)
      globe-1 → Alpha Widget    (globe_crm.products row 1)
      globe-2 → Beta Widget     (globe_crm.products row 2)

Tables:
    sales  — line-item-grain sales (multiple line items share a sale_id)
    quotes — line-item-grain quotes (multiple line items share a quote_id)
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "transactions.db"


def surrogate_key(source_system: str, source_id: str) -> str:
    """Reproduce dbt's generate_surrogate_key macro for a single source row.

    Mirrors ``md5(coalesce(cast(source_system as varchar), '') || '-'
    || coalesce(cast(source_id as varchar), ''))`` so seeded foreign keys
    match the ``customer_sk`` / ``product_sk`` values in ``unified_customers``
    and ``unified_products`` after dbt runs against the CRM seeds.

    Args:
        source_system: 'acme' or 'globe'.
        source_id: The source row's primary key as a string (e.g. '1').

    Returns:
        The 32-char lowercase MD5 hex surrogate key.
    """
    return hashlib.md5(f"{source_system}-{source_id}".encode()).hexdigest()


# Customer surrogate keys (2 from Acme, 2 from Globe).
CUST_ACME_1 = surrogate_key("acme", "1")
CUST_ACME_2 = surrogate_key("acme", "2")
CUST_GLOBE_1 = surrogate_key("globe", "1")
CUST_GLOBE_2 = surrogate_key("globe", "2")

# Product surrogate keys (2 from Acme, 2 from Globe).
PROD_ACME_1 = surrogate_key("acme", "1")
PROD_ACME_2 = surrogate_key("acme", "2")
PROD_GLOBE_1 = surrogate_key("globe", "1")
PROD_GLOBE_2 = surrogate_key("globe", "2")

SALES_DDL = """
CREATE TABLE IF NOT EXISTS sales (
    sale_line_id  TEXT    PRIMARY KEY,
    sale_id       TEXT    NOT NULL,
    customer_id   TEXT    NOT NULL,
    product_id    TEXT    NOT NULL,
    amount        REAL    NOT NULL,
    stage         TEXT    NOT NULL,  -- closed_won, closed_lost, pending
    close_date    TEXT,              -- ISO 8601 date string
    created_at    TEXT    NOT NULL   -- ISO 8601 datetime string
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

# 10 sales line items across 4 sale_ids. SALE-001 (3 lines) and SALE-002
# (2 lines) exercise the multi-line-item header hierarchy. Variety across
# stage and close_date (pending sales have no close_date).
SALES_DATA = [
    # sale_line_id, sale_id, customer_id, product_id, amount, stage, close_date, created_at
    ("SL-0001", "SALE-001", CUST_ACME_1,  PROD_ACME_1,   99.90, "closed_won",  "2025-01-15", "2025-01-10 09:30:00"),
    ("SL-0002", "SALE-001", CUST_ACME_1,  PROD_ACME_2,  149.90, "closed_won",  "2025-01-15", "2025-01-10 09:30:00"),
    ("SL-0003", "SALE-001", CUST_ACME_1,  PROD_GLOBE_1,  29.97, "closed_won",  "2025-01-15", "2025-01-10 09:30:00"),
    ("SL-0004", "SALE-002", CUST_GLOBE_1, PROD_GLOBE_2,  77.45, "closed_lost", "2025-02-03", "2025-01-28 14:05:00"),
    ("SL-0005", "SALE-002", CUST_GLOBE_1, PROD_ACME_1,    9.99, "closed_lost", "2025-02-03", "2025-01-28 14:05:00"),
    ("SL-0006", "SALE-003", CUST_GLOBE_2, PROD_GLOBE_1,  59.94, "closed_won",  "2025-02-20", "2025-02-18 11:15:00"),
    ("SL-0007", "SALE-003", CUST_GLOBE_2, PROD_ACME_2,   14.99, "closed_won",  "2025-02-20", "2025-02-18 11:15:00"),
    ("SL-0008", "SALE-004", CUST_ACME_2,  PROD_ACME_1,   19.98, "pending",     None,         "2025-03-05 16:45:00"),
    ("SL-0009", "SALE-004", CUST_ACME_2,  PROD_GLOBE_2,  52.99, "pending",     None,         "2025-03-05 16:45:00"),
    ("SL-0010", "SALE-004", CUST_ACME_2,  PROD_GLOBE_1,   6.99, "pending",     None,         "2025-03-05 16:45:00"),
]

# 10 quote line items across 6 quote_ids. QUOTE-001 (3 lines) and QUOTE-003
# (2 lines) exercise the multi-line-item header hierarchy. Variety across
# status and expiry_date.
QUOTES_DATA = [
    # quote_line_id, quote_id, customer_id, product_id, quoted_price, quantity, status, expiry_date, created_at
    ("QL-0001", "QUOTE-001", CUST_ACME_1,  PROD_ACME_1,    9.99,  5, "accepted", "2025-01-31", "2025-01-05 10:00:00"),
    ("QL-0002", "QUOTE-001", CUST_ACME_1,  PROD_ACME_2,   14.99,  2, "accepted", "2025-01-31", "2025-01-05 10:00:00"),
    ("QL-0003", "QUOTE-001", CUST_ACME_1,  PROD_GLOBE_1,   9.99, 10, "accepted", "2025-01-31", "2025-01-05 10:00:00"),
    ("QL-0004", "QUOTE-002", CUST_GLOBE_1, PROD_GLOBE_2,  52.99,  1, "sent",     "2025-02-28", "2025-02-01 13:20:00"),
    ("QL-0005", "QUOTE-003", CUST_GLOBE_2, PROD_ACME_1,    9.99,  3, "draft",    "2025-03-15", "2025-02-25 09:10:00"),
    ("QL-0006", "QUOTE-003", CUST_GLOBE_2, PROD_GLOBE_1,   6.99,  8, "draft",    "2025-03-15", "2025-02-25 09:10:00"),
    ("QL-0007", "QUOTE-004", CUST_ACME_2,  PROD_ACME_2,   14.99,  4, "expired",  "2025-02-10", "2025-01-20 15:30:00"),
    ("QL-0008", "QUOTE-004", CUST_ACME_2,  PROD_GLOBE_2,  52.99,  1, "expired",  "2025-02-10", "2025-01-20 15:30:00"),
    ("QL-0009", "QUOTE-005", CUST_GLOBE_1, PROD_ACME_1,    9.99,  6, "sent",     "2025-04-01", "2025-03-10 11:45:00"),
    ("QL-0010", "QUOTE-006", CUST_ACME_1,  PROD_GLOBE_1,   6.99, 12, "accepted", "2025-03-20", "2025-03-08 08:25:00"),
]


def seed() -> Path:
    """Create and populate the transactions database.

    Returns:
        Path to the created database file.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS sales")
    cur.execute("DROP TABLE IF EXISTS quotes")
    cur.execute(SALES_DDL)
    cur.execute(QUOTES_DDL)

    cur.executemany(
        "INSERT INTO sales "
        "(sale_line_id, sale_id, customer_id, product_id, amount, stage, close_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SALES_DATA,
    )
    cur.executemany(
        "INSERT INTO quotes "
        "(quote_line_id, quote_id, customer_id, product_id, quoted_price, quantity, status, expiry_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        QUOTES_DATA,
    )

    con.commit()
    sales_count = cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    quotes_count = cur.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    con.close()

    logger.info("Transactions seeded — %d sales, %d quotes → %s", sales_count, quotes_count, DB_PATH)
    return DB_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    path = seed()
    print(f"Transactions database created at {path}")
