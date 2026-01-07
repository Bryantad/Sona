"""
Ollama local model helpers.

Centralized checks for Ollama availability and model presence.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from typing import Any

DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def normalize_ollama_host(host: str | None = None) -> str:
    """Normalize the Ollama host URL."""
    host = host or os.getenv("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST
    host = host.strip()
    if not host:
        return DEFAULT_OLLAMA_HOST
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host.rstrip("/")


def request_ollama_json(
    host: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 3.0,
) -> dict[str, Any]:
    """Send a request to Ollama and parse the JSON response."""
    url = f"{host}{path}"
    data = None
    headers = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read()
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def _format_error(exc: Exception) -> str:
    return str(exc) or exc.__class__.__name__


def _model_installed(model: str, available: list[str]) -> bool:
    if not model:
        return False
    if model in available:
        return True
    if ":" not in model and f"{model}:latest" in available:
        return True
    return False


def _pull_model(model: str) -> dict[str, Any]:
    result = {"pulled": False}
    try:
        proc = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        result["error"] = _format_error(exc)
        return result

    if proc.returncode == 0:
        result["pulled"] = True
        return result

    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    result["error"] = stderr or stdout or "ollama pull failed"
    return result


def ensure_local_model(
    model: str | None = None,
    *,
    pull_if_missing: bool = False,
    quiet: bool = False,
    host: str | None = None,
) -> dict[str, Any]:
    """Check whether Ollama is running and the model is installed."""
    model = model or os.getenv("SONA_OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
    host = normalize_ollama_host(host)

    status: dict[str, Any] = {
        "status": "unknown",
        "model": model,
        "ollama_host": host,
        "ollama_running": False,
        "installed": False,
        "pulled": False,
        "models": [],
    }

    try:
        version = request_ollama_json(host, "/api/version")
    except Exception as exc:
        status["status"] = "not_running"
        status["error"] = _format_error(exc)
        return status

    status["ollama_running"] = True
    if isinstance(version, dict):
        status["version"] = version.get("version")

    try:
        tags = request_ollama_json(host, "/api/tags")
    except Exception as exc:
        status["status"] = "error"
        status["error"] = _format_error(exc)
        return status

    models: list[str] = []
    if isinstance(tags, dict):
        for entry in tags.get("models", []) or []:
            if isinstance(entry, dict):
                name = entry.get("name")
                if name:
                    models.append(name)
    status["models"] = models

    installed = _model_installed(model, models)
    status["installed"] = installed
    if installed:
        status["status"] = "ready"
        return status

    status["status"] = "missing"
    if not pull_if_missing:
        return status

    pull_result = _pull_model(model)
    status.update(pull_result)

    if pull_result.get("pulled"):
        try:
            tags = request_ollama_json(host, "/api/tags")
        except Exception as exc:
            status["status"] = "error"
            status["error"] = _format_error(exc)
            return status

        models = []
        if isinstance(tags, dict):
            for entry in tags.get("models", []) or []:
                if isinstance(entry, dict):
                    name = entry.get("name")
                    if name:
                        models.append(name)
        status["models"] = models

        installed = _model_installed(model, models)
        status["installed"] = installed
        status["status"] = "ready" if installed else "missing"
        return status

    if pull_result.get("error") and not quiet:
        status["error"] = pull_result["error"]
    return status
