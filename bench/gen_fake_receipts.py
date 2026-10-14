"""Generate SYNTHETIC receipt images + ground truth (no real data).

Usage: python bench/gen_fake_receipts.py [-n 30] [--seed 1] [-o bench/data]
"""
import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = [
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
# (vendor, category, currency, items[(name, price)])
VENDORS = [
    ("Highlands Coffee", "meals", "VND", [("Cà phê sữa đá", 39000), ("Bánh mì que", 19000), ("Trà đào", 45000)]),
    ("Phở 24", "meals", "VND", [("Phở bò tái", 65000), ("Quẩy", 10000), ("Trà đá", 5000)]),
    ("Grab", "travel", "VND", [("GrabCar chuyến đi", 128000)]),
    ("Starbucks", "meals", "USD", [("Latte", 5.45), ("Croissant", 3.95)]),
    ("Uber", "travel", "USD", [("Trip fare", 23.4), ("Booking fee", 2.5)]),
    ("GitHub", "software", "USD", [("Copilot Pro", 10.0)]),
    ("Figma", "software", "USD", [("Professional seat", 15.0)]),
    ("Staples", "office", "USD", [("Printer paper", 8.99), ("Pens (12)", 6.49), ("Stapler", 12.0)]),
    ("Viettel", "utilities", "VND", [("Cước internet tháng", 220000)]),
    ("EVN HCMC", "utilities", "VND", [("Tiền điện", 845000)]),
    ("Fahasa", "office", "VND", [("Sổ tay A5", 48000), ("Bút gel", 15000)]),
]


def font(size):
    for p in FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fmt(v, cur):
    return f"{v:,.0f} d" if cur == "VND" else f"${v:,.2f}"


def make(rng, idx, out: Path):
    vendor, cat, cur, pool = rng.choice(VENDORS)
    items = rng.sample(pool, k=rng.randint(1, len(pool)))
    total = round(sum(p for _, p in items), 2)
    date = f"2026-{rng.randint(1, 10):02d}-{rng.randint(1, 28):02d}"
    f, fb = font(22), font(28)
    lines = [(vendor.upper(), fb), (f"Date: {date}", f), ("-" * 28, f)]
    lines += [(f"{n[:16]:<16}{fmt(p, cur):>12}", f) for n, p in items]
    lines += [("-" * 28, f), (f"{'TOTAL':<16}{fmt(total, cur):>12}", fb)]
    h = 40 + sum(30 if ft is f else 38 for _, ft in lines) + 20
    img = Image.new("RGB", (540, h), (rng.randint(235, 255),) * 3)
    d, y = ImageDraw.Draw(img), 20
    for text, ft in lines:
        d.text((20, y), text, fill=(20, 20, 20), font=ft)
        y += 30 if ft is f else 38
    img = img.rotate(rng.uniform(-2.5, 2.5), expand=True, fillcolor=(255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0, 0.8)))
    name = f"receipt_{idx:03d}.png"
    img.save(out / name)
    return name, {"vendor": vendor, "date": date, "total": total, "currency": cur, "category": cat}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("-o", type=Path, default=Path("bench/data"))
    a = ap.parse_args()
    a.o.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    truth = dict(make(rng, i, a.o) for i in range(a.n))
    (a.o / "ground_truth.json").write_text(json.dumps(truth, indent=2, ensure_ascii=False))
    print(f"wrote {a.n} synthetic receipts to {a.o}")


if __name__ == "__main__":
    main()
