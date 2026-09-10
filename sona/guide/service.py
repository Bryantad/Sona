"""Bounded read-only Guide requests shared by CLI and editor transports."""

from __future__ import annotations

import json

from .adapters import diagnostic_from_payload
from .cascade import focus_diagnostics, render_focus_text
from .catalog import CATALOG, CONCEPTS
from .concepts import concept_payload, selection_concepts
from .explain import explain
from .fixes import explain_with_fixes
from .models import DENSITIES, MODES, STYLES, GuideError, GuideRequest
from .profile import LearningProfile, default_profile, mode_for_concepts
from .render import render_text

MAX_REQUEST_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 256 * 1024


def unavailable(error: GuideError) -> dict:
    return {"schema_version": 1, "status": "unavailable", "diagnostic": error.to_dict()}


def _invalid() -> GuideError:
    return GuideError(
        "SONA-GUIDE-002", "The Guide request is invalid or exceeds its size limit.",
        "Use a schema-1 diagnostic, selection, focus, or concept request with documented fields.",
    )


def request_json(raw: str, *, profile: LearningProfile | None = None) -> dict:
    try:
        if len(raw.encode("utf-8")) > MAX_REQUEST_BYTES:
            raise _invalid()

        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise _invalid()
                result[key] = value
            return result

        payload = json.loads(raw, object_pairs_hook=unique_pairs)
    except GuideError as exc:
        return unavailable(exc)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return unavailable(_invalid())
    return guide_request(payload, profile=profile)


def guide_request(payload, *, profile: LearningProfile | None = None) -> dict:
    try:
        if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
            raise _invalid()
        if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > MAX_REQUEST_BYTES:
            raise _invalid()
        if set(payload) - {"schema_version", "action", "diagnostic", "diagnostic_id", "source", "document", "selection", "options", "diagnostics", "concept_id"}:
            raise _invalid()
        options = payload.get("options", {})
        if not isinstance(options, dict) or set(options) - {"mode", "style", "density", "quiet"}:
            raise _invalid()
        for key, choices in (("mode", MODES), ("style", STYLES), ("density", DENSITIES)):
            if key in options and options[key] not in choices:
                raise _invalid()
        if "quiet" in options and type(options["quiet"]) is not bool:
            raise _invalid()
        profile = profile or default_profile()
        style = options.get("style", profile.explanation_style)
        density = options.get("density", profile.diagnostic_density)
        quiet = options.get("quiet", profile.quiet)
        source = payload.get("source")
        if source is not None and (not isinstance(source, str) or len(source.encode("utf-8")) > MAX_SOURCE_BYTES):
            raise _invalid()
        document = payload.get("document", "<editor>")
        if not isinstance(document, str) or not document or len(document) > 4096:
            raise _invalid()
        action = payload.get("action")
        if action == "diagnostic":
            item = diagnostic_from_payload(payload["diagnostic"], document) if "diagnostic" in payload else None
            identifier = item.diagnostic_id if item else payload.get("diagnostic_id", "")
            entry = CATALOG.get(identifier)
            mode = mode_for_concepts(profile, entry.concepts if entry else (), explicit_mode=options.get("mode"))
            request = GuideRequest(identifier, item, mode=mode, style=style, density=density)
            response = explain_with_fixes(request, source, document=document) if source is not None else explain(request)
            return {**response.to_dict(), "text": render_text(response)}
        if action == "concept":
            identifier = payload.get("concept_id")
            if identifier not in CONCEPTS:
                raise _invalid()
            mode = mode_for_concepts(profile, (identifier,), explicit_mode=options.get("mode"))
            concept = concept_payload(identifier, mode=mode, style=style)
            return {"schema_version": 1, "status": "explained", "mode": mode, "concept": concept, "text": concept["text"]}
        if action not in {"selection", "focus"}:
            raise _invalid()
        if action == "focus" and "diagnostics" in payload:
            if not isinstance(payload["diagnostics"], list) or len(payload["diagnostics"]) > 1000:
                raise _invalid()
            diagnostics = tuple(diagnostic_from_payload(item, document) for item in payload["diagnostics"])
        else:
            if source is None:
                raise _invalid()
            from sona.developer_intelligence.frontend import analyze_frontend
            diagnostics = analyze_frontend(source, file=document)
        focus = focus_diagnostics(diagnostics, density=density, quiet=quiet)
        if action == "focus":
            return {**focus.to_dict(), "text": render_focus_text(focus)}
        identifiers = ()
        if not any(item.severity == "error" for item in diagnostics):
            identifiers = selection_concepts(source, payload.get("selection"))
        mode = mode_for_concepts(profile, identifiers, explicit_mode=options.get("mode"))
        concepts = [concept_payload(item, mode=mode, style=style) for item in identifiers]
        text = "Sona Guide - Selection\n\nStatic explanation; no program was executed."
        if concepts:
            text += "\n\n" + "\n\n".join(item["title"] + "\n" + item["text"] for item in concepts)
        else:
            text += "\n\nNo reviewed concept explanation is available for this selection."
        if diagnostics:
            text += "\n\n" + render_focus_text(focus)
        return {
            "schema_version": 1, "status": "explained", "basis": "static-selection",
            "mode": mode, "style": style, "concepts": concepts, "focus": focus.to_dict(), "text": text,
        }
    except GuideError as exc:
        return unavailable(exc)
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return unavailable(_invalid())
