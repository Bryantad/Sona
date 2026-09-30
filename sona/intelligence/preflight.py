"""Static local-model checks that run before llama.cpp loads model weights."""

from __future__ import annotations

from .contracts import HardwareProfile, ModelIdentity
from .gguf import GGUFMetadata
from .llama_cpp_runtime import RuntimeDiscovery


def assess_model_preflight(
    identity: ModelIdentity,
    metadata: GGUFMetadata | None,
    hardware: HardwareProfile,
    runtime: RuntimeDiscovery,
    *,
    artifact_size_bytes: int | None = None,
) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    blockers: list[str] = []
    resource_warnings: list[str] = []
    if metadata is None:
        blockers.append("valid GGUF metadata was not available")
        checks.append({"name": "gguf_metadata", "status": "blocked"})
    elif metadata.tensor_count == 0:
        blockers.append("GGUF artifact contains no model tensors")
        checks.append({"name": "gguf_metadata", "status": "blocked"})
    else:
        checks.append({"name": "gguf_metadata", "status": "pass", "version": metadata.version})
        if identity.architecture and identity.architecture != metadata.architecture:
            blockers.append("registered architecture does not match GGUF metadata")
            checks.append(
                {
                    "name": "architecture_identity",
                    "status": "blocked",
                    "registered": identity.architecture,
                    "artifact": metadata.architecture,
                }
            )
        else:
            checks.append(
                {"name": "architecture_identity", "status": "pass", "value": metadata.architecture}
            )
        if metadata.context_length is None:
            checks.append({"name": "context_limit", "status": "unknown"})
        elif identity.context_tokens > metadata.context_length:
            blockers.append("configured context exceeds the GGUF-declared architecture context")
            checks.append(
                {
                    "name": "context_limit",
                    "status": "blocked",
                    "configured": identity.context_tokens,
                    "declared": metadata.context_length,
                }
            )
        else:
            checks.append(
                {
                    "name": "context_limit",
                    "status": "pass",
                    "configured": identity.context_tokens,
                    "declared": metadata.context_length,
                }
            )

    if not runtime.available or not runtime.cpu_supported:
        checks.append({"name": "llama_cpp_runtime", "status": "unavailable"})
    else:
        checks.append(
            {
                "name": "llama_cpp_runtime",
                "status": "pass",
                "version": runtime.version,
                "gpu_offload_compiled": runtime.gpu_offload_compiled,
            }
        )

    effective_device = "cpu" if identity.device == "auto" else identity.device
    if effective_device == "cuda":
        if not runtime.gpu_offload_compiled:
            blockers.append("CUDA was selected but this llama.cpp build has no GPU-offload support")
            checks.append({"name": "cuda_backend", "status": "blocked"})
        elif hardware.accelerator != "nvidia-cuda":
            blockers.append("CUDA was selected but no NVIDIA GPU was detected")
            checks.append({"name": "cuda_device", "status": "blocked"})
        else:
            checks.append(
                {
                    "name": "cuda_device",
                    "status": "pass",
                    "name_value": hardware.accelerator_name,
                    "memory_bytes": hardware.accelerator_memory_bytes,
                }
            )
    else:
        checks.append({"name": "execution_device", "status": "pass", "effective": "cpu"})

    if (
        artifact_size_bytes is not None
        and hardware.physical_memory_bytes is not None
        and artifact_size_bytes > hardware.physical_memory_bytes
    ):
        resource_warnings.append(
            "artifact is larger than observed physical RAM; paging or load failure may result"
        )
    if (
        effective_device == "cuda"
        and artifact_size_bytes is not None
        and hardware.accelerator_memory_bytes is not None
        and artifact_size_bytes > hardware.accelerator_memory_bytes
    ):
        resource_warnings.append(
            "artifact is larger than the first detected GPU's VRAM; full offload may not fit"
        )

    if blockers:
        status = "blocked"
    elif not runtime.available or not runtime.cpu_supported:
        status = "runtime_unavailable"
    else:
        status = "preflight_pass"
    return {
        "status": status,
        "effective_device": effective_device,
        "checks": checks,
        "blockers": blockers,
        "resource_warnings": resource_warnings,
        "load_required_to_certify": True,
        "resource_enforcement": "not_performed",
        "note": (
            "These checks validate file metadata and declared runtime/device choices only. "
            "They do not prove architecture support, available memory, load success, "
            "or performance; "
            "a successful explicit runtime load is still required."
        ),
    }
