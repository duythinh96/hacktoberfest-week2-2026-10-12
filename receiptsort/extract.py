"""Extract structured fields from a receipt image using a local Ollama vision model."""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma3:4b"

PROMPT = (
    "You read receipts and invoices. Return ONLY a JSON object with keys: "
    '"vendor" (string), "date" (YYYY-MM-DD or null), "total" (number or null), '
    '"currency" (ISO code or null), "category" (one of: meals, travel, software, '
    "office, utilities, other). No prose."
)


@dataclass
class Receipt:
    vendor: str = "unknown"
    date: str | None = None
    total: float | None = None
    currency: str | None = None
    category: str = "other"

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_date(value) -> str | None:
    """Accept YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY (Vietnamese day-first); else None."""
    if not value:
        return None
    v = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v
    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", v)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def parse_response(text: str) -> Receipt:
    """Parse model output (possibly wrapped in prose/code fences) into a Receipt."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in model output")
    data = json.loads(match.group(0))
    total = data.get("total")
    if isinstance(total, str):
        total = float(re.sub(r"[^\d.\-]", "", total) or "nan")
    return Receipt(
        vendor=str(data.get("vendor") or "unknown"),
        date=normalize_date(data.get("date")),
        total=total,
        currency=data.get("currency"),
        category=str(data.get("category") or "other").lower(),
    )


def extract(image_path: Path, model: str = DEFAULT_MODEL, url: str = OLLAMA_URL) -> Receipt:
    img = base64.b64encode(Path(image_path).read_bytes()).decode()
    body = json.dumps({
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [{"role": "user", "content": PROMPT, "images": [img]}],
    }).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        content = json.load(resp)["message"]["content"]
    return parse_response(content)


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def extract_gemini(image_path: Path, model: str, api_key: str | None = None) -> Receipt:
    """Hosted Gemma/Gemini via Google AI Studio. Sends the image to Google: dev/benchmark use on
    synthetic data only; the local Ollama path is the privacy-preserving default."""
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("set GEMINI_API_KEY to use the Google backend")
    suffix = Path(image_path).suffix.lower().lstrip(".")
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    body = json.dumps({"contents": [{"parts": [
        {"text": PROMPT},
        {"inline_data": {"mime_type": mime, "data": base64.b64encode(Path(image_path).read_bytes()).decode()}},
    ]}]}).encode()
    req = urllib.request.Request(
        GEMINI_URL.format(model=model), body,
        {"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return parse_response(gemini_text(json.load(resp)))
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == 3:
                raise
            time.sleep(2 ** attempt)


def gemini_text(data: dict) -> str:
    """Join answer parts, skipping 'thought' (reasoning) parts that some models emit first."""
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))
