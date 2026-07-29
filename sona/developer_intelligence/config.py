"""Consolidated workspace configuration loader."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"configuration must be an object: {path}")
    return data


def _read_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        result[key.strip()] = value.strip().strip("\"'")
    return result


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _without_secrets(value: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    from .redaction import is_sensitive_key
    removed: list[str] = []
    result: dict[str, Any] = {}
    for key, item in value.items():
        if is_sensitive_key(key):
            removed.append(key)
            continue
        if isinstance(item, dict):
            clean, nested = _without_secrets(item)
            result[key] = clean
            removed.extend(f"{key}.{name}" for name in nested)
        else:
            result[key] = item
    return result, removed


def _environment_config(values: dict[str, str]) -> dict[str, Any]:
    providers = {
            "selected": values.get("SONA_AI_PROVIDER"),
            "backend": values.get("SONA_AI_BACKEND"),
            "ollama_model": values.get("SONA_OLLAMA_MODEL"),
            "ollama_host": values.get("OLLAMA_HOST"),
            "azure_endpoint": values.get("AZURE_OPENAI_ENDPOINT"),
            "azure_deployment": values.get("AZURE_OPENAI_DEPLOYMENT") or values.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "openai_compatible_endpoint": values.get("SONA_OPENAI_COMPATIBLE_ENDPOINT"),
            "openai_compatible_model": values.get("SONA_OPENAI_COMPATIBLE_MODEL"),
    }
    providers = {key: value for key, value in providers.items() if value not in {None, ""}}
    return {"providers": providers} if providers else {}


@lru_cache(maxsize=32)
def load_config(workspace: str, user_home: str | None = None) -> dict[str, Any]:
    root = Path(workspace).resolve()
    home = Path(user_home).expanduser() if user_home else Path(os.getenv("SONA_HOME", Path.home() / ".sona"))
    defaults: dict[str, Any] = {
        "schema_version": 1,
        "routing": {"prefer_local": True, "fallback_order": ["deterministic:sona"], "maximum_task_cost_usd": 0.25},
        "runtime": {"maximum_call_depth": 512, "maximum_loop_iterations": 10000000, "maximum_execution_time_ms": 300000, "maximum_output_bytes": 10485760, "persistent_memory": False},
    }
    process = _environment_config(dict(os.environ))
    user, user_secrets = _without_secrets(_read_json(home / "config.json"))
    dotenv = _environment_config(_read_env(root / ".env"))
    legacy, legacy_secrets = _without_secrets(_read_json(root / "sona.config.json"))
    workspace_cfg, workspace_secrets = _without_secrets(_read_json(root / ".sona" / "config.json"))
    # Lowest to highest priority.
    result = _merge(_merge(_merge(_merge(_merge(defaults, process), user), dotenv), legacy), workspace_cfg)
    ignored_secrets = [
        *(f"user:{name}" for name in user_secrets),
        *(f"legacy:{name}" for name in legacy_secrets),
        *(f"workspace:{name}" for name in workspace_secrets),
    ]
    if ignored_secrets:
        result["credential_migration_warning"] = (
            "Plaintext credential fields were ignored; use process environment, "
            "workspace .env with explicit consent, or client secret storage."
        )
        result["ignored_plaintext_credential_fields"] = tuple(sorted(ignored_secrets))
    return result


def resolve_config(workspace: str | Path, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_config(str(Path(workspace).resolve()))
    return _merge(data, overrides or {})


def resolve_credential(workspace: str | Path, environment_name: str) -> str | None:
    """Resolve a credential without placing it in ordinary configuration."""
    workspace_values = _read_env(Path(workspace).resolve() / ".env")
    return workspace_values.get(environment_name) or os.getenv(environment_name)


def reload_config() -> None:
    load_config.cache_clear()
