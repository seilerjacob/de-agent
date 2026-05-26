"""
Data Transforms — pandas and polars patterns.

Shows common DE transformation patterns implemented in both pandas and polars,
highlighting idiomatic usage and performance considerations.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)


# ===========================================================================
# Pandas transforms
# ===========================================================================

def pd_clean_strings(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Strip whitespace and lowercase string columns.

    Args:
        df: Input DataFrame.
        columns: String columns to clean.

    Returns:
        DataFrame with cleaned string columns.
    """
    out = df.copy()
    for col in columns:
        out[col] = out[col].str.strip().str.lower()
    return out


def pd_add_fiscal_year(
    df: pd.DataFrame,
    date_col: str = "order_date",
    fiscal_start_month: int = 7,
) -> pd.DataFrame:
    """Derive a fiscal year column from a date column.

    Args:
        df: Input DataFrame with a date column.
        date_col: Name of the date column.
        fiscal_start_month: Month the fiscal year begins (default July = 7).

    Returns:
        DataFrame with a new ``fiscal_year`` column.
    """
    out = df.copy()
    dates = pd.to_datetime(out[date_col])
    out["fiscal_year"] = dates.apply(
        lambda d: d.year + 1 if d.month >= fiscal_start_month else d.year
    )
    return out


def pd_pivot_monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot sales data into a month-by-category matrix.

    Expects columns: ``order_date``, ``category``, ``net_amount``.

    Args:
        df: Sales DataFrame.

    Returns:
        Pivoted DataFrame with months as rows and categories as columns.
    """
    out = df.copy()
    out["month"] = pd.to_datetime(out["order_date"]).dt.to_period("M")
    return out.pivot_table(
        index="month",
        columns="category",
        values="net_amount",
        aggfunc="sum",
        fill_value=0,
    )


# ===========================================================================
# Polars transforms
# ===========================================================================

def pl_clean_strings(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Strip whitespace and lowercase string columns using polars expressions.

    Args:
        df: Input polars DataFrame.
        columns: String columns to clean.

    Returns:
        DataFrame with cleaned string columns.
    """
    return df.with_columns([
        pl.col(col).str.strip_chars().str.to_lowercase().alias(col)
        for col in columns
    ])


def pl_add_fiscal_year(
    df: pl.DataFrame,
    date_col: str = "order_date",
    fiscal_start_month: int = 7,
) -> pl.DataFrame:
    """Derive a fiscal year column using polars expressions.

    Args:
        df: Input polars DataFrame.
        date_col: Name of the date column.
        fiscal_start_month: Month the fiscal year begins.

    Returns:
        DataFrame with a new ``fiscal_year`` column.
    """
    return df.with_columns(
        pl.when(pl.col(date_col).dt.month() >= fiscal_start_month)
        .then(pl.col(date_col).dt.year() + 1)
        .otherwise(pl.col(date_col).dt.year())
        .alias("fiscal_year")
    )


def pl_aggregate_sales(
    df: pl.DataFrame,
    group_cols: list[str],
    amount_col: str = "net_amount",
) -> pl.DataFrame:
    """Aggregate sales using polars lazy evaluation for performance.

    Args:
        df: Input polars DataFrame.
        group_cols: Columns to group by.
        amount_col: Numeric column to aggregate.

    Returns:
        Aggregated DataFrame with total, mean, and count.
    """
    return (
        df.lazy()
        .group_by(group_cols)
        .agg([
            pl.col(amount_col).sum().alias("total_amount"),
            pl.col(amount_col).mean().alias("avg_amount"),
            pl.col(amount_col).count().alias("transaction_count"),
        ])
        .sort("total_amount", descending=True)
        .collect()
    )
