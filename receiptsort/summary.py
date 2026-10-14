"""Accountant-friendly roll-up: totals per month x category, one row per currency (never mixed)."""
import csv
from collections import defaultdict
from pathlib import Path

from .extract import Receipt

FIELDS = ["month", "category", "currency", "count", "total"]


def summarize(receipts: list[Receipt]) -> list[dict]:
    agg: dict[tuple, list] = defaultdict(lambda: [0, 0.0])
    for r in receipts:
        if r.total is None:
            continue
        key = ((r.date or "undated")[:7], r.category, r.currency or "unknown")
        agg[key][0] += 1
        agg[key][1] += r.total
    return [
        {"month": m, "category": c, "currency": cur, "count": n, "total": round(t, 2)}
        for (m, c, cur), (n, t) in sorted(agg.items())
    ]


def write_summary(receipts: list[Receipt], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(summarize(receipts))
