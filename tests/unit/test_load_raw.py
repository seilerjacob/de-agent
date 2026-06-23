"""Unit tests for ingestion/load_raw.py.

Tests cover:
- extract_sqlite_tables: happy path, multiple tables, exclusion of sqlite internals
- load_to_raw: skips missing source, loads tables into DuckDB, naming convention
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from ingestion.load_raw import extract_sqlite_tables, load_to_raw


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sqlite(db_path: Path, tables: dict[str, list[dict]]) -> None:
    """Create a SQLite database with the given tables and rows."""
    con = sqlite3.connect(str(db_path))
    for table_name, rows in tables.items():
        if not rows:
            con.execute(f"CREATE TABLE {table_name} (id INTEGER)")
        else:
            cols = list(rows[0].keys())
            col_defs = ", ".join(f"{c} TEXT" for c in cols)
            con.execute(f"CREATE TABLE {table_name} ({col_defs})")
            placeholders = ", ".join("?" for _ in cols)
            for row in rows:
                con.execute(
                    f"INSERT INTO {table_name} VALUES ({placeholders})",
                    [row[c] for c in cols],
                )
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# extract_sqlite_tables — happy path
# ---------------------------------------------------------------------------

class TestExtractSqliteTables:
    def test_single_table_columns_and_row_count(self, tmp_path: Path) -> None:
        db = tmp_path / "test.db"
        _make_sqlite(db, {
            "contacts": [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]
        })

        result = extract_sqlite_tables(db)

        assert "contacts" in result
        df = result["contacts"]
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["name", "email"]

    def test_multiple_tables_both_extracted(self, tmp_path: Path) -> None:
        db = tmp_path / "multi.db"
        _make_sqlite(db, {
            "orders": [{"order_id": "1", "amount": "99.99"}],
            "products": [
                {"product_id": "10", "name": "Widget"},
                {"product_id": "11", "name": "Gadget"},
            ],
        })

        result = extract_sqlite_tables(db)

        assert set(result.keys()) == {"orders", "products"}
        assert len(result["orders"]) == 1
        assert len(result["products"]) == 2

    def test_excludes_sqlite_internal_tables(self, tmp_path: Path) -> None:
        db = tmp_path / "internal.db"
        _make_sqlite(db, {"users": [{"id": "1", "name": "Test"}]})

        result = extract_sqlite_tables(db)

        for key in result:
            assert not key.startswith("sqlite_"), (
                f"Internal SQLite table '{key}' should be excluded"
            )

    def test_empty_table_still_returned(self, tmp_path: Path) -> None:
        db = tmp_path / "empty.db"
        con = sqlite3.connect(str(db))
        con.execute("CREATE TABLE things (id INTEGER, label TEXT)")
        con.commit()
        con.close()

        result = extract_sqlite_tables(db)

        assert "things" in result
        assert len(result["things"]) == 0


# ---------------------------------------------------------------------------
# load_to_raw
# ---------------------------------------------------------------------------

class TestLoadToRaw:
    def test_skips_missing_source_returns_empty(self, tmp_path: Path) -> None:
        warehouse = tmp_path / "warehouse" / "test.duckdb"
        missing_db = tmp_path / "nonexistent.db"

        result = load_to_raw(
            warehouse_path=warehouse,
            sources={"ghost": missing_db},
        )

        assert result == {}, "Expected empty dict when source DB does not exist"

    def test_loads_tables_into_duckdb(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        _make_sqlite(db, {
            "items": [
                {"sku": "A1", "qty": "10"},
                {"sku": "B2", "qty": "5"},
                {"sku": "C3", "qty": "7"},
            ]
        })
        warehouse = tmp_path / "warehouse" / "test.duckdb"

        result = load_to_raw(
            warehouse_path=warehouse,
            sources={"mycrm": db},
        )

        expected_key = "raw.mycrm__items"
        assert expected_key in result
        assert result[expected_key] == 3

    def test_naming_convention_pattern(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        _make_sqlite(db, {
            "contacts": [{"id": "1", "name": "Alice"}],
            "orders": [{"id": "99", "total": "100"}],
        })
        warehouse = tmp_path / "warehouse" / "test.duckdb"

        result = load_to_raw(
            warehouse_path=warehouse,
            sources={"acme": db},
        )

        for key in result:
            assert key.startswith("raw.acme__"), (
                f"Key '{key}' does not follow 'raw.acme__<table>' pattern"
            )
        assert "raw.acme__contacts" in result
        assert "raw.acme__orders" in result

    def test_warehouse_directory_created_automatically(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        _make_sqlite(db, {"t": [{"x": "1"}]})
        warehouse = tmp_path / "deep" / "nested" / "dir" / "wh.duckdb"

        load_to_raw(warehouse_path=warehouse, sources={"src": db})

        assert warehouse.exists(), "DuckDB file should be created automatically"

    def test_row_count_matches_source(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        rows = [{"val": str(i)} for i in range(50)]
        _make_sqlite(db, {"big_table": rows})
        warehouse = tmp_path / "wh.duckdb"

        result = load_to_raw(
            warehouse_path=warehouse,
            sources={"demo": db},
        )

        assert result["raw.demo__big_table"] == 50
