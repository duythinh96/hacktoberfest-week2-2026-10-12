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
