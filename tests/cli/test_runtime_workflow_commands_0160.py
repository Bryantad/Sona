"""CLI coverage for honest runtime status and inert workflow inspection."""

from __future__ import annotations

import json
from pathlib import Path

from sona import cli
from sona.workflow import (
    StepDefinition,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowJournalStore,
    WorkflowLedger,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


def _persist_workflow(root: Path) -> str:
    store = WorkflowJournalStore(root)
    ledger = WorkflowLedger(store=store)
    workflow_id = new_workflow_id()
    step_id = new_step_id()
    ledger.create(
        WorkflowDefinition(
            workflow_id,
            (
                TaskDefinition(
                    new_task_id(),
                    (StepDefinition(step_id, "build"),),
                ),
            ),
        )
    )
    return str(workflow_id)


def _execute(arguments, capsys) -> tuple[int, str, str]:
    args = cli.create_argument_parser().parse_args(arguments)
    result = {
        "workflow": cli.handle_workflow_command,
        "runtime": cli.handle_runtime_command,
        "service": cli.handle_service_command,
    }[args.command](args)
    captured = capsys.readouterr()
    return result, captured.out, captured.err


def test_workflow_list_when_no_journal_exists_does_not_create_workspace_data(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    code, output, error = _execute(["workflow", "list"], capsys)
    assert code == 0
    assert error == ""
    assert json.loads(output) == {"schema_version": 1, "status": "ok", "workflows": []}
    assert not (tmp_path / ".sona").exists()


def test_workflow_list_and_inspect_read_persisted_state_without_resuming(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / ".sona"
    workflow_id = _persist_workflow(root)

    code, output, error = _execute(["workflow", "list"], capsys)
    assert code == 0 and error == ""
    listed = json.loads(output)
    assert listed["workflows"][0]["workflow_id"] == workflow_id
    assert listed["workflows"][0]["state"] == "created"

    code, output, error = _execute(["workflow", "inspect", workflow_id], capsys)
    assert code == 0 and error == ""
    inspected = json.loads(output)
    assert inspected["recovery"].startswith("inert")
    assert inspected["workflow"]["tasks"][0]["steps"][0]["operation"] == "build"
    assert inspected["workflow"]["state"] == "created"


def test_workflow_inspect_missing_id_fails_without_leaking_root_path(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    code, output, error = _execute(
        ["workflow", "inspect", "00000000-0000-0000-0000-000000000000"], capsys
    )
    assert code == 1
    assert output == ""
    assert "unknown workflow ID" in error
    assert str(tmp_path) not in error


def test_runtime_and_service_status_do_not_claim_cross_process_visibility(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SONA_HOME", str(tmp_path / "sona-home"))
    code, output, error = _execute(["runtime", "status"], capsys)
    assert code == 0 and error == ""
    status = json.loads(output)
    assert status["status"] == "ok"
    assert status["models"]["registered"] == len(status["models"]["items"])
    assert status["workflows"]["persisted"] == 0
    assert status["services"]["status"] == "process_local"
    assert status["proof"]["receipt_schema"] == "schema-1"
    assert not (tmp_path / ".sona").exists()

    code, output, error = _execute(["service", "status"], capsys)
    assert code == 0 and error == ""
    service = json.loads(output)
    assert service["scope"] == "current-cli-process"
    assert service["registered_services"] is None


def test_runtime_status_lists_persistent_gguf_identities_without_claiming_readiness(
    tmp_path, monkeypatch, capsys, write_gguf
):
    from sona.intelligence import LocalModelRegistry, ModelFormat, ModelIdentity

    sona_home = tmp_path / "sona-home"
    monkeypatch.setenv("SONA_HOME", str(sona_home))
    artifact = tmp_path / "runtime-model.gguf"
    write_gguf(artifact)
    registry = LocalModelRegistry(sona_home / "models.json")
    registry.add(ModelIdentity(
        model_id="runtime-model",
        provider_id="local",
        runtime_id="llama-cpp",
        format=ModelFormat.GGUF,
        path=str(artifact),
        context_tokens=2048,
    ))
    registry.set_default("runtime-model")

    code, output, error = _execute(["runtime", "status", "--format", "json"], capsys)
    assert code == 0 and error == ""
    local_models = json.loads(output)["local_models"]
    assert local_models["registered"] == 1
    assert local_models["default_model_id"] == "runtime-model"
    assert local_models["items"][0]["artifact_exists"] is True
    assert local_models["items"][0]["hash_recorded"] is True
    assert "not_observable" in local_models["load_state"]


def test_doctor_parser_offers_machine_readable_format():
    args = cli.create_argument_parser().parse_args(["doctor", "--format", "json"])
    assert args.format == "json"


def test_doctor_json_contains_runtime_readiness_without_text_noise(monkeypatch, capsys):
    from sona.ai import local_models

    monkeypatch.setattr(
        local_models,
        "ensure_local_model",
        lambda **kwargs: {"status": "missing", "installed": False},
    )
    args = cli.create_argument_parser().parse_args(["doctor", "--format", "json"])
    assert cli.handle_doctor_command(args) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    result = json.loads(captured.out)
    assert result["runtime"]["schema_version"] == 1
    assert result["runtime"]["services"]["status"] == "process_local"
