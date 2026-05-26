# Python Skill: ETL Pipeline

Demonstrates a clean, idempotent Extract-Transform-Load (ETL) pipeline with logging
and validation between stages.

## What This Covers
- **Extract** from CSV (extensible to API/database sources)
- **Transform** with pandas — cleaning, type casting, derived columns
- **Load** into DuckDB (local analytical database)
- Logging with row counts at each stage
- Basic data validation between extract and transform

## File
- `pipeline.py` — Complete ETL pipeline implementation
