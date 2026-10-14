# Benchmark results

Dataset: 30 synthetic receipts (`python bench/gen_fake_receipts.py -n 30 --seed 1`), VND + USD, light rotation/blur.
Backend: hosted Google AI Studio (images sent to Google; synthetic data only). Run on 2026-10-14.

| Model | Backend | vendor | date | total | category | s/receipt |
|---|---|---|---|---|---|---|
| gemma-4-26b-a4b-it | google | 30/30 | 30/30 | 30/30 | 30/30 | 9.5 |
| gemma-4-31b-it | google | n/a | n/a | n/a | n/a | HTTP 500 on every request (server side, even text-only; retried with backoff) |

Local Ollama results (e.g. `gemma3:4b`) are still to be added.

Caveat: synthetic receipts are clean and templated, so these numbers are an upper bound for real photos.
