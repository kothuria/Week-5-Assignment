#!/usr/bin/env python3
"""
Creates synthetic bot logs (JSONL) and a simple throughput CSV for ROI/monitoring.
"""
import json, random, time, uuid
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
LOGS = DATA_DIR / "simulated_logs.jsonl"
THROUGHPUT = DATA_DIR / "throughput_summary.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

N = 10_000
start_ts = datetime.utcnow() - timedelta(hours=6)  # last 6 hours
warehouses = ["W1","W2","W3","W4","W5","W6","W7","W8"]
rows = []

def outcome():
    r = random.random()
    if r < 0.915:
        return "success", 0, None
    elif r < 0.985:
        return "retry", random.choice([1,1,2]), None
    else:
        return "fail", random.choice([1,2,3]), random.choice(["E_DB_TIMEOUT","E_API_429","E_NET_RESET"])

for i in range(N):
    ts = start_ts + timedelta(seconds=i * (6*3600/N))  # evenly over 6h
    wh = random.choice(warehouses)
    items = random.randint(40, 180)
    dur = random.uniform(0.03, 0.35)
    out, retries, err = outcome()
    cpu_time = dur * random.uniform(0.4, 0.9)
    rec = {
        "ts": ts.isoformat() + "Z",
        "level": "INFO" if out=="success" else ("WARNING" if out=="retry" else "ERROR"),
        "event": "batch_complete" if out=="success" else ("batch_retry" if out=="retry" else "batch_error"),
        "batch_id": str(uuid.uuid4()),
        "warehouse": wh,
        "items": items if out!="fail" else 0,
        "duration_sec": round(dur, 4),
        "cpu_time_sec": round(cpu_time, 4),
        "outcome": out,
        "retries": retries,
        "error_code": err
    }
    rows.append(rec)

with LOGS.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

# Throughput summary per 5-minute window
df = pd.DataFrame(rows)
df["ts"] = pd.to_datetime(df["ts"])
df.set_index("ts", inplace=True)
grp = df.resample("5min").agg(
    batches=("event","count"),
    success=("outcome", lambda s: (s=="success").sum()),
    retry=("outcome", lambda s: (s=="retry").sum()),
    fail=("outcome", lambda s: (s=="fail").sum()),
    items=("items","sum"),
    p95_duration=("duration_sec", lambda s: s.quantile(0.95)),
    mean_cpu=("cpu_time_sec","mean")
).reset_index()

grp.to_csv(THROUGHPUT, index=False)
print(f"Wrote {LOGS} and {THROUGHPUT}")
