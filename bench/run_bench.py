"""Score a model against bench/data ground truth.

Usage: python bench/run_bench.py [--model gemma3:4b] [--data bench/data]
"""
import argparse
import json
import time
from pathlib import Path

from receiptsort.extract import extract, extract_gemini


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma3:4b")
    ap.add_argument("--data", type=Path, default=Path("bench/data"))
    ap.add_argument("--backend", choices=["ollama", "google"], default="ollama")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    run = extract if a.backend == "ollama" else extract_gemini
    truth = json.loads((a.data / "ground_truth.json").read_text())
    names = sorted(truth)[: a.limit or None]
    hits = {"vendor": 0, "date": 0, "total": 0, "category": 0}
    t0 = time.time()
    for n in names:
        try:
            r = run(a.data / n, a.model)
        except Exception as e:
            print(f"! {n}: {e}")
            continue
        t = truth[n]
        hits["vendor"] += t["vendor"].lower() in r.vendor.lower()
        hits["date"] += r.date == t["date"]
        hits["total"] += r.total is not None and abs(r.total - t["total"]) < 0.01
        hits["category"] += r.category == t["category"]
    dt = time.time() - t0
    print(f"model={a.model} n={len(names)} secs/receipt={dt / len(names):.1f}")
    for k, v in hits.items():
        print(f"  {k:<9} {v}/{len(names)} = {v / len(names):.0%}")


if __name__ == "__main__":
    main()
