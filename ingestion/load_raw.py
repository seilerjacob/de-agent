"""
Raw Layer Ingestion — Load SQLite CRM sources into DuckDB.

Reads all tables from each upstream CRM SQLite database and lands them
as-is into the DuckDB raw layer, prefixed by source system name.

Target tables created:
    raw.acme__contacts
    raw.acme__inventory
    raw.globe__customers
    raw.globe__products
    raw.transactions__sales
    raw.transactions__quotes

Table names follow the ``{source}__{table}`` convention (double underscore)
so they line up with the dbt source declarations in
``dbt_project/models/staging/*/_*__sources.yml``.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE_PATH = PROJECT_ROOT / "warehouse" / "lakehouse.duckdb"

SOURCES: dict[str, Path] = {
    "acme": PROJECT_ROOT / "sources" / "crm_acme" / "acme_crm.db",
    "globe": PROJECT_ROOT / "sources" / "crm_globe" / "globe_crm.db",
    "transactions": PROJECT_ROOT / "sources" / "transactions" / "transactions.db",
}


def extract_sqlite_tables(db_path: Path) -> dict[str, pd.DataFrame]:
    """Extract all user tables from a SQLite database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Dict mapping table name to its DataFrame contents.
    """
    con = sqlite3.connect(str(db_path))
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    table_names = [row[0] for row in cursor.fetchall()]

    tables: dict[str, pd.DataFrame] = {}
    for table in table_names:
        df = pd.read_sql_query(f"SELECT * FROM {table}", con)  # noqa: S608
        # pandas 3.x defaults to StringDtype; DuckDB requires object dtype for strings
        string_cols = [c for c, d in df.dtypes.items() if isinstance(d, pd.StringDtype)]
        if string_cols:
            df[string_cols] = df[string_cols].astype(object)
        tables[table] = df
        logger.info("  Extracted %s.%s — %d rows, %d cols", db_path.stem, table, len(df), len(df.columns))

    con.close()
    return tables


def load_to_raw(
    warehouse_path: Path = WAREHOUSE_PATH,
    sources: dict[str, Path] | None = None,
) -> dict[str, int]:
    """Load all source tables into the DuckDB raw layer.

    Each table is written as ``raw.{source}__{table}`` (double underscore
    follows the dbt source naming convention). Each table is fully replaced
    on every run (DROP + recreate).

    Args:
        warehouse_path: Path to the target DuckDB file.
        sources: Dict of source_name → SQLite DB path. Defaults to SOURCES.

    Returns:
        Dict mapping raw table name to row count loaded.
    """
    if sources is None:
        sources = SOURCES

    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(warehouse_path))

    # Create the raw schema
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    results: dict[str, int] = {}

    for source_name, db_path in sources.items():
        if not db_path.exists():
            logger.error("Source database not found: %s — run the seed script first", db_path)
            continue

        logger.info("Ingesting source: %s (%s)", source_name, db_path)
        tables = extract_sqlite_tables(db_path)

        for table_name, df in tables.items():
            raw_table = f"raw.{source_name}__{table_name}"
            con.execute(f"DROP TABLE IF EXISTS {raw_table}")
            con.execute(f"CREATE TABLE {raw_table} AS SELECT * FROM df")
            row_count = con.execute(f"SELECT COUNT(*) FROM {raw_table}").fetchone()[0]
            results[raw_table] = row_count
            logger.info("  Loaded %s — %d rows", raw_table, row_count)

    con.close()
    logger.info("Raw layer load complete — %d tables loaded", len(results))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    loaded = load_to_raw()
    print("\nRaw layer summary:")
    for table, count in loaded.items():
        print(f"  {table}: {count} rows")
