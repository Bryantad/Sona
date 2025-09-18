"""
Azure setup helper for Sona.

Provides `sona setup azure` to:
- Ensure Azure CLI is installed and the user is logged in
- Let the user pick an Azure OpenAI (Cognitive Services) resource
- Retrieve an API key and endpoint
- Write ~/.sona/config.json and update local .env (if present)

No secrets are committed; .env is already in .gitignore.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess command capturing output (UP022)."""
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
        msg = cp.stderr.strip() or cp.stdout.strip() or "Azure CLI call failed"
        raise RuntimeError(msg)
    try:
        return json.loads(cp.stdout or "null")
    except Exception as e:  # B904
        raise RuntimeError(f"Failed to parse Azure CLI JSON: {e}") from e


def _ensure_az_login() -> None:
    cp = _run(["az", "account", "show", "-o", "none"])
    if cp.returncode != 0:
        print("🔐 Launching Azure login (browser or device code)...")
        cp2 = _run(["az", "login", "-o", "none"])
        if cp2.returncode != 0:
            raise RuntimeError("Azure login failed. Run 'az login' and retry.")


def _list_openai_accounts() -> list[dict[str, Any]]:
    # List all Cognitive Services accounts of kind OpenAI across subscriptions
    accounts = _az_json([
        "cognitiveservices", "account", "list", "--kind", "OpenAI"
    ])
    # Shape: [{name, resourceGroup, location, properties:{endpoint, ...}}]
    items: list[dict[str, Any]] = []
    for acc in accounts or []:
        items.append({
            "name": acc.get("name"),
            "rg": acc.get("resourceGroup"),
            "location": acc.get("location"),
            "endpoint": (acc.get("properties") or {}).get("endpoint"),
        })
    return items


