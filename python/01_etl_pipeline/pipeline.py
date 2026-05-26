"""
ETL Pipeline — Extract, Transform, Load

A production-style ETL pipeline that reads from a CSV source, applies
transformations, validates data, and loads into a DuckDB analytical database.
Designed to be idempotent and observable.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract_csv(file_path: str | Path, **read_kwargs: Any) -> pd.DataFrame:
    """Read a CSV file into a DataFrame.

    Args:
        file_path: Path to the source CSV file.
        **read_kwargs: Additional keyword arguments forwarded to ``pd.read_csv``.

    Returns:
        Raw DataFrame as read from disk.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    start = time.perf_counter()
    df = pd.read_csv(path, **read_kwargs)
    elapsed = time.perf_counter() - start

    logger.info("Extract complete — %d rows, %d cols in %.2fs", len(df), len(df.columns), elapsed)
    return df


# ---------------------------------------------------------------------------
# Validate (between Extract and Transform)
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when extracted data fails pre-transform validation."""


def validate_extracted(df: pd.DataFrame, required_columns: list[str]) -> None:
    """Run basic validation on the extracted DataFrame.

    Args:
        df: The extracted DataFrame to validate.
        required_columns: Column names that must be present and non-empty.

    Raises:
        ValidationError: If any check fails.
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValidationError(f"Missing required columns: {missing}")

    if df.empty:
        raise ValidationError("Extracted DataFrame is empty")

    for col in required_columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            logger.warning("Column '%s' has %d null values", col, null_count)

    logger.info("Validation passed — all %d required columns present", len(required_columns))


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Apply business transformations to raw sales data.

    Transformations:
        - Parse date columns
        - Compute net_amount and total_amount
        - Standardize string columns to lowercase/stripped
        - Drop fully-duplicate rows

    Args:
        df: Validated raw DataFrame.

    Returns:
        Transformed DataFrame ready for loading.
    """
    start = time.perf_counter()
    out = df.copy()

    # Parse dates
    out["order_date"] = pd.to_datetime(out["order_date"], errors="coerce")

    # Derived measures
    out["net_amount"] = (out["quantity"] * out["unit_price"]) - out.get("discount_amount", 0)
    out["total_amount"] = out["net_amount"] + out.get("tax_amount", 0)

    # Standardize strings
    for col in out.select_dtypes(include="object").columns:
        out[col] = out[col].str.strip().str.lower()

    # Deduplicate
    before = len(out)
    out = out.drop_duplicates()
    dupes_removed = before - len(out)
    if dupes_removed:
        logger.info("Removed %d duplicate rows", dupes_removed)

    elapsed = time.perf_counter() - start
    logger.info("Transform complete — %d rows in %.2fs", len(out), elapsed)
    return out


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_to_duckdb(
    df: pd.DataFrame,
    db_path: str | Path,
    table_name: str,
    if_exists: str = "replace",
) -> int:
    """Load a DataFrame into a DuckDB table.

    Args:
        df: Transformed DataFrame to load.
        db_path: Path to the DuckDB database file.
        table_name: Target table name.
        if_exists: How to handle an existing table — ``'replace'`` or ``'append'``.

    Returns:
        Number of rows loaded.
    """
    start = time.perf_counter()
    con = duckdb.connect(str(db_path))

    if if_exists == "replace":
        con.execute(f"DROP TABLE IF EXISTS {table_name}")

    con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    con.close()

    elapsed = time.perf_counter() - start
    logger.info("Load complete — %d rows into '%s' in %.2fs", row_count, table_name, elapsed)
    return row_count


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(
    source_path: str | Path,
    db_path: str | Path = "warehouse.duckdb",
    table_name: str = "fact_sales",
    required_columns: list[str] | None = None,
) -> int:
    """Execute the full ETL pipeline.

    Args:
        source_path: Path to the source CSV.
        db_path: Path to the target DuckDB file.
        table_name: Target table name in DuckDB.
        required_columns: Columns that must exist in the source.

    Returns:
        Number of rows loaded.
    """
    if required_columns is None:
        required_columns = ["order_id", "quantity", "unit_price"]

    logger.info("Pipeline starting — source=%s target=%s.%s", source_path, db_path, table_name)
    pipeline_start = time.perf_counter()

    # Extract
    raw = extract_csv(source_path)

    # Validate
    validate_extracted(raw, required_columns)

    # Transform
    transformed = transform_sales(raw)

    # Load
    rows_loaded = load_to_duckdb(transformed, db_path, table_name)

    elapsed = time.perf_counter() - pipeline_start
    logger.info("Pipeline finished — %d rows loaded in %.2fs", rows_loaded, elapsed)
    return rows_loaded


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_pipeline(source_path="data/raw_sales.csv")
