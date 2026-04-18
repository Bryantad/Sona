import importlib.util
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse

import pytest

from sona import cli
from sona.integrations.memory import MemoryDisabledError, RuntimeMemoryInstrumentation
from sona.integrations.memory.context import RuntimeMemoryContext
from sona.interpreter import SonaUnifiedInterpreter
from sona.stdlib.native_memory import build_native_bridge

DEMO_NAMESPACE = "/projects/sona-demo"
DEMO_NEGATIVE_NAMESPACE_PREFIX = "/projects/sona-demo-negative-"
DEMO_CONTENT = "demo memory seeded from sdk"
DEMO_SUBJECT = "sona-demo"
DEMO_KIND = "demo_seed"
MEMORY_SERVER_REPO = Path(
    os.getenv(
        "SONA_MEMORY_SERVER_REPO",
        r"F:\cognitive infastructure\persistent_memory_project",
    )
)
SDK_SEED_SCRIPT = MEMORY_SERVER_REPO / "examples" / "sdk_seed_memory.py"
OPENAI_SUPPORT_SCRIPT = MEMORY_SERVER_REPO / "tools" / "openai_demo_support.py"
OLLAMA_SUPPORT_SCRIPT = MEMORY_SERVER_REPO / "tools" / "ollama_demo_support.py"


