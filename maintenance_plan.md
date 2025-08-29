# Maintenance Plan

## Branching, Patch, and Release
- **Branching model**: `main` (stable), `develop` (integration), feature branches `feat/*`, hotfix branches `hotfix/*`.
- **Versioning**: Semantic Versioning (MAJOR.MINOR.PATCH).
- **Release**:
  1. Merge to `main` via PR with CI green.
  2. Tag `vX.Y.Z` (automated in CI on `main`).
  3. Build and push Docker image `inventory-bot:X.Y.Z` (optional registry step).
- **Hotfix flow**: Branch from `main` → fix → PR → tag `PATCH` release → fast deploy.

## Dependency Management
- **Pins** in `requirements.txt`. Enable GitHub Dependabot for updates and security advisories.
- Weekly `pip list --outdated` review; test in CI.

## CI/CD (GitHub Actions)
- Run `pytest` (if tests present), type checks (future), then build image and push tag.
- Workflow in `.github/workflows/ci.yml` demonstrates: checkout → install → test → build → push → tag.

## Scaling Strategy (5×, 10×, 100×)
- **Horizontal workers**: Run multiple bot instances per warehouse shard (hash by warehouse or item range).
- **Work queue**: Use idempotent job model; retries send to Dead‑Letter Queue (DLQ) after N attempts.
- **Backpressure**: Rate‑limit per upstream (API/DB) and auto‑tune concurrency based on p95 latency and error spikes.
- **Statelessness**: Keep no in‑memory state between batches; persist progress to durable store (e.g., DB, object storage).

## Recovery & Resilience
- **Retries with jitter**: Exponential backoff, cap, and randomized jitter to avoid thundering herd.
- **DLQ**: On exceeding max retries or fatal codes, send to DLQ for offline reprocessing.
- **Failover**: Run N+1 workers; health‑check loop restarts a failed worker; circuit‑breaker around dependent services.
- **Idempotency**: Use batch IDs and dedupe keys to safely retry without double‑processing.

## Python Patterns (Examples)
```python
# Exponential backoff with jitter
import random, time
def backoff(attempt, base=0.1, cap=2.0):
    wait = min(cap, base * (2 ** attempt)) + random.uniform(0, 0.05)
    time.sleep(wait)

# Horizontal scale: shard by warehouse
def shard_for(warehouse, workers):
    return hash(warehouse) % workers

# Dead-letter pattern
def handle_failure(job, attempts, max_attempts=3, dlq=list()):
    if attempts >= max_attempts:
        dlq.append(job)  # placeholder for durable DLQ
        return "DLQ"
    return "RETRY"
```