def _choose(items: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not items:
        raise RuntimeError(f"No {label} found in your Azure account(s).")
    if len(items) == 1:
        return items[0]
    print(f"\nSelect a {label}:")
    for i, it in enumerate(items, 1):
        print(
            f"  {i}. {it.get('name')} (rg={it.get('rg')}, "
            f"location={it.get('location')})"
        )
    while True:
        choice = input(f"Enter 1-{len(items)}: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print("Invalid selection. Try again.")


def _get_keys(name: str, rg: str) -> dict[str, str]:
    keys = _az_json([
        "cognitiveservices", "account", "keys", "list", "-n", name, "-g", rg
    ])
    # Keys shape: {key1: ..., key2: ...}
    if not keys or not keys.get("key1"):
        raise RuntimeError("Failed to retrieve keys for the selected account.")
    return keys


def _normalize_deployment(name: str) -> str:
    return "-".join(name.split()).lower() if name else "gpt-4o-mini"


def _write_user_config(endpoint: str, api_key: str, deployment: str) -> Path:
    cfg_dir = Path.home() / ".sona"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "config.json"
    data = {
        "endpoint": endpoint,
        "api_key": api_key,
        "deployment": deployment,
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return cfg_path


def _update_env_file(
    workspace_dir: Path, endpoint: str, api_key: str, deployment: str
) -> Path | None:
    env_path = workspace_dir / ".env"
    try:
        # Read existing if present
        existing = {}
        if env_path.exists():
            for line in env_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()

        existing.update({
            "AZURE_OPENAI_ENDPOINT": endpoint,
            "AZURE_OPENAI_API_KEY": api_key,
            "AZURE_OPENAI_DEPLOYMENT": deployment,
            "AZURE_OPENAI_DEPLOYMENT_NAME": deployment,
            "SONA_AI_PROVIDER": existing.get("SONA_AI_PROVIDER", "azure"),
        })

        # Write back
        lines = ["# Local environment for Sona (do not commit)"]
        for k in [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "SONA_AI_PROVIDER",
            "SONA_AI_MAX_TOKENS",
            "SONA_AI_TEMPERATURE",
        ]:
            val = existing.get(k)
            if val is None and k == "SONA_AI_MAX_TOKENS":
                val = "150"
            if val is None and k == "SONA_AI_TEMPERATURE":
                val = "0.3"
            if val is not None:
                lines.append(f"{k}={val}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return env_path
    except Exception:
        return None


def _manual_setup(dry_run: bool, workspace_dir: str | None) -> int:
    """Manual setup without Azure CLI - prompt for credentials."""
    print("🔧 Manual Azure OpenAI Setup")
    print("=" * 40)
    print("You'll need:")
    print(
        "  1. Azure OpenAI Endpoint (e.g., "
        "https://your-resource.openai.azure.com/)"
    )
    print("  2. API Key from Azure Portal")
    print("  3. Deployment name (e.g., gpt-4o-mini)")
    print()
    
    # Prompt for credentials
    endpoint = input("Azure OpenAI Endpoint: ").strip()
    if not endpoint:
        print("❌ Endpoint is required")
        return 1
    
    api_key = input("API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return 1
    
    default_dep = "gpt-4o-mini"
    deployment = (
        input(f"Deployment name [{default_dep}]: ").strip() or default_dep
    )
    deployment = _normalize_deployment(deployment)
    
    print("\nConfiguration:")
    print(f"  Endpoint:   {endpoint}")
    print(f"  Deployment: {deployment}")
    
    if dry_run:
        print("(dry-run) Skipping writes.")
        return 0
    
    # Write user config
    cfg_path = _write_user_config(endpoint, api_key, deployment)
    print(f"✅ Wrote user config: {cfg_path}")
    
    # Update workspace .env
    ws_path = Path(workspace_dir or os.getcwd())
    env_path = _update_env_file(ws_path, endpoint, api_key, deployment)
    if env_path:
        print(f"✅ Updated .env: {env_path}")
    else:
        print("ℹ️  Skipped .env update (file missing or write failed)")
    
    print("\n🎉 Manual setup complete! You can now use AI features.")
    return 0


def setup_azure(
    dry_run: bool = False,
    workspace_dir: str | None = None,
    manual_mode: bool = False,
) -> int:
    """Run interactive Azure setup. Returns exit code."""
    
    if manual_mode:
        return _manual_setup(dry_run, workspace_dir)
    
    # 1) Ensure az is present
    try:
        cp = _run(["az", "version", "-o", "none"])
        if cp.returncode != 0:
            print(
                "❌ Azure CLI not found. Install from "
                "https://aka.ms/azcli and retry."
            )
            print("   Or use: sona setup manual")
            return 2
    except FileNotFoundError:
        print(
            "❌ Azure CLI not found. Install from "
            "https://aka.ms/azcli and retry."
        )
        print("   Or use: sona setup manual")
        return 2

    # 2) Ensure login
    try:
        _ensure_az_login()
    except Exception as e:  # B904
        print(f"❌ {e}")
        return 3

    # 3) Pick account
    try:
        accounts = _list_openai_accounts()
        choice = _choose(accounts, "Azure OpenAI account")
    except Exception as e:  # B904
        print(f"❌ {e}")
        return 4

    name = choice["name"]
    rg = choice["rg"]
    endpoint = choice.get("endpoint") or ""
    if not endpoint:
        print("❌ Selected account has no endpoint visible.")
        return 5

    # 4) Get keys
    try:
        keys = _get_keys(name, rg)
    except Exception as e:  # B904
        print(f"❌ {e}")
        return 6
    api_key = keys.get("key1") or keys.get("key2") or ""
    if not api_key:
        print("❌ Failed to get an API key.")
        return 7

    # 5) Choose deployment name
    default_dep = "gpt-4o-mini"
    prompt = f"Model deployment name [{default_dep}]: "
    user_dep = (input(prompt).strip() or default_dep)
    deployment = _normalize_deployment(user_dep)

    print("\nPlanned configuration:")
    print(f"  Endpoint:   {endpoint}")
    print(f"  Deployment: {deployment}")
    if dry_run:
        print("(dry-run) Skipping writes.")
        return 0

    # 6) Write ~/.sona/config.json
    cfg_path = _write_user_config(endpoint, api_key, deployment)
    print(f"✅ Wrote user config: {cfg_path}")

    # 7) Update workspace .env if available
    ws_path = Path(workspace_dir or os.getcwd())
    env_path = _update_env_file(ws_path, endpoint, api_key, deployment)
    if env_path:
        print(f"✅ Updated .env: {env_path}")
    else:
        print("ℹ️  Skipped .env update (file missing or write failed)")

    print("\n🎉 Azure setup complete! You can now use AI features.")
    return 0


if __name__ == "__main__":
    code = setup_azure(dry_run=False)
    sys.exit(code)