def _load_openai_demo_support():
    if not OPENAI_SUPPORT_SCRIPT.exists():
        pytest.skip(f"OpenAI demo support script not found: {OPENAI_SUPPORT_SCRIPT}")
    spec = importlib.util.spec_from_file_location("openai_demo_support", OPENAI_SUPPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {OPENAI_SUPPORT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


OPENAI_SUPPORT = _load_openai_demo_support()
OPENAI_DEMO_NAMESPACE = OPENAI_SUPPORT.DEMO_NAMESPACE
OPENAI_DEMO_NEGATIVE_NAMESPACE_PREFIX = "/projects/openai-mcp-demo-negative-"
OPENAI_DEMO_CONTENT = OPENAI_SUPPORT.DEMO_CONTENT
OPENAI_DEMO_SUBJECT = OPENAI_SUPPORT.DEMO_SUBJECT
OPENAI_DEMO_KIND = OPENAI_SUPPORT.DEMO_KIND
OPENAI_DEMO_POSITIVE_OUTPUT = OPENAI_SUPPORT.EXPECTED_SONA_OUTPUT
OPENAI_DEMO_NEGATIVE_OUTPUT = OPENAI_SUPPORT.EXPECTED_SONA_NEGATIVE_OUTPUT


def _load_ollama_demo_support():
    if not OLLAMA_SUPPORT_SCRIPT.exists():
        pytest.skip(f"Ollama demo support script not found: {OLLAMA_SUPPORT_SCRIPT}")
    spec = importlib.util.spec_from_file_location("ollama_demo_support", OLLAMA_SUPPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {OLLAMA_SUPPORT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


OLLAMA_SUPPORT = _load_ollama_demo_support()
OLLAMA_DEMO_NAMESPACE = OLLAMA_SUPPORT.DEMO_NAMESPACE
OLLAMA_DEMO_NEGATIVE_NAMESPACE_PREFIX = "/projects/ollama-offline-demo-negative-"
OLLAMA_DEMO_CONTENT = OLLAMA_SUPPORT.DEMO_CONTENT
OLLAMA_DEMO_SUBJECT = OLLAMA_SUPPORT.DEMO_SUBJECT
OLLAMA_DEMO_KIND = OLLAMA_SUPPORT.DEMO_KIND
OLLAMA_DEMO_POSITIVE_OUTPUT = OLLAMA_SUPPORT.EXPECTED_SONA_OUTPUT
OLLAMA_DEMO_NEGATIVE_OUTPUT = OLLAMA_SUPPORT.EXPECTED_SONA_NEGATIVE_OUTPUT


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeMemoryBackend:
    def __init__(self):
        self.events: list[dict] = []
        self.memories: list[dict] = []
        self.reflections: list[dict] = []
        self.calls: list[tuple[str, str]] = []
        self.fail_event_kinds: set[str] = set()

    def urlopen(self, request, timeout=10.0):
        method = request.get_method()
        parsed = urlparse(request.full_url)
        path = parsed.path
        self.calls.append((method, path))
        body = (
            json.loads(request.data.decode("utf-8"))
            if getattr(request, "data", None)
            else None
        )

        if path == "/v1/events" and method == "POST":
            event = body["event"]
            if event["event_kind"] in self.fail_event_kinds:
                raise URLError(f"forced failure for {event['event_kind']}")
            event_id = f"evt_{len(self.events) + 1:03d}"
            stored = {
                "event_id": event_id,
                **event,
            }
            self.events.append(stored)
            return _FakeResponse({"event_id": event_id})

        if path == "/v1/memories" and method == "POST":
            memory_id = f"mem_{len(self.memories) + 1:03d}"
            stored = {"memory_id": memory_id, **body}
            self.memories.append(stored)
            return _FakeResponse({"memory_id": memory_id, "status": "accepted"})

        if path == "/v1/memories/search" and method == "POST":
            query = (body.get("query") or "").lower()
            subject = body.get("subject")
            kind = body.get("kind")
            namespace = body.get("namespace")
            items = []
            for memory in self.memories:
                if namespace and memory.get("namespace") != namespace:
                    continue
                if subject and memory.get("subject") != subject:
                    continue
                if kind and memory.get("kind") != kind:
                    continue
                if query and query not in str(memory.get("content", "")).lower():
                    continue
                items.append(memory)
            limit = int(body.get("limit") or len(items) or 25)
            return _FakeResponse({"items": items[:limit], "next_cursor": None})

        if path.startswith("/v1/traces/") and method == "GET":
            trace_id = path.split("/v1/traces/", 1)[1]
            events = [
                event
                for event in self.events
                if event.get("trace_id") == trace_id
            ]
            return _FakeResponse(
                {
                    "trace_id": trace_id,
                    "events": events,
                }
            )

        if path.startswith("/v1/traces/") and path.endswith(":replay") and method == "POST":
            trace_id = path.split("/v1/traces/", 1)[1].split(":replay", 1)[0]
            events = [
                event
                for event in self.events
                if event.get("trace_id") == trace_id
            ]
            return _FakeResponse(
                {
                    "trace_id": trace_id,
                    "mode": body.get("mode", "dry_run"),
                    "events": events,
                }
            )

        if path == "/v1/reflections:run" and method == "POST":
            reflection_id = f"refl_{len(self.reflections) + 1:03d}"
            stored = {"reflection_id": reflection_id, **body}
            self.reflections.append(stored)
            return _FakeResponse({"reflection_id": reflection_id, "status": "accepted"})

        raise AssertionError(f"Unexpected request: {method} {path}")


def _write_program(path: Path, source: str) -> Path:
    path.write_text(source.strip() + "\n", encoding="utf-8")
    return path


def _run_cli(args: list[str], monkeypatch, cwd: Path) -> int:
    cli.default_interpreter = None
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "argv", ["sona", *args])
    return cli.main()


def _enable_memory(
    monkeypatch,
    backend: FakeMemoryBackend,
    *,
    auto_reflect: bool = False,
    namespace: str | None = None,
) -> None:
    monkeypatch.setenv("SONA_MEMORY_ENABLED", "true")
    monkeypatch.setenv("SONA_MEMORY_BASE_URL", "http://memory.test")
    monkeypatch.setenv("SONA_MEMORY_TOKEN", "test-token")
    monkeypatch.setenv("SONA_MEMORY_AUTO_REFLECT", "true" if auto_reflect else "false")
    if namespace is None:
        monkeypatch.delenv("SONA_MEMORY_NAMESPACE", raising=False)
    else:
        monkeypatch.setenv("SONA_MEMORY_NAMESPACE", namespace)
    monkeypatch.setattr("sona.integrations.memory.client.urlopen", backend.urlopen)


def _example_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / name


def _load_sdk_seed_module():
    if not SDK_SEED_SCRIPT.exists():
        pytest.skip(f"SDK seed script not found: {SDK_SEED_SCRIPT}")
    spec = importlib.util.spec_from_file_location("sdk_seed_memory", SDK_SEED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {SDK_SEED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _last_output_line(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return ""
    return lines[-1]


def test_memory_smod_imports_when_memory_is_disabled():
    interpreter = SonaUnifiedInterpreter()
    result = interpreter.interpret(
        """
        import memory;
        [memory.module_format, memory.runtime_backend]
        """
    )
    assert result == ["smod-runtime", "smod-bridge"]


def test_memory_smod_imports_when_memory_is_misconfigured(monkeypatch):
    monkeypatch.setenv("SONA_MEMORY_ENABLED", "true")
    monkeypatch.delenv("SONA_MEMORY_BASE_URL", raising=False)
    monkeypatch.delenv("SONA_MEMORY_TOKEN", raising=False)

    interpreter = SonaUnifiedInterpreter()
    result = interpreter.interpret(
        """
        import memory;
        [memory.module_format, memory.runtime_backend]
        """
    )
    assert result == ["smod-runtime", "smod-bridge"]


def test_native_memory_bridge_raises_only_on_invocation(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    context = RuntimeMemoryContext.create_for_cli_run(
        project_root=tmp_path,
        program_path=str(tmp_path / "demo.sona"),
        entrypoint="demo",
        argv=["demo.sona"],
    )
    interpreter._runtime_memory_context = context
    bridge = build_native_bridge(interpreter)

    assert hasattr(bridge, "memory_search")
    assert hasattr(bridge, "memory_record")
    assert hasattr(bridge, "memory_get_trace")
    assert hasattr(bridge, "memory_reflect")

    with pytest.raises(MemoryDisabledError):
        bridge.memory_search("timeout")


def test_runtime_context_accessor_round_trip(tmp_path):
    interpreter = SonaUnifiedInterpreter(project_root=tmp_path)
    instrumentation = RuntimeMemoryInstrumentation(interpreter)
    context = instrumentation.create_context(file_path=str(tmp_path / "demo.sona"))

    instrumentation.attach_context(context)
    assert interpreter.get_runtime_memory_context() is context

    instrumentation.clear_context()
    assert interpreter.get_runtime_memory_context() is None


def test_lifecycle_failures_do_not_fail_cli_execution(tmp_path, monkeypatch):
    backend = FakeMemoryBackend()
    backend.fail_event_kinds.add("session.started")
    _enable_memory(monkeypatch, backend)

    captured: dict[str, RuntimeMemoryContext] = {}
    original_class = RuntimeMemoryInstrumentation

    class CapturingInstrumentation(original_class):
        def create_context(self, *, file_path: str | None):
            context = super().create_context(file_path=file_path)
            captured["context"] = context
            return context

    monkeypatch.setattr(
        "sona.integrations.memory.instrumentation.RuntimeMemoryInstrumentation",
        CapturingInstrumentation,
    )

    program = _write_program(
        tmp_path / "lifecycle_ok.sona",
        """
        "ok";
        """,
    )

    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)
    assert exit_code == 0
    assert captured["context"].memory_enabled is False
    assert captured["context"].lifecycle_failures


def test_trace_closed_attempted_and_auto_reflection_enqueue_once(tmp_path, monkeypatch):
    backend = FakeMemoryBackend()
    backend.fail_event_kinds.add("trace.closed")
    _enable_memory(monkeypatch, backend, auto_reflect=True)

    captured: dict[str, RuntimeMemoryContext] = {}
    original_class = RuntimeMemoryInstrumentation

    class CapturingInstrumentation(original_class):
        def create_context(self, *, file_path: str | None):
            context = super().create_context(file_path=file_path)
            captured["context"] = context
            return context

    monkeypatch.setattr(
        "sona.integrations.memory.instrumentation.RuntimeMemoryInstrumentation",
        CapturingInstrumentation,
    )

    program = _write_program(
        tmp_path / "reflect_once.sona",
        """
        import memory;
        memory.record("deploy timeout happened", {"kind": "failure_observation"});
        "done";
        """,
    )

    exit_code = _run_cli([str(program)], monkeypatch, tmp_path)

    assert exit_code == 0
    assert captured["context"].last_trace_closed_attempted is True
    assert captured["context"].auto_reflection_enqueued is True
    assert len(backend.reflections) == 0


def test_cli_memory_run_has_monotonic_sequence_across_lifecycle_and_native_calls(
    tmp_path,
    monkeypatch,
):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend)

    program = _write_program(
        tmp_path / "sequence_demo.sona",
        """
        import memory;
        memory.record("deployment timeout happened", {
            "kind": "failure_observation",
            "subject": "deploy_flow"
        });
        let hits = memory.search("deployment timeout", {"subject": "deploy_flow"});
        1;
        """,
    )

    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)

    assert exit_code == 0
    event_kinds = [event["event_kind"] for event in backend.events]
    assert event_kinds == [
        "session.started",
        "trace.opened",
        "message.user_received",
        "tool.call_requested",
        "tool.call_succeeded",
        "tool.call_requested",
        "tool.call_succeeded",
        "message.model_emitted",
        "trace.closed",
        "session.ended",
    ]

    event_sequences = [
        event["provenance"]["sona_runtime"]["sequence_no"]
        for event in backend.events
    ]
    memory_sequences = [
        memory["metadata"]["_sona_runtime"]["sequence_no"]
        for memory in backend.memories
    ]
    combined = sorted(event_sequences + memory_sequences)
    assert combined == list(range(1, len(combined) + 1))


def test_cli_memory_record_emits_one_visible_tool_pair_and_no_transport_tool_events(
    tmp_path,
    monkeypatch,
):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend)

    program = _write_program(
        tmp_path / "single_record.sona",
        """
        import memory;
        let receipt = memory.record("deployment timeout happened", {
            "kind": "failure_observation",
            "subject": "deploy_flow"
        });
        print(receipt["status"]);
        """,
    )

    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)

    assert exit_code == 0
    tool_events = [
        event
        for event in backend.events
        if event["event_kind"].startswith("tool.call_")
    ]
    assert [event["event_kind"] for event in tool_events] == [
        "tool.call_requested",
        "tool.call_succeeded",
    ]
    assert {
        event["payload"]["tool_name"]
        for event in tool_events
    } == {"memory.memory_record"}
    assert all(event["payload"]["module_name"] == "memory" for event in tool_events)
    assert all(
        event["payload"]["function_name"] == "memory_record"
        for event in tool_events
    )
    assert "message.model_emitted" not in [
        event["event_kind"] for event in backend.events
    ]


def test_cli_memory_persists_across_two_real_runs(tmp_path, monkeypatch, capsys):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend)

    writer = _write_program(
        tmp_path / "writer.sona",
        """
        import memory;
        memory.record("deployment timeout happened", {
            "kind": "failure_pattern",
            "subject": "deploy_flow"
        });
        print("recorded");
        """,
    )
    reader = _write_program(
        tmp_path / "reader.sona",
        """
        import memory;
        let hits = memory.search("deployment timeout", {
            "kind": "failure_pattern",
            "subject": "deploy_flow"
        });
        if hits["count"] > 0 {
            print("Known failure pattern detected");
        } else {
            print("No known failure pattern");
        }
        """,
    )

    first_exit = _run_cli(["run", str(writer)], monkeypatch, tmp_path)
    first_output = capsys.readouterr().out
    second_exit = _run_cli([str(reader)], monkeypatch, tmp_path)
    second_output = capsys.readouterr().out

    assert first_exit == 0
    assert second_exit == 0
    assert "recorded" in first_output
    assert "Known failure pattern detected" in second_output


def test_documented_pure_sona_demo_outputs_exact_messages(tmp_path, monkeypatch, capsys):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend, namespace=DEMO_NAMESPACE)

    first_program = _example_path("memory_first_run.sona")
    second_program = _example_path("memory_second_run.sona")

    first_exit = _run_cli(["run", str(first_program)], monkeypatch, tmp_path)
    first_output = _last_output_line(capsys.readouterr().out)
    second_exit = _run_cli(["run", str(second_program)], monkeypatch, tmp_path)
    second_output = _last_output_line(capsys.readouterr().out)

    assert first_exit == 0
    assert second_exit == 0
    assert first_output == "Recorded demo memory."
    assert second_output == "Prior demo memory found."


