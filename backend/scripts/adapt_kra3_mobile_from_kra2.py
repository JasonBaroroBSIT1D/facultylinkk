from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "mobile"

REPL = [
    ("Kra2", "Kra3"),
    ("kra2", "kra3"),
    ("KRA II", "KRA III"),
    ("Research", "Extension"),
    ("kra2_indicators.json", "kra3_indicators.json"),
    ("kra2_a_ux", "kra3_a_ux"),
    ("kra2_ocr_sync", "kra3_ocr_sync"),
]

paths = [
    ROOT / "lib" / "screens" / "kra3",
    ROOT / "lib" / "data" / "kra3_catalog.dart",
    ROOT / "lib" / "data" / "kra3_submit_readiness.dart",
]

for base in paths:
    files = [base] if base.is_file() else list(base.rglob("*.dart"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for old, new in REPL:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
print("Mobile KRA III adapt done")
