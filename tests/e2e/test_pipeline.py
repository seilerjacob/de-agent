"""Critical path end-to-end test for the medallion pipeline (Snowflake).

Runs the full pipeline: seed → ingest → dbt build, then validates the
curated intermediate Dynamic Tables for expected row counts and column
presence — all against a live Snowflake account.

This test requires Snowflake credentials. It is skipped gracefully when
`.env.snowflake` is absent (e.g. local dev without an account, or CI without
secrets configured) so the offline test suite stays green. When the file is
present its variables are loaded into the environment before the run.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_project"
ENV_FILE = PROJECT_ROOT / ".env.snowflake"
# Use the dbt from the same venv as pytest to avoid picking up system dbt.
DBT_CMD = str(Path(sys.executable).parent / "dbt")
INTERMEDIATE_SCHEMA = "INTERMEDIATE"

REQUIRED_ENV = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE"]


def _load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines from an env file into os.environ (no overwrite)."""
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


# Load .env.snowflake (if present) before computing the skip condition so a
# developer with the file checked in locally runs the test automatically.
if ENV_FILE.exists():
    _load_env_file(ENV_FILE)

_creds_present = all(os.environ.get(k) for k in REQUIRED_ENV)


@pytest.mark.skipif(
    not _creds_present,
    reason=(
        "Snowflake credentials not available — set up .env.snowflake "
        "(see .env.snowflake.example / docs/reference-snowflake.md) to run "
        "the Snowflake critical-path test."
    ),
)
def test_full_pipeline_critical_path() -> None:
    """Seed both CRMs, ingest to RAW, run dbt build, assert curated shape."""

    # Step 1: Seed both source CRM databases
    from sources.crm_acme.seed_acme import seed as seed_acme
    from sources.crm_globe.seed_globe import seed as seed_globe

    seed_acme()
    seed_globe()

    # Step 2: Load raw layer into Snowflake
    from ingestion.load_raw import get_snowflake_connection, load_to_raw

    loaded = load_to_raw()
    assert len(loaded) == 4, (
        f"Expected 4 raw tables, got {len(loaded)}: {list(loaded.keys())}"
    )

    # Step 3: Run dbt build
    result = subprocess.run(
        [DBT_CMD, "build", "--profiles-dir", str(DBT_PROJECT_DIR)],
        cwd=str(DBT_PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"dbt build failed (returncode={result.returncode}).\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Step 4: Validate curated Dynamic Tables via the Snowflake connector
    con = get_snowflake_connection()
    try:
        cur = con.cursor()

        # --- int_unified_customers ---
        customer_count = cur.execute(
            f"SELECT COUNT(*) FROM {INTERMEDIATE_SCHEMA}.int_unified_customers"
        ).fetchone()[0]
        assert customer_count == 22, (
            f"Expected 22 rows in int_unified_customers, got {customer_count}"
        )

        customer_cols = {
            row[0].upper()
            for row in cur.execute(
                f"DESCRIBE TABLE {INTERMEDIATE_SCHEMA}.int_unified_customers"
            ).fetchall()
        }
        expected_customer_cols = {
            "CUSTOMER_SK",
            "SOURCE_SYSTEM",
            "SOURCE_CUSTOMER_ID",
            "FULL_NAME",
            "EMAIL",
            "STATUS",
        }
        missing_customer_cols = expected_customer_cols - customer_cols
        assert not missing_customer_cols, (
            f"int_unified_customers is missing columns: {missing_customer_cols}"
        )

        # --- int_unified_products ---
        product_count = cur.execute(
            f"SELECT COUNT(*) FROM {INTERMEDIATE_SCHEMA}.int_unified_products"
        ).fetchone()[0]
        assert product_count == 21, (
            f"Expected 21 rows in int_unified_products, got {product_count}"
        )

        product_cols = {
            row[0].upper()
            for row in cur.execute(
                f"DESCRIBE TABLE {INTERMEDIATE_SCHEMA}.int_unified_products"
            ).fetchall()
        }
        expected_product_cols = {
            "PRODUCT_SK",
            "SOURCE_SYSTEM",
            "SOURCE_PRODUCT_ID",
            "PRODUCT_NAME",
            "RETAIL_PRICE",
            "IS_AVAILABLE",
        }
        missing_product_cols = expected_product_cols - product_cols
        assert not missing_product_cols, (
            f"int_unified_products is missing columns: {missing_product_cols}"
        )
    finally:
        con.close()
