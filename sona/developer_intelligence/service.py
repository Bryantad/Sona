"""Preview-first developer task orchestration."""
from __future__ import annotations

import math
import os
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable

from .config import resolve_config, resolve_credential
from .cognitive import analyze_source
from .contracts import BudgetEstimate, ExecutionReceipt, TaskPlan, TaskRequest, TaskResult, TaskStatus
from .diagnostics import diagnostic
from .governance import append_audit, load_policy, policy_hash
from .models import ModelRegistry
from .providers import DeterministicProvider, HuggingFaceEndpointProvider, HuggingFaceLocalProvider, JsonHttpProvider, OllamaProvider
from .receipts import build_task_receipt, write_receipt
from .routing import route


class DeveloperIntelligenceService:
    def __init__(
        self, workspace: str | Path, registry: ModelRegistry | None = None,
        credential_resolver: Callable[[str], str | None] | None = None,
    ):
        self.workspace = Path(workspace).resolve()
        self.config = resolve_config(self.workspace)
        self.policy, self.policy_source = load_policy(self.workspace)
        self.registry = registry or ModelRegistry()
        self.credential_resolver = credential_resolver
        self._configure_builtin_models()
        self.registry.load_directory(Path(os.getenv("SONA_HOME", Path.home() / ".sona")) / "models", override=True)
        self.registry.load_directory(self.workspace / ".sona" / "models", override=True)

    def _configure_builtin_models(self) -> None:
        providers = self.config.get("providers", {})
        ollama = self.registry.get("ollama:qwen2.5-coder:7b")
        if ollama:
            model_name = str(providers.get("ollama_model") or ollama.provider_model_name)
            self.registry.upsert(replace(
                ollama, model_id=f"ollama:{model_name}", provider_model_name=model_name,
                configuration={"host": providers.get("ollama_host") or "http://127.0.0.1:11434"},
            ))

        azure = self.registry.get("azure:configured-deployment")
        endpoint = providers.get("azure_endpoint")
        deployment = providers.get("azure_deployment")
        if azure and endpoint and deployment:
            url = str(endpoint).rstrip("/") + f"/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview"
            self.registry.upsert(replace(azure, enabled=True, provider_model_name=str(deployment), configuration={"endpoint": url, "credential_env": "AZURE_OPENAI_API_KEY"}))
        compatible = self.registry.get("openai-compatible:configured-model")
        compatible_endpoint = providers.get("openai_compatible_endpoint")
        compatible_model = providers.get("openai_compatible_model")
        if compatible and compatible_endpoint and compatible_model:
            self.registry.upsert(replace(
                compatible, enabled=True, provider_model_name=str(compatible_model),
                configuration={"endpoint": str(compatible_endpoint), "credential_env": "SONA_OPENAI_COMPATIBLE_API_KEY"},
            ))

    def _credential(self, environment_name: str) -> str | None:
        if self.credential_resolver is not None:
            injected = self.credential_resolver(environment_name)
            if injected:
                return injected
        return resolve_credential(self.workspace, environment_name)

    def execute(self, request: TaskRequest, *, write_task_receipt: bool = True) -> TaskResult:
        started = time.perf_counter()
        if not request.instruction.strip():
            result = TaskResult(request.task_id, request.task_type, TaskStatus.FAILED, "Task instruction is required.", diagnostics=(diagnostic("SONA-AI-006", "provider", "Task instruction is required."),))
            return self._receipt(request, result, started) if write_task_receipt else result
        limits = self.policy.get("limits", {})
        max_files = min(request.constraints.maximum_files, int(limits.get("maximum_files_per_task", 10)))
        if len(request.target_files) > max_files:
            result = TaskResult(request.task_id, request.task_type, TaskStatus.DENIED, "Task exceeds the file-count limit.", diagnostics=(diagnostic("SONA-GOV-004", "governance", f"Maximum files per task is {max_files}."),))
            return self._receipt(request, result, started) if write_task_receipt else result
        max_context = min(request.constraints.maximum_context_tokens, int(limits.get("maximum_context_tokens", 32000)))
        estimated_context = math.ceil((len(request.instruction) + len(request.context.selected_text or "")) / 4)
        if estimated_context > max_context:
            result = TaskResult(request.task_id, request.task_type, TaskStatus.DENIED, "Task exceeds the context limit.", diagnostics=(diagnostic("SONA-GOV-004", "governance", f"Maximum context is {max_context} estimated tokens."),))
            return self._receipt(request, result, started) if write_task_receipt else result
        routed = route(request, self.registry, self.config, self.policy, self.policy_source)
        for decision in routed.governance:
            append_audit(self.workspace, decision)
        if routed.model is None:
            approval = any(item.get("decision") == "require_approval" for item in routed.governance)
            status = TaskStatus.APPROVAL_REQUIRED if approval else TaskStatus.UNAVAILABLE
            diagnostic_id = "SONA-GOV-003" if approval else "SONA-AI-002"
            category = "governance" if approval else "provider"
            result = TaskResult(request.task_id, request.task_type, status, "; ".join(routed.explanation), diagnostics=(diagnostic(diagnostic_id, category, "Provider use requires approval." if approval else "No compatible model is available.", hint="Inspect `sona model list` and the governance policy."),), governance_decisions=routed.governance)
            return self._receipt(request, result, started) if write_task_receipt else result
        model = routed.model
        input_tokens = math.ceil((len(request.instruction) + len(request.context.selected_text or "")) / 4)
        estimated_cost = None
        if model.input_cost_per_million_usd is not None and model.output_cost_per_million_usd is not None:
            estimated_cost = input_tokens * model.input_cost_per_million_usd / 1_000_000 + 256 * model.output_cost_per_million_usd / 1_000_000
        estimate = BudgetEstimate(estimated_input_tokens=input_tokens, maximum_output_tokens=256, estimated_cost_usd=estimated_cost, method="characters_per_token_v1")
        try:
            if model.provider_id == "deterministic":
                response = DeterministicProvider().execute(request, model)
            elif model.provider_id == "ollama":
                response = OllamaProvider().execute(request, model)
            elif model.provider_id == "huggingface" and model.locality == "local":
                response = HuggingFaceLocalProvider().execute(request, model)
            elif model.provider_id == "huggingface":
                endpoint = str(model.configuration.get("endpoint") or "")
                if not endpoint:
                    raise RuntimeError("Hugging Face remote model has no configured endpoint")
                credential_env = str(model.configuration.get("credential_env") or "HF_TOKEN")
                response = HuggingFaceEndpointProvider(endpoint=endpoint, api_key=self._credential(credential_env)).execute(request, model)
            else:
                endpoint = str(model.configuration.get("endpoint") or "")
                if not endpoint:
                    raise RuntimeError(f"provider '{model.provider_id}' has no configured endpoint")
                credential_env = str(model.configuration.get("credential_env") or "")
                api_key = self._credential(credential_env) if credential_env else None
                response = JsonHttpProvider(endpoint=endpoint, api_key=api_key).execute(request, model)
            proposed = request.task_type.value in {"edit", "fix", "refactor", "generate_tests"}
            deterministic_diagnostics = (
                self._deterministic_diagnostics(request)
                if model.provider_id == "deterministic" else ()
            )
            source_failed = any(item.severity == "error" for item in deterministic_diagnostics)
            result = TaskResult(
                request.task_id, request.task_type,
                TaskStatus.FAILED if source_failed else (TaskStatus.PROPOSED if proposed else TaskStatus.OK),
                "Source validation failed." if source_failed else str(response.get("summary") or "Task completed."),
                diagnostics=deterministic_diagnostics,
                plan=TaskPlan(summary=f"Preview {request.task_type.value} task.", intended_files=request.target_files, required_capabilities=("read_workspace",)),
                provider_id=model.provider_id, model_id=model.model_id,
                governance_decisions=routed.governance, budget=estimate,
            )
        except Exception as exc:
            result = TaskResult(request.task_id, request.task_type, TaskStatus.FAILED, "Provider task failed.", diagnostics=(diagnostic("SONA-AI-003", "provider", str(exc), hint="Verify optional dependencies and provider configuration."),), provider_id=model.provider_id, model_id=model.model_id, governance_decisions=routed.governance, budget=estimate, errors=(str(exc),))
        return self._receipt(request, result, started) if write_task_receipt else result

    def _deterministic_diagnostics(self, request: TaskRequest):
        findings = []
        profile = str(request.governance_metadata.get("profile") or "standard")
        for target in request.target_files:
            active_file = request.context.active_file
            if request.context.selected_text is not None and active_file and str(target) == str(active_file):
                from .frontend import analyze_frontend
                findings.extend(analyze_frontend(
                    request.context.selected_text,
                    file=str(target),
                    profile=profile,
                ))
                continue
            path = Path(target)
            if not path.is_absolute():
                path = self.workspace / path
            try:
                resolved = path.resolve()
                resolved.relative_to(self.workspace)
            except (ValueError, OSError):
                continue
            if resolved.exists() and resolved.is_file():
                source = resolved.read_text(encoding="utf-8-sig", errors="replace")
                from .frontend import analyze_frontend
                findings.extend(analyze_frontend(source, file=str(resolved), profile=profile))
        return tuple(findings)

    def _receipt(self, request: TaskRequest, result: TaskResult, started: float) -> TaskResult:
        receipt = build_task_receipt(request, result, policy_hash=policy_hash(self.policy), duration_ms=int((time.perf_counter() - started) * 1000))
        path = self.workspace / ".sona" / "receipts" / "tasks" / f"{request.task_id}.json"
        write_receipt(receipt, path)
        execution_receipt = ExecutionReceipt(
            schema_version=1, task_id=request.task_id, receipt_hash=receipt.get("receipt_hash"),
            prompt_hash=receipt.get("prompt_hash"), response_hash=receipt.get("response_hash"),
            context_hash=receipt.get("context_hash"), policy_hash=receipt.get("policy_hash"),
            patch_hash=receipt.get("patch_hash"), started_at=receipt.get("started_at"),
            completed_at=receipt.get("completed_at"), duration_ms=int(receipt.get("duration_ms", 0)),
            status=result.status, provider_id=result.provider_id, model_id=result.model_id,
            metadata={"receipt_path": str(path)},
        )
        return TaskResult(
            task_id=result.task_id, task_type=result.task_type, status=result.status, summary=result.summary,
            diagnostics=result.diagnostics, plan=result.plan, patch_set=result.patch_set,
            provider_id=result.provider_id, model_id=result.model_id,
            governance_decisions=result.governance_decisions, budget=result.budget,
            approval=result.approval, verification_plan=result.verification_plan,
            verification=result.verification, execution_receipt=execution_receipt,
            receipt_path=str(path), errors=result.errors,
        )
