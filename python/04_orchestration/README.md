# Python Skill: Orchestration

Demonstrates Apache Airflow Directed Acyclic Graph (DAG) patterns commonly
used to schedule and monitor Data Engineering (DE) pipelines.

## What This Covers
- **TaskFlow API** using ``@task`` decorators
- Sensible default arguments (retries, catchup, etc.)
- Parameterized connections and table names
- Error callbacks for alerting
- DAG documentation via ``doc_md``

## File
- `dag_example.py` — A reference Airflow DAG for an ETL workflow

> **Note**: This file is a reference implementation. It requires an Airflow
> environment to run but demonstrates the patterns Claude should follow when
> generating DAGs.
