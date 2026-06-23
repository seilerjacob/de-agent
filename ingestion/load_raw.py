"""
Raw Layer Ingestion — Load SQLite CRM sources into Snowflake.

Reads all tables from each upstream CRM SQLite database and lands them
as-is into the Snowflake ``DE_AGENT`` schema, prefixed by source system name.

Snowflake uppercases unquoted identifiers, so raw tables are created with
uppercase names to match how dbt sources reference them:

    DE_AGENT_RAW.RAW_ACME__CONTACTS
    DE_AGENT_RAW.RAW_ACME__INVENTORY
    DE_AGENT_RAW.RAW_GLOBE__CUSTOMERS
    DE_AGENT_RAW.RAW_GLOBE__PRODUCTS

Credentials are read exclusively from environment variables (sourced from
``.env.snowflake`` — see ``.env.snowflake.example``). Both password and
key-pair authentication are supported; whichever env var is present is used.

This is the Snowflake reference implementation of the raw ingestion layer.
On ``dev`` the equivalent module targets DuckDB.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_SCHEMA = "DE_AGENT_RAW"

SOURCES: dict[str, Path] = {
    "acme": PROJECT_ROOT / "sources" / "crm_acme" / "acme_crm.db",
    "globe": PROJECT_ROOT / "sources" / "crm_globe" / "globe_crm.db",
}


def get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    """Open a Snowflake connection from environment variables.

    Supports both username/password and key-pair authentication. If
    ``SNOWFLAKE_PRIVATE_KEY_PATH`` is set it takes precedence; otherwise
    ``SNOWFLAKE_PASSWORD`` is used. Optional parameters (role, private key)
    are only passed when present so the connector applies its defaults.

    Returns:
        An open Snowflake connection scoped to the ``DE_AGENT_RAW`` schema.

    Raises:
        KeyError: if a required env var is missing.
    """
    params: dict[str, str] = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": RAW_SCHEMA,
    }

    authenticator = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "").strip()
    if authenticator:
        params["authenticator"] = authenticator
    elif os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "").strip():
        params["private_key_file"] = os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"].strip()
    else:
        params["password"] = os.environ["SNOWFLAKE_PASSWORD"]

    role = os.environ.get("SNOWFLAKE_ROLE", "").strip()
    if role:
        params["role"] = role

    return snowflake.connector.connect(**params)


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
        # pandas 3.x defaults to StringDtype; the Snowflake pandas writer
        # expects plain object dtype for string columns.
        string_cols = [c for c, d in df.dtypes.items() if isinstance(d, pd.StringDtype)]
        if string_cols:
            df[string_cols] = df[string_cols].astype(object)
        tables[table] = df
        logger.info("  Extracted %s.%s — %d rows, %d cols", db_path.stem, table, len(df), len(df.columns))

    con.close()
    return tables


def load_to_raw(
    warehouse_path: Path | None = None,
    sources: dict[str, Path] | None = None,
) -> dict[str, int]:
    """Load all source tables into the Snowflake raw layer.

    Each table is written as ``DE_AGENT_RAW.RAW_{SOURCE}__{TABLE}`` (uppercased to
    match Snowflake's unquoted-identifier convention; double underscore
    follows the dbt source naming convention). Each table is fully
    replaced on every run (DROP + recreate), matching the DuckDB baseline.

    Args:
        warehouse_path: Unused on Snowflake. Kept in the signature so callers
            written against the DuckDB baseline require no changes.
        sources: Dict of source_name → SQLite DB path. Defaults to SOURCES.

    Returns:
        Dict mapping raw table name (``raw.raw_{source}__{table}``, lowercased
        for caller stability) to row count loaded.
    """
    if sources is None:
        sources = SOURCES

    con = get_snowflake_connection()
    results: dict[str, int] = {}

    try:
        con.cursor().execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")

        for source_name, db_path in sources.items():
            if not db_path.exists():
                logger.error("Source database not found: %s — run the seed script first", db_path)
                continue

            logger.info("Ingesting source: %s (%s)", source_name, db_path)
            tables = extract_sqlite_tables(db_path)

            for table_name, df in tables.items():
                sf_table = f"{source_name.upper()}__{table_name.upper()}"
                fq_table = f"{RAW_SCHEMA}.{sf_table}"

                # Full replace: drop then recreate via write_pandas
                # (auto_create_table builds the table from the DataFrame schema).
                con.cursor().execute(f"DROP TABLE IF EXISTS {fq_table}")
                success, _nchunks, nrows, _ = write_pandas(
                    con,
                    df,
                    table_name=sf_table,
                    schema=RAW_SCHEMA,
                    auto_create_table=True,
                    overwrite=True,
                    quote_identifiers=False,
                )
                if not success:
                    raise RuntimeError(f"write_pandas failed for {fq_table}")

                con.cursor().execute(f"ALTER TABLE {fq_table} SET CHANGE_TRACKING = TRUE")

                # Track under the lowercase key for caller/test stability.
                result_key = f"de_agent_raw.raw_{source_name}__{table_name}"
                results[result_key] = nrows
                logger.info("  Loaded %s — %d rows", fq_table, nrows)
    finally:
        con.close()

    logger.info("Raw layer load complete — %d tables loaded", len(results))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    loaded = load_to_raw()
    print("\nRaw layer summary:")
    for table, count in loaded.items():
        print(f"  {table}: {count} rows")