def test_documented_negative_demo_flow_uses_unique_namespace(tmp_path, monkeypatch, capsys):
    backend = FakeMemoryBackend()
    unique_namespace = f"{DEMO_NEGATIVE_NAMESPACE_PREFIX}{uuid.uuid4().hex[:8]}"
    _enable_memory(monkeypatch, backend, namespace=unique_namespace)

    second_program = _example_path("memory_second_run.sona")

    exit_code = _run_cli(["run", str(second_program)], monkeypatch, tmp_path)
    output = _last_output_line(capsys.readouterr().out)

    assert exit_code == 0
    assert output == "No prior demo memory found."


def test_shared_backend_sdk_seed_then_sona_reader_demo(tmp_path, monkeypatch, capsys):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend, namespace=DEMO_NAMESPACE)
    seed_module = _load_sdk_seed_module()

    class FakeSdkClient:
        def __init__(self):
            self.record_calls: list[tuple[dict, str]] = []

        def record_memory(self, payload: dict, idempotency_key: str):
            self.record_calls.append((payload, idempotency_key))
            memory_id = f"mem_{len(backend.memories) + 1:03d}"
            backend.memories.append({"memory_id": memory_id, **payload})
            return {
                "accepted": True,
                "details": {"memory_id": memory_id},
                "event_ids": [f"evt_seed_{len(self.record_calls):03d}"],
            }

        def close(self):
            return None

    fake_client = FakeSdkClient()
    seed_exit = seed_module.main([], client_factory=lambda *_args, **_kwargs: fake_client)
    seed_output = capsys.readouterr().out

    second_program = _example_path("memory_second_run.sona")
    second_exit = _run_cli(["run", str(second_program)], monkeypatch, tmp_path)
    second_output = _last_output_line(capsys.readouterr().out)

    assert seed_exit == 0
    assert seed_output.splitlines()[0] == f"Seeded demo memory into {DEMO_NAMESPACE}."
    assert fake_client.record_calls[0][0]["namespace"] == DEMO_NAMESPACE
    assert fake_client.record_calls[0][0]["content"] == DEMO_CONTENT
    assert fake_client.record_calls[0][0]["subject"] == DEMO_SUBJECT
    assert fake_client.record_calls[0][0]["kind"] == DEMO_KIND
    assert second_exit == 0
    assert second_output == "Prior demo memory found."


