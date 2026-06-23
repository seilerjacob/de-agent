"""Unit tests for sources/transactions/seed_transactions.py.

The non-trivial logic in the transactions seed is surrogate-key alignment:
the customer_id / product_id values must equal the keys dbt's
generate_surrogate_key macro will produce for the existing CRM seed rows.
These tests reproduce the macro independently and assert alignment, plus
verify the seed structure (row counts, multi-line-item headers, value
domains) without touching Snowflake.

Runs fully offline against a tmp SQLite database.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from sources.transactions import seed_transactions


def _macro_surrogate_key(*fields: str) -> str:
    """Independent reimplementation of dbt's generate_surrogate_key macro.

    md5(coalesce(cast(f as varchar), '') || '-' || ...) over the field list.
    Used to prove the seed's keys match what dbt will generate downstream.
    """
    joined = "-".join(f if f is not None else "" for f in fields)
    return hashlib.md5(joined.encode()).hexdigest()


@pytest.fixture()
def seeded_db(tmp_path: Path, monkeypatch) -> Path:
    """Run the seed against a tmp DB path and return it."""
    db_path = tmp_path / "transactions.db"
    monkeypatch.setattr(seed_transactions, "DB_PATH", db_path)
    return seed_transactions.seed()


class TestSurrogateKeyAlignment:
    def test_helper_matches_macro_for_known_inputs(self) -> None:
        # Acme/Globe customers 1 & 2 and products 1 & 2 — the rows the seed
        # references. The helper must equal the macro's md5 output.
        for system in ("acme", "globe"):
            for source_id in ("1", "2"):
                assert seed_transactions.surrogate_key(system, source_id) == (
                    _macro_surrogate_key(system, source_id)
                )

    def test_constants_use_expected_source_rows(self) -> None:
        assert seed_transactions.CUST_ACME_1 == _macro_surrogate_key("acme", "1")
        assert seed_transactions.CUST_GLOBE_2 == _macro_surrogate_key("globe", "2")
        assert seed_transactions.PROD_ACME_2 == _macro_surrogate_key("acme", "2")
        assert seed_transactions.PROD_GLOBE_1 == _macro_surrogate_key("globe", "1")

    def test_seed_fks_are_all_valid_surrogate_keys(self, seeded_db: Path) -> None:
        valid_customer_sks = {
            seed_transactions.surrogate_key(s, i)
            for s in ("acme", "globe")
            for i in ("1", "2")
        }
        valid_product_sks = valid_customer_sks  # same input domain

        con = sqlite3.connect(str(seeded_db))
        try:
            sale_custs = {r[0] for r in con.execute("SELECT customer_id FROM sales")}
            sale_prods = {r[0] for r in con.execute("SELECT product_id FROM sales")}
            quote_custs = {r[0] for r in con.execute("SELECT customer_id FROM quotes")}
            quote_prods = {r[0] for r in con.execute("SELECT product_id FROM quotes")}
        finally:
            con.close()

        assert sale_custs | quote_custs <= valid_customer_sks
        assert sale_prods | quote_prods <= valid_product_sks
        # At least 4 distinct customers (2 Acme, 2 Globe) exercised.
        assert len(sale_custs | quote_custs) >= 4
        # At least 4 distinct products exercised.
        assert len(sale_prods | quote_prods) >= 4


class TestSeedStructure:
    def test_row_counts_meet_minimums(self, seeded_db: Path) -> None:
        con = sqlite3.connect(str(seeded_db))
        try:
            sales = con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            quotes = con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        finally:
            con.close()
        assert sales >= 10
        assert quotes >= 10

    def test_multiple_line_items_per_header(self, seeded_db: Path) -> None:
        con = sqlite3.connect(str(seeded_db))
        try:
            multi_sales = con.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT sale_id FROM sales GROUP BY sale_id HAVING COUNT(*) > 1)"
            ).fetchone()[0]
            multi_quotes = con.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT quote_id FROM quotes GROUP BY quote_id HAVING COUNT(*) > 1)"
            ).fetchone()[0]
        finally:
            con.close()
        assert multi_sales >= 2, "At least two sale_ids must have multiple line items"
        assert multi_quotes >= 2, "At least two quote_ids must have multiple line items"

    def test_pk_uniqueness(self, seeded_db: Path) -> None:
        con = sqlite3.connect(str(seeded_db))
        try:
            sale_lines = con.execute("SELECT COUNT(DISTINCT sale_line_id) FROM sales").fetchone()[0]
            total_sales = con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            quote_lines = con.execute(
                "SELECT COUNT(DISTINCT quote_line_id) FROM quotes"
            ).fetchone()[0]
            total_quotes = con.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        finally:
            con.close()
        assert sale_lines == total_sales
        assert quote_lines == total_quotes

    def test_value_domains(self, seeded_db: Path) -> None:
        con = sqlite3.connect(str(seeded_db))
        try:
            stages = {r[0] for r in con.execute("SELECT DISTINCT stage FROM sales")}
            statuses = {r[0] for r in con.execute("SELECT DISTINCT status FROM quotes")}
        finally:
            con.close()
        assert stages <= {"closed_won", "closed_lost", "pending"}
        assert statuses <= {"draft", "sent", "accepted", "expired"}
        # Variety: more than one distinct value in each.
        assert len(stages) >= 2
        assert len(statuses) >= 2
