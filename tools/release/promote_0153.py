#!/usr/bin/env python3
"""Push, review, and normally merge the manifest-replayed Sona 0.15.3 branch."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .certify_0153 import clean_repository, require_external_root
except ImportError:  # Direct script execution.
    from certify_0153 import clean_repository, require_external_root


ROOT = Path(__file__).resolve().parents[2]
BRANCH = "release/0.15.3"
TITLE = "Sona 0.15.3 \u2014 Runtime Reliability and Native Core Preview"


def _run(
    argv: list[str],
    repository: Path,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        argv,
        cwd=repository,
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
    return _run(["git", *arguments], repository).stdout.strip()


def _fetch(repository: Path) -> None:
    _run(["git", "fetch", "origin", "--prune", "--tags"], repository)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_current_checks(pr: dict[str, Any], expected_head: str) -> None:
    if pr.get("headRefOid") != expected_head:
        raise RuntimeError("pull-request checks belong to an earlier head SHA")
    checks = pr.get("statusCheckRollup") or []
    if not checks:
        raise RuntimeError("the release PR has no certification checks")
    incomplete = []
    for check in checks:
        is_check_run = (
            check.get("status") == "COMPLETED"
            and check.get("conclusion") == "SUCCESS"
            and check.get("state") is None
        )
        is_status_context = (
            check.get("state") == "SUCCESS"
            and check.get("status") is None
            and check.get("conclusion") is None
        )
        if not (is_check_run or is_status_context):
            incomplete.append(check)
    if incomplete:
        raise RuntimeError(f"release PR checks are incomplete or unsuccessful: {incomplete}")


def _pr_view(repository: Path, number: int) -> dict[str, Any]:
    return json.loads(
        _run(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--json",
                (
                    "number,url,state,isDraft,baseRefName,headRefName,headRefOid,"
                    "mergeStateStatus,statusCheckRollup,mergeCommit"
                ),
            ],
            repository,
        ).stdout
    )


def _report(
    output_root: Path,
    operation: str,
    repository: Path,
    payload: dict[str, Any],
) -> Path:
    report = {
        "schema_id": "sona.release-promotion.schema-1",
        "schema": 1,
        "sona_version": "0.15.3",
        "source_commit": payload["source_commit"],
        "generated_at_utc": _utc_now(),
        "host_os": platform.system(),
        "architecture": platform.machine(),
        "tool_versions": {
            "python": platform.python_version(),
            "git": _git(repository, "--version"),
            "gh": _run(["gh", "--version"], repository).stdout.splitlines()[0],
        },
        "command_summary": payload.pop("command_summary"),
        "result_counters": {"pass": 1, "fail": 0},
        "artifact_relative_evidence_paths": [
            f"sona-0.15.3-{operation}.json"
        ],
        "operation": operation,
        **payload,
    }
    path = output_root / f"sona-0.15.3-{operation}.json"
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def open_pr(repository: Path, output_root: Path) -> Path:
    repository = repository.resolve(strict=True)
    output_root = require_external_root(repository, output_root)
    clean_repository(repository)
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI is required for guarded promotion")
    if _git(repository, "branch", "--show-current") != BRANCH:
        raise RuntimeError(f"current branch must be {BRANCH}")
    head = _git(repository, "rev-parse", "HEAD")
    _fetch(repository)
    base = _git(repository, "rev-parse", "origin/main")
    remote = _git(repository, "ls-remote", "--heads", "origin", BRANCH)
    if remote:
        raise RuntimeError(f"remote branch {BRANCH} already exists")

    _fetch(repository)
    if _git(repository, "rev-parse", "origin/main") != base:
        raise RuntimeError("origin/main changed before branch push")
    _run(["git", "push", "--set-upstream", "origin", BRANCH], repository)

    _fetch(repository)
    if _git(repository, "rev-parse", f"origin/{BRANCH}") != head:
        raise RuntimeError("remote release branch does not match the intended commit")
    if _git(repository, "rev-parse", "origin/main") != base:
        raise RuntimeError("origin/main changed before PR creation")
    created = _run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            BRANCH,
            "--title",
            TITLE,
            "--body",
            (
                "Manifest-replayed Sona 0.15.3 release candidate. "
                "Publication remains blocked on every certification check."
            ),
        ],
        repository,
    ).stdout.strip()
    pr = json.loads(
        _run(
            [
                "gh",
                "pr",
                "view",
                BRANCH,
                "--json",
                "number,url,state,baseRefName,headRefName,headRefOid",
            ],
            repository,
        ).stdout
    )
    if (
        pr.get("state") != "OPEN"
        or pr.get("baseRefName") != "main"
        or pr.get("headRefName") != BRANCH
        or pr.get("headRefOid") != head
    ):
        raise RuntimeError("created PR does not match the release branch state")
    return _report(
        output_root,
        "pr-open",
        repository,
        {
            "source_commit": head,
            "base_commit": base,
            "pr_number": pr["number"],
            "pr_url": pr["url"],
            "command_summary": [
                ["git", "push", "--set-upstream", "origin", BRANCH],
                ["gh", "pr", "create", "--base", "main", "--head", BRANCH],
            ],
            "create_output": created,
        },
    )


def merge_pr(repository: Path, output_root: Path, number: int) -> Path:
    repository = repository.resolve(strict=True)
    output_root = require_external_root(repository, output_root)
    clean_repository(repository)
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI is required for guarded promotion")
    _fetch(repository)
    pr = _pr_view(repository, number)
    expected_head = _git(repository, "rev-parse", f"origin/{BRANCH}")
    if (
        pr.get("state") != "OPEN"
        or pr.get("isDraft")
        or pr.get("baseRefName") != "main"
        or pr.get("headRefName") != BRANCH
        or pr.get("mergeStateStatus") not in {"CLEAN", "HAS_HOOKS"}
    ):
        raise RuntimeError("release PR is not ready for a normal merge")
    validate_current_checks(pr, expected_head)
    base_before = _git(repository, "rev-parse", "origin/main")

    _fetch(repository)
    current = _pr_view(repository, number)
    if _git(repository, "rev-parse", f"origin/{BRANCH}") != expected_head:
        raise RuntimeError("release branch changed before merge")
    if _git(repository, "rev-parse", "origin/main") != base_before:
        raise RuntimeError("origin/main changed before merge")
    validate_current_checks(current, expected_head)
    _run(
        ["gh", "pr", "merge", str(number), "--merge", "--delete-branch=false"],
        repository,
    )
    _fetch(repository)
    merged = _pr_view(repository, number)
    main = _git(repository, "rev-parse", "origin/main")
    if (
        merged.get("state") != "MERGED"
        or merged.get("mergeCommit", {}).get("oid") != main
    ):
        raise RuntimeError("merged PR does not identify the resulting origin/main SHA")
    return _report(
        output_root,
        "pr-merge",
        repository,
        {
            "source_commit": main,
            "release_branch_sha": expected_head,
            "base_commit": base_before,
            "validated_main_sha": main,
            "pr_number": merged["number"],
            "pr_url": merged["url"],
            "command_summary": [
                ["gh", "pr", "merge", str(number), "--merge"],
                ["git", "fetch", "origin", "--prune", "--tags"],
            ],
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    opened = subparsers.add_parser("open-pr")
    opened.add_argument("--repository", type=Path, default=ROOT)
    opened.add_argument("--output-root", type=Path, required=True)
    merged = subparsers.add_parser("merge-pr")
    merged.add_argument("--repository", type=Path, default=ROOT)
    merged.add_argument("--output-root", type=Path, required=True)
    merged.add_argument("--pr-number", type=int, required=True)
    args = parser.parse_args(argv)
    if args.operation == "open-pr":
        report = open_pr(args.repository, args.output_root)
    else:
        report = merge_pr(args.repository, args.output_root, args.pr_number)
    print(f"Sona 0.15.3 promotion control passed: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
