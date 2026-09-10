"""Deterministic provider/model routing."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .contracts import TaskRequest
from .governance import evaluate
from .models import ModelDescriptor, ModelRegistry


@dataclass(frozen=True, slots=True)
class RoutingResult:
    model: ModelDescriptor | None
    explanation: tuple[str, ...]
    governance: tuple[dict[str, Any], ...] = ()


def _approval_covers(request: TaskRequest, capability: str, model: ModelDescriptor) -> bool:
    approval = request.governance_metadata.get("approval")
    if not isinstance(approval, dict):
        return False
    capabilities = {str(item) for item in approval.get("capabilities", [])}
    return bool(
        str(approval.get("status", "")).lower() in {"approved", "granted"}
        and approval.get("task_id") == request.task_id
        and capability in capabilities
        and approval.get("provider_id", model.provider_id) == model.provider_id
        and approval.get("model_id", model.model_id) == model.model_id
    )


def route(request: TaskRequest, registry: ModelRegistry, config: dict[str, Any], policy: dict[str, Any], source: str) -> RoutingResult:
    explanations: list[str] = []
    decisions: list[dict[str, Any]] = []
    candidates: list[ModelDescriptor] = []
    if request.model_id:
        selected = registry.get(request.model_id)
        if selected is None:
            return RoutingResult(None, (f"Explicit model '{request.model_id}' is not registered.",))
        if request.provider_id and selected.provider_id != request.provider_id:
            return RoutingResult(None, (f"Explicit model '{request.model_id}' does not belong to provider '{request.provider_id}'.",))
        candidates = [selected]
    else:
        order = list(config.get("routing", {}).get("fallback_order") or ["deterministic:sona"])
        candidates = [item for model_id in order if (item := registry.get(model_id)) is not None]
        if request.provider_id:
            candidates = [item for item in registry.list() if item.provider_id == request.provider_id]
        elif config.get("routing", {}).get("prefer_local", True):
            indexed = list(enumerate(candidates))
            candidates = [item for _index, item in sorted(indexed, key=lambda pair: (pair[1].locality != "local", pair[0]))]
    for item in candidates:
        if item.provider_id in {"claude", "codex"}:
            explanations.append(f"{item.model_id}: provider is unavailable in Sona 0.15.6")
            continue
        if not item.enabled:
            explanations.append(f"{item.model_id}: disabled")
            continue
        if request.task_type not in item.supported_tasks:
            explanations.append(f"{item.model_id}: task not supported")
            continue
        estimated_tokens = math.ceil((len(request.instruction) + len(request.context.selected_text or "")) / 4)
        context_limit = item.maximum_context_tokens or item.capabilities.maximum_context_tokens
        if context_limit is not None and estimated_tokens > context_limit:
            explanations.append(f"{item.model_id}: estimated context exceeds the model limit")
            continue
        if item.capabilities.network_required and not request.constraints.allow_network:
            explanations.append(f"{item.model_id}: task constraints deny network access")
            continue
        if item.locality == "remote":
            input_cost = item.input_cost_per_million_usd
            output_cost = item.output_cost_per_million_usd
            approved_cost = _approval_covers(request, "remote_cost", item)
            require_known = bool(policy.get("limits", {}).get("require_known_cost", False))
            if input_cost is None or output_cost is None:
                decision = "deny" if require_known else "require_approval"
                decisions.append({
                    "decision": decision, "source": source,
                    "reason": "Remote model cost is unknown.", "task_type": request.task_type.value,
                    "provider": item.provider_id, "model": item.model_id, "capability": "remote_cost",
                    "approval_required": decision == "require_approval", "blocked": require_known or not approved_cost,
                })
                if require_known or not approved_cost:
                    explanations.append(f"{item.model_id}: unknown remote cost requires approval" if not require_known else f"{item.model_id}: policy requires known remote cost")
                    continue
            else:
                estimate = estimated_tokens * input_cost / 1_000_000 + 256 * output_cost / 1_000_000
                maximum = min(
                    request.constraints.maximum_estimated_cost_usd if request.constraints.maximum_estimated_cost_usd is not None else float("inf"),
                    float(policy.get("limits", {}).get("maximum_estimated_cost_usd", 0.25)),
                )
                if estimate > maximum:
                    explanations.append(f"{item.model_id}: estimated cost exceeds the task limit")
                    decisions.append({"decision": "deny", "source": source, "reason": "Estimated remote cost exceeds the task limit.", "task_type": request.task_type.value, "provider": item.provider_id, "model": item.model_id, "capability": "remote_cost", "approval_required": False, "blocked": True})
                    continue
        decision = evaluate(policy, source=source, task_type=request.task_type.value, provider=item.provider_id, model=item.model_id)
        provider_decision = decision.to_dict()
        provider_approved = _approval_covers(request, f"provider:{item.provider_id}", item)
        if decision.decision == "require_approval" and provider_approved:
            provider_decision["blocked"] = False
            provider_decision["approval_satisfied"] = True
        decisions.append(provider_decision)
        if decision.blocked and not provider_approved:
            explanations.append(f"{item.model_id}: {decision.decision}")
            continue
        if item.capabilities.network_required:
            network_decision = evaluate(
                policy, source=source, task_type=request.task_type.value,
                provider=item.provider_id, model=item.model_id, capability="network_access",
            )
            network_payload = network_decision.to_dict()
            network_approved = _approval_covers(request, "network_access", item)
            if network_decision.decision == "require_approval" and network_approved:
                network_payload["blocked"] = False
                network_payload["approval_satisfied"] = True
            decisions.append(network_payload)
            if network_decision.blocked and not network_approved:
                explanations.append(f"{item.model_id}: network access {network_decision.decision}")
                continue
        explanations.append(f"Selected {item.model_id}: first compatible configured candidate.")
        return RoutingResult(item, tuple(explanations), tuple(decisions))
    return RoutingResult(None, tuple(explanations or ["No compatible configured model is available."]), tuple(decisions))
