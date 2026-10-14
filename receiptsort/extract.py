"""Extract structured fields from a receipt image using a local Ollama vision model."""
import base64
import json
import re
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
        date=data.get("date"),
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
