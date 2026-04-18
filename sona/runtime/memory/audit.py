"""Append-only governance audit log for persistent memory operations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .ids import make_prefixed_id, utc_now


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


AUDIT_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        subject_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        action TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        policy_fingerprint TEXT,
        details_json TEXT NOT NULL,
        policy_context_json TEXT
    )
    """,
    (
        "CREATE INDEX IF NOT EXISTS idx_audit_subject_ts "
        "ON audit_log(subject_id, timestamp DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_audit_actor_ts "
        "ON audit_log(actor_id, timestamp DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_audit_action "
        "ON audit_log(action, timestamp DESC)"
    ),
]


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: str
    timestamp: str
    subject_type: str
    subject_id: str
    action: str
    actor_id: str
    policy_fingerprint: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    policy_context: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class AuditSummary:
    total_events: int
    actions: dict[str, int]
    subject_types: dict[str, int]
    actors: dict[str, int]
    first_timestamp: str | None
    last_timestamp: str | None


class AuditKernel:
    """Append-only audit log for governance-relevant memory operations.

    Every logged event is immutable.  The kernel never modifies or deletes
    existing audit records.
    """

    def __init__(self, store: Any):
        self.store = store
        self._ensure_audit_schema()

    def _ensure_audit_schema(self) -> None:
        self.store.initialize()
        conn = self.store._connect()
        try:
            for stmt in AUDIT_SCHEMA_STATEMENTS:
                conn.execute(stmt)
            conn.commit()
        finally:
            conn.close()

    def log_action(
        self,
        *,
        subject_type: str,
        subject_id: str,
        action: str,
        actor_id: str,
        policy_fingerprint: str | None = None,
        details: dict[str, Any] | None = None,
        policy_context: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=make_prefixed_id("audit"),
            timestamp=utc_now(),
            subject_type=subject_type,
            subject_id=subject_id,
            action=action,
            actor_id=actor_id,
            policy_fingerprint=policy_fingerprint,
            details=details or {},
            policy_context=policy_context,
        )
        conn = self.store._connect()
        try:
            conn.execute(
                """
                INSERT INTO audit_log (
                    id, timestamp, subject_type, subject_id, action,
                    actor_id, policy_fingerprint, details_json,
                    policy_context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.timestamp,
                    event.subject_type,
                    event.subject_id,
                    event.action,
                    event.actor_id,
                    event.policy_fingerprint,
                    _canonical_json(event.details),
                    _canonical_json(event.policy_context) if event.policy_context else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return event

    def query_audit_trail(
        self,
        subject_id: str,
        *,
        limit: int = 100,
    ) -> list[AuditEvent]:
        conn = self.store._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE subject_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (subject_id, limit),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def query_by_actor(
        self,
        actor_id: str,
        *,
        limit: int = 100,
    ) -> list[AuditEvent]:
        conn = self.store._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE actor_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (actor_id, limit),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def query_by_action(
        self,
        action: str,
        *,
        limit: int = 100,
    ) -> list[AuditEvent]:
        conn = self.store._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE action = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (action, limit),
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def count_events(self) -> int:
        conn = self.store._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def summarize(self) -> AuditSummary:
        conn = self.store._connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()
            total_events = total[0] if total else 0

            actions: dict[str, int] = {}
            for row in conn.execute(
                "SELECT action, COUNT(*) FROM audit_log GROUP BY action"
            ).fetchall():
                actions[row[0]] = row[1]

            subject_types: dict[str, int] = {}
            for row in conn.execute(
                "SELECT subject_type, COUNT(*) FROM audit_log GROUP BY subject_type"
            ).fetchall():
                subject_types[row[0]] = row[1]

            actors: dict[str, int] = {}
            for row in conn.execute(
                "SELECT actor_id, COUNT(*) FROM audit_log GROUP BY actor_id"
            ).fetchall():
                actors[row[0]] = row[1]

            first_row = conn.execute(
                "SELECT timestamp FROM audit_log ORDER BY timestamp ASC LIMIT 1"
            ).fetchone()
            last_row = conn.execute(
                "SELECT timestamp FROM audit_log ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()

            return AuditSummary(
                total_events=total_events,
                actions=actions,
                subject_types=subject_types,
                actors=actors,
                first_timestamp=first_row[0] if first_row else None,
                last_timestamp=last_row[0] if last_row else None,
            )
        finally:
            conn.close()

    def verify_episode_immutability(self, episode_id: str) -> bool:
        """Return True when no mutation actions exist for this episode."""
        trail = self.query_audit_trail(episode_id)
        mutation_actions = {
            "retention_transition",
            "delete",
            "forget",
            "update",
        }
        return not any(event.action in mutation_actions for event in trail)

    def export_forensic_report(
        self,
        *,
        subject_id: str | None = None,
        actor_id: str | None = None,
        action: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """Export a portable forensic report as a JSON-serialisable dict."""
        clauses: list[str] = []
        params: list[Any] = []
        if subject_id is not None:
            clauses.append("subject_id = ?")
            params.append(subject_id)
        if actor_id is not None:
            clauses.append("actor_id = ?")
            params.append(actor_id)
        if action is not None:
            clauses.append("action = ?")
            params.append(action)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        conn = self.store._connect()
        try:
            rows = conn.execute(
                f"SELECT * FROM audit_log {where} "
                "ORDER BY timestamp ASC LIMIT ?",
                params,
            ).fetchall()
            events = [self._row_to_event(row) for row in rows]
        finally:
            conn.close()
        return {
            "report_type": "forensic_audit",
            "generated_at": utc_now(),
            "filters": {
                "subject_id": subject_id,
                "actor_id": actor_id,
                "action": action,
            },
            "total_events": len(events),
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp,
                    "subject_type": e.subject_type,
                    "subject_id": e.subject_id,
                    "action": e.action,
                    "actor_id": e.actor_id,
                    "policy_fingerprint": e.policy_fingerprint,
                    "details": e.details,
                    "policy_context": e.policy_context,
                }
                for e in events
            ],
        }

    def _row_to_event(self, row: Any) -> AuditEvent:
        details_raw = row[7] if isinstance(row, tuple) else row["details_json"]
        policy_raw = row[8] if isinstance(row, tuple) else row["policy_context_json"]
        return AuditEvent(
            id=row[0] if isinstance(row, tuple) else row["id"],
            timestamp=row[1] if isinstance(row, tuple) else row["timestamp"],
            subject_type=row[2] if isinstance(row, tuple) else row["subject_type"],
            subject_id=row[3] if isinstance(row, tuple) else row["subject_id"],
            action=row[4] if isinstance(row, tuple) else row["action"],
            actor_id=row[5] if isinstance(row, tuple) else row["actor_id"],
            policy_fingerprint=row[6] if isinstance(row, tuple) else row["policy_fingerprint"],
            details=json.loads(details_raw) if details_raw else {},
            policy_context=json.loads(policy_raw) if policy_raw else None,
        )


__all__ = [
    "AUDIT_SCHEMA_STATEMENTS",
    "AuditEvent",
    "AuditKernel",
    "AuditSummary",
]
