# Monitoring Strategy (One-Page)

## Telemetry Emission
- **Metrics**: Prometheus counters/gauges/summaries exposed over HTTP (`:9100`) by the bot (`prometheus_client`). 
  - `inv_batches_total{{status}}`, `inv_items_total`, `inv_batch_seconds`, `inv_process_cpu_percent`, `inv_process_mem_mb`, `inv_retries_total`, `inv_errors_total{{error_code}}`.
- **Logs**: Structured JSON logs via Python `logging` with nightly rotation (7-day retention). Events include `bot_start`, `batch_complete`, `batch_error` with fields: timestamp, batch_id, warehouse, items, duration, outcome, error_code (when present).

## Storage
- **Metrics**: Exposed locally via HTTP for scraping; persisted optionally by a Prometheus server (out of scope here). 
- **Logs**: Written to `logs/inventory.log` and synthetic dataset `data/simulated_logs.jsonl` for demos.

## Visualization & Alerting
- **Visualization (code-first)**: 
  - Generate matplotlib charts from logs/metrics (**no external dashboards**). See `docs/roi.md` and `diagrams/*.png`.
- **Alerting (code-first)**:
  - `scripts/alerting.py` scans recent logs (last 5 min) and emits alerts to `alerts/alerts.log` and console.
  - Thresholds: error rate > 2%, p95 latency > 0.30s, ≥5 consecutive failures.
  - Extendable to email/Slack via SMTP/webhook (omitted per no-external-services constraint).

## KPIs
- **Stability**: Error rate (%), retry rate (%), consecutive failure streaks, `inv_errors_total` by code.
- **Performance**: p95/p99 batch duration, items/minute throughput, CPU% and memory footprint.
- **Efficiency**: Cost per transaction (derived), retries per 1K transactions, success ratio.
- **Capacity**: Batches/min at target SLO (e.g., p95 < 300ms), headroom estimate.

## SLOs (example targets)
- **Availability**: ≥ 99.5% successful batches per hour.
- **Latency**: p95 batch duration ≤ 300 ms, p99 ≤ 500 ms.
- **Quality**: Error rate ≤ 2% sustained; retries ≤ 7% sustained.

See `diagrams/monitoring_arch.png` for telemetry flow and `scripts/*` for generators and watchers.
