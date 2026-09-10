"""Presentation of provider facts, not a verifier or a project-state reader.

Only the outside coordinator selects and runs the actual verifier/checker.
This pure API does not authenticate caller-supplied Python objects.
"""

from __future__ import annotations

import json
from copy import deepcopy

from .models import GuideError, GuideRequest
from .render import _terminal_text

_PROOF_LIMITS = (
    "Receipt integrity is self-consistency, not producer authentication, signatures, host integrity, or remote attestation.",
    "Effects describe recorded instrumentation only; not observed does not mean impossible.",
    "A Guardian binding in a receipt is not a checked baseline; use sona guardian proof verify for that check.",
)
_GUARDIAN_LIMITS = (
    "This is a project-local policy/state check, not execution evidence or host authentication.",
    "Capability decisions constrain supported Native operations only when that policy participates in execution.",
)


def explain_facts(request: GuideRequest) -> dict:
    if request.fact_kind not in ("proof", "guardian") or request.facts is None:
        raise GuideError("SONA-GUIDE-002", "A provider fact request is required.", "Use the verified-fact coordinator.")
    facts = deepcopy(request.facts)
    sections = []

    def section(key, title, body):
        sections.append({"key": key, "title": title, "body": body})

    try:
        if request.fact_kind == "proof":
            limits = list(_PROOF_LIMITS)
            provider = "sona.proof.inspect_receipt"
            if facts["status"] == "valid":
                execution, engine = facts["execution"], facts["engine"]
                section("what", "What the receipt records", f"Receipt integrity: VALID\nExecution: {execution['status']} (exit {execution['exit_code']})\n"
                        f"Runtime: Sona {facts['sona_version']}\nEngine: {engine['label']}\nPython required: {str(engine['python_required']).lower()}\n"
                        f"Python embedded: {str(engine['python_embedded']).lower()}\nFallback: {str(engine['fallback_used']).lower()}")
                section("program", "Recorded program", f"Kind: {facts['program']['kind']}\nSource: {facts['program']['source']['bytes']} B\n"
                        "Content identity is retained in complete facts; no source filename is inferred.")
                section("capabilities", "Recorded capabilities", "\n".join(
                    f"{name}: {'granted' if granted else 'denied'}" for name, granted in facts["capabilities"].items()))
                section("effects", "Recorded effects", "\n".join(
                    f"{effect.get('effect') or (effect['scope'] + '.' + effect['operation'])}: {effect['outcome']}"
                    + (f" ({effect['support']})" if effect.get("support") else "") for effect in facts["effects"])
                    or "No effects recorded; this is not proof that no other activity occurred.")
                section("output", "Recorded output sizes", f"stdout: {execution['stdout']['bytes']} B\nstderr: {execution['stderr']['bytes']} B")
                diagnostic = execution.get("diagnostic")
                if diagnostic:
                    section("diagnostic", "Execution diagnostic", str(diagnostic.get("id") or diagnostic.get("diagnostic_id")))
                section("next", "Next step", "Inspect the complete facts for program/runtime/output identities. Valid receipt integrity does not mean successful execution.")
            elif facts["status"] == "invalid":
                diagnostic = facts["diagnostic"]
                section("what", "Verification failed", f"{diagnostic['diagnostic_id']}: {diagnostic['message']}")
                section("next", "Next step", diagnostic["hint"])
            else:
                raise ValueError("unsupported status")
        else:
            limits = list(_GUARDIAN_LIMITS)
            provider = "sona.stdlib.native_guardian.guardian_check"
            status = facts["status"]
            section("what", "Guardian state", status)
            if facts.get("diagnostic_id"):
                section("diagnostic", "Guardian diagnostic", f"{facts['diagnostic_id']}: {facts['message']}")
                section("next", "Next step", facts.get("hint", "Review Guardian state before retrying."))
            else:
                if status not in ("ok", "drift", "uninitialized"):
                    raise ValueError("unsupported status")
                policy, proof = facts["policy"], facts["proof_mode"]
                section("policy", "Policy participation", f"Source: {policy['source']}\nBinding ready: {str(proof['ready']).lower()}\n"
                        f"Policy enforced for binding: {str(proof['policy_enforced']).lower()}")
                section("capabilities", "Policy capability decisions", "\n".join(
                    f"{item['capability']}: {item['decision']}" for item in facts["capability_decisions"]))
                if policy["legacy_baseline"]:
                    limits.append("Legacy baseline: binding readiness does not establish capability policy enforcement.")
                if policy["working_matches_trusted"] is False:
                    limits.append("Working policy differs from the trusted policy; the trusted policy remains authoritative.")
                if status == "drift":
                    limits.append("Project drift is present. Review changes before trusting the current project state.")
                section("next", "Next step", {
                    "ok": "For execution evidence, use Proof Mode with an explicit --guardian-root.",
                    "uninitialized": "Select the intended project before explicitly initializing Guardian. This explanation creates no baseline.",
                    "drift": "Review sona guardian diff. This explanation does not repair or approve changed state.",
                }[status])
    except (KeyError, TypeError, ValueError) as exc:
        raise GuideError("SONA-GUIDE-002", "The provider fact shape cannot be explained safely.",
                         "Use facts returned by the current shared verifier or Guardian checker.") from exc

    section("limits", "Assurance limits", "\n".join(limits))
    title = "Sona Guide - " + ("Proof Mode" if request.fact_kind == "proof" else "Guardian")
    visible = sections
    if request.mode == "expert":
        visible = [item for item in sections if item["key"] in {"what", "diagnostic", "limits"}]
    elif request.mode == "balanced":
        visible = [item for item in sections if item["key"] not in {"output"}]
    lines = [title]
    if request.style == "visual" and request.mode == "guided":
        lines.extend(["", "provider facts -> explanation (no change to evidence)"])
    for item in visible:
        lines.extend(["", item["title"], item["body"]])
    if request.style == "technical":
        lines.extend(["", "Complete provider facts", json.dumps(facts, indent=2, sort_keys=True)])
    return {"schema_version": 1, "status": "explained", "basis": "provider-facts", "fact_kind": request.fact_kind,
            "facts": facts, "mode": request.mode, "style": request.style, "density": request.density,
            "sections": sections, "assurance_limits": limits, "fixes": [],
            "provenance": {"source": "sona-guide-facts", "catalog_version": 1, "provider": provider},
            "text": _terminal_text("\n".join(lines))}
