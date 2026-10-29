"""Deployment and Admin-controlled SET/SEF automatic approval policy."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import BASE_DIR, Config

POLICY_VERSION = "1.1.0"
_POLICY_FILENAME = "set_sef_auto_approval_policy.json"


def _policy_path() -> Path:
    folder = BASE_DIR / "instance"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / _POLICY_FILENAME


def _read_file() -> dict[str, Any]:
    path = _policy_path()
    if not path.is_file():
        return {"enabled": False, "policyVersion": POLICY_VERSION}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"enabled": False, "policyVersion": POLICY_VERSION}
    return raw if isinstance(raw, dict) else {"enabled": False, "policyVersion": POLICY_VERSION}


def admin_may_toggle_policy() -> bool:
    """Server must explicitly allow Admin to turn automatic approval on."""
    return (Config.SET_SEF_AUTO_APPROVAL_ALLOW_ADMIN_TOGGLE or "").lower() in (
        "1",
        "true",
        "yes",
    )


def env_forces_enabled() -> bool:
    return (Config.SET_SEF_AUTO_APPROVAL_ENABLED or "").lower() in ("1", "true", "yes")


def is_auto_approval_active() -> bool:
    if env_forces_enabled():
        return True
    state = _read_file()
    return state.get("enabled") is True


def policy_state_for_api() -> dict[str, Any]:
    state = _read_file()
    return {
        "policyVersion": POLICY_VERSION,
        "active": is_auto_approval_active(),
        "adminToggleAllowed": admin_may_toggle_policy(),
        "envForcedOn": env_forces_enabled(),
        "enabledInStore": bool(state.get("enabled")),
        "enabledAt": state.get("enabledAt"),
        "enabledByUserId": state.get("enabledByUserId"),
        "disabledAt": state.get("disabledAt"),
        "disabledByUserId": state.get("disabledByUserId"),
    }


def set_admin_policy_enabled(*, enabled: bool, admin_public_id: str) -> dict[str, Any]:
    if enabled and not env_forces_enabled() and not admin_may_toggle_policy():
        raise ValueError("policy_toggle_not_allowed")

    now = datetime.now(timezone.utc).isoformat()
    state = _read_file()
    state["policyVersion"] = POLICY_VERSION
    state["enabled"] = bool(enabled)
    if enabled:
        state["enabledAt"] = now
        state["enabledByUserId"] = admin_public_id
        state.pop("disabledAt", None)
        state.pop("disabledByUserId", None)
    else:
        state["disabledAt"] = now
        state["disabledByUserId"] = admin_public_id
    _policy_path().write_text(json.dumps(state, indent=2), encoding="utf-8")
    return policy_state_for_api()
