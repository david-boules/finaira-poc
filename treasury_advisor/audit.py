from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import AUDIT_LOG_PATH, DATA_DIR


def append_audit_record(record: dict[str, Any], path: Path = AUDIT_LOG_PATH) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    payload = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str) + "\n")


def load_audit_records(path: Path = AUDIT_LOG_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def audit_dataframe(path: Path = AUDIT_LOG_PATH) -> pd.DataFrame:
    records = load_audit_records(path)
    if not records:
        return pd.DataFrame()
    rows = []
    for record in records:
        recommendation = record.get("recommendation", {})
        confidence = record.get("confidence", {})
        rows.append(
            {
                "logged_at": record.get("logged_at"),
                "event_type": record.get("event_type"),
                "run_id": record.get("run_id"),
                "scenario": record.get("scenario"),
                "action": recommendation.get("action_type"),
                "amount_usd_m": recommendation.get("amount"),
                "confidence_status": confidence.get("status"),
                "confidence_score": confidence.get("score"),
                "human_decision": record.get("human_decision"),
                "outcome": record.get("outcome"),
            }
        )
    return pd.DataFrame(rows)
