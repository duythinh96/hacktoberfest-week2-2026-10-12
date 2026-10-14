"""Rename/copy files and write CSV output."""
import csv
import re
import shutil
from pathlib import Path

from .extract import Receipt

FIELDS = ["file", "vendor", "date", "total", "currency", "category"]


def safe_name(r: Receipt, suffix: str) -> str:
    vendor = re.sub(r"[^A-Za-z0-9]+", "-", r.vendor).strip("-").lower() or "unknown"
    total = f"{r.total:.2f}" if r.total is not None else "na"
    return f"{r.date or 'undated'}_{vendor}_{total}{suffix}"


def unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    n = 2
    while (cand := dest.with_name(f"{dest.stem}-{n}{dest.suffix}")).exists():
        n += 1
    return cand


def copy_sorted(src: Path, r: Receipt, out_dir: Path) -> Path:
    folder = out_dir / r.category
    folder.mkdir(parents=True, exist_ok=True)
    dest = unique_path(folder / safe_name(r, src.suffix.lower()))
    shutil.copy2(src, dest)
    return dest


def write_csv(rows: list[tuple[str, Receipt]], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for name, r in rows:
            w.writerow({"file": name, **r.to_dict()})
