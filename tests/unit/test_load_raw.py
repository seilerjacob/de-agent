"""Unit tests for ingestion/load_raw.py (Snowflake reference implementation).

These tests run fully offline — no Snowflake credentials or network access.
The Snowflake connection and the pandas writer are mocked so we can assert
on the SQL/connector calls without a live account.

Tests cover:
- extract_sqlite_tables: happy path, multiple tables, exclusion of sqlite internals
- get_snowflake_connection: password vs. key-pair auth, optional role
- load_to_raw: skips missing source, RAW schema creation, full-replace (drop +
  overwrite), Snowflake uppercase naming convention, lowercase result keys
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest import mock

import pandas as pd

from ingestion import load_raw
from ingestion.load_raw import extract_sqlite_tables, get_snowflake_connection, load_to_raw


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


def _install_fake_snowflake(monkeypatch, write_rowcounts: dict[str, int] | None = None):
    """Patch the Snowflake connection + write_pandas with offline fakes.

    Returns the mock connection so tests can inspect executed SQL.
    write_pandas is patched to report a row count taken from the DataFrame
    (or an override keyed by table name) and to succeed.
    """
    executed_sql: list[str] = []

    cursor = mock.MagicMock()

    def _execute(sql, *args, **kwargs):
        executed_sql.append(sql)
        return cursor

    cursor.execute.side_effect = _execute

    conn = mock.MagicMock()
    conn.cursor.return_value = cursor
    conn.executed_sql = executed_sql

    monkeypatch.setattr(load_raw, "get_snowflake_connection", lambda: conn)

    def _fake_write_pandas(connection, df, table_name, schema, **kwargs):
        n = (write_rowcounts or {}).get(table_name, len(df))
        return True, 1, n, None

    monkeypatch.setattr(load_raw, "write_pandas", _fake_write_pandas)
    return conn


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
# get_snowflake_connection — auth selection (mock the connector)
# ---------------------------------------------------------------------------

class TestGetSnowflakeConnection:
    _BASE_ENV = {
        "SNOWFLAKE_ACCOUNT": "myorg-myacct",
        "SNOWFLAKE_USER": "svc_user",
        "SNOWFLAKE_WAREHOUSE": "WH",
        "SNOWFLAKE_DATABASE": "DB",
    }

    def test_password_auth_passes_password_not_key(self, monkeypatch) -> None:
        env = {**self._BASE_ENV, "SNOWFLAKE_PASSWORD": "secret"}
        monkeypatch.setattr(load_raw.os, "environ", env)
        connect = mock.MagicMock()
        monkeypatch.setattr(load_raw.snowflake.connector, "connect", connect)

        get_snowflake_connection()

        kwargs = connect.call_args.kwargs
        assert kwargs["password"] == "secret"
        assert "private_key_file" not in kwargs
        assert "role" not in kwargs  # not set → omitted
        assert kwargs["schema"] == "RAW"

    def test_key_pair_auth_takes_precedence(self, monkeypatch) -> None:
        env = {
            **self._BASE_ENV,
            "SNOWFLAKE_PASSWORD": "secret",
            "SNOWFLAKE_PRIVATE_KEY_PATH": "/keys/rsa.p8",
        }
        monkeypatch.setattr(load_raw.os, "environ", env)
        connect = mock.MagicMock()
        monkeypatch.setattr(load_raw.snowflake.connector, "connect", connect)

        get_snowflake_connection()

        kwargs = connect.call_args.kwargs
        assert kwargs["private_key_file"] == "/keys/rsa.p8"
        assert "password" not in kwargs

    def test_optional_role_included_when_set(self, monkeypatch) -> None:
        env = {**self._BASE_ENV, "SNOWFLAKE_PASSWORD": "secret", "SNOWFLAKE_ROLE": "TRANSFORMER"}
        monkeypatch.setattr(load_raw.os, "environ", env)
        connect = mock.MagicMock()
        monkeypatch.setattr(load_raw.snowflake.connector, "connect", connect)

        get_snowflake_connection()

        assert connect.call_args.kwargs["role"] == "TRANSFORMER"


# ---------------------------------------------------------------------------
# load_to_raw — mocked Snowflake
# ---------------------------------------------------------------------------

class TestLoadToRaw:
    def test_skips_missing_source_returns_empty(self, tmp_path: Path, monkeypatch) -> None:
        _install_fake_snowflake(monkeypatch)
        missing_db = tmp_path / "nonexistent.db"

        result = load_to_raw(sources={"ghost": missing_db})

        assert result == {}, "Expected empty dict when source DB does not exist"

    def test_creates_raw_schema_before_writes(self, tmp_path: Path, monkeypatch) -> None:
        conn = _install_fake_snowflake(monkeypatch)
        db = tmp_path / "source.db"
        _make_sqlite(db, {"items": [{"sku": "A1"}]})

        load_to_raw(sources={"mycrm": db})

        assert any("CREATE SCHEMA IF NOT EXISTS RAW" in s for s in conn.executed_sql)

    def test_full_replace_drops_table_first(self, tmp_path: Path, monkeypatch) -> None:
        conn = _install_fake_snowflake(monkeypatch)
        db = tmp_path / "source.db"
        _make_sqlite(db, {"items": [{"sku": "A1"}]})

        load_to_raw(sources={"mycrm": db})

        assert any(
            "DROP TABLE IF EXISTS RAW.RAW_MYCRM__ITEMS" in s for s in conn.executed_sql
        ), "Each table must be dropped before reload (full replace)"

    def test_result_key_lowercase_for_caller_stability(self, tmp_path: Path, monkeypatch) -> None:
        _install_fake_snowflake(monkeypatch, write_rowcounts={"RAW_MYCRM__ITEMS": 3})
        db = tmp_path / "source.db"
        _make_sqlite(db, {
            "items": [{"sku": "A1"}, {"sku": "B2"}, {"sku": "C3"}],
        })

        result = load_to_raw(sources={"mycrm": db})

        assert result == {"raw.raw_mycrm__items": 3}

    def test_uppercase_naming_convention(self, tmp_path: Path, monkeypatch) -> None:
        captured: list[str] = []
        conn = mock.MagicMock()
        conn.cursor.return_value = mock.MagicMock()
        monkeypatch.setattr(load_raw, "get_snowflake_connection", lambda: conn)

        def _fake_write_pandas(connection, df, table_name, schema, **kwargs):
            captured.append(f"{schema}.{table_name}")
            return True, 1, len(df), None

        monkeypatch.setattr(load_raw, "write_pandas", _fake_write_pandas)

        db = tmp_path / "source.db"
        _make_sqlite(db, {
            "contacts": [{"id": "1"}],
            "orders": [{"id": "99"}],
        })

        load_to_raw(sources={"acme": db})

        assert "RAW.RAW_ACME__CONTACTS" in captured
        assert "RAW.RAW_ACME__ORDERS" in captured

    def test_row_count_matches_source(self, tmp_path: Path, monkeypatch) -> None:
        _install_fake_snowflake(monkeypatch)
        db = tmp_path / "source.db"
        rows = [{"val": str(i)} for i in range(50)]
        _make_sqlite(db, {"big_table": rows})

        result = load_to_raw(sources={"demo": db})

        assert result["raw.raw_demo__big_table"] == 50

    def test_connection_closed_on_completion(self, tmp_path: Path, monkeypatch) -> None:
        conn = _install_fake_snowflake(monkeypatch)
        db = tmp_path / "source.db"
        _make_sqlite(db, {"items": [{"sku": "A1"}]})

        load_to_raw(sources={"mycrm": db})

        conn.close.assert_called_once()
