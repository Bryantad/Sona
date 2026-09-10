from __future__ import annotations

import json

import pytest

from sona.guide import (
    GuideError,
    LearningProfile,
    default_profile,
    load_profile_state,
    mode_for_concepts,
    reset_profile,
    save_profile,
    set_preferences,
    update_concepts,
)
from sona.guide.profile import MAX_PROFILE_BYTES


def test_missing_profile_uses_defaults_without_creating_project_state(tmp_path):
    state = load_profile_state(tmp_path)

    assert state.persisted is False
    assert state.profile == default_profile()
    assert not (tmp_path / ".sona").exists()


def test_save_profile_writes_deterministic_bounded_json_without_sensitive_fields(tmp_path):
    profile = LearningProfile(
        guidance_mode="balanced",
        diagnostic_density="focused",
        explanation_style="technical",
        quiet=True,
        concepts={"scope": "comfortable", "variables": "learning"},
    )

    state = save_profile(tmp_path, profile)

    path = tmp_path / ".sona" / "learning.json"
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert state.persisted is True
    assert text.endswith("\n")
    assert list(payload) == sorted(payload)
    assert list(payload["concepts"]) == ["scope", "variables"]
    assert set(payload) == {
        "schema",
        "guidance_mode",
        "diagnostic_density",
        "explanation_style",
        "quiet",
        "concepts",
    }
    assert "cart.sona" not in text
    assert "source" not in text
    assert "credential" not in text
    assert load_profile_state(tmp_path).profile.to_dict() == profile.to_dict()


def test_invalid_corrupt_and_oversized_profiles_fail_safely(tmp_path):
    path = tmp_path / ".sona" / "learning.json"
    path.parent.mkdir()
    path.write_text("{this is not json", encoding="utf-8")

    with pytest.raises(GuideError) as corrupt:
        load_profile_state(tmp_path)
    assert corrupt.value.diagnostic_id == "SONA-GUIDE-005"
    assert "this is not json" not in corrupt.value.message

    path.write_text(
        json.dumps({
            "schema": "schema-one",
            "guidance_mode": "guided",
            "diagnostic_density": "normal",
            "explanation_style": "simple",
            "quiet": False,
            "concepts": {},
        }),
        encoding="utf-8",
    )
    with pytest.raises(GuideError) as invalid:
        load_profile_state(tmp_path)
    assert invalid.value.diagnostic_id == "SONA-GUIDE-005"

    path.write_text(" " * (MAX_PROFILE_BYTES + 1), encoding="utf-8")
    with pytest.raises(GuideError) as oversized:
        load_profile_state(tmp_path)
    assert oversized.value.diagnostic_id == "SONA-GUIDE-005"


def test_reset_profile_recovers_from_corrupt_local_json(tmp_path):
    path = tmp_path / ".sona" / "learning.json"
    path.parent.mkdir()
    path.write_text("{", encoding="utf-8")

    state = reset_profile(tmp_path)

    assert state.persisted is True
    assert load_profile_state(tmp_path).profile.to_dict() == default_profile().to_dict()


def test_set_preferences_and_update_concepts_validate_contracts(tmp_path):
    state = set_preferences(
        tmp_path,
        guidance_mode="expert",
        diagnostic_density="complete",
        explanation_style="technical",
        quiet=True,
    )
    assert state.profile.guidance_mode == "expert"
    assert state.profile.diagnostic_density == "complete"
    assert state.profile.explanation_style == "technical"
    assert state.profile.quiet is True

    learned = update_concepts(
        tmp_path,
        ("scope", "variables", "scope"),
        familiarity="comfortable",
    )
    assert learned.profile.to_dict()["concepts"] == {
        "scope": "comfortable",
        "variables": "comfortable",
    }

    with pytest.raises(GuideError) as bad_mode:
        set_preferences(tmp_path, guidance_mode="teach-me-like-a-wizard")
    assert bad_mode.value.diagnostic_id == "SONA-GUIDE-005"

    with pytest.raises(GuideError) as bad_concept:
        update_concepts(tmp_path, ("Variables",), familiarity="learning")
    assert bad_concept.value.diagnostic_id == "SONA-GUIDE-005"

    with pytest.raises(GuideError) as bad_familiarity:
        update_concepts(tmp_path, ("variables",), familiarity="mastered")
    assert bad_familiarity.value.diagnostic_id == "SONA-GUIDE-005"


def test_profile_write_refuses_non_directory_sona_state(tmp_path):
    (tmp_path / ".sona").write_text("not a directory", encoding="utf-8")

    with pytest.raises(GuideError) as caught:
        save_profile(tmp_path, default_profile())

    assert caught.value.diagnostic_id == "SONA-GUIDE-006"
    assert not (tmp_path / "learning.json").exists()


def test_guided_profile_decays_to_balanced_only_for_comfortable_related_concepts():
    profile = LearningProfile(
        guidance_mode="guided",
        concepts={"variables": "comfortable", "scope": "comfortable"},
    )

    assert mode_for_concepts(profile, ("variables", "scope")) == "balanced"
    assert mode_for_concepts(profile, ("variables", "modules")) == "guided"
    assert mode_for_concepts(profile, ("variables", "scope"), explicit_mode="expert") == "expert"
    assert mode_for_concepts(LearningProfile(guidance_mode="balanced"), ("variables",)) == "balanced"


@pytest.mark.parametrize("schema", [True, 1.0, 1.5, "1", None])
def test_profile_schema_is_an_exact_integer(tmp_path, schema):
    path = tmp_path / ".sona" / "learning.json"
    path.parent.mkdir()
    path.write_text(json.dumps({**default_profile().to_dict(), "schema": schema}), encoding="utf-8")
    with pytest.raises(GuideError) as caught:
        load_profile_state(tmp_path)
    assert caught.value.diagnostic_id == "SONA-GUIDE-005"


def test_profile_path_resolution_errors_are_sanitized(tmp_path, monkeypatch):
    from pathlib import Path

    save_profile(tmp_path, default_profile())
    original = Path.resolve

    def inaccessible(path, *args, **kwargs):
        if path.name == ".sona":
            raise PermissionError("secret-path-and-host-error")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", inaccessible)
    with pytest.raises(GuideError) as caught:
        load_profile_state(tmp_path)
    assert caught.value.diagnostic_id == "SONA-GUIDE-005"
    assert "secret" not in json.dumps(caught.value.to_dict())
