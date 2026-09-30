"""Exact, one-shot capability contract for editor-buffer-only Guide edits."""

from __future__ import annotations

import json
from pathlib import Path

from sona.guide.editor_authorization import (
    EditorBufferCapabilityBroker,
    GuideBufferPolicy,
    editor_buffer_authorization_audit,
)
from sona.runtime import CapabilityRequest, EffectClass, EffectDecision
from sona.stdlib import native_guardian as guardian

URI = "file:///private/workspace/app.sona"
SOURCE = "print(1);\n"
REPLACEMENT = "2"
PROPOSED = "print(2);\n"
SELECTION = {"start": {"line": 0, "character": 6}, "end": {"line": 0, "character": 7}}


def _project(root: Path, *, guardian_enabled: bool = False, allow_write: bool = False) -> Path:
    root.mkdir(parents=True)
    (root / "app.sona").write_text(SOURCE, encoding="utf-8")
    if guardian_enabled:
        (root / "sona.guard.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "capabilities": {
                        "filesystem_read": "deny",
                        "filesystem_write": "allow" if allow_write else "deny",
                        "network": "deny",
                    },
                }
            ),
            encoding="utf-8",
        )
        assert guardian.guardian_init(root)["status"] == "initialized"
    return root


def _prepare(broker: EditorBufferCapabilityBroker, root: Path, **overrides):
    args = {
        "project_root": root,
        "document_uri": URI,
        "document_version": 7,
        "selection": SELECTION,
        "source": SOURCE,
        "proposed_source": PROPOSED,
        "replacement": REPLACEMENT,
    }
    args.update(overrides)
    return broker.prepare(**args), args


def _consume(broker, handle, args, **overrides):
    args = {**args, **overrides}
    return broker.consume(handle=handle, **args)


def test_uninitialized_guardian_uses_narrow_policy_and_never_maps_fs_write(tmp_path):
    root = _project(tmp_path / "project")
    policy = GuideBufferPolicy(root)
    edit = policy.evaluate(
        CapabilityRequest(EffectClass.EDITOR_BUFFER_REPLACE, "guide-edit:" + "a" * 64, 5)
    )
    write = policy.evaluate(CapabilityRequest(EffectClass.FS_WRITE, "guide-edit:" + "a" * 64, 5))
    process = policy.evaluate(
        CapabilityRequest(EffectClass.PROCESS_EXECUTE, "guide-edit:" + "a" * 64, 5)
    )
    assert edit.decision is EffectDecision.ALLOWED
    assert write.decision is EffectDecision.DENIED
    assert process.decision is EffectDecision.DENIED

    broker = EditorBufferCapabilityBroker()
    prepared, args = _prepare(broker, root)
    assert prepared["status"] == "prepared"
    assert prepared["effect"] == "EDITOR.BUFFER_REPLACE"
    authorized = _consume(broker, prepared["handle"], args)
    assert authorized["status"] == "authorized"
    assert _consume(broker, prepared["handle"], args)["status"] == "denied"
    audit = broker.audit_snapshot(root)
    assert all(record.effect is EffectClass.EDITOR_BUFFER_REPLACE for record in audit)
    assert all(
        URI not in record.resource_ref and str(root) not in record.resource_ref for record in audit
    )
    assert json.dumps(prepared).find(str(root)) == -1
    assert (root / "app.sona").read_text(encoding="utf-8") == SOURCE
    assert not (root / ".sona" / "receipts").exists()


def test_guardian_valid_is_optional_gate_and_does_not_require_fs_write(tmp_path):
    root = _project(tmp_path / "project", guardian_enabled=True, allow_write=False)
    broker = EditorBufferCapabilityBroker()
    prepared, args = _prepare(broker, root)
    assert prepared["status"] == "prepared"
    assert _consume(broker, prepared["handle"], args)["status"] == "authorized"


def test_guardian_initialization_after_prepare_invalidates_exact_authorization(tmp_path):
    root = _project(tmp_path / "project")
    broker = EditorBufferCapabilityBroker()
    prepared, args = _prepare(broker, root)
    assert prepared["status"] == "prepared"
    (root / "sona.guard.json").write_text(
        json.dumps({"capabilities": {"filesystem_write": "deny"}}), encoding="utf-8"
    )
    assert guardian.guardian_init(root)["status"] == "initialized"
    result = _consume(broker, prepared["handle"], args)
    assert result["status"] == "denied"
    assert result["diagnostic_id"] == "SONA-GUIDE-AUTH-TRUST-CHANGED"


