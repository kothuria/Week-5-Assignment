#!/usr/bin/env python3
"""
Simple local alerting that scans JSONL logs and emits alerts to alerts/alerts.log.
Thresholds:
- Error rate > 2% in the last 5 minutes
- P95 duration > 0.30s in the last 5 minutes
- Consecutive failures >= 5
"""
import json, time
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "simulated_logs.jsonl"
ALOG = BASE / "alerts" / "alerts.log"
ALOG.parent.mkdir(parents=True, exist_ok=True)

def now_utc():
    return datetime.utcnow()

def emit(msg: str):
    line = f"{now_utc().isoformat()}Z ALERT {msg}"
    print(line)
    with ALOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_df():
    # read streaming if large; here it's fine to read into memory
    rows = [json.loads(l) for l in DATA.read_text().splitlines()]
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def main():
    if not DATA.exists():
        print("No data file found. Run scripts/generate_fake_logs.py first.")
        return
    df = load_df()
    # consider only last 5 minutes window based on timestamps in file
    end = df["ts"].max()
    start = end - timedelta(minutes=5)
    win = df[(df["ts"] >= start) & (df["ts"] <= end)]
    if len(win)==0:
        print("Window empty.")
        return
    total = len(win)
    errs = (win["outcome"]=="fail").sum()
    retries = (win["outcome"]=="retry").sum()
    p95 = win["duration_sec"].quantile(0.95)
    err_rate = errs/total if total else 0.0

    if err_rate > 0.02:
        emit(f"Error rate {err_rate:.2%} over last 5 minutes (threshold 2%)")

    if p95 > 0.30:
        emit(f"P95 duration {p95:.3f}s over last 5 minutes (threshold 0.30s)")

    # consecutive failures check
    consec = 0
    max_consec = 0
    for out in win.sort_values("ts")["outcome"]:
        if out == "fail":
            consec += 1
            max_consec = max(max_consec, consec)
        else:
            consec = 0
    if max_consec >= 5:
        emit(f"Consecutive failures observed: {max_consec} (threshold 5)")

if __name__ == "__main__":
    main()
