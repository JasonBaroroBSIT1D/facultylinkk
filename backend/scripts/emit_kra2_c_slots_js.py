"""Print CRITERION_C_REQUIRED_SLOTS / LABELS for web/js/kra2-a-workspace-ui.js."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from documents.kra2_evidence.kra2_c_evidence_slots import _CRITERION_C_SLOTS, _SLOT_LABELS  # noqa: E402


def main() -> None:
    lines = ["  CRITERION_C_REQUIRED_SLOTS: {"]
    for k in sorted(_CRITERION_C_SLOTS.keys()):
        v = list(_CRITERION_C_SLOTS[k])
        if len(v) <= 3:
            lines.append(f'    "{k}": {json.dumps(v)},')
        else:
            lines.append(f'    "{k}": [')
            for s in v:
                lines.append(f'      "{s}",')
            lines[-1] = lines[-1].rstrip(",")
            lines.append("    ],")
    lines.append("  },")
    lines.append("")
    lines.append("  CRITERION_C_SLOT_LABELS: {")
    for sk, lab in sorted(_SLOT_LABELS.items()):
        esc = lab.replace('"', '\\"')
        lines.append(f'    {sk}: "{esc}",')
    lines[-1] = lines[-1].rstrip(",")
    lines.append("  },")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
