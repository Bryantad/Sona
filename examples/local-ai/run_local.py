"""Run one direct GGUF inference without Ollama or a cloud fallback."""

from __future__ import annotations

import argparse

from sona.intelligence.contracts import InferenceRequest, ModelFormat, ModelIdentity
from sona.intelligence.llama_cpp_runtime import (
    LlamaCppRuntimeAdapter,
    LocalRuntimeError,
    discover_runtime,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", help="Path to a local GGUF artifact")
    parser.add_argument("--model-id", default="local-demo-model")
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--prompt", default="In one sentence, explain why bounded task queues matter."
    )
    args = parser.parse_args()

    discovery = discover_runtime()
    if not discovery.available:
        parser.error(discovery.diagnostic or "direct llama.cpp runtime is unavailable")

    identity = ModelIdentity(
        model_id=args.model_id,
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=args.model_path,
        context_tokens=args.context,
        device=args.device,
    )
    runtime = LlamaCppRuntimeAdapter()
    try:
        runtime.load(identity)
        response = runtime.infer(
            InferenceRequest(
                model_id=identity.model_id,
                prompt=args.prompt,
                maximum_output_tokens=min(256, args.context // 2),
            )
        )
        print(response.text, end="" if response.text.endswith("\n") else "\n")
        print(f"Runtime: {response.runtime_id} {response.runtime_version or ''}".strip())
        print(f"Provider: {response.provider_id} (local; no fallback)")
        return 0
    except LocalRuntimeError as exc:
        print(f"Direct local inference failed: {exc}")
        return 1
    finally:
        runtime.unload(identity.model_id)


if __name__ == "__main__":
    raise SystemExit(main())
