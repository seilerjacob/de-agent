# Example: End-to-End Pipeline

A complete worked example that ties together Python extraction, SQL-based
transformation logic, and Python loading — demonstrating how the SQL and
Python skills combine in a real Data Engineering (DE) workflow.

## Workflow
1. **`extract.py`** — Generates sample sales data and writes it to CSV.
2. **`transform.sql`** — SQL transformations to run against the extracted data (via DuckDB).
3. **`load.py`** — Reads the transformed results and loads them into a DuckDB warehouse.

## Running

```bash
# From the project root (with virtualenv activated):
python examples/end_to_end_pipeline/extract.py
python examples/end_to_end_pipeline/load.py
```
