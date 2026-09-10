"""Lesson metadata and explicit practice progress, never execution semantics."""

from __future__ import annotations

from ..example_catalog import ExampleError, load_manifest
from .catalog import CONCEPTS
from .concepts import concept_payload
from .profile import (
    LearningProfile,
    load_profile_state,
    mode_for_concepts,
    update_concepts,
)


def lessons(profile: LearningProfile) -> list[dict]:
    entries = {entry["concept"]: entry for entry in load_manifest()["examples"] if entry["concept"]}
    result = []
    for concept, knowledge in CONCEPTS.items():
        if concept in entries:
            entry = entries[concept]
            result.append({"concept": concept, "title": knowledge.title, "example": entry["name"],
                           "runtime": entry["runtime"], "familiarity": (profile.concepts or {}).get(concept, "new")})
    return result


def lesson(topic: str, profile: LearningProfile, *, mode: str | None = None) -> dict:
    for item in lessons(profile):
        if item["concept"] == topic:
            selected_mode = mode_for_concepts(profile, [topic], explicit_mode=mode)
            return {**item, "explanation": concept_payload(topic, mode=selected_mode, style=profile.explanation_style),
                    "practice_command": f"sona learn run {topic}",
                    "progress_rule": "A passed practice check records learning, not mastery. Comfortable is preserved."}
    raise ExampleError("SONA-EXAMPLE-001", "The lesson topic is unknown.", "Run `sona learn` for available topics.")


def record_practice(project_root: str, topic: str) -> dict:
    state = load_profile_state(project_root)
    lesson(topic, state.profile)
    if (state.profile.concepts or {}).get(topic) == "comfortable":
        return state.to_dict()
    return update_concepts(project_root, [topic], familiarity="learning").to_dict()
