"""User-facing local GGUF registry commands."""

from __future__ import annotations

import json

from sona import cli


def _execute(arguments, capsys) -> tuple[int, str, str]:
    args = cli.create_argument_parser().parse_args(arguments)
    code = cli.handle_model_command(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_model_add_list_inspect_default_and_remove_use_one_persistent_registry(
    tmp_path, monkeypatch, capsys, write_gguf
):
    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    artifact = tmp_path / "Qwen Coder.gguf"
    write_gguf(artifact)

    code, output, error = _execute(
        ["model", "add", str(artifact), "--context", "8192", "--device", "cpu", "--set-default"],
        capsys,
    )
    assert code == 0 and error == ""
    added = json.loads(output)
    assert added["status"] == "ok"
    assert added["model"]["model_id"] == "Qwen-Coder"
    assert added["model"]["runtime_id"] == "llama-cpp"
    assert added["model"]["context_tokens"] == 8192
    assert added["default_model_id"] == "Qwen-Coder"

    code, output, error = _execute(["model", "list"], capsys)
    assert code == 0 and error == ""
    listed = json.loads(output)
    assert listed["default_local_model_id"] == "Qwen-Coder"
    assert listed["local_models"][0]["artifact_exists"] is True
    assert listed["local_models"][0]["is_default"] is True

    code, output, error = _execute(["model", "inspect", "Qwen-Coder", "--verify-hash"], capsys)
    assert code == 0 and error == ""
    inspected = json.loads(output)
    assert inspected["hash_verified"] is True
    assert inspected["gguf_metadata"]["architecture"] == "llama"
    assert inspected["gguf_metadata"]["quantization"] == "Q4_K_M"
    assert inspected["compatibility"]["status"] in {"preflight_pass", "runtime_unavailable"}
    assert inspected["compatibility"]["load_required_to_certify"] is True

    write_gguf(artifact, model_name="Modified after registration")
    code, output, error = _execute(["model", "inspect", "Qwen-Coder", "--verify-hash"], capsys)
    assert code == 1 and error == ""
    assert json.loads(output)["status"] == "integrity_mismatch"

    next_artifact = tmp_path / "next.gguf"
    write_gguf(next_artifact)
    code, output, error = _execute(
        ["model", "add", str(next_artifact), "--id", "next-model"], capsys
    )
    assert code == 0 and error == ""
    code, output, error = _execute(["model", "default", "next-model"], capsys)
    assert code == 0 and error == ""
    assert json.loads(output)["default_model_id"] == "next-model"

    code, output, error = _execute(["model", "remove", "Qwen-Coder"], capsys)
    assert code == 0 and error == ""
    removed = json.loads(output)
    assert removed["artifact_deleted"] is False
    assert removed["default_model_id"] == "next-model"
    assert artifact.is_file()

    code, output, error = _execute(["model", "remove", "next-model"], capsys)
    assert code == 0 and error == ""
    assert json.loads(output)["default_model_id"] is None
    assert next_artifact.is_file()


def test_model_commands_reject_invalid_artifacts_and_context_before_registry_mutation(
    tmp_path, monkeypatch, capsys, write_gguf
):
    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    invalid = tmp_path / "not-a-model.gguf"
    invalid.write_bytes(b"NOPE" + b"data")

    code, output, error = _execute(["model", "add", str(invalid)], capsys)
    assert code == 1
    assert output == ""
    assert "valid supported GGUF" in error
    registry_path = tmp_path / "sona-home" / "models.json"
    assert not registry_path.exists()

    valid = tmp_path / "valid.gguf"
    write_gguf(valid)
    code, output, error = _execute(["model", "add", str(valid), "--context", "0"], capsys)
    assert code == 1
    assert output == ""
    assert "context_tokens must be positive" in error
    assert not registry_path.exists()


def test_model_list_text_is_read_only_when_registry_is_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    code, output, error = _execute(["model", "list", "--format", "text"], capsys)
    assert code == 0 and error == ""
    assert "No local GGUF models are registered." in output
    assert not (tmp_path / "sona-home").exists()


def test_model_inspect_blocks_cuda_before_any_model_load(tmp_path, monkeypatch, capsys, write_gguf):
    from sona.intelligence import HardwareProfile, RuntimeDiscovery

    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    artifact = write_gguf(tmp_path / "cuda-model.gguf")
    code, _, error = _execute(
        ["model", "add", str(artifact), "--id", "cuda-model", "--device", "cuda"],
        capsys,
    )
    assert code == 0 and error == ""

    import sona.intelligence as intelligence

    monkeypatch.setattr(
        intelligence,
        "discover_runtime",
        lambda: RuntimeDiscovery(
            available=True,
            version="test-runtime",
            cpu_supported=True,
            gpu_offload_compiled=False,
        ),
    )
    monkeypatch.setattr(
        intelligence,
        "discover_hardware_profile",
        lambda **kwargs: HardwareProfile(logical_cpu_count=8),
    )

    code, output, error = _execute(["model", "inspect", "cuda-model"], capsys)

    assert code == 1 and error == ""
    result = json.loads(output)
    assert result["compatibility"]["status"] == "blocked"
    assert "no GPU-offload support" in result["compatibility"]["blockers"][0]


def test_model_inspect_text_is_clear_and_never_claims_load_certification(
    tmp_path, monkeypatch, capsys, write_gguf
):
    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    artifact = write_gguf(tmp_path / "text-model.gguf")
    code, _, error = _execute(
        ["model", "add", str(artifact), "--id", "text-model", "--device", "cpu"],
        capsys,
    )
    assert code == 0 and error == ""

    code, output, error = _execute(["model", "inspect", "text-model", "--format", "text"], capsys)

    assert code == 0 and error == ""
    assert "Sona Model Inspection" in output
    assert "Architecture   llama" in output
    assert "Quantization   Q4_K_M" in output
    assert "GPU offload" in output
    assert "Preflight" in output
    assert "does not load weights or certify" in output
