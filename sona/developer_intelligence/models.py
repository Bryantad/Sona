"""Central model registry and custom manifest loading."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contracts import ProviderCapabilities, Serializable, TaskType


@dataclass(frozen=True, slots=True)
class ModelDescriptor(Serializable):
    model_id: str
    provider_id: str
    provider_model_name: str
    display_name: str
    supported_tasks: tuple[TaskType, ...]
    capabilities: ProviderCapabilities
    privacy: str
    locality: str
    enabled: bool = True
    maximum_context_tokens: int | None = None
    input_cost_per_million_usd: float | None = None
    output_cost_per_million_usd: float | None = None
    configuration: dict[str, Any] = field(default_factory=dict)
    required_configuration: tuple[str, ...] = ()


ALL_TASKS = tuple(TaskType)


def builtins() -> tuple[ModelDescriptor, ...]:
    structured = ProviderCapabilities(completion=True, structured_output=True, code_editing=True)
    remote = ProviderCapabilities(completion=True, structured_output=True, code_editing=True, network_required=True, local_execution=False)
    unavailable = ProviderCapabilities()
    return (
        ModelDescriptor("deterministic:sona", "deterministic", "sona", "Sona deterministic analysis", ALL_TASKS, structured, "workspace-local", "local"),
        ModelDescriptor("ollama:qwen2.5-coder:7b", "ollama", "qwen2.5-coder:7b", "Qwen 2.5 Coder via Ollama", ALL_TASKS, structured, "configured-endpoint", "local"),
        ModelDescriptor("azure:configured-deployment", "azure", "configured-deployment", "Azure OpenAI configured deployment", ALL_TASKS, remote, "remote", "remote", enabled=False, required_configuration=("endpoint", "deployment", "credential_env")),
        ModelDescriptor("openai-compatible:configured-model", "openai_compatible", "configured-model", "OpenAI-compatible configured model", ALL_TASKS, remote, "remote", "remote", enabled=False, required_configuration=("endpoint", "model", "credential_env")),
        ModelDescriptor("huggingface:custom-model", "huggingface", "custom-model", "Custom Hugging Face model", ALL_TASKS, remote, "configured", "remote", enabled=False, required_configuration=("endpoint_or_local_path",)),
        ModelDescriptor("gpt2:legacy-local", "gpt2", "gpt2", "Legacy local GPT-2 compatibility model", (TaskType.COMPLETE,), structured, "workspace-local", "local", enabled=False, configuration={"compatibility": "legacy"}),
        ModelDescriptor("claude:unavailable", "claude", "unavailable", "Claude (unavailable)", (), unavailable, "remote", "remote", enabled=False),
        ModelDescriptor("codex:unavailable", "codex", "unavailable", "Codex (unavailable)", (), unavailable, "remote", "remote", enabled=False),
    )


class ModelRegistry:
    def __init__(self, descriptors: tuple[ModelDescriptor, ...] | None = None):
        self._models: dict[str, ModelDescriptor] = {}
        for item in descriptors or builtins():
            self.register(item)

    def register(self, descriptor: ModelDescriptor) -> None:
        if descriptor.model_id in self._models:
            raise ValueError(f"duplicate model id: {descriptor.model_id}")
        self._models[descriptor.model_id] = descriptor

    def upsert(self, descriptor: ModelDescriptor) -> None:
        self._models[descriptor.model_id] = descriptor

    def get(self, model_id: str) -> ModelDescriptor | None:
        return self._models.get(model_id)

    def list(self, *, enabled_only: bool = False) -> list[ModelDescriptor]:
        values = sorted(self._models.values(), key=lambda item: item.model_id)
        return [item for item in values if item.enabled or not enabled_only]

    def load_directory(self, path: str | Path, *, override: bool = False) -> None:
        root = Path(path)
        if not root.exists():
            return
        for manifest in sorted(root.glob("*.json")):
            descriptor = descriptor_from_manifest(json.loads(manifest.read_text(encoding="utf-8")))
            if override:
                self.upsert(descriptor)
            else:
                self.register(descriptor)


def descriptor_from_manifest(data: dict[str, Any]) -> ModelDescriptor:
    if data.get("schema_version") != 1:
        raise ValueError("model manifest requires schema_version 1")
    required = ("model_id", "provider_id", "provider_model_name", "display_name", "supported_tasks")
    missing = [name for name in required if not data.get(name)]
    if missing:
        raise ValueError(f"model manifest missing: {', '.join(missing)}")
    identifier = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    if not identifier.fullmatch(str(data["model_id"])) or not identifier.fullmatch(str(data["provider_id"])):
        raise ValueError("model_id and provider_id must be safe identifiers")
    from .redaction import is_sensitive_key
    def contains_secret_key(value: Any) -> bool:
        if isinstance(value, dict):
            return any(is_sensitive_key(str(key)) or contains_secret_key(item) for key, item in value.items())
        if isinstance(value, (list, tuple)):
            return any(contains_secret_key(item) for item in value)
        return False
    if contains_secret_key(data.get("configuration") or {}):
        raise ValueError("model manifests cannot contain plaintext credentials; reference a credential_env name")
    tasks = tuple(TaskType(item) for item in data["supported_tasks"])
    caps = ProviderCapabilities(**dict(data.get("capabilities") or {}))
    locality = str(data.get("locality", "remote"))
    configuration = dict(data.get("configuration") or {})
    if str(data["provider_id"]) == "huggingface" and locality == "local":
        local_path = Path(str(configuration.get("local_path") or "")).expanduser()
        if not str(configuration.get("local_path") or "") or not local_path.exists():
            raise ValueError("local Hugging Face manifests require an existing local_path")
    return ModelDescriptor(
        model_id=str(data["model_id"]), provider_id=str(data["provider_id"]),
        provider_model_name=str(data["provider_model_name"]), display_name=str(data["display_name"]),
        supported_tasks=tasks, capabilities=caps, privacy=str(data.get("privacy", "configured")),
        locality=locality, enabled=bool(data.get("enabled", True)),
        maximum_context_tokens=data.get("maximum_context_tokens"),
        input_cost_per_million_usd=data.get("input_cost_per_million_usd"),
        output_cost_per_million_usd=data.get("output_cost_per_million_usd"),
        configuration=configuration,
        required_configuration=tuple(str(item) for item in data.get("required_configuration", ())),
    )
