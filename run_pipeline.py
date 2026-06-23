"""
End-to-end pipeline runner for the medallion architecture demo (Snowflake).

Steps:
    1. Seed both upstream CRM SQLite databases.
    2. Ingest raw data from SQLite → Snowflake DE_AGENT schema.
    3. Run dbt to build curated models (staging views + intermediate Dynamic Tables).
    4. Print summary of intermediate tables (queried via the Snowflake connector).

This is the Snowflake reference implementation. Credentials are read from
environment variables sourced from `.env.snowflake` — see
`docs/reference-snowflake.md`.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_project"
DBT_PROFILES_DIR = DBT_PROJECT_DIR / "local"

INTERMEDIATE_SCHEMA = "DE_AGENT_INT"


def step_seed_sources() -> None:
    """Step 1: Seed both CRM SQLite databases."""
    logger.info("=" * 60)
    logger.info("STEP 1: Seeding upstream CRM databases")
    logger.info("=" * 60)

    from sources.crm_acme.seed_acme import seed as seed_acme
    from sources.crm_globe.seed_globe import seed as seed_globe

    seed_acme()
    seed_globe()


def step_ingest_raw() -> None:
    """Step 2: Load raw data from SQLite into Snowflake."""
    logger.info("=" * 60)
    logger.info("STEP 2: Ingesting raw layer into Snowflake (DE_AGENT schema)")
    logger.info("=" * 60)

    from ingestion.load_raw import load_to_raw

    load_to_raw()


def step_dbt_deps() -> None:
    """Install dbt package dependencies."""
    logger.info("=" * 60)
    logger.info("STEP 3a: Installing dbt dependencies")
    logger.info("=" * 60)

    result = subprocess.run(
        ["dbt", "deps", "--profiles-dir", str(DBT_PROFILES_DIR)],
        cwd=str(DBT_PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError("dbt deps failed")


def step_dbt_run() -> None:
    """Step 3: Run dbt to build curated models."""
    logger.info("=" * 60)
    logger.info("STEP 3b: Running dbt build (models + tests)")
    logger.info("=" * 60)

    result = subprocess.run(
        ["dbt", "build", "--profiles-dir", str(DBT_PROFILES_DIR)],
        cwd=str(DBT_PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError("dbt build failed")


def step_print_summary() -> None:
    """Step 4: Print a summary of intermediate tables from Snowflake."""
    logger.info("=" * 60)
    logger.info("STEP 4: Intermediate layer summary")
    logger.info("=" * 60)

    from ingestion.load_raw import get_snowflake_connection

    con = get_snowflake_connection()
    try:
        for table in ["unified_customers", "unified_products"]:
            fq_table = f"{INTERMEDIATE_SCHEMA}.{table}"
            try:
                cur = con.cursor()
                count = cur.execute(f"SELECT COUNT(*) FROM {fq_table}").fetchone()[0]
                logger.info("  %s: %d rows", table, count)

                sample = cur.execute(f"SELECT * FROM {fq_table} LIMIT 5").fetch_pandas_all()
                print(f"\n--- {table} (first 5 rows) ---")
                print(sample.to_string(index=False))
            except Exception as exc:  # noqa: BLE001
                logger.warning("  Could not read %s: %s", fq_table, exc)
    finally:
        con.close()


def main() -> None:
    """Run the full pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    step_seed_sources()
    step_ingest_raw()
    step_dbt_deps()
    step_dbt_run()
    step_print_summary()

    logger.info("Pipeline complete!")


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_ROOT))
    main()
