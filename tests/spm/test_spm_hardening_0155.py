from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sona import spm_core
from sona.spm import (
    SpmError,
    add_dependency,
    init_project,
    install,
    lock,
    verify_lock,
)

ROOT = Path(__file__).resolve().parents[2]


def _manifest(project: Path) -> dict:
    return json.loads((project / "sona.json").read_text(encoding="utf-8"))


def _write_manifest(project: Path, payload: dict) -> None:
    (project / "sona.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _project(tmp_path: Path, name: str = "app") -> Path:
    project = tmp_path / name
    project.mkdir()
    init_project(project, name="app")
    return project


def _directory_dependency(tmp_path: Path, name: str = "dependency") -> Path:
    dependency = tmp_path / name
    dependency.mkdir()
    (dependency / "__init__.smod").write_text(
        "func answer() { return 42; }\n",
        encoding="utf-8",
    )
    return dependency


def test_manifest_and_lock_output_are_deterministic(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    first_manifest = (project / "sona.json").read_bytes()
    assert first_manifest == init_project(project, name="app").read_bytes()

    add_dependency(project, "local.dep", str(dependency))
    first_lock = lock(project)
    first_bytes = (project / "sona.lock.json").read_bytes()
    second_lock = lock(project)
    second_bytes = (project / "sona.lock.json").read_bytes()

    assert first_lock == second_lock
    assert first_bytes == second_bytes
    assert first_lock["schema"] == 2
    assert first_lock["integrityAlgorithm"] == "sha256-tree-v2"
    assert "lockedAt" not in first_lock
    assert "installedAt" not in first_bytes.decode("utf-8")
    assert first_bytes.endswith(b"\n")


def test_local_sibling_directory_install_is_staged_locked_and_verified(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    add_dependency(project, "local.dep", str(dependency))

    result = install(project)
    verification = verify_lock(project)

    assert result["installed"] == ["local.dep"]
    assert result["lockSchema"] == 2
    assert (project / ".sona_modules/local/dep/__init__.smod").is_file()
    assert verification["ok"] == ["local.dep"]
    assert verification["mismatched"] == []
    assert verification["missing"] == []
    assert verification["manifestMismatched"] == []


def test_single_smod_and_non_smod_file_install_shapes_verify(tmp_path):
    project = _project(tmp_path)
    module = tmp_path / "single.smod"
    module.write_text("func single() { return 1; }\n", encoding="utf-8")
    data = tmp_path / "notes.txt"
    data.write_text("local package data\n", encoding="utf-8")
    add_dependency(project, "single", str(module))
    add_dependency(project, "assets.notes", str(data))

    install(project)
    verification = verify_lock(project)

    assert (project / ".sona_modules/single.smod").read_bytes() == module.read_bytes()
    assert (project / ".sona_modules/assets/notes/notes.txt").read_bytes() == data.read_bytes()
    assert verification["ok"] == ["assets.notes", "single"]


@pytest.mark.parametrize(
    "modules_dir",
    ["../outside", "nested/../../outside", "C:\\outside", "/outside"],
)
def test_modules_directory_escape_is_rejected_without_outside_writes(tmp_path, modules_dir):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    manifest = _manifest(project)
    manifest["dependencies"]["safe"] = {"path": str(dependency), "version": "*"}
    manifest["spm"]["modulesDir"] = modules_dir
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code in {"SPM-PATH-002", "SPM-PATH-003"}
    assert not (tmp_path / "outside").exists()
    assert not list(project.glob(".spm-stage-*"))


@pytest.mark.parametrize(
    "name",
    ["../escape", "..", "bad/name", "bad\\name", "a..b", ".hidden"],
)
def test_dependency_name_traversal_is_rejected(name, tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    manifest = _manifest(project)
    manifest["dependencies"][name] = {"path": str(dependency), "version": "*"}
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-MANIFEST-003"
    assert not (tmp_path / "escape").exists()


def test_overlapping_dependency_targets_are_rejected_before_staging(tmp_path):
    project = _project(tmp_path)
    first = _directory_dependency(tmp_path, "first")
    second = _directory_dependency(tmp_path, "second")
    manifest = _manifest(project)
    manifest["dependencies"] = {
        "package": {"path": str(first), "version": "*"},
        "package.child": {"path": str(second), "version": "*"},
    }
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-MANIFEST-008"
    assert not (project / ".sona_modules").exists()


def test_declared_integrity_mismatch_preserves_existing_state(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    modules = project / ".sona_modules"
    modules.mkdir()
    marker = modules / "existing.txt"
    marker.write_text("keep me\n", encoding="utf-8")
    old_lock = project / "sona.lock.json"
    old_lock.write_text("old lock\n", encoding="utf-8")
    manifest = _manifest(project)
    manifest["dependencies"]["local"] = {
        "path": str(dependency),
        "version": "*",
        "integrity": f"sha256-{'0' * 64}",
    }
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-INTEGRITY-001"
    assert marker.read_text(encoding="utf-8") == "keep me\n"
    assert old_lock.read_text(encoding="utf-8") == "old lock\n"
    assert not list(project.glob(".spm-*"))


def test_commit_failure_rolls_back_modules_and_lock(tmp_path, monkeypatch):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    add_dependency(project, "replacement", str(dependency))
    modules = project / ".sona_modules"
    modules.mkdir()
    marker = modules / "existing.txt"
    marker.write_text("previous modules\n", encoding="utf-8")
    lock_path = project / "sona.lock.json"
    lock_path.write_text("previous lock\n", encoding="utf-8")
    original_replace = spm_core.os.replace

    def fail_lock_commit(source, destination):
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            destination_path == lock_path
            and source_path.name == "sona.lock.json"
            and source_path.parent.name.startswith(".spm-stage-")
        ):
            raise OSError("injected commit failure")
        return original_replace(source, destination)

    monkeypatch.setattr(spm_core.os, "replace", fail_lock_commit)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-INSTALL-004"
    assert "restored" in str(raised.value)
    assert marker.read_text(encoding="utf-8") == "previous modules\n"
    assert lock_path.read_text(encoding="utf-8") == "previous lock\n"
    assert not (modules / "replacement").exists()
    assert not list(project.glob(".spm-stage-*"))
    assert not list(project.glob(".spm-*-backup-*"))


def test_tampered_installed_package_fails_verification(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    add_dependency(project, "local", str(dependency))
    install(project)
    installed = project / ".sona_modules/local/__init__.smod"
    installed.write_text("tampered\n", encoding="utf-8")

    result = verify_lock(project)

    assert result["ok"] == []
    assert result["mismatched"][0]["name"] == "local"


def test_manifest_change_after_install_is_reported_read_only(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    add_dependency(project, "local", str(dependency))
    install(project)
    manifest = _manifest(project)
    manifest["dependencies"]["new_dependency"] = {
        "path": str(dependency),
        "version": "*",
    }
    _write_manifest(project, manifest)
    before = (project / "sona.lock.json").read_bytes()

    result = verify_lock(project)

    assert result["manifestMismatched"] == ["new_dependency"]
    assert (project / "sona.lock.json").read_bytes() == before


def test_malformed_lock_fails_instead_of_becoming_empty(tmp_path):
    project = _project(tmp_path)
    (project / "sona.lock.json").write_text("not-json", encoding="utf-8")

    with pytest.raises(SpmError) as raised:
        verify_lock(project)

    assert raised.value.code == "SPM-STATE-002"


def test_legacy_schema1_lock_remains_verifiable(tmp_path):
    project = _project(tmp_path)
    installed = project / ".sona_modules/legacy.smod"
    installed.parent.mkdir()
    installed.write_text("func legacy() { return true; }\n", encoding="utf-8")
    legacy_lock = {
        "schema": 1,
        "lockedAt": "2025-01-01T00:00:00Z",
        "packages": {
            "legacy": {
                "version": "*",
                "path": "../legacy.smod",
                "integrity": spm_core._compute_integrity_v1(installed),
            }
        },
    }
    (project / "sona.lock.json").write_text(
        json.dumps(legacy_lock),
        encoding="utf-8",
    )

    result = verify_lock(project)

    assert result["schema"] == 1
    assert result["ok"] == ["legacy"]
    assert result["integrityAlgorithm"] == "legacy-schema-1"


def _symlink_or_skip(target: Path, link: Path, *, directory: bool = False) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")


def test_symlink_dependency_source_is_rejected(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    link = tmp_path / "dependency-link"
    _symlink_or_skip(dependency, link, directory=True)
    manifest = _manifest(project)
    manifest["dependencies"]["linked"] = {"path": str(link), "version": "*"}
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-PATH-004"


def test_symlink_source_guard_fails_before_resolution(tmp_path, monkeypatch):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    manifest = _manifest(project)
    manifest["dependencies"]["linked"] = {
        "path": str(dependency),
        "version": "*",
    }
    _write_manifest(project, manifest)
    original = spm_core._has_symlink_component

    def report_dependency_as_symlink(path):
        return Path(path) == dependency or original(path)

    monkeypatch.setattr(spm_core, "_has_symlink_component", report_dependency_as_symlink)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-PATH-004"
    assert not (project / ".sona_modules").exists()


def test_symlink_inside_dependency_tree_is_rejected(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    outside = tmp_path / "private.txt"
    outside.write_text("private\n", encoding="utf-8")
    _symlink_or_skip(outside, dependency / "escape.txt")
    manifest = _manifest(project)
    manifest["dependencies"]["linked"] = {
        "path": str(dependency),
        "version": "*",
    }
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-PATH-004"
    assert not (project / ".sona_modules").exists()


def test_modules_directory_symlink_is_rejected(tmp_path):
    project = _project(tmp_path)
    dependency = _directory_dependency(tmp_path)
    outside = tmp_path / "outside-modules"
    outside.mkdir()
    _symlink_or_skip(outside, project / ".sona_modules", directory=True)
    manifest = _manifest(project)
    manifest["dependencies"]["local"] = {
        "path": str(dependency),
        "version": "*",
    }
    _write_manifest(project, manifest)

    with pytest.raises(SpmError) as raised:
        install(project)

    assert raised.value.code == "SPM-PATH-004"
    assert list(outside.iterdir()) == []


def test_cli_failure_is_sanitized_and_has_no_traceback(tmp_path):
    project = _project(tmp_path)
    (project / "sona.json").write_text("{ private host detail", encoding="utf-8")
    process = subprocess.run(
        [sys.executable, "-m", "sona.spm", "--root", str(project), "install"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert process.returncode == 1
    assert "SPM-STATE-002" in process.stdout
    assert "private host detail" not in process.stdout
    assert "Traceback" not in process.stdout + process.stderr


def test_primary_sona_cli_exposes_hardened_package_workflow(tmp_path):
    project = tmp_path / "primary-cli"
    project.mkdir()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)

    def run(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "sona", "pkg", *arguments],
            cwd=project,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    assert run("init", "--name", "primary_cli").returncode == 0
    lock_result = run("lock")
    install_result = run("install")
    verify_result = run("verify")

    assert lock_result.returncode == 0, lock_result.stdout + lock_result.stderr
    assert install_result.returncode == 0, install_result.stdout + install_result.stderr
    assert verify_result.returncode == 0, verify_result.stdout + verify_result.stderr
    assert "All packages verified." in verify_result.stdout
    written_lock = json.loads(
        (project / "sona.lock.json").read_text(encoding="utf-8")
    )
    assert written_lock["schema"] == spm_core.LOCK_SCHEMA_VERSION
