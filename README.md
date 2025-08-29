# Week 5 — Scaling & Maintaining a Code‑First Automation Platform

This repository implements the end‑to‑end deliverables for the Week 5 assignment:

- **Monitoring Strategy** (docs + working code)
- **Maintenance Plan** (docs + CI/CD config)
- **ROI Evaluation** (docs + synthetic data + chart)
- **Slide Deck** (PowerPoint or HTML fallback with speaker notes)
- **Synthetic Data Generator** (`/scripts/generate_fake_logs.py`)
- **System Diagrams** (`/diagrams/*.png`)

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Start the inventory bot with metrics + JSON logs
python inventory_bot/inventory_bot.py

# 2) Generate synthetic logs for ROI/monitoring demos (10,000 rows by default)
python scripts/generate_fake_logs.py

# 3) Run a simple alert watcher (reads logs & emits threshold alerts)
python scripts/alerting.py

# 4) See Prometheus metrics (bot runs an HTTP exporter on :9100)
# Open http://localhost:9100 in your browser while the bot is running.
```

## Project Structure

```
week5_automation_platform/
├── inventory_bot/
│   ├── inventory_bot.py
│   ├── logging_conf.json
│   └── __init__.py
├── scripts/
│   ├── generate_fake_logs.py
│   ├── simulate_load.py
│   └── alerting.py
├── docs/
│   ├── monitoring_plan.md
│   ├── maintenance_plan.md
│   └── roi.md
├── data/
│   ├── simulated_logs.jsonl
│   ├── throughput_summary.csv
│   └── roi_summary.csv
├── diagrams/
│   ├── monitoring_arch.png
│   └── scaling_topology.png
├── alerts/
│   └── alerts.log
├── logs/
│   └── inventory.log
├── slides/
│   ├── deck.pptx (if python-pptx available; else deck.html)
│   └── assets/
├── .github/workflows/
│   └── ci.yml
├── requirements.txt
└── README.md
```

## Demo Notes

- Logs rotate nightly via `TimedRotatingFileHandler` (keep last 7 days).
- Prometheus metrics exposed on `:9100`.
- Alerts are simulated locally by a Python watcher (no external dashboard).
- ROI notebook is code‑driven: we derive cost/benefit from the synthetic dataset.

## License

MIT
