"""Print criterionCSlots map body for mobile/lib/data/kra2_catalog.dart."""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.kra2_c_evidence_slots import _CRITERION_C_SLOTS  # noqa: E402


def main() -> None:
    for k in sorted(_CRITERION_C_SLOTS.keys()):
        v = list(_CRITERION_C_SLOTS[k])
        inner = ", ".join(f"'{s}'" for s in v)
        print(f"        '{k}': [{inner}],")


if __name__ == "__main__":
    main()
