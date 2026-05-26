"""
Data Quality Check Framework

A lightweight, pipeline-embeddable data quality validation framework.
Each check returns a structured result; the runner aggregates them and
optionally raises on failure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of a single data quality check."""

    name: str
    passed: bool
    failing_rows: int = 0
    details: str = ""


@dataclass
class QualityReport:
    """Aggregated report from all data quality checks."""

    results: list[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Return True if every check passed."""
        return all(r.passed for r in self.results)

    @property
    def summary(self) -> str:
        """Human-readable summary string."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        return f"{passed}/{total} checks passed"

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to a DataFrame for reporting."""
        return pd.DataFrame([
            {"check": r.name, "passed": r.passed, "failing_rows": r.failing_rows, "details": r.details}
            for r in self.results
        ])


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_not_null(df: pd.DataFrame, column: str) -> CheckResult:
    """Check that a column contains no null values.

    Args:
        df: DataFrame to check.
        column: Column name to validate.

    Returns:
        CheckResult with pass/fail and count of nulls.
    """
    null_count = int(df[column].isna().sum())
    return CheckResult(
        name=f"not_null({column})",
        passed=null_count == 0,
        failing_rows=null_count,
        details=f"{null_count} null values found" if null_count else "",
    )


def check_unique(df: pd.DataFrame, columns: list[str]) -> CheckResult:
    """Check that the given column(s) form a unique key.

    Args:
        df: DataFrame to check.
        columns: Column(s) that should be unique together.

    Returns:
        CheckResult with pass/fail and count of duplicates.
    """
    dupe_count = int(df.duplicated(subset=columns, keep=False).sum())
    key = ", ".join(columns)
    return CheckResult(
        name=f"unique({key})",
        passed=dupe_count == 0,
        failing_rows=dupe_count,
        details=f"{dupe_count} duplicate rows" if dupe_count else "",
    )


def check_range(
    df: pd.DataFrame,
    column: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> CheckResult:
    """Check that values in a numeric column fall within [min_value, max_value].

    Args:
        df: DataFrame to check.
        column: Numeric column to validate.
        min_value: Minimum acceptable value (inclusive). None = no lower bound.
        max_value: Maximum acceptable value (inclusive). None = no upper bound.

    Returns:
        CheckResult with pass/fail and count of out-of-range rows.
    """
    series = df[column].dropna()
    mask = pd.Series(True, index=series.index)
    if min_value is not None:
        mask &= series >= min_value
    if max_value is not None:
        mask &= series <= max_value
    failing = int((~mask).sum())
    bounds = f"[{min_value}, {max_value}]"
    return CheckResult(
        name=f"range({column} in {bounds})",
        passed=failing == 0,
        failing_rows=failing,
        details=f"{failing} values out of range" if failing else "",
    )


def check_referential_integrity(
    df: pd.DataFrame,
    column: str,
    reference_values: set[Any],
) -> CheckResult:
    """Check that all values in a column exist in a reference set.

    Args:
        df: DataFrame to check.
        column: Foreign key column to validate.
        reference_values: Set of valid reference values.

    Returns:
        CheckResult with pass/fail and count of orphan rows.
    """
    orphans = df[~df[column].isin(reference_values) & df[column].notna()]
    orphan_count = len(orphans)
    return CheckResult(
        name=f"referential_integrity({column})",
        passed=orphan_count == 0,
        failing_rows=orphan_count,
        details=f"{orphan_count} orphan rows" if orphan_count else "",
    )


# ---------------------------------------------------------------------------
# Quality runner
# ---------------------------------------------------------------------------

def run_quality_checks(
    df: pd.DataFrame,
    checks: list[Callable[[pd.DataFrame], CheckResult]],
    raise_on_failure: bool = False,
) -> QualityReport:
    """Execute a list of quality checks and return an aggregated report.

    Args:
        df: DataFrame to validate.
        checks: List of callables, each accepting a DataFrame and returning
            a CheckResult.
        raise_on_failure: If True, raise ``ValueError`` on the first failure.

    Returns:
        QualityReport summarizing all check results.

    Raises:
        ValueError: If *raise_on_failure* is True and any check fails.
    """
    report = QualityReport()
    for check_fn in checks:
        result = check_fn(df)
        report.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        logger.info("DQ %s: %s %s", status, result.name, result.details)
        if not result.passed and raise_on_failure:
            raise ValueError(f"Data quality check failed: {result.name} — {result.details}")

    logger.info("Quality report: %s", report.summary)
    return report
