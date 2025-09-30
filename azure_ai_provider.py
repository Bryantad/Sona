#!/usr/bin/env python3
"""
CLEAN Azure OpenAI Provider - Returns Text Only
==============================================

Fixed provider with correct Azure OpenAI endpoint, headers, and API version.
Uses httpx for reliable HTTP handling and returns clean text strings.
"""

import json
import logging
import os
import sys
from pathlib import Path

import httpx


# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        import io
        # Only wrap if not already wrapped
        if not hasattr(sys.stdout, '_original'):
            sys.stdout._original = sys.stdout
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='replace'
            )
        if not hasattr(sys.stderr, '_original'):
            sys.stderr._original = sys.stderr
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding='utf-8', errors='replace'
            )
    except Exception:
        # If UTF-8 wrapping fails, continue with default encoding
        pass

log = logging.getLogger("sona.azure")
log.setLevel(logging.INFO)

# Load environment variables from .env file if available (fallback only)
try:
    from dotenv import load_dotenv
    load_dotenv()  # Silent loading - no duplicates
except ImportError:
    # Don't require python-dotenv; prefer user-level config
    pass


# ---- Sona user config (exports required by CLI) ----------------------------
# Allow override via SONA_HOME for portability/tests
USER_CONFIG_DIR = Path(os.getenv("SONA_HOME") or (Path.home() / ".sona"))
USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
USER_CONFIG_PATH = USER_CONFIG_DIR / "config.json"

def _load_user_config() -> dict:
    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.warning("Failed to read %s: %s", USER_CONFIG_PATH, e)
        return {}

def _save_user_config(cfg: dict) -> None:
    try:
        with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg or {}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error("Failed to write %s: %s", USER_CONFIG_PATH, e)
        raise

USER_CONFIG = _load_user_config()

__all__ = [
    "USER_CONFIG_PATH", "USER_CONFIG", "_save_user_config",
    "AzureAIProvider",
]
# ---------------------------------------------------------------------------


API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")  # GA


def _normalize_deployment(name: str) -> str:
    """Collapse whitespace (handles 'gpt -4o mini' -> 'gpt-4o-mini')"""
    return "-".join((name or "").split()).lower()


def _as_text(resp_json) -> str:
    """Convert Azure OpenAI response to clean text"""
    try:
        return (resp_json["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return json.dumps(resp_json, ensure_ascii=False)


class AzureAIProvider:
    def __init__(self):
        # Load from environment and user config
        self.endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY") or ""
        self.deployment = _normalize_deployment(
            os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4o-mini"
        )

        # Load user config as fallback
        user_config = USER_CONFIG
        if not self.endpoint or not self.api_key:
            self.endpoint = self.endpoint or user_config.get("AZURE_OPENAI_ENDPOINT", "")
            self.api_key = self.api_key or user_config.get("AZURE_OPENAI_API_KEY", "")
            self.deployment = user_config.get("AZURE_OPENAI_DEPLOYMENT_NAME", self.deployment)

        # Normalize deployment name
        self.deployment = _normalize_deployment(self.deployment)

        # Warn on common 401 source: wrong domain
        if "cognitiveservices.azure.com" in self.endpoint.lower():
            log.warning("Endpoint looks wrong for Azure OpenAI. Use https://{resource}.openai.azure.com")

        if not (self.endpoint and self.api_key and self.deployment):
            log.warning("Missing Azure OpenAI config: endpoint/api_key/deployment")
        else:
            log.info("Azure OpenAI ready | endpoint=%s | deployment=%s", self.endpoint, self.deployment)

    def _chat(self, system: str, user: str) -> str:
        """Execute a chat completion and return CLEAN TEXT ONLY."""
        if not (self.endpoint and self.api_key and self.deployment):
            return "[AI Error] Azure OpenAI not configured"
        
        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={API_VERSION}"
        headers = {
            "api-key": self.api_key,            # << correct header
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            return _as_text(r.json())
        except httpx.HTTPStatusError as e:
            # Surface 401s clearly
            return f"[AI Error] {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"[AI Error] {e}"

    # --- Public API: ALWAYS return str ---
    def ai_complete(self, prompt: str) -> str:
        return self._chat(
            "Generate concise, production-quality code and explanation.",
            prompt,
        )

    def ai_explain(self, context: str, audience: str = "intermediate") -> str:
        return self._chat(
            f"Explain clearly for a {audience} developer.",
            context,
        )

    def ai_debug(self, context: str, code: str = None) -> str:
        # Handle single parameter case (just code)
        if code is None:
            code = context
            context = "Debug this code"
        
        return self._chat(
            "Senior debugging assistant. Diagnose causes and provide minimal fixes.",
            f"Context:\n{context}\n\nCode:\n{code}",
        )

    def ai_optimize(self, code: str) -> str:
        return self._chat(
            "Improve performance, readability, and safety without changing behavior.",
            code,
        )

    def ai_simplify(self, text: str) -> str:
        return self._chat(
            "Simplify complex explanations into clear, accessible language.",
            text,
        )

    def ai_break_down(self, task: str) -> str:
        return self._chat(
            "Break down complex tasks into clear, actionable steps.",
            task,
        )


# For backward compatibility
def create_provider():
    """Create a new provider instance"""
    return AzureAIProvider()
