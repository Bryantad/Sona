"""Project-local Sona Guide learning profile.

The profile stores explicit preferences and bounded concept familiarity only.
It never stores source text, paths, output bodies, credentials, or inferred
medical state.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .models import DENSITIES, MODES, STYLES, GuideError

PROFILE_SCHEMA = 1
PROFILE_RELATIVE_PATH = ".sona/learning.json"
MAX_PROFILE_BYTES = 16 * 1024
FAMILIARITY_VALUES = ("new", "learning", "comfortable")

_CONCEPT_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_ALLOWED_KEYS = {
    "schema",
    "guidance_mode",
    "diagnostic_density",
    "explanation_style",
    "quiet",
    "concepts",
}


@dataclass(frozen=True, slots=True)
class LearningProfile:
    schema: int = PROFILE_SCHEMA
    guidance_mode: str = "guided"
    diagnostic_density: str = "normal"
    explanation_style: str = "simple"
    quiet: bool = False
    concepts: dict[str, str] | None = None

    def __post_init__(self) -> None:
        concepts = dict(self.concepts or {})
        if (
            type(self.schema) is not int
            or self.schema != PROFILE_SCHEMA
            or self.guidance_mode not in MODES
            or self.diagnostic_density not in DENSITIES
            or self.explanation_style not in STYLES
            or not isinstance(self.quiet, bool)
            or any(not _valid_concept(key) for key in concepts)
            or any(value not in FAMILIARITY_VALUES for value in concepts.values())
        ):
            raise GuideError(
                "SONA-GUIDE-005",
                "The Sona Guide learning profile is invalid.",
                "Reset it with `sona guide profile reset` or edit only documented fields.",
            )
        object.__setattr__(self, "concepts", concepts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "guidance_mode": self.guidance_mode,
            "diagnostic_density": self.diagnostic_density,
            "explanation_style": self.explanation_style,
            "quiet": self.quiet,
            "concepts": {
                key: self.concepts[key]
                for key in sorted(self.concepts or {})
            },
        }


@dataclass(frozen=True, slots=True)
class ProfileState:
    profile: LearningProfile
    persisted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "ok",
            "profile_path": PROFILE_RELATIVE_PATH,
            "persisted": self.persisted,
            "profile": self.profile.to_dict(),
        }


def default_profile() -> LearningProfile:
    return LearningProfile()


def load_profile_state(project_root: str | Path = ".") -> ProfileState:
    root = _project_root(project_root)
    path = _profile_path(root, writing=False)
    if not path.exists():
        return ProfileState(default_profile(), persisted=False)
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_PROFILE_BYTES + 1)
        if len(raw) > MAX_PROFILE_BYTES:
            raise GuideError(
                "SONA-GUIDE-005",
                "The Sona Guide learning profile is too large.",
                "Reset it with `sona guide profile reset` or reduce it to documented fields.",
            )
        payload = json.loads(raw.decode("utf-8"))
    except GuideError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide learning profile could not be read.",
            "Reset it with `sona guide profile reset` or fix the JSON syntax.",
        ) from exc
    return ProfileState(_profile_from_payload(payload), persisted=True)


def save_profile(project_root: str | Path, profile: LearningProfile) -> ProfileState:
    root = _project_root(project_root)
    path = _profile_path(root, writing=True)
    payload = profile.to_dict()
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if len(text.encode("utf-8")) > MAX_PROFILE_BYTES:
        raise GuideError(
            "SONA-GUIDE-006",
            "The Sona Guide learning profile is too large to write.",
            "Store only documented preferences and bounded concept familiarity.",
        )
    _write_atomic(path, text)
    return ProfileState(profile, persisted=True)


def reset_profile(project_root: str | Path = ".") -> ProfileState:
    return save_profile(project_root, default_profile())


def set_preferences(
    project_root: str | Path = ".",
    *,
    guidance_mode: str | None = None,
    diagnostic_density: str | None = None,
    explanation_style: str | None = None,
    quiet: bool | None = None,
) -> ProfileState:
    state = load_profile_state(project_root)
    profile = replace(
        state.profile,
        guidance_mode=guidance_mode or state.profile.guidance_mode,
        diagnostic_density=diagnostic_density or state.profile.diagnostic_density,
        explanation_style=explanation_style or state.profile.explanation_style,
        quiet=state.profile.quiet if quiet is None else quiet,
    )
    return save_profile(project_root, profile)


def update_concepts(
    project_root: str | Path,
    concepts: list[str] | tuple[str, ...],
    *,
    familiarity: str = "learning",
) -> ProfileState:
    if familiarity not in FAMILIARITY_VALUES:
        raise GuideError(
            "SONA-GUIDE-005",
            "The concept familiarity value is invalid.",
            "Use new, learning, or comfortable.",
        )
    normalized = tuple(dict.fromkeys(str(concept) for concept in concepts))
    if not normalized or any(not _valid_concept(concept) for concept in normalized):
        raise GuideError(
            "SONA-GUIDE-005",
            "The concept identifier is invalid.",
            "Use lowercase concept identifiers such as variables or proof-mode.",
        )
    state = load_profile_state(project_root)
    updated = dict(state.profile.concepts or {})
    for concept in normalized:
        updated[concept] = familiarity
    profile = replace(state.profile, concepts=updated)
    return save_profile(project_root, profile)


def mode_for_concepts(
    profile: LearningProfile,
    concepts: tuple[str, ...] | list[str],
    *,
    explicit_mode: str | None = None,
) -> str:
    if explicit_mode:
        if explicit_mode not in MODES:
            raise GuideError(
                "SONA-GUIDE-002",
                "The Guide mode is invalid.",
                "Use guided, balanced, or expert.",
            )
        return explicit_mode
    base = profile.guidance_mode
    if (
        base == "guided"
        and concepts
        and all((profile.concepts or {}).get(concept) == "comfortable" for concept in concepts)
    ):
        return "balanced"
    return base


def render_profile_text(state: ProfileState) -> str:
    profile = state.profile
    lines = [
        "Sona Guide Profile",
        "",
        f"Status       {'PERSISTED' if state.persisted else 'DEFAULT'}",
        f"Path         {PROFILE_RELATIVE_PATH}",
        f"Guidance     {profile.guidance_mode}",
        f"Density      {profile.diagnostic_density}",
        f"Style        {profile.explanation_style}",
        f"Quiet        {str(profile.quiet).lower()}",
    ]
    concepts = profile.concepts or {}
    if concepts:
        lines.extend(("", "Concepts"))
        for concept in sorted(concepts):
            lines.append(f"  {concept:<16} {concepts[concept]}")
    else:
        lines.extend(("", "Concepts     none recorded"))
    return "\n".join(lines)


def _profile_from_payload(payload: Any) -> LearningProfile:
    if not isinstance(payload, dict):
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide learning profile must be a JSON object.",
            "Reset it with `sona guide profile reset` or edit only documented fields.",
        )
    if set(payload) - _ALLOWED_KEYS:
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide learning profile contains unsupported fields.",
            "Remove unsupported fields; the profile must not store source, paths, output, or credentials.",
        )
    concepts = payload.get("concepts", {})
    if not isinstance(concepts, dict):
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide concept familiarity map is invalid.",
            "Use an object mapping concept identifiers to new, learning, or comfortable.",
        )
    try:
        return LearningProfile(
            schema=payload.get("schema", 0),
            guidance_mode=str(payload.get("guidance_mode", "")),
            diagnostic_density=str(payload.get("diagnostic_density", "")),
            explanation_style=str(payload.get("explanation_style", "")),
            quiet=payload.get("quiet"),
            concepts={str(key): str(value) for key, value in concepts.items()},
        )
    except (TypeError, ValueError) as exc:
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide learning profile contains invalid field values.",
            "Reset it with `sona guide profile reset` or edit only documented fields.",
        ) from exc


def _project_root(project_root: str | Path) -> Path:
    try:
        root = Path(project_root).resolve(strict=True)
    except OSError as exc:
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide project root is unavailable.",
            "Choose an existing project directory.",
        ) from exc
    if not root.is_dir():
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide project root is not a directory.",
            "Choose an existing project directory.",
        )
    return root


def _profile_path(root: Path, *, writing: bool) -> Path:
    sona_dir = root / ".sona"
    if sona_dir.exists():
        _assert_inside(root, sona_dir)
        if not sona_dir.is_dir():
            raise GuideError(
                "SONA-GUIDE-006" if writing else "SONA-GUIDE-005",
                "The Sona Guide state location is not a directory.",
                "Review `.sona` before storing a learning profile.",
            )
    elif writing:
        try:
            sona_dir.mkdir(mode=0o700)
        except OSError as exc:
            raise GuideError(
                "SONA-GUIDE-006",
                "The Sona Guide state directory could not be created.",
                "Check project permissions and `.sona` state.",
            ) from exc
    else:
        return sona_dir / "learning.json"
    path = sona_dir / "learning.json"
    if path.exists():
        _assert_inside(root, path)
    return path


def _assert_inside(root: Path, path: Path) -> None:
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GuideError(
            "SONA-GUIDE-005",
            "The Sona Guide state path could not be resolved.",
            "Check project permissions and the .sona state path.",
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GuideError(
            "SONA-GUIDE-006",
            "The Sona Guide state path leaves the selected project.",
            "Review `.sona`; learning profile writes are confined to the project root.",
        ) from exc


def _write_atomic(path: Path, text: str) -> None:
    directory = path.parent
    for counter in range(100):
        temporary = directory / f".learning.json.{os.getpid()}.{counter}.tmp"
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        except OSError as exc:
            raise GuideError(
                "SONA-GUIDE-006",
                "The Sona Guide learning profile could not be written.",
                "Check project permissions and `.sona` state.",
            ) from exc
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            os.replace(temporary, path)
            return
        except OSError as exc:
            raise GuideError(
                "SONA-GUIDE-006",
                "The Sona Guide learning profile could not be written atomically.",
                "Check project permissions and `.sona` state.",
            ) from exc
        finally:
            try:
                if temporary.exists():
                    temporary.unlink()
            except OSError:
                pass
    raise GuideError(
        "SONA-GUIDE-006",
        "The Sona Guide learning profile temporary file could not be reserved.",
        "Retry after checking project-local `.sona` state.",
    )


def _valid_concept(value: str) -> bool:
    return isinstance(value, str) and bool(_CONCEPT_RE.fullmatch(value))
