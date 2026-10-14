"""Record a real CLI run on synthetic receipts, then render docs/media/demo.gif and summary.png.

Needs GEMINI_API_KEY (or edit BACKEND args for Ollama). Usage: PYTHONPATH=. python docs/make_demo.py
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "docs" / "media"
SRC, OUT = ROOT / "out" / "demo_in", ROOT / "out" / "demo_out"
N = 10
CMD = ["--backend", "google", "-m", "gemma-4-26b-a4b-it"]
PROMPT = "$ receiptsort ./receipts -o ./sorted --backend google -m gemma-4-26b-a4b-it"
BG, FG, DIM, GREEN = (24, 26, 32), (220, 223, 228), (130, 136, 148), (120, 220, 140)
FONT = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 15)
W, LH, PAD = 940, 22, 18


def record() -> list[tuple[float, str]]:
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.rmtree(SRC, ignore_errors=True)
    SRC.mkdir(parents=True)
    for p in sorted((ROOT / "bench/data").glob("*.png"))[:N]:
        shutil.copy(p, SRC / p.name)
    t0, events = time.time(), []
    proc = subprocess.Popen([sys.executable, "-m", "receiptsort.cli", str(SRC), "-o", str(OUT), *CMD],
                            stdout=subprocess.PIPE, text=True, cwd=ROOT)
    for line in proc.stdout:
        events.append((time.time() - t0, line.rstrip().replace(str(OUT), "./sorted")))
    proc.wait()
    return events


def frame(lines, height):
    img = Image.new("RGB", (W, height), BG)
    d = ImageDraw.Draw(img)
    d.ellipse((16, 12, 28, 24), fill=(255, 95, 86)); d.ellipse((38, 12, 50, 24), fill=(255, 189, 46)); d.ellipse((60, 12, 72, 24), fill=(39, 201, 63))
    y = 42
    for text, color in lines:
        d.text((PAD, y), text, font=FONT, fill=color)
        y += LH
    return img


def main():
    events = record()
    lines = [(PROMPT, GREEN)]
    height = 42 + LH * (len(events) + 2) + PAD
    frames, durs = [frame(lines, height)], [700]
    prev = 0.0
    for t, text in events:
        durs[-1] = int(min(max(t - prev, 0.25), 1.6) * 1000)
        prev = t
        lines.append((text, FG if "->" in text else GREEN))
        frames.append(frame(lines, height))
        durs.append(100)
    durs[-1] = 3000
    MEDIA.mkdir(parents=True, exist_ok=True)
    frames[0].save(MEDIA / "demo.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)

    rows = (OUT / "summary.csv").read_text().splitlines()
    tree = ["sorted/"] + [f"  {d.name}/  ({len(list(d.iterdir()))} file(s))" for d in sorted(OUT.iterdir()) if d.is_dir()]
    body = [("$ cat sorted/summary.csv", GREEN)] + [(r.replace(",", "  |  "), FG) for r in rows] + [("", FG), ("$ tree sorted", GREEN)] + [(t, FG) for t in tree]
    frame(body, 42 + LH * len(body) + PAD).save(MEDIA / "summary.png")
    print(f"{len(events)} events, wrote {MEDIA}/demo.gif and summary.png")


if __name__ == "__main__":
    main()
