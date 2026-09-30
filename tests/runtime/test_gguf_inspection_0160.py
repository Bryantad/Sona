"""Safe GGUF metadata inspection and pre-load compatibility checks."""

from __future__ import annotations

import json
import struct
from dataclasses import replace

import pytest

from sona.intelligence import (
    GGUFFormatError,
    LocalModelRegistry,
    ModelFormat,
    ModelIdentity,
    ModelRegistryError,
    RuntimeDiscovery,
    assess_model_preflight,
    read_gguf_metadata,
)
from sona.intelligence.contracts import HardwareProfile


def _identity(path, *, architecture=None, context=4096, device="cpu"):
    return ModelIdentity(
        model_id="inspection-model",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=str(path),
        context_tokens=context,
        architecture=architecture,
        device=device,
    )


def test_reader_extracts_metadata_and_skips_tokenizer_string_arrays(tmp_path, write_gguf):
    path = write_gguf(tmp_path / "model.gguf", with_tokenizer_array=True)

    metadata = read_gguf_metadata(path)

    assert metadata.version == 3
    assert metadata.tensor_count == 1
    assert metadata.metadata_key_count == 5
    assert metadata.architecture == "llama"
    assert metadata.model_name == "Sona test model"
    assert metadata.context_length == 8192
    assert metadata.quantization == "Q4_K_M"
    assert metadata.alignment == 32


def test_reader_accepts_v2_and_rejects_bad_magic_unsupported_version_and_truncation(
    tmp_path, write_gguf
):
    v2 = write_gguf(tmp_path / "v2.gguf", version=2)
    assert read_gguf_metadata(v2).version == 2

    bad_magic = tmp_path / "bad-magic.gguf"
    bad_magic.write_bytes(b"NOPE" + v2.read_bytes()[4:])
    with pytest.raises(GGUFFormatError, match="magic is invalid"):
        read_gguf_metadata(bad_magic)

    unsupported = write_gguf(tmp_path / "future.gguf", version=4)
    with pytest.raises(GGUFFormatError, match="version 4 is unsupported"):
        read_gguf_metadata(unsupported)

    truncated = tmp_path / "truncated.gguf"
    truncated.write_bytes(v2.read_bytes()[:20])
    with pytest.raises(GGUFFormatError, match="truncated"):
        read_gguf_metadata(truncated)


def test_reader_bounds_header_counts_and_tensor_descriptors(tmp_path, write_gguf):
    for index, counts in enumerate(((1_000_001, 0), (0, 1_000_001))):
        oversized = tmp_path / f"oversized-{index}.gguf"
        oversized.write_bytes(b"GGUF" + struct.pack("<IQQ", 3, *counts))
        with pytest.raises(GGUFFormatError, match="entry count exceeds"):
            read_gguf_metadata(oversized)

    misaligned = write_gguf(tmp_path / "misaligned.gguf", tensor_offset=1)
    with pytest.raises(GGUFFormatError, match="violates the declared alignment"):
        read_gguf_metadata(misaligned)

    excessive_dimensions = write_gguf(tmp_path / "too-many-dimensions.gguf", tensor_dimensions=5)
    with pytest.raises(GGUFFormatError, match="dimension count is unsupported"):
        read_gguf_metadata(excessive_dimensions)


def test_reader_rejects_truncated_string_arrays(tmp_path):
    def encoded_string(value: str) -> bytes:
        raw = value.encode("utf-8")
        return struct.pack("<Q", len(raw)) + raw

    malformed = (
        b"GGUF"
        + struct.pack("<IQQ", 3, 0, 1)
        + encoded_string("tokenizer.ggml.tokens")
        + struct.pack("<IIQ", 9, 8, 1)
        + struct.pack("<Q", 10)
        + b"short"
    )
    path = tmp_path / "truncated-array.gguf"
    path.write_bytes(malformed)

    with pytest.raises(GGUFFormatError, match="file boundary"):
        read_gguf_metadata(path)


