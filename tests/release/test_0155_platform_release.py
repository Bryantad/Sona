from __future__ import annotations

from pathlib import Path

import pytest

from tools.release import platform_release_0155 as release

ROOT = Path(__file__).resolve().parents[2]


def test_0155_platform_release_contract_uses_current_artifact_names() -> None:
    assert release.VERSION == "0.15.5"
    assert "sona-native-0.15.5-windows-x86_64.zip" in release.NATIVE_ASSETS
    assert "sona-native-0.15.5-linux-x86_64-musl.tar.gz" in release.NATIVE_ASSETS
    assert "sona-native-0.15.5-linux-aarch64-musl.tar.gz" in release.NATIVE_ASSETS
    assert "sona-native-0.15.5-macos-x86_64.tar.gz" in release.NATIVE_ASSETS
    assert "sona-native-0.15.5-macos-aarch64.tar.gz" in release.NATIVE_ASSETS


def test_host_default_target_avoids_redundant_explicit_target_directory() -> None:
    windows = release.NATIVE_SPECS[("windows", "x86_64")]
    linux_musl = release.NATIVE_SPECS[("linux", "x86_64")]

    assert release._rustc_host_target(
        "rustc 1.94.0\nhost: x86_64-pc-windows-msvc\n"
    ) == "x86_64-pc-windows-msvc"
    assert release._cargo_target_arguments(
        windows,
        "x86_64-pc-windows-msvc",
    ) == []
    assert release._cargo_target_arguments(
        linux_musl,
        "x86_64-unknown-linux-gnu",
    ) == ["--target", "x86_64-unknown-linux-musl"]


def test_dirty_local_build_omits_optional_source_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(release, "_git", lambda *args: " M sona/proof.py")

    assert release._source_revision_for_build() is None


def test_github_build_embeds_validated_source_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    commit = "a" * 40
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SHA", commit.upper())

    assert release._source_revision_for_build() == commit


def test_invalid_configured_source_revision_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_SHA", "not-a-commit")

    with pytest.raises(RuntimeError, match="complete 40-character Git SHA"):
        release._source_commit()


def test_0155_workflow_uses_matching_tool_and_host_matrix() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "release-platforms-0155.yml"
    ).read_text(encoding="utf-8")

    assert "Sona 0.15.5 cross-platform release candidates" in workflow
    assert "tools/release/platform_release_0155.py" in workflow
    assert "sona-ai-native-programming-0.15.5.vsix" in workflow
    for fragment in (
        "windows-2025",
        "ubuntu-24.04",
        "ubuntu-24.04-arm",
        "macos-15-intel",
        "macos-15",
        "x86_64-unknown-linux-musl",
        "aarch64-unknown-linux-musl",
        "x86_64-apple-darwin",
        "aarch64-apple-darwin",
        "aarch64-linux-android",
        "aarch64-apple-ios",
        "platform_release_0155.py verify",
    ):
        assert fragment in workflow
    assert "contents: read" in workflow
    assert "continue-on-error: true" in workflow
    assert "needs: [portable, native, desktop-verify]" in workflow
    assert "needs: [portable, native, desktop-verify, mobile-compile]" not in workflow
    assert "contents: write" not in workflow
    assert "gh release" not in workflow
    assert "softprops/action-gh-release" not in workflow
