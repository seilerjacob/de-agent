"""
Airflow DAG Example — Sales ETL Pipeline

A reference Directed Acyclic Graph (DAG) demonstrating best practices for
Data Engineering (DE) pipeline orchestration with Apache Airflow.

NOTE: This file requires an Airflow environment to execute. It serves as a
template and skill demonstration.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DAG_DOC = """
### Sales ETL Pipeline

**Owner**: Data Engineering  
**Schedule**: Daily at 06:00 UTC  
**Source**: Raw sales CSV landing zone  
**Target**: DuckDB analytical warehouse (`fact_sales`)

#### Workflow
1. **extract** — Read new files from the landing zone.
2. **validate** — Run data quality checks on raw data.
3. **transform** — Apply business logic and compute derived columns.
4. **load** — Upsert into the target table.
5. **notify** — Send completion notification.
"""

DEFAULT_ARGS: dict[str, Any] = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
    "email_on_failure": True,
    "email": [Variable.get("alert_email", default_var="de-team@example.com")],
}


def _on_failure_callback(context: dict[str, Any]) -> None:
    """Send an alert when a task fails.

    In production, this would post to Slack, PagerDuty, etc.
    """
    task_instance = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    print(f"ALERT: Task {task_instance} in DAG {dag_id} failed.")


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

@dag(
    dag_id="sales_etl_pipeline",
    default_args=DEFAULT_ARGS,
    description="Daily ETL pipeline: raw sales → DuckDB fact_sales",
    doc_md=DAG_DOC,
    schedule="0 6 * * *",  # Daily at 06:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["etl", "sales", "data-engineering"],
    on_failure_callback=_on_failure_callback,
)
def sales_etl_pipeline() -> None:
    """Daily Sales ETL Pipeline."""

    @task()
    def extract() -> dict[str, Any]:
        """Extract raw sales data from the landing zone."""
        source_path = Variable.get("sales_source_path", default_var="/data/landing/sales/")
        # In production: list new files, read them, return metadata
        return {"source_path": source_path, "row_count": 15000}

    @task()
    def validate(extract_result: dict[str, Any]) -> dict[str, Any]:
        """Run data quality checks on extracted data."""
        row_count = extract_result["row_count"]
        if row_count == 0:
            raise ValueError("No rows extracted — aborting pipeline")
        return {**extract_result, "validation": "passed"}

    @task()
    def transform(validated: dict[str, Any]) -> dict[str, Any]:
        """Apply business transformations."""
        # In production: pandas/polars transforms, derived columns, dedup
        return {**validated, "transformed_rows": validated["row_count"]}

    @task()
    def load(transformed: dict[str, Any]) -> int:
        """Load transformed data into the target table."""
        target_table = Variable.get("sales_target_table", default_var="fact_sales")
        rows = transformed["transformed_rows"]
        # In production: duckdb / SQLAlchemy insert
        print(f"Loaded {rows} rows into {target_table}")
        return rows

    @task(trigger_rule=TriggerRule.ALL_DONE)
    def notify(rows_loaded: int) -> None:
        """Send a completion notification."""
        print(f"Pipeline complete — {rows_loaded} rows loaded")

    # Wire up the DAG
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end", trigger_rule=TriggerRule.ALL_DONE)

    extracted = extract()
    validated = validate(extracted)
    transformed = transform(validated)
    loaded = load(transformed)
    notified = notify(loaded)

    start >> extracted  # type: ignore[override]
    notified >> end     # type: ignore[override]


# Instantiate the DAG
sales_etl_pipeline()
