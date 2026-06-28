from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import BASE_DATE
from .synthetic_data import REQUIRED_COLUMNS


CRITICAL_FORECAST_FIELDS = [
    "customer_receipts",
    "supplier_payments",
    "payroll",
    "debt_service",
    "capex",
    "fx_payments",
    "ar_due",
    "ap_due",
]


@dataclass(frozen=True)
class DataQualityResult:
    completeness_score: float
    freshness_score: float
    missing_fields: list[str]
    stale_days: int
    consistency_issues: list[str]
    critical_missing: bool
    usable: bool


def validate_data(df: pd.DataFrame) -> DataQualityResult:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        return DataQualityResult(
            completeness_score=0.0,
            freshness_score=0.0,
            missing_fields=missing_columns,
            stale_days=999,
            consistency_issues=["Required columns are absent."],
            critical_missing=True,
            usable=False,
        )

    future = df[df["date"] >= BASE_DATE]
    critical_missing = bool(future[CRITICAL_FORECAST_FIELDS].isna().any().any())
    missing_fields = [
        col for col in CRITICAL_FORECAST_FIELDS if future[col].isna().any()
    ]
    missing_cells = int(future[CRITICAL_FORECAST_FIELDS].isna().sum().sum())
    total_cells = max(1, int(future[CRITICAL_FORECAST_FIELDS].size))
    completeness_score = round(max(0.0, 100.0 * (1 - missing_cells / total_cells)), 1)

    latest_update = pd.to_datetime(df["data_updated_at"]).max()
    stale_days = int((BASE_DATE - latest_update).days)
    freshness_score = round(max(0.0, 100.0 - stale_days * 18.0), 1)

    consistency_issues = []
    calculable = df.dropna(subset=CRITICAL_FORECAST_FIELDS + ["opening_cash", "closing_cash"])
    expected = (
        calculable["opening_cash"]
        + calculable["customer_receipts"]
        + calculable["other_inflows"]
        - calculable["supplier_payments"]
        - calculable["payroll"]
        - calculable["operating_expenses"]
        - calculable["debt_service"]
        - calculable["capex"]
        - calculable["fx_payments"]
    )
    mismatches = (expected - calculable["closing_cash"]).abs() > 0.08
    if bool(mismatches.any()):
        consistency_issues.append(
            f"{int(mismatches.sum())} rows do not reconcile opening cash to closing cash."
        )

    stale_is_critical = stale_days > 7
    usable = not critical_missing and not stale_is_critical and not consistency_issues
    if stale_is_critical:
        consistency_issues.append("Data timestamp is older than the 7-day freshness limit.")

    return DataQualityResult(
        completeness_score=completeness_score,
        freshness_score=freshness_score,
        missing_fields=missing_fields,
        stale_days=stale_days,
        consistency_issues=consistency_issues,
        critical_missing=critical_missing or stale_is_critical,
        usable=usable,
    )
