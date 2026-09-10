"""Deterministic Sona Guide explanations, independent of optional AI providers."""

from .cascade import focus_diagnostics, render_focus_text
from .explain import explain
from .fixes import (
    apply_fixes,
    concepts_for_fixes,
    explain_with_fixes,
    preview_diagnostic_fixes,
    preview_stdlib_api_migration,
)
from .models import (
    DiagnosticRelation,
    FocusResult,
    GuideError,
    GuideFix,
    GuideRequest,
    GuideResponse,
    SourceEdit,
)
from .profile import (
    FAMILIARITY_VALUES,
    LearningProfile,
    ProfileState,
    default_profile,
    load_profile_state,
    mode_for_concepts,
    render_profile_text,
    reset_profile,
    save_profile,
    set_preferences,
    update_concepts,
)
from .render import render_text

__all__ = [
    "FAMILIARITY_VALUES",
    "DiagnosticRelation",
    "FocusResult",
    "GuideError",
    "GuideFix",
    "GuideRequest",
    "GuideResponse",
    "LearningProfile",
    "ProfileState",
    "SourceEdit",
    "apply_fixes",
    "concepts_for_fixes",
    "default_profile",
    "explain",
    "explain_with_fixes",
    "focus_diagnostics",
    "load_profile_state",
    "mode_for_concepts",
    "preview_diagnostic_fixes",
    "preview_stdlib_api_migration",
    "render_focus_text",
    "render_profile_text",
    "render_text",
    "reset_profile",
    "save_profile",
    "set_preferences",
    "update_concepts",
]
