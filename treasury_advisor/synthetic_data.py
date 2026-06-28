from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import numpy as np
import pandas as pd

from .config import BASE_DATE, DATA_DIR, SCENARIOS


REQUIRED_COLUMNS = [
    "date",
    "opening_cash",
    "customer_receipts",
    "other_inflows",
    "supplier_payments",
    "payroll",
    "operating_expenses",
    "debt_service",
    "capex",
    "fx_payments",
    "closing_cash",
    "ar_due",
    "ap_due",
    "currency_exposure",
    "data_updated_at",
    "is_actual",
]


@dataclass(frozen=True)
class ScenarioProfile:
    start_cash: float
    receipt_level: float
    supplier_level: float
    opex_level: float
    capex_day: int
    capex_amount: float
    future_receipt_multiplier: float = 1.0
    fx_multiplier: float = 1.0
    stale_days: int = 0
    missing_payroll: bool = False
    delayed_receivables: bool = False


PROFILES = {
    "healthy_surplus": ScenarioProfile(
        start_cash=1325.0,
        receipt_level=9.3,
        supplier_level=5.8,
        opex_level=2.1,
        capex_day=45,
        capex_amount=175.0,
    ),
    "liquidity_shortfall": ScenarioProfile(
        start_cash=1715.0,
        receipt_level=9.8,
        supplier_level=7.2,
        opex_level=2.3,
        capex_day=50,
        capex_amount=185.0,
        future_receipt_multiplier=0.62,
        delayed_receivables=True,
    ),
    "stale_missing_data": ScenarioProfile(
        start_cash=850.0,
        receipt_level=10.5,
        supplier_level=5.9,
        opex_level=2.1,
        capex_day=40,
        capex_amount=160.0,
        stale_days=14,
        missing_payroll=True,
    ),
    "stress_receivables_fx": ScenarioProfile(
        start_cash=740.0,
        receipt_level=10.8,
        supplier_level=6.4,
        opex_level=2.1,
        capex_day=42,
        capex_amount=185.0,
        future_receipt_multiplier=0.76,
        fx_multiplier=1.18,
        delayed_receivables=True,
    ),
}


def ensure_synthetic_data() -> dict[str, pd.DataFrame]:
    DATA_DIR.mkdir(exist_ok=True)
    datasets = {}
    for scenario in SCENARIOS:
        df = generate_synthetic_treasury_data(scenario)
        path = DATA_DIR / f"{scenario}.csv"
        tmp_path = DATA_DIR / f".{scenario}.{uuid4().hex}.tmp.csv"
        df.to_csv(tmp_path, index=False)
        tmp_path.replace(path)
        datasets[scenario] = df
    return datasets


def load_scenario_data(scenario: str) -> pd.DataFrame:
    path = DATA_DIR / f"{scenario}.csv"
    if not path.exists():
        ensure_synthetic_data()
    df = pd.read_csv(path, parse_dates=["date", "data_updated_at"])
    return df


def generate_synthetic_treasury_data(scenario: str) -> pd.DataFrame:
    if scenario not in PROFILES:
        raise ValueError(f"Unknown scenario: {scenario}")

    profile = PROFILES[scenario]
    rng = np.random.default_rng(20260627 + list(PROFILES).index(scenario))
    start = BASE_DATE - pd.Timedelta(days=548)
    dates = pd.date_range(start, BASE_DATE + pd.Timedelta(days=89), freq="D")
    rows = []
    cash = profile.start_cash

    for idx, day in enumerate(dates):
        is_actual = day < BASE_DATE
        future_day = max((day - BASE_DATE).days, 0)
        weekday = day.weekday()
        month_day = day.day
        trend = 1 + idx / len(dates) * 0.08
        weekly_receipts = 1.18 if weekday in (0, 1) else 0.92
        future_multiplier = profile.future_receipt_multiplier if not is_actual else 1.0

        receipts = max(
            0.0,
            rng.normal(profile.receipt_level * trend * weekly_receipts, 1.1),
        )
        if profile.delayed_receivables and not is_actual and 20 <= future_day <= 65:
            receipts *= 0.55
        receipts *= future_multiplier

        other_inflows = max(0.0, rng.normal(1.1, 0.25))
        supplier_payments = max(
            0.0,
            rng.normal(profile.supplier_level * (1.35 if weekday == 4 else 0.9), 0.85),
        )
        if weekday == 3 and rng.random() < 0.08:
            supplier_payments += rng.uniform(20, 42)

        payroll = 0.0
        if (day - start).days % 14 == 4:
            payroll = max(0.0, rng.normal(16.5, 0.6))

        operating_expenses = max(0.0, rng.normal(profile.opex_level, 0.25))
        debt_service = 32.0 if month_day == 15 else 0.0
        capex = profile.capex_amount if future_day == profile.capex_day else 0.0
        fx_base = 2.8 if weekday in (1, 3) else 0.9
        fx_payments = max(0.0, rng.normal(fx_base * profile.fx_multiplier, 0.18))

        ar_due = receipts * (1.45 if profile.delayed_receivables and not is_actual else 1.08)
        if profile.delayed_receivables and not is_actual and 20 <= future_day <= 65:
            ar_due += 80.0
        ap_due = supplier_payments * (1.14 if weekday == 4 else 0.95)
        currency_exposure = fx_payments * (1.7 if scenario == "stress_receivables_fx" else 1.15)

        net = (
            receipts
            + other_inflows
            - supplier_payments
            - payroll
            - operating_expenses
            - debt_service
            - capex
            - fx_payments
        )
        closing = cash + net

        data_updated_at = BASE_DATE - pd.Timedelta(days=profile.stale_days)
        rows.append(
            {
                "date": day,
                "opening_cash": round(cash, 2),
                "customer_receipts": round(receipts, 2),
                "other_inflows": round(other_inflows, 2),
                "supplier_payments": round(supplier_payments, 2),
                "payroll": round(payroll, 2),
                "operating_expenses": round(operating_expenses, 2),
                "debt_service": round(debt_service, 2),
                "capex": round(capex, 2),
                "fx_payments": round(fx_payments, 2),
                "closing_cash": round(closing, 2),
                "ar_due": round(ar_due, 2),
                "ap_due": round(ap_due, 2),
                "currency_exposure": round(currency_exposure, 2),
                "data_updated_at": data_updated_at,
                "is_actual": is_actual,
            }
        )
        cash = closing

    df = pd.DataFrame(rows, columns=REQUIRED_COLUMNS)
    if profile.missing_payroll:
        mask = (df["date"] >= BASE_DATE) & (df["payroll"] > 0)
        df.loc[mask, "payroll"] = np.nan
        df.loc[df["date"] >= BASE_DATE + pd.Timedelta(days=35), "ar_due"] = np.nan
    return df