def test_fs_dispatcher_routes_minimal_subset_without_changing_behavior(
    tmp_path,
    monkeypatch,
    capsys,
):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend)

    program = _write_program(
        tmp_path / "fs_dispatch_demo.sona",
        """
        import fs;
        fs.write("dispatch-demo.txt", "bridge data");
        if fs.exists("dispatch-demo.txt") {
            print(fs.read("dispatch-demo.txt"));
        }
        """,
    )

    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)
    output = _last_output_line(capsys.readouterr().out)

    tool_events = [
        event
        for event in backend.events
        if event["event_kind"] in {"tool.call_requested", "tool.call_succeeded"}
    ]

    assert exit_code == 0
    assert output == "bridge data"
    assert (tmp_path / "dispatch-demo.txt").read_text(encoding="utf-8") == "bridge data"
    assert [event["payload"]["tool_name"] for event in tool_events] == [
        "fs.fs_write",
        "fs.fs_write",
        "fs.fs_exists",
        "fs.fs_exists",
        "fs.fs_read",
        "fs.fs_read",
    ]


def test_cli_sequence_is_monotonic_across_lifecycle_memory_and_fs_calls(
    tmp_path,
    monkeypatch,
):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend, namespace=DEMO_NAMESPACE)

    program = _write_program(
        tmp_path / "sequence_memory_fs_demo.sona",
        """
        import fs;
        import memory;
        fs.write("seq-demo.txt", "bridge data");
        let present = fs.exists("seq-demo.txt");
        if present {
            fs.read("seq-demo.txt");
        }
        memory.record("demo memory seeded from sdk", {
            "kind": "demo_seed",
            "subject": "sona-demo"
        });
        print("dispatch mix ok");
        """,
    )

    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)

    assert exit_code == 0
    event_sequences = [
        event["provenance"]["sona_runtime"]["sequence_no"]
        for event in backend.events
    ]
    memory_sequences = [
        memory["metadata"]["_sona_runtime"]["sequence_no"]
        for memory in backend.memories
    ]
    combined = sorted(event_sequences + memory_sequences)
    assert combined == list(range(1, len(combined) + 1))


