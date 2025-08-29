#!/usr/bin/env python3
import os, json, time, random, socket, psutil, logging, logging.config, pathlib
from datetime import datetime
from prometheus_client import start_http_server, Summary, Counter, Gauge

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
LOG_CONF = BASE_DIR / "inventory_bot" / "logging_conf.json"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

with open(LOG_CONF) as f:
    conf = json.load(f)
# Inject runtime path for log file
for h in conf.get("handlers", {}).values():
    if "filename" in h and h["filename"].startswith("logs/"):
        h["filename"] = str(BASE_DIR / h["filename"])

logging.config.dictConfig(conf)
logger = logging.getLogger("inventory")

# Prometheus metrics
BATCH_SECONDS = Summary("inv_batch_seconds", "Inventory batch duration in seconds")
ITEMS_PROCESSED = Counter("inv_items_total", "Total items processed")
BATCHES = Counter("inv_batches_total", "Total batches processed", ["status"])
CPU_GAUGE = Gauge("inv_process_cpu_percent", "Process CPU percent")
MEM_GAUGE = Gauge("inv_process_mem_mb", "Process memory (MB)")
RETRIES = Counter("inv_retries_total", "Retries attempted")
ERRORS = Counter("inv_errors_total", "Errors encountered", ["error_code"])

WAREHOUSES = ["W1", "W2", "W3", "W4", "W5"]
OUTCOMES = ["success", "retry", "fail"]

def json_log(level, **fields):
    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level.upper(),
        "app": "inventory-bot",
        "host": socket.gethostname(),
        **fields,
    }
    getattr(logger, level)(json.dumps(record))

def process_items(n: int) -> int:
    """Simulates processing items with occasional retries/failures."""
    processed = 0
    for _ in range(n):
        r = random.random()
        if r < 0.92:
            processed += 1
        elif r < 0.98:
            # retry path
            RETRIES.inc()
            time.sleep(random.uniform(0.005, 0.02))
            processed += 1
        else:
            # failure path
            ERRORS.labels(error_code="E_DB_TIMEOUT").inc()
            raise RuntimeError("E_DB_TIMEOUT")
    return processed

@BATCH_SECONDS.time()
def run_batch(batch_id: int, warehouse: str):
    items_in_batch = random.randint(50, 150)
    start = time.perf_counter()
    try:
        count = process_items(items_in_batch)
        ITEMS_PROCESSED.inc(count)
        BATCHES.labels(status="success").inc()
        json_log("info",
            event="batch_complete",
            batch_id=batch_id,
            warehouse=warehouse,
            items=count,
            duration_sec=round(time.perf_counter() - start, 4),
            outcome="success"
        )
    except Exception as e:
        BATCHES.labels(status="fail").inc()
        json_log("error",
            event="batch_error",
            batch_id=batch_id,
            warehouse=warehouse,
            items=0,
            duration_sec=round(time.perf_counter() - start, 4),
            outcome="fail",
            error=str(e)
        )

def update_resource_gauges(proc: psutil.Process):
    try:
        CPU_GAUGE.set(proc.cpu_percent(interval=None))
        mem_mb = proc.memory_info().rss / (1024 * 1024)
        MEM_GAUGE.set(mem_mb)
    except Exception:
        pass

def main():
    start_http_server(9100)
    proc = psutil.Process(os.getpid())
    # warm up CPU percent
    proc.cpu_percent(interval=None)
    batch_id = 0
    json_log("info", event="bot_start", msg="inventory bot started")
    while True:
        update_resource_gauges(proc)
        run_batch(batch_id, random.choice(WAREHOUSES))
        batch_id += 1
        time.sleep(random.uniform(0.05, 0.15))

if __name__ == "__main__":
    main()
