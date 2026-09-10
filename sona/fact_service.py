"""Read-only fact acquisition outside the pure Guide presentation package."""

from __future__ import annotations

import json

from .guide.facts import explain_facts
from .guide.models import GuideError, GuideRequest
from .guide.profile import default_profile, load_profile_state, mode_for_concepts


def explain_checked_facts(kind, *, receipt=None, project_root=".", mode=None, style=None, no_profile=False):
    # No transport accepts a caller-asserted verification result.
    if kind == "proof":
        from .proof import inspect_receipt
        facts = inspect_receipt(receipt)
        concept = "proof-mode"
    elif kind == "guardian":
        from .developer_intelligence.redaction import redact
        from .stdlib.native_guardian import guardian_check
        facts = redact(guardian_check(project_root))
        concept = "guardian"
    else:
        raise GuideError("SONA-GUIDE-002", "Unknown fact provider.", "Use proof or guardian.")
    profile_diagnostic = None
    try:
        profile = default_profile() if no_profile else load_profile_state(project_root).profile
    except GuideError as error:
        # Preferences must never erase an already-produced verifier/check result.
        profile = default_profile()
        profile_diagnostic = error.to_dict()
    response = explain_facts(GuideRequest(
        fact_kind=kind, facts=facts, mode=mode_for_concepts(profile, (concept,), explicit_mode=mode),
        style=style or profile.explanation_style, density=profile.diagnostic_density,
    ))
    response["profile_diagnostic"] = profile_diagnostic
    if profile_diagnostic:
        response["text"] += (f"\n\nProfile unavailable; default presentation used.\n"
                             f"{profile_diagnostic['diagnostic_id']}: {profile_diagnostic['message']}\n"
                             f"  hint: {profile_diagnostic['hint']}")
    return response


def handle_fact_command(args):
    from .cli import safe_print
    try:
        result = explain_checked_facts(args.guide_cmd, receipt=getattr(args, "receipt", None),
                                       project_root=args.project_root, mode=args.mode, style=args.style,
                                       no_profile=args.no_profile)
        success = (result["facts"]["status"] == ("valid" if args.guide_cmd == "proof" else "ok")
                   and result["profile_diagnostic"] is None)
    except GuideError as error:
        result = {"schema_version": 1, "status": "unavailable", "diagnostic": error.to_dict(),
                  "text": f"{error.diagnostic_id}: {error.message}\n  hint: {error.hint}"}
        success = False
    safe_print(json.dumps(result, sort_keys=True) if args.json else result["text"])
    return 0 if success else 1