def test_openai_demo_reader_prints_exact_positive_output(tmp_path, monkeypatch, capsys):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend, namespace=OPENAI_DEMO_NAMESPACE)
    backend.memories.append(
        {
            "memory_id": "mem_openai_demo_001",
            "namespace": OPENAI_DEMO_NAMESPACE,
            "content": OPENAI_DEMO_CONTENT,
            "subject": OPENAI_DEMO_SUBJECT,
            "kind": OPENAI_DEMO_KIND,
        }
    )
    backend.memories.append(
        {
            "memory_id": "mem_openai_demo_other",
            "namespace": OPENAI_DEMO_NAMESPACE,
            "content": "other memory in same namespace",
            "subject": OPENAI_DEMO_SUBJECT,
            "kind": OPENAI_DEMO_KIND,
        }
    )

    program = _example_path("openai_memory_reader.sona")
    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)
    output = _last_output_line(capsys.readouterr().out)

    assert exit_code == 0
    assert output == OPENAI_DEMO_POSITIVE_OUTPUT


def test_openai_demo_reader_prints_exact_negative_output_for_unique_namespace(
    tmp_path,
    monkeypatch,
    capsys,
):
    backend = FakeMemoryBackend()
    unique_namespace = f"{OPENAI_DEMO_NEGATIVE_NAMESPACE_PREFIX}{uuid.uuid4().hex[:8]}"
    _enable_memory(monkeypatch, backend, namespace=unique_namespace)

    program = _example_path("openai_memory_reader.sona")
    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)
    output = _last_output_line(capsys.readouterr().out)

    assert exit_code == 0
    assert output == OPENAI_DEMO_NEGATIVE_OUTPUT


