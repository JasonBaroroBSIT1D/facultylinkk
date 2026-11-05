"""One-time bootstrap: copy KRA III evidence/config modules to KRA IV templates."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = [
    ("kra3_evidence", "kra4_evidence"),
    ("KRA III", "KRA IV"),
    ("KRA3", "KRA4"),
    ("kra3_", "kra4_"),
    ("kra3-", "kra4-"),
    ("Kra3", "Kra4"),
]


def _transform(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for path in dst.rglob("*"):
        if path.suffix == ".py":
            path.write_text(_transform(path.read_text(encoding="utf-8")), encoding="utf-8")
        if path.name.startswith("kra3_"):
            path.rename(path.with_name(path.name.replace("kra3_", "kra4_", 1)))


def main() -> None:
    copy_tree(ROOT / "documents" / "kra3_evidence", ROOT / "documents" / "kra4_evidence")
    for name in ("kra3_annex.py", "kra3_indicator_registry.py", "kra3_workflow.py", "kra3_official_reference.py"):
        src = ROOT / "kra_configuration" / name
        dst = ROOT / "kra_configuration" / name.replace("kra3_", "kra4_")
        dst.write_text(_transform(src.read_text(encoding="utf-8")), encoding="utf-8")
    sim = ROOT / "documents" / "scoring" / "kra3_simulation_adapter.py"
    sim_dst = ROOT / "documents" / "scoring" / "kra4_simulation_adapter.py"
    sim_dst.write_text(_transform(sim.read_text(encoding="utf-8")), encoding="utf-8")
    print("Bootstrap complete: documents/kra4_evidence + kra4_configuration modules")


if __name__ == "__main__":
    main()