def test_registry_captures_metadata_and_rejects_declared_identity_or_context_mismatch(
    tmp_path, write_gguf
):
    path = write_gguf(tmp_path / "model.gguf")
    registry = LocalModelRegistry(tmp_path / "models.json")

    with pytest.raises(ModelRegistryError, match="architecture does not match"):
        registry.add(_identity(path, architecture="mpt"))
    with pytest.raises(ModelRegistryError, match="quantization does not match"):
        registry.add(replace(_identity(path), quantization="Q8_0"))
    with pytest.raises(ModelRegistryError, match="context exceeds"):
        registry.add(_identity(path, context=16384))
    assert not (tmp_path / "models.json").exists()


def test_model_registry_rejects_metadata_only_gguf_container(tmp_path, write_gguf):
    path = write_gguf(tmp_path / "metadata-only.gguf", tensor=False)
    with pytest.raises(ModelRegistryError, match="contains no model tensors"):
        LocalModelRegistry(tmp_path / "models.json").add(_identity(path))


def test_preflight_blocks_context_and_cuda_mismatches_without_claiming_certification(
    tmp_path, write_gguf
):
    path = write_gguf(tmp_path / "model.gguf")
    metadata = read_gguf_metadata(path)
    hardware = HardwareProfile(
        logical_cpu_count=8,
        physical_memory_bytes=16 * 1024**3,
        accelerator=None,
    )
    runtime = RuntimeDiscovery(
        available=True,
        version="test",
        cpu_supported=True,
        gpu_offload_compiled=False,
    )

    context = assess_model_preflight(_identity(path, context=16384), metadata, hardware, runtime)
    assert context["status"] == "blocked"
    assert context["load_required_to_certify"] is True
    assert "context" in context["blockers"][0]

    cuda = assess_model_preflight(_identity(path, device="cuda"), metadata, hardware, runtime)
    assert cuda["status"] == "blocked"
    assert any("CUDA" in blocker for blocker in cuda["blockers"])


def test_preflight_reports_runtime_unavailable_without_mislabeling_model_support(
    tmp_path, write_gguf
):
    path = write_gguf(tmp_path / "model.gguf")
    result = assess_model_preflight(
        _identity(path),
        read_gguf_metadata(path),
        HardwareProfile(logical_cpu_count=4),
        RuntimeDiscovery(available=False, cpu_supported=False),
    )

    assert result["status"] == "runtime_unavailable"
    assert result["resource_enforcement"] == "not_performed"
    assert "do not prove" in result["note"]


def test_preflight_reports_memory_risk_without_falsely_claiming_enforcement(tmp_path, write_gguf):
    path = write_gguf(tmp_path / "model.gguf")
    result = assess_model_preflight(
        _identity(path),
        read_gguf_metadata(path),
        HardwareProfile(physical_memory_bytes=1),
        RuntimeDiscovery(available=True, cpu_supported=True),
        artifact_size_bytes=path.stat().st_size,
    )

    assert result["status"] == "preflight_pass"
    assert "larger than observed physical RAM" in result["resource_warnings"][0]
    assert result["resource_enforcement"] == "not_performed"


def test_persisted_registry_with_invalid_gguf_stays_inspectable_as_invalid(tmp_path, write_gguf):
    path = write_gguf(tmp_path / "model.gguf")
    document = {
        "schema_version": 1,
        "default_model_id": "inspection-model",
        "models": [
            {
                "model_id": "inspection-model",
                "provider_id": "local",
                "runtime_id": "llama-cpp",
                "format": "gguf",
                "path": str(path),
                "context_tokens": 4096,
                "sha256": None,
                "architecture": None,
                "quantization": None,
                "device": "cpu",
                "schema_version": 1,
            }
        ],
    }
    registry_path = tmp_path / "models.json"
    registry_path.write_text(json.dumps(document), encoding="utf-8")
    registry = LocalModelRegistry(registry_path)
    path.write_bytes(b"GGUF" + b"truncated")

    inspection = registry.inspect("inspection-model")

    assert inspection.artifact_exists is True
    assert inspection.format_valid is False
    assert inspection.metadata is None
    assert inspection.metadata_error
