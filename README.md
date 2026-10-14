# ReceiptSort

Local-first receipt & invoice sorter for freelancers. A vision model running on **your own laptop** (via [Ollama](https://ollama.com)) reads each receipt, renames it `date_vendor_total`, files it by category, and exports a CSV for your accountant. **No cloud, no API key, no client data leaving your machine.**

## Why open-weight?
- **Privacy:** receipts contain client names and amounts; nothing is uploaded.
- **Cost:** zero per-receipt cost after the model download.
- **Swappable:** `--model` accepts any Ollama vision model (Qwen2.5-VL, Gemma 3, ...).

## Quick start
```bash
ollama pull gemma3:4b   # ~3GB, fits 16GB RAM (or qwen2.5vl:3b)
pip install -e .
receiptsort ./my-receipts -o ./sorted
```
Output: `sorted/<category>/<date>_<vendor>_<total>.jpg` and `sorted/receipts.csv`.

## Develop
```bash
pip install -e ".[dev]" && pytest
```

## Roadmap / contribute
See open issues labelled `hacktoberfest` and `good first issue`. Ideas: PDF support, multi-currency totals, duplicate detection, simple web UI.

License: MIT
