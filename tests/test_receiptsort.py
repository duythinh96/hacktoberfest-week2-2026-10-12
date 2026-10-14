from receiptsort.extract import Receipt, parse_response
from receiptsort.organize import safe_name, unique_path, write_csv


def test_parse_plain_json():
    r = parse_response('{"vendor":"Acme","date":"2026-10-01","total":12.5,"currency":"USD","category":"Meals"}')
    assert r.vendor == "Acme" and r.total == 12.5 and r.category == "meals"


def test_parse_fenced_and_string_total():
    r = parse_response('```json\n{"vendor":"X","total":"$1,234.50"}\n```')
    assert r.total == 1234.50


def test_safe_name():
    r = Receipt(vendor="Cà Phê & Co.", date="2026-10-01", total=3)
    assert safe_name(r, ".jpg") == "2026-10-01_c-ph-co_3.00.jpg"


def test_unique_path(tmp_path):
    (tmp_path / "a.jpg").write_text("x")
    assert unique_path(tmp_path / "a.jpg").name == "a-2.jpg"


def test_write_csv(tmp_path):
    write_csv([("a.jpg", Receipt(vendor="V", total=1.0))], tmp_path / "o.csv")
    assert "vendor" in (tmp_path / "o.csv").read_text().splitlines()[0]


def test_gemini_text_skips_thought_parts():
    from receiptsort.extract import gemini_text
    data = {"candidates": [{"content": {"parts": [
        {"text": "reasoning {not json}", "thought": True},
        {"text": '{"vendor": "A"}'},
    ]}}]}
    assert parse_response(gemini_text(data)).vendor == "A"


def test_normalize_date_vietnamese_formats():
    from receiptsort.extract import normalize_date
    assert normalize_date("12/10/2026") == "2026-10-12"
    assert normalize_date("5.3.2026") == "2026-03-05"
    assert normalize_date("2026-10-12") == "2026-10-12"
    assert normalize_date("last Tuesday") is None


def test_summary_groups_and_keeps_currencies_apart():
    from receiptsort.summary import summarize
    rs = [
        Receipt(vendor="A", date="2026-10-01", total=10, currency="USD", category="meals"),
        Receipt(vendor="B", date="2026-10-20", total=5.5, currency="USD", category="meals"),
        Receipt(vendor="C", date="2026-10-02", total=50000, currency="VND", category="meals"),
        Receipt(vendor="D", date="2026-10-03", total=None, currency="USD", category="meals"),
    ]
    rows = summarize(rs)
    assert {"month": "2026-10", "category": "meals", "currency": "USD", "count": 2, "total": 15.5} in rows
    assert len(rows) == 2
