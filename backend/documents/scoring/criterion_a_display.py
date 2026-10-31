"""Criterion A display metadata (formulas unchanged — presentation only)."""

from __future__ import annotations

from typing import Any


def authoritative_criterion_a_estimated_points(summary: dict[str, Any]) -> float | None:
    """Same priority as rank simulation: combined provisional, then combined validated."""
    prov = summary.get("combinedProvisionalPoints")
    if prov is not None:
        return round(float(prov), 2)
    val = summary.get("combinedValidatedPoints")
    if val is not None:
        return round(float(val), 2)
    return None


def _upload_count(block: dict[str, Any]) -> int:
    cov = block.get("coverageSummary") if isinstance(block.get("coverageSummary"), dict) else {}
    try:
        return int(cov.get("totalUploads") or 0)
    except (TypeError, ValueError):
        return 0


def component_display(block: dict[str, Any], *, full_name: str, short_name: str) -> dict[str, Any]:
    """SET or SEF component for UI — does not alter scoring."""
    uploads = _upload_count(block)
    prov = block.get("provisionalPoints")
    val = block.get("validatedPoints")
    missing = list(block.get("missingPeriods") or [])
    note = (block.get("scoringNote") or "").strip()
    cov = block.get("coverageSummary") if isinstance(block.get("coverageSummary"), dict) else {}
    required = cov.get("requiredPeriods")
    evidenced = cov.get("evidencedRatings")

    if uploads == 0:
        return {
            "indicator": short_name,
            "fullName": full_name,
            "state": "awaiting_evidence",
            "displayLabel": f"Awaiting eligible {full_name} evidence",
            "estimatedPoints": None,
            "validatedPoints": None,
            "explanation": None,
        }

    if prov is not None:
        return {
            "indicator": short_name,
            "fullName": full_name,
            "state": "estimated",
            "displayLabel": f"Estimated component: {prov}",
            "estimatedPoints": prov,
            "validatedPoints": val,
            "explanation": (
                "Includes eligible pending and accepted semester ratings."
                if val is None
                else "Provisional estimate; validated component also available."
            ),
            "semesterCoverage": f"{evidenced or 0} of {required or '—'} required semester rating(s) evidenced",
        }

    if val is not None:
        return {
            "indicator": short_name,
            "fullName": full_name,
            "state": "validated_component",
            "displayLabel": f"Validated component: {val}",
            "estimatedPoints": val,
            "validatedPoints": val,
            "explanation": "Based on reviewer-validated semester records only.",
            "semesterCoverage": f"{evidenced or 0} of {required or '—'} required semester rating(s) evidenced",
        }

    parts: list[str] = []
    if missing:
        parts.extend(missing)
    if note:
        parts.append(note)
    if not parts and required is not None and evidenced is not None:
        parts.append(
            f"Incomplete coverage: {evidenced} of {required} required semester(s) with eligible ratings."
        )
    explanation = "; ".join(parts) if parts else "Not yet computable — check semester coverage and published scoring rules."

    return {
        "indicator": short_name,
        "fullName": full_name,
        "state": "not_computable",
        "displayLabel": "Not yet computable",
        "estimatedPoints": None,
        "validatedPoints": None,
        "explanation": explanation,
        "semesterCoverage": f"{evidenced or 0} of {required or '—'} required semester rating(s) evidenced",
    }


def enrich_criterion_a_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Attach authoritative estimatedPoints and structured display (mutates copy)."""
    out = dict(summary)
    set_b = out.get("set") if isinstance(out.get("set"), dict) else {}
    sef_b = out.get("sef") if isinstance(out.get("sef"), dict) else {}
    set_display = component_display(set_b, full_name="SET", short_name="SET")
    sef_display = component_display(sef_b, full_name="SEF", short_name="SEF")
    set_up = _upload_count(set_b)
    sef_up = _upload_count(sef_b)
    est = authoritative_criterion_a_estimated_points(out)

    if est is not None:
        criterion_status = "complete"
        criterion_label = "Estimated Criterion A (SET + SEF)"
        criterion_explanation = (
            "Teaching Effectiveness points = SET component + SEF component per published JC 01 rules."
        )
    elif set_up > 0 and sef_up == 0:
        criterion_status = "incomplete_awaiting_sef"
        criterion_label = "Incomplete — awaiting SEF"
        criterion_explanation = (
            "SET evidence is present but Criterion A requires both SET and SEF component scores. "
            "Upload and extract eligible SEF evaluations to compute the combined estimate."
        )
    elif sef_up > 0 and set_up == 0:
        criterion_status = "incomplete_awaiting_set"
        criterion_label = "Incomplete — awaiting SET"
        criterion_explanation = (
            "SEF evidence is present but Criterion A requires both SET and SEF component scores."
        )
    elif set_up > 0 or sef_up > 0:
        criterion_status = "incomplete_not_computable"
        criterion_label = "Incomplete — not yet computable"
        parts = []
        if set_display.get("state") == "not_computable" and set_display.get("explanation"):
            parts.append(f"SET: {set_display['explanation']}")
        if sef_display.get("state") in ("not_computable", "awaiting_evidence") and sef_display.get("explanation"):
            parts.append(f"SEF: {sef_display['explanation']}")
        elif sef_display.get("state") == "awaiting_evidence":
            parts.append("SEF: awaiting eligible evidence.")
        criterion_explanation = " ".join(parts) if parts else (
            "Both SET and SEF need eligible semester coverage before Criterion A can be estimated."
        )
    else:
        criterion_status = "not_assessed"
        criterion_label = "Not yet assessed"
        criterion_explanation = "Upload SET and SEF evaluation PDFs to begin."

    out["estimatedPoints"] = est
    out["criterionADisplay"] = {
        "estimatedPoints": est,
        "status": criterion_status,
        "displayLabel": criterion_label,
        "explanation": criterion_explanation,
        "set": set_display,
        "sef": sef_display,
    }
    if isinstance(out.get("set"), dict):
        out["set"] = {**out["set"], "componentDisplay": set_display}
    if isinstance(out.get("sef"), dict):
        out["sef"] = {**out["sef"], "componentDisplay": sef_display}
    return out


def enrich_indicator_aggregate_block(block: dict[str, Any], *, full_name: str, short_name: str) -> dict[str, Any]:
    out = dict(block)
    out["componentDisplay"] = component_display(out, full_name=full_name, short_name=short_name)
    return out
