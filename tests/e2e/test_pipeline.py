"""Critical path end-to-end test for the medallion pipeline.

Runs the full pipeline: seed → ingest → dbt build, then validates the
curated intermediate tables for expected row counts and column presence.

The dbt profile writes to ../warehouse/lakehouse.duckdb relative to
dbt_project/, so this test uses the real project warehouse path and does
not attempt to redirect it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_project"
# Use the dbt from the same venv as pytest to avoid picking up system dbt
DBT_CMD = str(Path(sys.executable).parent / "dbt")
WAREHOUSE_PATH = PROJECT_ROOT / "warehouse" / "lakehouse.duckdb"


def test_full_pipeline_critical_path() -> None:
    """Seed both CRMs, ingest to raw, run dbt build, assert curated shape."""

    # Step 1: Seed both source CRM databases
    from sources.crm_acme.seed_acme import seed as seed_acme
    from sources.crm_globe.seed_globe import seed as seed_globe

    seed_acme()
    seed_globe()

    # Step 2: Load raw layer (uses module defaults — real warehouse path)
    from ingestion.load_raw import load_to_raw

    loaded = load_to_raw()
    assert len(loaded) == 4, (
        f"Expected 4 raw tables, got {len(loaded)}: {list(loaded.keys())}"
    )

    # Step 3: Run dbt build
    result = subprocess.run(
        [
            DBT_CMD,
            "build",
            "--profiles-dir",
            str(DBT_PROJECT_DIR),
        ],
        cwd=str(DBT_PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"dbt build failed (returncode={result.returncode}).\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Step 4: Validate curated tables
    con = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)
    try:
        # --- unified_customers ---
        customer_count = con.execute(
            "SELECT COUNT(*) FROM intermediate.unified_customers"
        ).fetchone()[0]
        assert customer_count == 22, (
            f"Expected 22 rows in unified_customers, got {customer_count}"
        )

        customer_cols = {
            row[0]
            for row in con.execute(
                "DESCRIBE intermediate.unified_customers"
            ).fetchall()
        }
        expected_customer_cols = {
            "customer_sk",
            "source_system",
            "source_customer_id",
            "full_name",
            "email",
            "status",
        }
        missing_customer_cols = expected_customer_cols - customer_cols
        assert not missing_customer_cols, (
            f"unified_customers is missing columns: {missing_customer_cols}"
        )

        # --- unified_products ---
        product_count = con.execute(
            "SELECT COUNT(*) FROM intermediate.unified_products"
        ).fetchone()[0]
        assert product_count == 21, (
            f"Expected 21 rows in unified_products, got {product_count}"
        )

        product_cols = {
            row[0]
            for row in con.execute(
                "DESCRIBE intermediate.unified_products"
            ).fetchall()
        }
        expected_product_cols = {
            "product_sk",
            "source_system",
            "source_product_id",
            "product_name",
            "retail_price",
            "is_available",
        }
        missing_product_cols = expected_product_cols - product_cols
        assert not missing_product_cols, (
            f"unified_products is missing columns: {missing_product_cols}"
        )
    finally:
        con.close()
