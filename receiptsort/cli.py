import argparse
import sys
from pathlib import Path

from .extract import DEFAULT_MODEL, extract, extract_gemini
from .organize import copy_sorted, write_csv

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="receiptsort", description=__doc__)
    p.add_argument("input", type=Path, help="folder of receipt images")
    p.add_argument("-o", "--out", type=Path, default=Path("out"), help="output folder")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Ollama model name")
    p.add_argument("--backend", choices=["ollama", "google"], default="ollama",
                   help="'google' sends images to Google AI Studio (needs GEMINI_API_KEY)")
    args = p.parse_args(argv)
    run = extract if args.backend == "ollama" else extract_gemini

    files = sorted(f for f in args.input.iterdir() if f.suffix.lower() in IMAGE_EXT)
    if not files:
        print("no images found", file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in files:
        try:
            r = run(f, args.model)
        except Exception as e:  # keep going on a bad file
            print(f"! {f.name}: {e}", file=sys.stderr)
            continue
        dest = copy_sorted(f, r, args.out)
        rows.append((dest.name, r))
        print(f"{f.name} -> {dest.relative_to(args.out)}")
    write_csv(rows, args.out / "receipts.csv")
    print(f"done: {len(rows)}/{len(files)} processed, see {args.out / 'receipts.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
