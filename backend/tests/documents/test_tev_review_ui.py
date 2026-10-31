"""Synthetic checks for SET/SEF reviewer UI helpers (no database)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2].parent
NODE_TEST = REPO_ROOT / "web" / "tests" / "tev-review-ui.test.js"
CA_UI_TEST = REPO_ROOT / "web" / "tests" / "criterion-a-workspace-ui.test.js"


def test_tev_review_ui_node_helpers():
    if not NODE_TEST.is_file():
        raise AssertionError(f"Missing UI test script: {NODE_TEST}")
    result = subprocess.run(
        ["node", str(NODE_TEST)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_criterion_a_workspace_ui_node_helpers():
    if not CA_UI_TEST.is_file():
        raise AssertionError(f"Missing UI test script: {CA_UI_TEST}")
    result = subprocess.run(
        ["node", str(CA_UI_TEST)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
