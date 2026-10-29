"""SET/SEF automatic approval (policy-gated, disabled by default)."""

from documents.set_sef_auto_approval.policy import POLICY_VERSION, is_auto_approval_active, policy_state_for_api

__all__ = [
    "POLICY_VERSION",
    "is_auto_approval_active",
    "policy_state_for_api",
]
