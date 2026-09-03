"""Hardened local-only package operations for SPM.

This module owns manifest validation, deterministic dependency locks, staged
installation, and rollback. It deliberately has no network or archive support.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST_NAME = "sona.json"
DEFAULT_LOCK_NAME = "sona.lock.json"
DEFAULT_MODULES_DIR = ".sona_modules"
MANIFEST_SCHEMA_VERSION = 2
LOCK_SCHEMA_VERSION = 2
LOCK_INTEGRITY_ALGORITHM = "sha256-tree-v2"
DEFAULT_PROJECT_VERSION = "0.15.5"

_PACKAGE_NAME_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)
_INTEGRITY_RE = re.compile(r"^sha256-[0-9a-f]{64}$")


class SpmError(RuntimeError):
    """A deterministic, user-facing local package error."""

    def __init__(self, message: str, code: str = "SPM-001"):
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        return f"{self.code}: {super().__str__()}"


@dataclass(frozen=True)
class DependencySpec:
    name: str
    path: str
    version: str = "*"
    integrity: str = ""


@dataclass(frozen=True)
class ResolvedDependency:
    spec: DependencySpec
    source: Path
    integrity: str
    source_type: str
    install_kind: str


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _project_root(explicit: str | None) -> Path:
    candidate = Path(explicit).expanduser() if explicit else Path.cwd()
    try:
        root = candidate.resolve(strict=True)
    except OSError as error:
        raise SpmError(
            "Project root is unavailable. Choose an existing project directory.",
            "SPM-PATH-001",
        ) from error
    if not root.is_dir():
        raise SpmError(
            "Project root must be a directory.",
            "SPM-PATH-001",
        )
    return root


def _validated_root(root: Path) -> Path:
    return _project_root(str(root))


def _manifest_path(root: Path) -> Path:
    return root / DEFAULT_MANIFEST_NAME


def _lock_path(root: Path) -> Path:
    return root / DEFAULT_LOCK_NAME


def _safe_json_load(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise SpmError(
            f"{label} is missing or is not a regular file.",
            "SPM-STATE-001",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SpmError(
            f"{label} is not valid UTF-8 JSON.",
            "SPM-STATE-002",
        ) from error
    if not isinstance(payload, dict):
        raise SpmError(
            f"{label} must contain a JSON object.",
            "SPM-STATE-003",
        )
    return payload


def _validate_package_name(name: Any) -> str:
    if not isinstance(name, str) or not _PACKAGE_NAME_RE.fullmatch(name):
        raise SpmError(
            "Dependency names must be dotted Sona identifiers.",
            "SPM-MANIFEST-003",
        )
    return name


def _dependency_group(manifest: dict[str, Any], key: str) -> list[DependencySpec]:
    raw_group = manifest.get(key, {})
    if not isinstance(raw_group, dict):
        raise SpmError(
            f"Manifest field '{key}' must be an object.",
            "SPM-MANIFEST-002",
        )

    dependencies: list[DependencySpec] = []
    for raw_name in sorted(raw_group):
        name = _validate_package_name(raw_name)
        payload = raw_group[raw_name]
        if isinstance(payload, str):
            path_value = payload
            version = "*"
            integrity = ""
        elif isinstance(payload, dict):
            path_value = payload.get("path")
            version = payload.get("version", "*")
            integrity = payload.get("integrity", "")
        else:
            raise SpmError(
                f"Dependency '{name}' must use a local path record.",
                "SPM-MANIFEST-004",
            )
        if not isinstance(path_value, str) or not path_value.strip() or "\x00" in path_value:
            raise SpmError(
                f"Dependency '{name}' requires a non-empty local path.",
                "SPM-MANIFEST-004",
            )
        if not isinstance(version, str) or not version:
            raise SpmError(
                f"Dependency '{name}' has an invalid version value.",
                "SPM-MANIFEST-005",
            )
        if not isinstance(integrity, str) or (
            integrity and not _INTEGRITY_RE.fullmatch(integrity)
        ):
            raise SpmError(
                f"Dependency '{name}' has an invalid integrity value.",
                "SPM-MANIFEST-006",
            )
        dependencies.append(
            DependencySpec(
                name=name,
                path=path_value,
                version=version,
                integrity=integrity,
            )
        )
    return dependencies


def _validate_manifest(manifest: dict[str, Any]) -> None:
    spm = manifest.get("spm")
    if not isinstance(spm, dict) or spm.get("schema") != MANIFEST_SCHEMA_VERSION:
        raise SpmError(
            f"Manifest must declare spm.schema {MANIFEST_SCHEMA_VERSION}.",
            "SPM-MANIFEST-001",
        )
    modules_dir = spm.get("modulesDir", DEFAULT_MODULES_DIR)
    if not isinstance(modules_dir, str):
        raise SpmError(
            "Manifest spm.modulesDir must be a relative path.",
            "SPM-PATH-002",
        )
    regular = _dependency_group(manifest, "dependencies")
    development = _dependency_group(manifest, "devDependencies")
    duplicate = sorted({item.name for item in regular} & {item.name for item in development})
    if duplicate:
        raise SpmError(
            f"Dependency '{duplicate[0]}' is declared more than once.",
            "SPM-MANIFEST-007",
        )


def _load_manifest(root: Path) -> dict[str, Any]:
    payload = _safe_json_load(_manifest_path(root), DEFAULT_MANIFEST_NAME)
    _validate_manifest(payload)
    return payload


def _iter_dependencies(
    manifest: dict[str, Any],
    *,
    include_dev: bool = False,
) -> list[DependencySpec]:
    _validate_manifest(manifest)
    dependencies = _dependency_group(manifest, "dependencies")
    if include_dev:
        dependencies.extend(_dependency_group(manifest, "devDependencies"))
    return sorted(dependencies, key=lambda item: item.name)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"


def _write_new_text(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_write_json(root: Path, path: Path, payload: dict[str, Any]) -> None:
    if path.is_symlink():
        raise SpmError(
            "Package metadata destination cannot be a symlink.",
            "SPM-PATH-004",
        )
    resolved_parent = path.parent.resolve(strict=True)
    if not _is_within(resolved_parent, root) or path == root:
        raise SpmError(
            "Package metadata destination escapes the project boundary.",
            "SPM-PATH-003",
        )
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _write_new_text(temporary, _canonical_json(payload))
        os.replace(temporary, path)
    except OSError as error:
        raise SpmError(
            "Package metadata could not be written atomically.",
            "SPM-STATE-004",
        ) from error
    finally:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)


def _write_manifest(root: Path, manifest: dict[str, Any]) -> None:
    _validate_manifest(manifest)
    _atomic_write_json(root, _manifest_path(root), manifest)


def init_project(
    root: Path,
    *,
    name: str | None = None,
    version: str = DEFAULT_PROJECT_VERSION,
) -> Path:
    project = _validated_root(root)
    path = _manifest_path(project)
    if path.is_symlink():
        raise SpmError(
            "Project manifest cannot be a symlink.",
            "SPM-PATH-004",
        )
    if path.exists():
        if not path.is_file():
            raise SpmError(
                "Project manifest path is not a regular file.",
                "SPM-STATE-001",
            )
        return path
    manifest: dict[str, Any] = {
        "name": name or project.name,
        "version": version,
        "description": "",
        "author": "",
        "license": "MIT",
        "keywords": [],
        "repository": "",
        "sona": {"minVersion": DEFAULT_PROJECT_VERSION},
        "dependencies": {},
        "devDependencies": {},
        "spm": {
            "schema": MANIFEST_SCHEMA_VERSION,
            "modulesDir": DEFAULT_MODULES_DIR,
        },
    }
    _write_manifest(project, manifest)
    return path


def _source_candidate(root: Path, value: str) -> Path:
    raw = Path(value).expanduser()
    return raw if raw.is_absolute() else root / raw


def _path_is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            if _path_is_link(current):
                return True
        except OSError:
            return True
    return False


def _resolve_dependency_source(root: Path, value: str, name: str) -> Path:
    candidate = _source_candidate(root, value)
    if _has_symlink_component(candidate):
        raise SpmError(
            f"Dependency '{name}' source cannot use symlinks.",
            "SPM-PATH-004",
        )
    try:
        return candidate.resolve(strict=True)
    except OSError as error:
        raise SpmError(
            f"Dependency '{name}' source is unavailable.",
            "SPM-PATH-005",
        ) from error


def _validate_source_tree(source: Path, root: Path, modules_dir: Path) -> None:
    if _has_symlink_component(source):
        raise SpmError(
            "Local dependency sources cannot use symlinks.",
            "SPM-PATH-004",
        )
    if not source.exists() or not (source.is_file() or source.is_dir()):
        raise SpmError(
            "Local dependency source is missing or unsupported.",
            "SPM-PATH-005",
        )
    if source.is_dir() and (source == root or source in root.parents):
        raise SpmError(
            "A dependency source cannot contain the destination project.",
            "SPM-PATH-006",
        )
    if _is_within(source, modules_dir):
        raise SpmError(
            "Installed package state cannot be used as a dependency source.",
            "SPM-PATH-006",
        )
    if source.is_dir():
        try:
            for child in source.rglob("*"):
                if _path_is_link(child):
                    raise SpmError(
                        "Local dependency trees cannot contain symlinks.",
                        "SPM-PATH-004",
                    )
                if not child.is_file() and not child.is_dir():
                    raise SpmError(
                        "Local dependency trees may contain only regular files and directories.",
                        "SPM-PATH-005",
                    )
        except OSError as error:
            raise SpmError(
                "Local dependency tree could not be inspected safely.",
                "SPM-PATH-005",
            ) from error


def _modules_dir(root: Path, manifest: dict[str, Any]) -> tuple[str, Path]:
    spm = manifest["spm"]
    value = spm.get("modulesDir", DEFAULT_MODULES_DIR)
    if (
        not isinstance(value, str)
        or not value.strip()
        or "\x00" in value
    ):
        raise SpmError(
            "Manifest spm.modulesDir must be a non-empty relative path.",
            "SPM-PATH-002",
        )
    relative = Path(value)
    if (
        relative.is_absolute()
        or relative.drive
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise SpmError(
            "Manifest spm.modulesDir must stay inside the project.",
            "SPM-PATH-002",
        )
    lexical = root.joinpath(*relative.parts)
    if _has_symlink_component(lexical):
        raise SpmError(
            "Manifest spm.modulesDir cannot traverse a symlink.",
            "SPM-PATH-004",
        )
    resolved = lexical.resolve(strict=False)
    if resolved == root or not _is_within(resolved, root):
        raise SpmError(
            "Manifest spm.modulesDir escapes the project boundary.",
            "SPM-PATH-003",
        )
    return relative.as_posix(), resolved


def _portable_relative_path(source: Path, root: Path) -> str:
    try:
        relative = os.path.relpath(source, root)
    except ValueError:
        return source.as_posix()
    return Path(relative).as_posix()


def add_dependency(
    root: Path,
    dep_name: str,
    dep_path: str,
    *,
    dev: bool = False,
) -> None:
    project = _validated_root(root)
    name = _validate_package_name(dep_name)
    manifest = _load_manifest(project)
    _, modules_dir = _modules_dir(project, manifest)
    source = _resolve_dependency_source(project, dep_path, name)
    _validate_source_tree(source, project, modules_dir)

    key = "devDependencies" if dev else "dependencies"
    other_key = "dependencies" if dev else "devDependencies"
    if name in manifest.get(other_key, {}):
        raise SpmError(
            f"Dependency '{name}' is already declared in {other_key}.",
            "SPM-MANIFEST-007",
        )
    manifest[key][name] = {
        "path": _portable_relative_path(source, project),
        "version": "*",
    }
    _write_manifest(project, manifest)


def _hash_file_record(hasher: Any, relative: str, path: Path) -> None:
    size = path.stat().st_size
    encoded = relative.encode("utf-8")
    hasher.update(b"F\x00")
    hasher.update(str(len(encoded)).encode("ascii"))
    hasher.update(b"\x00")
    hasher.update(encoded)
    hasher.update(b"\x00")
    hasher.update(str(size).encode("ascii"))
    hasher.update(b"\x00")
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    hasher.update(b"\x00")


def _tree_integrity(entries: list[tuple[str, Path]]) -> str:
    hasher = hashlib.sha256()
    hasher.update(b"sona.spm.sha256-tree-v2\x00")
    for relative, path in sorted(entries, key=lambda item: item[0]):
        _hash_file_record(hasher, relative, path)
    return f"sha256-{hasher.hexdigest()}"


def _compute_integrity_v2(source: Path) -> str:
    if source.is_file():
        return _tree_integrity([("", source)])
    entries = [
        (path.relative_to(source).as_posix(), path)
        for path in source.rglob("*")
        if path.is_file()
    ]
    return _tree_integrity(entries)


def _compute_source_integrity(source: Path) -> str:
    if source.is_file() and source.suffix != ".smod":
        return _tree_integrity([(source.name, source)])
    return _compute_integrity_v2(source)


def _compute_integrity_v1(source: Path) -> str:
    hasher = hashlib.sha256()
    if source.is_file():
        hasher.update(source.read_bytes())
    elif source.is_dir():
        for path in sorted(source.rglob("*")):
            if path.is_file():
                hasher.update(path.relative_to(source).as_posix().encode("utf-8"))
                hasher.update(path.read_bytes())
    return f"sha256-{hasher.hexdigest()}"


def _install_kind(source: Path) -> str:
    return "module-file" if source.is_file() and source.suffix == ".smod" else "package-dir"


def _resolve_dependencies(
    root: Path,
    manifest: dict[str, Any],
    modules_dir: Path,
    *,
    include_dev: bool,
) -> list[ResolvedDependency]:
    resolved: list[ResolvedDependency] = []
    for spec in _iter_dependencies(manifest, include_dev=include_dev):
        source = _resolve_dependency_source(root, spec.path, spec.name)
        _validate_source_tree(source, root, modules_dir)
        integrity = _compute_source_integrity(source)
        if spec.integrity and spec.integrity != integrity:
            raise SpmError(
                f"Dependency '{spec.name}' does not match its declared integrity.",
                "SPM-INTEGRITY-001",
            )
        resolved.append(
            ResolvedDependency(
                spec=spec,
                source=source,
                integrity=integrity,
                source_type="file" if source.is_file() else "directory",
                install_kind=_install_kind(source),
            )
        )
    return resolved


def _target_for(
    modules_dir: Path,
    name: str,
    install_kind: str,
) -> Path:
    parts = _validate_package_name(name).split(".")
    target = modules_dir.joinpath(*parts)
    return target.with_suffix(".smod") if install_kind == "module-file" else target


def _validate_target_set(modules_dir: Path, dependencies: list[ResolvedDependency]) -> None:
    targets = [
        (_target_for(modules_dir, item.spec.name, item.install_kind), item.spec.name)
        for item in dependencies
    ]
    for index, (left, left_name) in enumerate(targets):
        if not _is_within(left, modules_dir):
            raise SpmError(
                f"Dependency '{left_name}' escapes the modules directory.",
                "SPM-PATH-003",
            )
        for right, right_name in targets[index + 1 :]:
            if left == right or left in right.parents or right in left.parents:
                raise SpmError(
                    f"Dependencies '{left_name}' and '{right_name}' have "
                    "overlapping install targets.",
                    "SPM-MANIFEST-008",
                )


def _copy_dependency(dependency: ResolvedDependency, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if dependency.source.is_dir():
        shutil.copytree(dependency.source, target)
    elif dependency.install_kind == "module-file":
        shutil.copy2(dependency.source, target)
    else:
        target.mkdir(parents=True, exist_ok=False)
        shutil.copy2(dependency.source, target / dependency.source.name)


def _lock_payload(
    dependencies: list[ResolvedDependency],
    *,
    include_dev: bool,
) -> dict[str, Any]:
    packages: dict[str, dict[str, Any]] = {}
    for dependency in dependencies:
        packages[dependency.spec.name] = {
            "version": dependency.spec.version or "*",
            "path": dependency.spec.path.replace("\\", "/"),
            "integrity": dependency.integrity,
            "sourceType": dependency.source_type,
            "installKind": dependency.install_kind,
        }
    return {
        "schema": LOCK_SCHEMA_VERSION,
        "integrityAlgorithm": LOCK_INTEGRITY_ALGORITHM,
        "includeDev": include_dev,
        "packages": packages,
    }


def _safe_remove(path: Path, root: Path) -> None:
    resolved = path.resolve(strict=False)
    if resolved == root or not _is_within(resolved, root):
        raise SpmError(
            "SPM refused to remove a path outside the project boundary.",
            "SPM-PATH-003",
        )
    if _path_is_link(path) or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _commit_install(
    root: Path,
    modules_dir: Path,
    stage_modules: Path,
    staged_lock: Path,
    token: str,
) -> None:
    lock_path = _lock_path(root)
    modules_backup = root / f".spm-modules-backup-{token}"
    lock_backup = root / f".spm-lock-backup-{token}"
    had_modules = modules_dir.exists()
    had_lock = lock_path.exists()
    modules_backed_up = False
    lock_backed_up = False
    modules_committed = False
    lock_committed = False

    try:
        modules_dir.parent.mkdir(parents=True, exist_ok=True)
        if had_modules:
            os.replace(modules_dir, modules_backup)
            modules_backed_up = True
        if had_lock:
            if lock_path.is_symlink() or not lock_path.is_file():
                raise OSError("unsafe lock path")
            os.replace(lock_path, lock_backup)
            lock_backed_up = True
        os.replace(stage_modules, modules_dir)
        modules_committed = True
        os.replace(staged_lock, lock_path)
        lock_committed = True
    except OSError as error:
        recovery_ok = True
        try:
            if lock_committed and lock_path.exists():
                _safe_remove(lock_path, root)
            if modules_committed and modules_dir.exists():
                _safe_remove(modules_dir, root)
            if lock_backed_up and lock_backup.exists():
                os.replace(lock_backup, lock_path)
            if modules_backed_up and modules_backup.exists():
                os.replace(modules_backup, modules_dir)
        except (OSError, SpmError):
            recovery_ok = False
        message = (
            "Package install commit failed; previous package state was restored."
            if recovery_ok
            else "Package install commit failed and automatic recovery is incomplete."
        )
        raise SpmError(message, "SPM-INSTALL-004") from error
    finally:
        if lock_committed:
            with suppress(OSError, SpmError):
                _safe_remove(lock_backup, root)
        if modules_committed:
            with suppress(OSError, SpmError):
                _safe_remove(modules_backup, root)


def install(root: Path, *, include_dev: bool = False) -> dict[str, Any]:
    project = _validated_root(root)
    manifest = _load_manifest(project)
    modules_dir_name, modules_dir = _modules_dir(project, manifest)
    dependencies = _resolve_dependencies(
        project,
        manifest,
        modules_dir,
        include_dev=include_dev,
    )

    token = uuid.uuid4().hex
    stage_root = project / f".spm-stage-{token}"
    stage_modules = stage_root / "modules"
    staged_lock = stage_root / DEFAULT_LOCK_NAME
    _validate_target_set(stage_modules, dependencies)

    try:
        stage_modules.mkdir(parents=True, exist_ok=False)
        for dependency in dependencies:
            target = _target_for(
                stage_modules,
                dependency.spec.name,
                dependency.install_kind,
            )
            _copy_dependency(dependency, target)
            staged_integrity = _compute_integrity_v2(target)
            if staged_integrity != dependency.integrity:
                raise SpmError(
                    f"Dependency '{dependency.spec.name}' failed staged verification.",
                    "SPM-INTEGRITY-002",
                )
        payload = _lock_payload(dependencies, include_dev=include_dev)
        _write_new_text(staged_lock, _canonical_json(payload))
        _commit_install(
            project,
            modules_dir,
            stage_modules,
            staged_lock,
            token,
        )
    except SpmError:
        raise
    except OSError as error:
        raise SpmError(
            "Package staging failed before live state was changed.",
            "SPM-INSTALL-003",
        ) from error
    finally:
        with suppress(OSError, SpmError):
            _safe_remove(stage_root, project)

    return {
        "installed": [item.spec.name for item in dependencies],
        "errors": {},
        "modulesDir": modules_dir_name,
        "lockSchema": LOCK_SCHEMA_VERSION,
        "integrityAlgorithm": LOCK_INTEGRITY_ALGORITHM,
    }


def list_deps(root: Path) -> list[DependencySpec]:
    project = _validated_root(root)
    return _iter_dependencies(_load_manifest(project), include_dev=True)


def lock(root: Path) -> dict[str, Any]:
    project = _validated_root(root)
    manifest = _load_manifest(project)
    _, modules_dir = _modules_dir(project, manifest)
    dependencies = _resolve_dependencies(
        project,
        manifest,
        modules_dir,
        include_dev=True,
    )
    payload = _lock_payload(dependencies, include_dev=True)
    _atomic_write_json(project, _lock_path(project), payload)
    return payload


def _load_lock(root: Path) -> dict[str, Any]:
    return _safe_json_load(_lock_path(root), DEFAULT_LOCK_NAME)


def _schema2_manifest_mismatches(
    manifest: dict[str, Any],
    lock_data: dict[str, Any],
) -> list[str]:
    include_dev = lock_data.get("includeDev")
    if not isinstance(include_dev, bool):
        raise SpmError(
            "Schema-2 lock includeDev value is invalid.",
            "SPM-LOCK-003",
        )
    expected = {
        item.name: (item.path.replace("\\", "/"), item.version or "*")
        for item in _iter_dependencies(manifest, include_dev=include_dev)
    }
    packages = lock_data.get("packages")
    if not isinstance(packages, dict):
        raise SpmError(
            "Package lock packages field must be an object.",
            "SPM-LOCK-002",
        )
    actual: dict[str, tuple[str, str]] = {}
    for raw_name, raw_entry in packages.items():
        name = _validate_package_name(raw_name)
        if not isinstance(raw_entry, dict):
            raise SpmError(
                f"Lock entry '{name}' must be an object.",
                "SPM-LOCK-004",
            )
        path_value = raw_entry.get("path")
        version = raw_entry.get("version")
        if not isinstance(path_value, str) or not isinstance(version, str):
            raise SpmError(
                f"Lock entry '{name}' is incomplete.",
                "SPM-LOCK-004",
            )
        actual[name] = (path_value.replace("\\", "/"), version)
    names = sorted(set(expected) | set(actual))
    return [name for name in names if expected.get(name) != actual.get(name)]


def verify_lock(root: Path) -> dict[str, Any]:
    project = _validated_root(root)
    manifest = _load_manifest(project)
    _, modules_dir = _modules_dir(project, manifest)
    lock_data = _load_lock(project)
    schema = lock_data.get("schema")
    if schema not in {1, LOCK_SCHEMA_VERSION}:
        raise SpmError(
            "Package lock schema is unsupported.",
            "SPM-LOCK-001",
        )
    if schema == LOCK_SCHEMA_VERSION and (
        lock_data.get("integrityAlgorithm") != LOCK_INTEGRITY_ALGORITHM
    ):
        raise SpmError(
            "Package lock integrity algorithm is unsupported.",
            "SPM-LOCK-001",
        )

    packages = lock_data.get("packages")
    if not isinstance(packages, dict):
        raise SpmError(
            "Package lock packages field must be an object.",
            "SPM-LOCK-002",
        )
    manifest_mismatched = (
        _schema2_manifest_mismatches(manifest, lock_data)
        if schema == LOCK_SCHEMA_VERSION
        else []
    )

    ok: list[str] = []
    mismatched: list[dict[str, str]] = []
    missing: list[str] = []
    for raw_name in sorted(packages):
        name = _validate_package_name(raw_name)
        entry = packages[raw_name]
        if not isinstance(entry, dict):
            raise SpmError(
                f"Lock entry '{name}' must be an object.",
                "SPM-LOCK-004",
            )
        expected = entry.get("integrity")
        if not isinstance(expected, str) or (
            schema == LOCK_SCHEMA_VERSION and not _INTEGRITY_RE.fullmatch(expected)
        ):
            raise SpmError(
                f"Lock entry '{name}' has invalid integrity.",
                "SPM-LOCK-004",
            )

        if schema == LOCK_SCHEMA_VERSION:
            source_type = entry.get("sourceType")
            install_kind = entry.get("installKind")
            if source_type not in {"file", "directory"} or install_kind not in {
                "module-file",
                "package-dir",
            }:
                raise SpmError(
                    f"Lock entry '{name}' has invalid source metadata.",
                    "SPM-LOCK-004",
                )
            installed = _target_for(modules_dir, name, install_kind)
        else:
            installed = _target_for(modules_dir, name, "module-file")
            if not installed.exists():
                installed = _target_for(modules_dir, name, "package-dir")

        if not installed.exists():
            missing.append(name)
            continue
        try:
            _validate_source_tree(installed, project, Path("__spm_no_modules__"))
            actual = (
                _compute_integrity_v2(installed)
                if schema == LOCK_SCHEMA_VERSION
                else _compute_integrity_v1(installed)
            )
        except SpmError:
            actual = "unsafe-installed-state"
        if expected and actual != expected:
            mismatched.append(
                {"name": name, "expected": expected, "actual": actual}
            )
        else:
            ok.append(name)

    return {
        "schema": schema,
        "integrityAlgorithm": (
            LOCK_INTEGRITY_ALGORITHM if schema == LOCK_SCHEMA_VERSION else "legacy-schema-1"
        ),
        "ok": ok,
        "mismatched": mismatched,
        "missing": missing,
        "manifestMismatched": manifest_mismatched,
    }