def test_changed_but_still_valid_guardian_state_invalidates_capability(tmp_path):
    root = _project(tmp_path / "project", guardian_enabled=True)
    broker = EditorBufferCapabilityBroker()
    prepared, args = _prepare(broker, root)
    baseline = root / ".sona" / "guardian" / "baseline.json"
    state = json.loads(baseline.read_text(encoding="utf-8"))
    baseline.write_text(json.dumps(state, indent=2), encoding="utf-8")
    assert guardian.guardian_check(root)["status"] == "ok"
    denied = _consume(broker, prepared["handle"], args)
    assert denied["status"] == "denied"
    assert denied["diagnostic_id"] == "SONA-GUIDE-AUTH-TRUST-CHANGED"


def test_guardian_drift_or_validation_error_fails_closed(tmp_path, monkeypatch):
    drift = _project(tmp_path / "drift", guardian_enabled=True)
    (drift / "app.sona").write_text("print(99);\n", encoding="utf-8")
    broker = EditorBufferCapabilityBroker()
    result, _ = _prepare(broker, drift)
    assert result["status"] == "denied"

    expected = _project(tmp_path / "expected", guardian_enabled=True)
    broker = EditorBufferCapabilityBroker()
    prepared, args = _prepare(broker, expected)
    assert prepared["status"] == "prepared"
    monkeypatch.setattr(
        guardian, "guardian_check", lambda _root: (_ for _ in ()).throw(RuntimeError("fail"))
    )
    consumed = _consume(broker, prepared["handle"], args)
    assert consumed["status"] == "denied"
    assert consumed["diagnostic_id"] == "SONA-GUIDE-AUTH-GUARDIAN-DENIED"


def test_exact_binding_rejects_wrong_selection_source_version_replacement_and_reuse(tmp_path):
    root = _project(tmp_path / "project")
    for change in (
        {"selection": {"start": {"line": 0, "character": 5}, "end": SELECTION["end"]}},
        {"document_version": 8},
        {"source": "print(9);\n"},
        {"replacement": "3", "proposed_source": "print(3);\n"},
    ):
        broker = EditorBufferCapabilityBroker()
        prepared, args = _prepare(broker, root)
        assert prepared["status"] == "prepared"
        denied = _consume(broker, prepared["handle"], args, **change)
        assert denied["status"] == "denied"
        assert _consume(broker, prepared["handle"], args)["status"] == "denied"


def test_capability_expiry_and_revocation_are_denied(tmp_path):
    now = [100.0]
    broker = EditorBufferCapabilityBroker(clock=lambda: now[0])
    root = _project(tmp_path / "project")
    prepared, args = _prepare(broker, root)
    now[0] += 6
    assert _consume(broker, prepared["handle"], args)["status"] == "denied"

    prepared, args = _prepare(broker, root)
    pending = broker._pending[prepared["handle"]]
    assert pending.authority.revoke(pending.token)
    result = _consume(broker, prepared["handle"], args)
    assert result["status"] == "denied"
    assert result["diagnostic_id"] == "SONA-GUIDE-AUTH-CAPABILITY-DENIED"


def test_invalid_proposal_never_mints_capability_and_policy_error_fails_closed(
    tmp_path, monkeypatch
):
    root = _project(tmp_path / "project")
    broker = EditorBufferCapabilityBroker()
    invalid, _ = _prepare(broker, root, proposed_source="print((2);\n")
    assert invalid["status"] == "denied"
    assert broker.audit_snapshot(root) == ()
    assert (
        broker.consume(
            handle="no-human-approval-no-capability",
            project_root=root,
            document_uri=URI,
            document_version=7,
            selection=SELECTION,
            source=SOURCE,
            proposed_source=PROPOSED,
            replacement=REPLACEMENT,
        )["status"]
        == "denied"
    )

    monkeypatch.setattr(
        GuideBufferPolicy, "evaluate", lambda *_args: (_ for _ in ()).throw(RuntimeError("policy"))
    )
    error, _ = _prepare(EditorBufferCapabilityBroker(), root)
    assert error["status"] == "denied"


def test_selection_mismatch_proposal_validation_and_root_identity_are_bound(tmp_path):
    root = _project(tmp_path / "project")
    broker = EditorBufferCapabilityBroker()
    bad, _ = _prepare(broker, root, proposed_source="print(3);\n")
    assert bad["status"] == "denied"
    good, args = _prepare(broker, root)
    other_root = _project(tmp_path / "other")
    result = _consume(broker, good["handle"], args, project_root=other_root)
    assert result["status"] == "denied"


def test_audit_records_have_only_opaque_resource_and_dedicated_effect(tmp_path):
    root = _project(tmp_path / "project")
    broker = EditorBufferCapabilityBroker()
    prepared, args = _prepare(broker, root)
    _consume(broker, prepared["handle"], args)
    audit = broker.audit_snapshot(root)
    assert [record.action for record in audit] == ["grant_issued", "check_allowed", "grant_revoked"]
    assert all(record.effect is EffectClass.EDITOR_BUFFER_REPLACE for record in audit)
    assert all(
        URI not in record.resource_ref and str(root) not in record.resource_ref for record in audit
    )
    assert editor_buffer_authorization_audit(root) == ()
