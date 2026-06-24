"""Azure OpenAI setup helper for the Sona CLI."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_DEPLOYMENT = "gpt-4o-mini"
DEFAULT_LOCAL_MODEL = "qwen2.5-coder:7b"
ENV_KEYS = (
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    "SONA_AI_PROVIDER",
    "SONA_AI_MAX_TOKENS",
    "SONA_AI_TEMPERATURE",
)
LOCAL_ENV_KEYS = (
    "SONA_AI_PROVIDER",
    "SONA_AI_BACKEND",
    "SONA_OLLAMA_MODEL",
    "OLLAMA_HOST",
    "SONA_AI_MAX_TOKENS",
    "SONA_AI_TEMPERATURE",
)
LOCAL_QWEN_MODEL_PREFERENCE = (
    "qwen3-coder-next",
    "qwen3-coder:30b",
    "qwen3-coder:480b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:0.5b",
    "qwen3:32b",
    "qwen3:14b",
    "qwen3:8b",
    "qwen2.5:14b",
    "qwen2.5:7b",
    "qwen2.5:3b",
)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )


def _az_json(args: list[str]) -> Any:
    cp = _run(["az", *args, "-o", "json"])
    if cp.returncode != 0:
        message = cp.stderr.strip() or cp.stdout.strip() or "Azure CLI call failed"
        raise RuntimeError(message)
    try:
        return json.loads(cp.stdout or "null")
    except Exception as exc:
        raise RuntimeError(f"Failed to parse Azure CLI JSON: {exc}") from exc


def _sona_home() -> Path:
    override = os.getenv("SONA_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".sona"


def _ensure_az_login() -> None:
    cp = _run(["az", "account", "show", "-o", "none"])
    if cp.returncode == 0:
        return

    print("[INFO] Launching Azure login.")
    login = _run(["az", "login", "-o", "none"])
    if login.returncode != 0:
        raise RuntimeError("Azure login failed. Run 'az login' and retry.")


def _list_openai_accounts() -> list[dict[str, Any]]:
    accounts = _az_json(["cognitiveservices", "account", "list", "--kind", "OpenAI"])
    items: list[dict[str, Any]] = []
    for account in accounts or []:
        properties = account.get("properties") or {}
        items.append(
            {
                "name": account.get("name"),
                "rg": account.get("resourceGroup"),
                "location": account.get("location"),
                "endpoint": properties.get("endpoint"),
            }
        )
    return items


def _choose(items: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not items:
        raise RuntimeError(f"No {label} found in your Azure account.")
    if len(items) == 1:
        return items[0]

    print(f"\nSelect a {label}:")
    for index, item in enumerate(items, 1):
        print(
            f"  {index}. {item.get('name')} "
            f"(rg={item.get('rg')}, location={item.get('location')})"
        )

    while True:
        choice = input(f"Enter 1-{len(items)}: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("Invalid selection. Try again.")


def _get_keys(name: str, resource_group: str) -> dict[str, str]:
    keys = _az_json(
        [
            "cognitiveservices",
            "account",
            "keys",
            "list",
            "-n",
            name,
            "-g",
            resource_group,
        ]
    )
    if not keys or not keys.get("key1"):
        raise RuntimeError("Failed to retrieve keys for the selected account.")
    return keys


def _normalize_deployment(name: str) -> str:
    candidate = name.strip()
    return candidate or DEFAULT_DEPLOYMENT


def _write_user_config(endpoint: str, api_key: str, deployment: str) -> Path:
    config_dir = _sona_home()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    payload = {
        "endpoint": endpoint,
        "api_key": api_key,
        "deployment": deployment,
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path


def _write_local_config(model: str, host: str) -> Path:
    config_dir = _sona_home()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    payload = {
        "provider": "ollama",
        "backend": "ollama",
        "model": model,
        "ollama_host": host,
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path


def _format_env_value(value: str) -> str:
    if value == "" or any(character.isspace() for character in value) or "#" in value:
        return json.dumps(value)
    return value


def _parse_env_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, _value = stripped.split("=", 1)
    key = key.strip()
    return key or None


def _update_env_values(
    workspace_dir: str | os.PathLike[str],
    updates: dict[str, str],
    ordered_keys: tuple[str, ...],
    *,
    header: str = "# Local environment for Sona. Do not commit secrets.",
) -> Path:
    workspace_path = Path(workspace_dir)
    workspace_path.mkdir(parents=True, exist_ok=True)
    env_path = workspace_path / ".env"

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        lines = []

    seen: set[str] = set()
    rewritten: list[str] = []
    for line in lines:
        key = _parse_env_key(line)
        if key in updates:
            rewritten.append(f"{key}={_format_env_value(str(updates[key]))}")
            seen.add(key)
        else:
            rewritten.append(line)

    if rewritten and rewritten[-1].strip():
        rewritten.append("")

    missing_keys = [key for key in ordered_keys if key in updates and key not in seen]
    if missing_keys and not rewritten:
        rewritten.append(header)
    elif missing_keys and rewritten[-1].strip():
        rewritten.append("")

    for key in missing_keys:
        rewritten.append(f"{key}={_format_env_value(str(updates[key]))}")

    env_path.write_text("\n".join(rewritten).rstrip() + "\n", encoding="utf-8")
    return env_path


def _update_env_file(
    workspace_dir: str | os.PathLike[str],
    endpoint: str,
    api_key: str,
    deployment: str,
) -> Path:
    env_path = Path(workspace_dir) / ".env"
    lines = (
        env_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if env_path.exists()
        else []
    )
    existing: dict[str, str] = {}
    for line in lines:
        key = _parse_env_key(line)
        if key and "=" in line:
            _raw_key, raw_value = line.split("=", 1)
            existing[key] = raw_value.strip()

    updates = {
        "AZURE_OPENAI_ENDPOINT": endpoint,
        "AZURE_OPENAI_API_KEY": api_key,
        "AZURE_OPENAI_DEPLOYMENT": deployment,
        "AZURE_OPENAI_DEPLOYMENT_NAME": deployment,
        "SONA_AI_PROVIDER": existing.get("SONA_AI_PROVIDER", "azure"),
        "SONA_AI_MAX_TOKENS": existing.get("SONA_AI_MAX_TOKENS", "150"),
        "SONA_AI_TEMPERATURE": existing.get("SONA_AI_TEMPERATURE", "0.3"),
    }

    return _update_env_values(workspace_dir, updates, ENV_KEYS)


def _update_local_env_file(
    workspace_dir: str | os.PathLike[str],
    model: str,
    host: str,
) -> Path:
    updates = {
        "SONA_AI_PROVIDER": "ollama",
        "SONA_AI_BACKEND": "ollama",
        "SONA_OLLAMA_MODEL": model,
        "OLLAMA_HOST": host,
        "SONA_AI_MAX_TOKENS": "150",
        "SONA_AI_TEMPERATURE": "0.3",
    }
    return _update_env_values(workspace_dir, updates, LOCAL_ENV_KEYS)


def _local_model_status(model: str | None = None) -> dict[str, Any]:
    from .ai.local_models import ensure_local_model

    return ensure_local_model(
        model or DEFAULT_LOCAL_MODEL,
        quiet=True,
        timeout=0.75,
    )


def _select_installed_qwen_model(models: list[str]) -> str | None:
    if not models:
        return None
    by_lower = {model.lower(): model for model in models}
    for candidate in LOCAL_QWEN_MODEL_PREFERENCE:
        matched = by_lower.get(candidate.lower())
        if matched:
            return matched
    for model in models:
        lowered = model.lower()
        if "qwen" in lowered and "coder" in lowered:
            return model
    for model in models:
        lowered = model.lower()
        if "qwen" in lowered and "vl" not in lowered:
            return model
    for model in models:
        if "qwen" in model.lower():
            return model
    return None


def _manual_provider_choice(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in {"azure", "az", "openai", "azure-openai", "azure_openai"}:
        return "azure"
    if lowered in {
        "local",
        "ollama",
        "offline",
        "qwen",
        "qwen2.5",
        "qwen2.5-coder",
        "qwen3",
        "qwen3-coder",
    }:
        return "local"
    return None


def _looks_like_local_model(value: str) -> bool:
    lowered = value.strip().lower()
    return "qwen" in lowered and ("coder" in lowered or ":" in lowered)


def _input(prompt: str) -> str | None:
    try:
        return input(prompt)
    except EOFError:
        return None


def _manual_azure_setup(
    dry_run: bool,
    workspace_dir: str | os.PathLike[str] | None,
    *,
    endpoint: str | None = None,
) -> int:
    print("[INFO] Manual Azure OpenAI setup")
    print("You'll need your Azure OpenAI endpoint, API key, and deployment name.")

    endpoint = (endpoint or (_input("Azure OpenAI endpoint: ") or "")).strip()
    if not endpoint:
        print("[ERROR] Endpoint is required.")
        return 1

    api_key = (_input("API key: ") or "").strip()
    if not api_key:
        print("[ERROR] API key is required.")
        return 1

    raw_deployment = (_input(f"Deployment name [{DEFAULT_DEPLOYMENT}]: ") or "").strip()
    deployment = _normalize_deployment(raw_deployment or DEFAULT_DEPLOYMENT)

    print("\nPlanned configuration:")
    print(f"  Endpoint:   {endpoint}")
    print(f"  Deployment: {deployment}")

    if dry_run:
        print("[INFO] Dry run: skipping writes.")
        return 0

    config_path = _write_user_config(endpoint, api_key, deployment)
    print(f"[OK] Wrote user config: {config_path}")

    env_path = _update_env_file(workspace_dir or os.getcwd(), endpoint, api_key, deployment)
    print(f"[OK] Updated workspace .env: {env_path}")
    print("[OK] Manual Azure setup complete.")
    return 0


def _manual_local_setup(
    dry_run: bool,
    workspace_dir: str | os.PathLike[str] | None,
    *,
    initial_model: str | None = None,
) -> int:
    print("[INFO] Manual local AI setup")
    print("This uses an Ollama model that is already downloaded.")

    initial_status = _local_model_status(DEFAULT_LOCAL_MODEL)
    installed_models = list(initial_status.get("models") or [])
    detected_model = _select_installed_qwen_model(installed_models)
    default_model = detected_model or DEFAULT_LOCAL_MODEL

    if initial_model:
        model = initial_model.strip() or default_model
    else:
        raw_model = (_input(f"Ollama model [{default_model}]: ") or "").strip()
        model = raw_model or default_model

    status = (
        initial_status
        if model == initial_status.get("model")
        else _local_model_status(model)
    )
    host = str(status.get("ollama_host") or "http://localhost:11434")

    if not status.get("ollama_running"):
        print("[ERROR] Ollama is not running or is not reachable.")
        if status.get("error"):
            print(f"        {status['error']}")
        print("        Start Ollama, then rerun: sona setup manual")
        return 1

    if not status.get("installed"):
        print(f"[ERROR] Model '{model}' is not installed in Ollama.")
        print(f"        Download it with: sona ai-model pull --model {model}")
        print(f"        Or run: ollama pull {model}")
        return 1

    print("\nPlanned configuration:")
    print("  Provider:   Ollama")
    print(f"  Host:       {host}")
    print(f"  Model:      {model}")

    if dry_run:
        print("[INFO] Dry run: skipping writes.")
        return 0

    config_path = _write_local_config(model, host)
    print(f"[OK] Wrote user config: {config_path}")

    env_path = _update_local_env_file(workspace_dir or os.getcwd(), model, host)
    print(f"[OK] Updated workspace .env: {env_path}")
    print("[OK] Manual local AI setup complete.")
    return 0


def _manual_setup(dry_run: bool, workspace_dir: str | os.PathLike[str] | None) -> int:
    print("[INFO] Manual Sona AI setup")
    first_raw = _input("Provider [azure/local] (Enter for azure): ")
    if first_raw is None:
        print("[ERROR] Endpoint is required.")
        return 1

    first = first_raw.strip()
    if not first:
        return _manual_azure_setup(dry_run, workspace_dir)

    choice = _manual_provider_choice(first)
    if choice == "local":
        return _manual_local_setup(dry_run, workspace_dir)
    if choice == "azure":
        return _manual_azure_setup(dry_run, workspace_dir)
    if _looks_like_local_model(first):
        return _manual_local_setup(dry_run, workspace_dir, initial_model=first)

    # Backward compatibility: older integrations send the Azure endpoint first.
    return _manual_azure_setup(dry_run, workspace_dir, endpoint=first)


def setup_azure(
    dry_run: bool = False,
    workspace_dir: str | os.PathLike[str] | None = None,
    manual_mode: bool = False,
) -> int:
    """Run interactive Azure OpenAI setup and return a process-style exit code."""
    if manual_mode:
        return _manual_setup(dry_run, workspace_dir)

    try:
        version = _run(["az", "version", "-o", "none"])
    except FileNotFoundError:
        print("[ERROR] Azure CLI not found. Install it from https://aka.ms/azcli.")
        print("        Or use: sona setup manual")
        return 2

    if version.returncode != 0:
        print("[ERROR] Azure CLI not found or not working.")
        print("        Install it from https://aka.ms/azcli or use: sona setup manual")
        return 2

    try:
        _ensure_az_login()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 3

    try:
        choice = _choose(_list_openai_accounts(), "Azure OpenAI account")
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 4

    name = choice.get("name")
    resource_group = choice.get("rg")
    endpoint = choice.get("endpoint") or ""
    if not name or not resource_group:
        print("[ERROR] Selected account is missing a name or resource group.")
        return 5
    if not endpoint:
        print("[ERROR] Selected account has no visible endpoint.")
        return 5

    try:
        keys = _get_keys(name, resource_group)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 6

    api_key = keys.get("key1") or keys.get("key2") or ""
    if not api_key:
        print("[ERROR] Failed to get an API key.")
        return 7

    raw_deployment = (_input(f"Model deployment name [{DEFAULT_DEPLOYMENT}]: ") or "").strip()
    deployment = _normalize_deployment(raw_deployment or DEFAULT_DEPLOYMENT)

    print("\nPlanned configuration:")
    print(f"  Endpoint:   {endpoint}")
    print(f"  Deployment: {deployment}")

    if dry_run:
        print("[INFO] Dry run: skipping writes.")
        return 0

    config_path = _write_user_config(endpoint, api_key, deployment)
    print(f"[OK] Wrote user config: {config_path}")

    env_path = _update_env_file(workspace_dir or os.getcwd(), endpoint, api_key, deployment)
    print(f"[OK] Updated workspace .env: {env_path}")
    print("[OK] Azure setup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(setup_azure())
