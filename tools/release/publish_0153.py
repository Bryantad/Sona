#!/usr/bin/env python3
"""Publish the already-certified Sona 0.15.3 assets as one atomic GitHub release."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .certify_0153 import clean_repository, require_external_root
    from .finalize_0153_release import PUBLISHED_FILES, verify_sha256sums
except ImportError:  # Direct script execution.
    from certify_0153 import clean_repository, require_external_root
    from finalize_0153_release import PUBLISHED_FILES, verify_sha256sums


VERSION = "0.15.3"
TAG = f"v{VERSION}"
TITLE = "Sona 0.15.3 \u2014 Runtime Reliability and Native Core Preview"
ROOT = Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(
    argv: list[str | Path],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [str(value) for value in argv],
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {argv}\n{completed.stderr}"
        )
    return completed


def _git(repository: Path, *arguments: str) -> str:
    return _run(["git", *arguments], cwd=repository).stdout.strip()


def _fetch(repository: Path) -> None:
    _run(["git", "fetch", "origin", "--prune", "--tags"], cwd=repository)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _certified_commit(assets: Path) -> str:
    report = json.loads(
        (assets / f"sona-{VERSION}-certification.json").read_text(encoding="utf-8")
    )
    if (
        report.get("schema_id") != "sona.release-certification.schema-1"
        or report.get("result") != "pass"
    ):
        raise RuntimeError("aggregate certification report is not a passing schema-1 report")
    commit = report.get("source_commit", "")
    if not isinstance(commit, str) or len(commit) != 40:
        raise RuntimeError("aggregate certification report has no full source commit")
    return commit


def validate_assets(assets: Path) -> dict[str, dict[str, Any]]:
    observed = {path.name for path in assets.iterdir() if path.is_file()}
    if observed != PUBLISHED_FILES:
        raise RuntimeError(
            f"release asset set mismatch: observed={sorted(observed)} "
            f"expected={sorted(PUBLISHED_FILES)}"
        )
    verify_sha256sums(assets)
    return {
        path.name: {
            "byte_size": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(assets.iterdir())
        if path.is_file()
    }


def _assert_remote_state(repository: Path, certified_commit: str) -> None:
    _fetch(repository)
    main = _git(repository, "rev-parse", "origin/main")
    if main != certified_commit:
        raise RuntimeError(
            f"origin/main moved: certified={certified_commit} current={main}"
        )
    tag_commit = _run(
        ["git", "rev-parse", f"refs/tags/{TAG}^{{commit}}"],
        cwd=repository,
        check=False,
    )
    if tag_commit.returncode == 0 and tag_commit.stdout.strip() != certified_commit:
        raise RuntimeError(f"{TAG} points to a conflicting commit")


def _release_view(repository: Path, *, required: bool) -> dict[str, Any] | None:
    completed = _run(
        [
            "gh",
            "release",
            "view",
            TAG,
            "--json",
            "tagName,targetCommitish,name,isDraft,isPrerelease,assets,url",
        ],
        cwd=repository,
        check=False,
    )
    if completed.returncode != 0:
        if required:
            raise RuntimeError(f"GitHub release {TAG} is unavailable: {completed.stderr}")
        return None
    return json.loads(completed.stdout)


def _validate_release_metadata(
    release: dict[str, Any],
    *,
    draft: bool,
) -> None:
    if release.get("tagName") != TAG:
        raise RuntimeError("GitHub release has the wrong tag")
    if release.get("name") != TITLE:
        raise RuntimeError("GitHub release has the wrong title")
    if release.get("isDraft") is not draft:
        raise RuntimeError("GitHub release draft state is incorrect")
    if release.get("isPrerelease") is not False:
        raise RuntimeError("GitHub release is incorrectly marked prerelease")


def _validate_remote_asset_metadata(
    release: dict[str, Any],
    local: dict[str, dict[str, Any]],
) -> None:
    remote = {
        asset["name"]: {"byte_size": asset["size"]}
        for asset in release.get("assets", [])
    }
    if set(remote) != PUBLISHED_FILES:
        raise RuntimeError(
            f"remote asset filenames mismatch: {sorted(remote)}"
        )
    for filename, expected in local.items():
        if remote[filename]["byte_size"] != expected["byte_size"]:
            raise RuntimeError(f"remote asset size mismatch: {filename}")


def _download_and_verify(
    repository: Path,
    destination: Path,
    local: dict[str, dict[str, Any]],
) -> None:
    if destination.exists():
        raise RuntimeError(f"verification destination already exists: {destination}")
    destination.mkdir(parents=True)
    _run(
        ["gh", "release", "download", TAG, "--dir", destination],
        cwd=repository,
    )
    downloaded = validate_assets(destination)
    if downloaded != local:
        raise RuntimeError("downloaded asset hashes or sizes differ from certified assets")


def publish(
    repository: Path,
    assets: Path,
    publication_root: Path,
    pr_number: int,
) -> Path:
    repository = repository.resolve(strict=True)
    assets = assets.resolve(strict=True)
    publication_root = require_external_root(repository, publication_root)
    clean_repository(repository)
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI is required for guarded publication")
    local = validate_assets(assets)
    certified_commit = _certified_commit(assets)
    if _git(repository, "rev-parse", "HEAD") != certified_commit:
        raise RuntimeError("the publication clone is not at the certified commit")
    pr = json.loads(
        _run(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--json",
                "number,url,state,baseRefName,headRefName,headRefOid,mergeCommit",
            ],
            cwd=repository,
        ).stdout
    )
    if (
        pr.get("state") != "MERGED"
        or pr.get("baseRefName") != "main"
        or pr.get("headRefName") != "release/0.15.3"
        or pr.get("mergeCommit", {}).get("oid") != certified_commit
    ):
        raise RuntimeError("the merged release PR does not identify the certified main commit")

    _assert_remote_state(repository, certified_commit)
    local_tag = _run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{TAG}"],
        cwd=repository,
        check=False,
    )
    remote_tag = _git(repository, "ls-remote", "--tags", "origin", f"refs/tags/{TAG}")
    if local_tag.returncode == 0 or remote_tag:
        raise RuntimeError(f"{TAG} already exists locally or remotely")
    if _release_view(repository, required=False) is not None:
        raise RuntimeError(f"a conflicting GitHub release already exists for {TAG}")

    _fetch(repository)
    _assert_remote_state(repository, certified_commit)
    _run(
        [
            "git",
            "-c",
            "tag.gpgSign=false",
            "tag",
            "-a",
            TAG,
            certified_commit,
            "-m",
            TITLE,
        ],
        cwd=repository,
    )
    tag_object = _git(repository, "rev-parse", f"{TAG}^{{tag}}")
    _assert_remote_state(repository, certified_commit)
    _run(["git", "push", "origin", f"refs/tags/{TAG}"], cwd=repository)

    _assert_remote_state(repository, certified_commit)
    _run(
        [
            "gh",
            "release",
            "create",
            TAG,
            "--draft",
            "--verify-tag",
            "--title",
            TITLE,
            "--notes-file",
            assets / f"RELEASE_NOTES_v{VERSION}.md",
        ],
        cwd=repository,
    )
    for filename in sorted(PUBLISHED_FILES):
        _assert_remote_state(repository, certified_commit)
        release = _release_view(repository, required=True)
        assert release is not None
        _validate_release_metadata(release, draft=True)
        _run(
            ["gh", "release", "upload", TAG, assets / filename],
            cwd=repository,
        )

    _assert_remote_state(repository, certified_commit)
    draft_release = _release_view(repository, required=True)
    assert draft_release is not None
    _validate_release_metadata(draft_release, draft=True)
    _validate_remote_asset_metadata(draft_release, local)
    _download_and_verify(
        repository,
        publication_root / "draft-download",
        local,
    )

    _assert_remote_state(repository, certified_commit)
    _run(
        [
            "gh",
            "release",
            "edit",
            TAG,
            "--draft=false",
            "--prerelease=false",
            "--latest",
            "--title",
            TITLE,
            "--notes-file",
            assets / f"RELEASE_NOTES_v{VERSION}.md",
        ],
        cwd=repository,
    )

    _assert_remote_state(repository, certified_commit)
    public_release = _release_view(repository, required=True)
    assert public_release is not None
    _validate_release_metadata(public_release, draft=False)
    _validate_remote_asset_metadata(public_release, local)
    _download_and_verify(
        repository,
        publication_root / "public-download",
        local,
    )
    report = {
        "schema_id": "sona.github-publication.schema-1",
        "schema": 1,
        "sona_version": VERSION,
        "source_commit": certified_commit,
        "generated_at_utc": _utc_now(),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python": platform.python_version(),
            "git": _git(repository, "--version"),
            "gh": _run(["gh", "--version"], cwd=repository).stdout.splitlines()[0],
        },
        "command_summary": [
            ["git", "push", "origin", f"refs/tags/{TAG}"],
            ["gh", "release", "create", TAG, "--draft"],
            ["gh", "release", "upload", TAG, "<asset>"],
            ["gh", "release", "edit", TAG, "--draft=false"],
        ],
        "result_counters": {
            "assets_uploaded": len(local),
            "assets_reverified": len(local),
            "fail": 0,
        },
        "artifact_relative_evidence_paths": [
            "draft-download/",
            "public-download/",
            f"sona-{VERSION}-publication.json",
        ],
        "branch": _git(repository, "branch", "--show-current"),
        "release_branch": pr["headRefName"],
        "release_branch_sha": pr["headRefOid"],
        "pr_url": pr["url"],
        "pr_number": pr["number"],
        "validated_main_sha": certified_commit,
        "annotated_tag": TAG,
        "tag_object_sha": tag_object,
        "release_url": public_release["url"],
        "title": public_release["name"],
        "stable": not public_release["isDraft"] and not public_release["isPrerelease"],
        "assets": local,
        "pypi_publication": "not_performed",
        "vscode_marketplace_publication": "not_performed",
        "native_core": "preview",
        "compatibility_engine": "python",
    }
    report_path = publication_root / f"sona-{VERSION}-publication.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    clean_repository(repository)
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--publication-root", type=Path, required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    args = parser.parse_args(argv)
    report = publish(
        args.repository,
        args.assets,
        args.publication_root,
        args.pr_number,
    )
    print(f"Sona {VERSION} public GitHub release independently verified: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