def test_ollama_demo_reader_prints_exact_positive_output(tmp_path, monkeypatch, capsys):
    backend = FakeMemoryBackend()
    _enable_memory(monkeypatch, backend, namespace=OLLAMA_DEMO_NAMESPACE)
    backend.memories.append(
        {
            "memory_id": "mem_ollama_demo_001",
            "namespace": OLLAMA_DEMO_NAMESPACE,
            "content": OLLAMA_DEMO_CONTENT,
            "subject": OLLAMA_DEMO_SUBJECT,
            "kind": OLLAMA_DEMO_KIND,
        }
    )
    backend.memories.append(
        {
            "memory_id": "mem_ollama_demo_other",
            "namespace": OLLAMA_DEMO_NAMESPACE,
            "content": "other memory in same namespace",
            "subject": OLLAMA_DEMO_SUBJECT,
            "kind": OLLAMA_DEMO_KIND,
        }
    )

    program = _example_path("ollama_memory_reader.sona")
    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)
    output = _last_output_line(capsys.readouterr().out)

    assert exit_code == 0
    assert output == OLLAMA_DEMO_POSITIVE_OUTPUT


def test_ollama_demo_reader_prints_exact_negative_output_for_unique_namespace(
    tmp_path,
    monkeypatch,
    capsys,
):
    backend = FakeMemoryBackend()
    unique_namespace = f"{OLLAMA_DEMO_NEGATIVE_NAMESPACE_PREFIX}{uuid.uuid4().hex[:8]}"
    _enable_memory(monkeypatch, backend, namespace=unique_namespace)

    program = _example_path("ollama_memory_reader.sona")
    exit_code = _run_cli(["run", str(program)], monkeypatch, tmp_path)
    output = _last_output_line(capsys.readouterr().out)

    assert exit_code == 0
    assert output == OLLAMA_DEMO_NEGATIVE_OUTPUT
