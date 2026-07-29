from __future__ import annotations

import subprocess
import os
import warnings
import zipfile
from pathlib import Path

import pytest

from tools.release.certify_0153 import (
    _extract_commit,
    _python_metadata,
    assert_clone_unchanged,
    clean_repository,
    clone_tree_snapshot,
    external_environment,
    node_command,
    npm_ci_command,
    require_external_root,
)
from tools.validate_release_metadata import tracked_source_maps


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return completed.stdout.strip()


def _clean_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "clone"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.name", "Certification Test")
    _git(repository, "config", "user.email", "certification@example.invalid")
    (repository / "tracked.txt").write_text("stable\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(
        repository,
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        "fixture",
    )
    return repository


def test_commit_staging_avoids_default_tar_extraction_warning(
    tmp_path: Path,
) -> None:
    repository = _clean_repository(tmp_path)
    destination = tmp_path / "staged"
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        _extract_commit(repository, _git(repository, "rev-parse", "HEAD"), destination)
    assert (destination / "tracked.txt").read_text(encoding="utf-8") == "stable\n"
    assert not [
        warning
        for warning in observed
        if warning.category is DeprecationWarning
        and "tar archives" in str(warning.message)
    ]


def test_metadata_map_scan_supports_git_archive_staging(tmp_path: Path) -> None:
    stage = tmp_path / "stage-without-git"
    (stage / "vscode-extension" / "out").mkdir(parents=True)
    assert tracked_source_maps(stage) == []
    source_map = stage / "vscode-extension" / "out" / "extension.js.map"
    source_map.write_text("{}\n", encoding="utf-8")
    assert tracked_source_maps(stage) == [
        "vscode-extension/out/extension.js.map"
    ]


def test_node_commands_use_windows_cmd_shims_without_a_shell() -> None:
    suffix = ".cmd" if os.name == "nt" else ""
    assert node_command("npm") == f"npm{suffix}"
    assert node_command("npx") == f"npx{suffix}"
    with pytest.raises(ValueError, match="unsupported Node command shim"):
        node_command("node")
    assert npm_ci_command() == [
        f"npm{suffix}",
        "ci",
        "--omit=optional",
        "--no-audit",
        "--fund=false",
    ]


def test_wheel_python_bounds_allow_backend_normalized_order(
    tmp_path: Path,
) -> None:
    wheel = tmp_path / "sona_lang-0.15.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "sona_lang-0.15.3.dist-info/METADATA",
            (
                "Metadata-Version: 2.4\n"
                "Name: sona-lang\n"
                "Version: 0.15.3\n"
                "Requires-Python: <3.13,>=3.11\n"
            ),
        )
    assert _python_metadata(wheel)["requires_python"] == "<3.13,>=3.11"

    invalid = tmp_path / "invalid.whl"
    with zipfile.ZipFile(invalid, "w") as archive:
        archive.writestr(
            "sona_lang-0.15.3.dist-info/METADATA",
            (
                "Metadata-Version: 2.4\n"
                "Name: sona-lang\n"
                "Version: 0.15.3\n"
                "Requires-Python: >=3.11\n"
            ),
        )
    with pytest.raises(RuntimeError, match="incorrect Requires-Python"):
        _python_metadata(invalid)


def test_external_root_must_be_absolute_and_outside_clone(tmp_path: Path) -> None:
    repository = _clean_repository(tmp_path)
    with pytest.raises(ValueError, match="absolute"):
        require_external_root(repository, Path("relative"))
    with pytest.raises(ValueError, match="outside"):
        require_external_root(repository, repository / "certification")
    external = require_external_root(repository, tmp_path / "certification")
    assert external.is_dir()


def test_clone_snapshot_detects_content_metadata_and_untracked_drift(
    tmp_path: Path,
) -> None:
    repository = _clean_repository(tmp_path)
    baseline = clone_tree_snapshot(repository)
    assert_clone_unchanged(repository, baseline, "baseline")

    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="dirty"):
        assert_clone_unchanged(repository, baseline, "content")

    (repository / "tracked.txt").write_text("stable\n", encoding="utf-8")
    (repository / "untracked.txt").write_text("output\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="dirty"):
        clean_repository(repository)


def test_external_environment_routes_every_required_output_class(
    tmp_path: Path,
) -> None:
    repository = _clean_repository(tmp_path)
    cert_root = require_external_root(repository, tmp_path / "certification")
    commit = _git(repository, "rev-parse", "HEAD")
    environment = external_environment(cert_root, commit)

    required = {
        "CARGO_TARGET_DIR",
        "TMPDIR",
        "TEMP",
        "TMP",
        "PYTHONPYCACHEPREFIX",
        "PIP_CACHE_DIR",
        "npm_config_cache",
        "npm_config_update_notifier",
        "XDG_CACHE_HOME",
        "HYPOTHESIS_STORAGE_DIRECTORY",
        "COVERAGE_FILE",
    }
    assert required <= environment.keys()
    assert environment["SONA_SOURCE_COMMIT"] == commit
    assert environment["npm_config_update_notifier"] == "false"
    for name in required - {"npm_config_update_notifier"}:
        assert Path(environment[name]).is_absolute()
        assert not (
            Path(environment[name]).resolve() == repository.resolve()
            or repository.resolve() in Path(environment[name]).resolve().parents
        )
