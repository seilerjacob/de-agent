"""
Load — Read extracted CSV, run SQL transforms in DuckDB, and persist.

Ties together the extract (CSV) and transform (SQL) steps into a single
runnable script.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "raw_sales.csv"
TRANSFORM_SQL = BASE_DIR / "transform.sql"
DB_FILE = BASE_DIR / "data" / "warehouse.duckdb"


def load_pipeline() -> None:
    """Execute the full load pipeline: CSV → DuckDB transforms → persist."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Raw data not found at {DATA_FILE}. Run extract.py first."
        )

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_FILE))

    # Read CSV into a DuckDB table
    logger.info("Reading raw CSV from %s", DATA_FILE)
    con.execute(f"CREATE OR REPLACE TABLE raw_sales AS SELECT * FROM read_csv_auto('{DATA_FILE}')")
    raw_count = con.execute("SELECT COUNT(*) FROM raw_sales").fetchone()[0]
    logger.info("Loaded %d raw rows into DuckDB", raw_count)

    # Execute SQL transforms
    logger.info("Running transform SQL from %s", TRANSFORM_SQL)
    sql = TRANSFORM_SQL.read_text()
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            con.execute(stmt)

    # Report results
    staged_count = con.execute("SELECT COUNT(*) FROM staged_sales").fetchone()[0]
    logger.info("Staged %d rows after transform", staged_count)

    summary = con.execute("SELECT * FROM sales_summary").fetchdf()
    logger.info("Sales summary:\n%s", summary.to_string(index=False))

    con.close()
    logger.info("Pipeline complete — database persisted to %s", DB_FILE)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_pipeline()
