#!/usr/bin/env python3
"""
Simple load generator that spawns batches in parallel to simulate 5x/10x/100x scale.
This doesn't connect to the bot; it's a standalone throughput simulator for sizing.
"""
import concurrent.futures as cf
import random, time
from statistics import mean
from typing import Tuple

def work(batch_size: int) -> Tuple[float, bool, int]:
    dur = random.uniform(0.02, 0.25) * (batch_size/100.0)
    r = random.random()
    # success, retry, fail probabilities roughly similar to bot defaults
    if r < 0.92:
        outcome = True
        retries = 0
    elif r < 0.98:
        outcome = True
        retries = random.choice([1,1,2])
        dur *= 1.1
    else:
        outcome = False
        retries = random.choice([1,2,3])
        dur *= 1.3
    time.sleep(dur/10)  # scaled down wait so the script completes quickly
    return dur, outcome, retries

def simulate(concurrency: int, batches: int = 1000, batch_size: int = 100):
    durs, succ, fails, retries = [], 0, 0, 0
    with cf.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(work, batch_size) for _ in range(batches)]
        for f in cf.as_completed(futs):
            dur, ok, r = f.result()
            durs.append(dur)
            retries += r
            if ok: succ += 1
            else: fails += 1
    return {
        "concurrency": concurrency,
        "p95_sec": sorted(durs)[int(0.95*len(durs))-1],
        "mean_sec": mean(durs),
        "success": succ,
        "fails": fails,
        "retries": retries
    }

if __name__ == "__main__":
    for c in [1, 5, 10, 50, 100]:
        res = simulate(concurrency=c, batches=1000, batch_size=100)
        print(res)
