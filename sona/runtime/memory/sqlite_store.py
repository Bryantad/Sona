"""SQLite reference backend for the persistent memory subsystem."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .enums import (
    CheckpointState,
    ClassificationTier,
    GoalState,
    ProcedureReviewState,
    RetentionState,
    TrustState,
)
from .ids import make_prefixed_id, utc_now
from .models import (
    AgentCheckpoint,
    Episode,
    Fact,
    Goal,
    MemoryClaim,
    MemoryLink,
    MemoryReceiptRef,
    Procedure,
)
from .schema import SCHEMA_STATEMENTS, SCHEMA_VERSION
from .storage import MemoryStore


_RETENTION_TABLES = {
    "episode": "episodes",
    "claim": "claims",
    "fact": "facts",
    "procedure": "procedures",
    "goal": "goals",
}


def _json_dump(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _json_load(value: str | None, default: Any) -> Any:
    if value in (None, ""):
        return default
    return json.loads(value)


class SQLiteMemoryStore(MemoryStore):
    """SQLite-backed durable memory store."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES(?, ?)",
                ("schema_version", SCHEMA_VERSION),
            )
            conn.commit()

    def append_episode(self, episode: Episode) -> Episode:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO episodes (
                    id, agent_id, tenant_id, workspace_id, project_id,
                    session_id, goal_id, trace_id, correlation_id,
                    timestamp, kind, source_type, payload_json,
                    classification, trust_state, retention_state,
                    privacy_scope, importance, confidence
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    episode.id,
                    episode.agent_id,
                    episode.tenant_id,
                    episode.workspace_id,
                    episode.project_id,
                    episode.session_id,
                    episode.goal_id,
                    episode.trace_id,
                    episode.correlation_id,
                    episode.timestamp,
                    episode.kind,
                    episode.source_type,
                    _json_dump(episode.payload),
                    episode.classification.value,
                    episode.trust_state.value,
                    episode.retention_state.value,
                    episode.privacy_scope,
                    episode.importance,
                    episode.confidence,
                ),
            )
            self._persist_receipt_refs(
                conn,
                "episode",
                episode.id,
                episode.receipt_refs,
            )
            conn.commit()
        return episode

    def query_episodes(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Episode]:
        self.initialize()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM episodes {where} "
                    "ORDER BY timestamp DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_episode(conn, row) for row in rows]

    def get_episode(self, episode_id: str) -> Episode | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM episodes WHERE id = ?",
                (episode_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_episode(conn, row)

    def save_claim(self, claim: MemoryClaim) -> MemoryClaim:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO claims (
                    id, statement, claim_type, derived_from_episode_ids_json,
                    created_at, updated_at, agent_id, tenant_id, workspace_id,
                    project_id, session_id, goal_id, privacy_scope, confidence,
                    trust_state, retention_state, contradicts_claim_ids_json,
                    supports_claim_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim.id,
                    claim.statement,
                    claim.claim_type,
                    _json_dump(claim.derived_from_episode_ids),
                    claim.created_at,
                    claim.updated_at,
                    claim.agent_id,
                    claim.tenant_id,
                    claim.workspace_id,
                    claim.project_id,
                    claim.session_id,
                    claim.goal_id,
                    claim.privacy_scope,
                    claim.confidence,
                    claim.trust_state.value,
                    claim.retention_state.value,
                    _json_dump(claim.contradicts_claim_ids),
                    _json_dump(claim.supports_claim_ids),
                ),
            )
            self._replace_receipt_refs(
                conn,
                "claim",
                claim.id,
                claim.receipt_refs,
            )
            conn.commit()
        return claim

    def query_claims(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryClaim]:
        self.initialize()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM claims {where} "
                    "ORDER BY created_at DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_claim(conn, row) for row in rows]

    def get_claim(self, claim_id: str) -> MemoryClaim | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM claims WHERE id = ?",
                (claim_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_claim(conn, row)

    def save_fact(self, fact: Fact) -> Fact:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO facts (
                    id, canonical_statement, supporting_claim_ids_json,
                    supporting_episode_ids_json, created_at, updated_at,
                    agent_id,
                    tenant_id, workspace_id, project_id, session_id, goal_id,
                    privacy_scope, trust_state, retention_state,
                    validity_window_json,
                    supersedes_fact_id, provenance_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.id,
                    fact.canonical_statement,
                    _json_dump(fact.supporting_claim_ids),
                    _json_dump(fact.supporting_episode_ids),
                    fact.created_at,
                    fact.updated_at,
                    fact.agent_id,
                    fact.tenant_id,
                    fact.workspace_id,
                    fact.project_id,
                    fact.session_id,
                    fact.goal_id,
                    fact.privacy_scope,
                    fact.trust_state.value,
                    fact.retention_state.value,
                    (
                        _json_dump(fact.validity_window)
                        if fact.validity_window is not None
                        else None
                    ),
                    fact.supersedes_fact_id,
                    fact.provenance_summary,
                ),
            )
            self._replace_receipt_refs(
                conn,
                "fact",
                fact.id,
                fact.receipt_refs,
            )
            conn.commit()
        return fact

    def query_facts(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Fact]:
        self.initialize()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM facts {where} "
                    "ORDER BY created_at DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_fact(conn, row) for row in rows]

    def get_fact(self, fact_id: str) -> Fact | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM facts WHERE id = ?",
                (fact_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_fact(conn, row)

    def save_procedure(self, procedure: Procedure) -> Procedure:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO procedures (
                    id, title, procedure_type, steps_or_pattern_json,
                    supporting_fact_ids_json, created_at, updated_at, agent_id,
                    tenant_id, workspace_id, project_id, session_id, goal_id,
                    privacy_scope, trust_state, retention_state,
                    success_evidence_ids_json, version, review_state
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    procedure.id,
                    procedure.title,
                    procedure.procedure_type,
                    _json_dump(procedure.steps_or_pattern),
                    _json_dump(procedure.supporting_fact_ids),
                    procedure.created_at,
                    procedure.updated_at,
                    procedure.agent_id,
                    procedure.tenant_id,
                    procedure.workspace_id,
                    procedure.project_id,
                    procedure.session_id,
                    procedure.goal_id,
                    procedure.privacy_scope,
                    procedure.trust_state.value,
                    procedure.retention_state.value,
                    _json_dump(procedure.success_evidence_ids),
                    procedure.version,
                    procedure.review_state.value,
                ),
            )
            self._replace_receipt_refs(
                conn,
                "procedure",
                procedure.id,
                procedure.receipt_refs,
            )
            conn.commit()
        return procedure

    def query_procedures(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Procedure]:
        self.initialize()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM procedures {where} "
                    "ORDER BY created_at DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_procedure(conn, row) for row in rows]

    def get_procedure(self, procedure_id: str) -> Procedure | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM procedures WHERE id = ?",
                (procedure_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_procedure(conn, row)

    def save_goal(self, goal: Goal) -> Goal:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO goals (
                    id, title, status, opened_at, priority, resumed_at,
                    suspended_at, completed_at, agent_id, tenant_id,
                    workspace_id,
                    project_id, session_id, goal_id, privacy_scope,
                    trust_state,
                    retention_state, linked_episode_ids_json,
                    linked_fact_ids_json,
                    linked_procedure_ids_json
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    goal.id,
                    goal.title,
                    goal.status.value,
                    goal.opened_at,
                    goal.priority,
                    goal.resumed_at,
                    goal.suspended_at,
                    goal.completed_at,
                    goal.agent_id,
                    goal.tenant_id,
                    goal.workspace_id,
                    goal.project_id,
                    goal.session_id,
                    goal.goal_id,
                    goal.privacy_scope,
                    goal.trust_state.value,
                    goal.retention_state.value,
                    _json_dump(goal.linked_episode_ids),
                    _json_dump(goal.linked_fact_ids),
                    _json_dump(goal.linked_procedure_ids),
                ),
            )
            self._replace_receipt_refs(
                conn,
                "goal",
                goal.id,
                goal.receipt_refs,
            )
            conn.commit()
        return goal

    def query_goals(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        statuses: list[str] | None = None,
        limit: int = 50,
    ) -> list[Goal]:
        self.initialize()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        if statuses:
            clauses.append(
                f"status IN ({','.join('?' for _ in statuses)})"
            )
            params.extend(statuses)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM goals {where} "
                    "ORDER BY opened_at DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_goal(conn, row) for row in rows]

    def get_goal(self, goal_id: str) -> Goal | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM goals WHERE id = ?",
                (goal_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_goal(conn, row)

    def save_checkpoint(self, checkpoint: AgentCheckpoint) -> AgentCheckpoint:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints (
                    id, agent_id, working_state_blob_json,
                    last_processed_episode_id, created_at, session_id,
                    trace_id, state, active_goal_stack_json,
                    focus_stack_json, last_receipt_ref_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.id,
                    checkpoint.agent_id,
                    _json_dump(checkpoint.working_state_blob),
                    checkpoint.last_processed_episode_id,
                    checkpoint.created_at,
                    checkpoint.session_id,
                    checkpoint.trace_id,
                    checkpoint.state.value,
                    _json_dump(checkpoint.active_goal_stack),
                    _json_dump(checkpoint.focus_stack),
                    (
                        _json_dump(checkpoint.last_receipt_ref.to_dict())
                        if checkpoint.last_receipt_ref
                        else None
                    ),
                ),
            )
            conn.commit()
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> AgentCheckpoint | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE id = ?",
                (checkpoint_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_checkpoint(row)

    def query_checkpoints(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentCheckpoint]:
        self.initialize()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id is not None:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM checkpoints {where} "
                    "ORDER BY created_at DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_checkpoint(row) for row in rows]

    def get_latest_checkpoint(self, agent_id: str) -> AgentCheckpoint | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                (
                    "SELECT * FROM checkpoints WHERE agent_id = ? "
                    "ORDER BY created_at DESC LIMIT 1"
                ),
                (agent_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_checkpoint(row)

    def add_link(self, link: MemoryLink) -> MemoryLink:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO links (
                    id, from_id, to_id, relation_type, created_at,
                    weight, source_episode_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link.id,
                    link.from_id,
                    link.to_id,
                    link.relation_type,
                    link.created_at,
                    link.weight,
                    _json_dump(link.source_episode_ids),
                ),
            )
            conn.commit()
        return link

    def query_links_for(
        self,
        object_id: str,
        *,
        relation_type: str | None = None,
        limit: int = 200,
    ) -> list[MemoryLink]:
        self.initialize()
        clauses = ["(from_id = ? OR to_id = ?)"]
        params: list[Any] = [object_id, object_id]
        if relation_type is not None:
            clauses.append("relation_type = ?")
            params.append(relation_type)
        where = f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                (
                    f"SELECT * FROM links {where} "
                    "ORDER BY created_at DESC LIMIT ?"
                ),
                params,
            ).fetchall()
            return [self._row_to_link(row) for row in rows]

    def update_retention(
        self,
        owner_type: str,
        owner_id: str,
        retention_state: str,
    ) -> None:
        self.initialize()
        table = _RETENTION_TABLES.get(owner_type)
        if table is None:
            raise ValueError(f"Unsupported owner_type: {owner_type}")
        with self._connect() as conn:
            conn.execute(
                f"UPDATE {table} SET retention_state = ? WHERE id = ?",
                (retention_state, owner_id),
            )
            conn.commit()

    def delete_record(self, owner_type: str, owner_id: str) -> None:
        self.initialize()
        table = _RETENTION_TABLES.get(owner_type)
        if table is None and owner_type != "checkpoint":
            raise ValueError(f"Unsupported owner_type: {owner_type}")
        with self._connect() as conn:
            if owner_type == "checkpoint":
                conn.execute(
                    "DELETE FROM checkpoints WHERE id = ?",
                    (owner_id,),
                )
            else:
                conn.execute(f"DELETE FROM {table} WHERE id = ?", (owner_id,))
            conn.execute(
                (
                    "DELETE FROM receipt_refs WHERE owner_type = ? "
                    "AND owner_id = ?"
                ),
                (owner_type, owner_id),
            )
            conn.commit()

    def get_receipt_refs(
        self,
        owner_type: str,
        owner_id: str,
    ) -> list[MemoryReceiptRef]:
        self.initialize()
        with self._connect() as conn:
            rows = conn.execute(
                (
                    "SELECT * FROM receipt_refs WHERE owner_type = ? "
                    "AND owner_id = ? ORDER BY created_at ASC"
                ),
                (owner_type, owner_id),
            ).fetchall()
            return [self._row_to_receipt_ref(row) for row in rows]

    def _persist_receipt_refs(
        self,
        conn: sqlite3.Connection,
        owner_type: str,
        owner_id: str,
        refs: list[MemoryReceiptRef],
    ) -> None:
        for ref in refs:
            conn.execute(
                """
                INSERT INTO receipt_refs (
                    id, owner_type, owner_id, receipt_id, event_kind_or_path,
                    receipt_hash, classification, policy_fingerprint,
                    event_offset,
                    sealed_mode_ref, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_prefixed_id("receiptref"),
                    owner_type,
                    owner_id,
                    ref.receipt_id,
                    ref.event_kind_or_path,
                    ref.receipt_hash,
                    ref.classification.value,
                    ref.policy_fingerprint,
                    ref.event_offset,
                    ref.sealed_mode_ref,
                    utc_now(),
                ),
            )

    def _replace_receipt_refs(
        self,
        conn: sqlite3.Connection,
        owner_type: str,
        owner_id: str,
        refs: list[MemoryReceiptRef],
    ) -> None:
        conn.execute(
            "DELETE FROM receipt_refs WHERE owner_type = ? AND owner_id = ?",
            (owner_type, owner_id),
        )
        self._persist_receipt_refs(conn, owner_type, owner_id, refs)

    def _row_to_episode(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> Episode:
        episode = Episode(
            id=row["id"],
            agent_id=row["agent_id"],
            tenant_id=row["tenant_id"],
            workspace_id=row["workspace_id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            goal_id=row["goal_id"],
            trace_id=row["trace_id"],
            correlation_id=row["correlation_id"],
            timestamp=row["timestamp"],
            kind=row["kind"],
            source_type=row["source_type"],
            payload=_json_load(row["payload_json"], {}),
            classification=ClassificationTier(row["classification"]),
            trust_state=TrustState(row["trust_state"]),
            retention_state=RetentionState(row["retention_state"]),
            privacy_scope=row["privacy_scope"],
            importance=row["importance"],
            confidence=row["confidence"],
            receipt_refs=[],
        )
        episode.receipt_refs.extend(
            self._fetch_receipt_refs_conn(conn, "episode", episode.id)
        )
        return episode

    def _row_to_claim(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> MemoryClaim:
        claim = MemoryClaim(
            id=row["id"],
            statement=row["statement"],
            claim_type=row["claim_type"],
            derived_from_episode_ids=_json_load(
                row["derived_from_episode_ids_json"],
                [],
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            agent_id=row["agent_id"],
            tenant_id=row["tenant_id"],
            workspace_id=row["workspace_id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            goal_id=row["goal_id"],
            privacy_scope=row["privacy_scope"],
            confidence=row["confidence"],
            trust_state=TrustState(row["trust_state"]),
            retention_state=RetentionState(row["retention_state"]),
            contradicts_claim_ids=_json_load(
                row["contradicts_claim_ids_json"],
                [],
            ),
            supports_claim_ids=_json_load(
                row["supports_claim_ids_json"],
                [],
            ),
            receipt_refs=[],
        )
        claim.receipt_refs.extend(
            self._fetch_receipt_refs_conn(conn, "claim", claim.id)
        )
        return claim

    def _row_to_fact(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> Fact:
        fact = Fact(
            id=row["id"],
            canonical_statement=row["canonical_statement"],
            supporting_claim_ids=_json_load(
                row["supporting_claim_ids_json"],
                [],
            ),
            supporting_episode_ids=_json_load(
                row["supporting_episode_ids_json"],
                [],
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            agent_id=row["agent_id"],
            tenant_id=row["tenant_id"],
            workspace_id=row["workspace_id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            goal_id=row["goal_id"],
            privacy_scope=row["privacy_scope"],
            trust_state=TrustState(row["trust_state"]),
            retention_state=RetentionState(row["retention_state"]),
            validity_window=_json_load(row["validity_window_json"], None),
            supersedes_fact_id=row["supersedes_fact_id"],
            provenance_summary=row["provenance_summary"],
            receipt_refs=[],
        )
        fact.receipt_refs.extend(
            self._fetch_receipt_refs_conn(conn, "fact", fact.id)
        )
        return fact

    def _row_to_procedure(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> Procedure:
        procedure = Procedure(
            id=row["id"],
            title=row["title"],
            procedure_type=row["procedure_type"],
            steps_or_pattern=_json_load(row["steps_or_pattern_json"], []),
            supporting_fact_ids=_json_load(
                row["supporting_fact_ids_json"],
                [],
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            agent_id=row["agent_id"],
            tenant_id=row["tenant_id"],
            workspace_id=row["workspace_id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            goal_id=row["goal_id"],
            privacy_scope=row["privacy_scope"],
            trust_state=TrustState(row["trust_state"]),
            retention_state=RetentionState(row["retention_state"]),
            success_evidence_ids=_json_load(
                row["success_evidence_ids_json"],
                [],
            ),
            version=row["version"],
            review_state=ProcedureReviewState(row["review_state"]),
            receipt_refs=[],
        )
        procedure.receipt_refs.extend(
            self._fetch_receipt_refs_conn(conn, "procedure", procedure.id)
        )
        return procedure

    def _row_to_goal(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> Goal:
        goal = Goal(
            id=row["id"],
            title=row["title"],
            status=GoalState(row["status"]),
            opened_at=row["opened_at"],
            priority=row["priority"],
            resumed_at=row["resumed_at"],
            suspended_at=row["suspended_at"],
            completed_at=row["completed_at"],
            agent_id=row["agent_id"],
            tenant_id=row["tenant_id"],
            workspace_id=row["workspace_id"],
            project_id=row["project_id"],
            session_id=row["session_id"],
            goal_id=row["goal_id"],
            privacy_scope=row["privacy_scope"],
            trust_state=TrustState(row["trust_state"]),
            retention_state=RetentionState(row["retention_state"]),
            linked_episode_ids=_json_load(
                row["linked_episode_ids_json"],
                [],
            ),
            linked_fact_ids=_json_load(
                row["linked_fact_ids_json"],
                [],
            ),
            linked_procedure_ids=_json_load(
                row["linked_procedure_ids_json"],
                [],
            ),
            receipt_refs=[],
        )
        goal.receipt_refs.extend(
            self._fetch_receipt_refs_conn(conn, "goal", goal.id)
        )
        return goal

    def _row_to_checkpoint(self, row: sqlite3.Row) -> AgentCheckpoint:
        ref_payload = _json_load(row["last_receipt_ref_json"], None)
        ref = None
        if ref_payload is not None:
            ref = MemoryReceiptRef(
                receipt_id=ref_payload["receipt_id"],
                event_kind_or_path=ref_payload["event_kind_or_path"],
                receipt_hash=ref_payload.get("receipt_hash"),
                classification=ClassificationTier(
                    ref_payload.get(
                        "classification",
                        ClassificationTier.INTERNAL.value,
                    )
                ),
                policy_fingerprint=ref_payload.get("policy_fingerprint"),
                event_offset=ref_payload.get("event_offset"),
                sealed_mode_ref=ref_payload.get("sealed_mode_ref"),
            )
        return AgentCheckpoint(
            id=row["id"],
            agent_id=row["agent_id"],
            working_state_blob=_json_load(row["working_state_blob_json"], {}),
            last_processed_episode_id=row["last_processed_episode_id"],
            created_at=row["created_at"],
            session_id=row["session_id"],
            trace_id=row["trace_id"],
            state=CheckpointState(row["state"]),
            active_goal_stack=_json_load(row["active_goal_stack_json"], []),
            focus_stack=_json_load(row["focus_stack_json"], []),
            last_receipt_ref=ref,
        )

    def _row_to_link(self, row: sqlite3.Row) -> MemoryLink:
        return MemoryLink(
            id=row["id"],
            from_id=row["from_id"],
            to_id=row["to_id"],
            relation_type=row["relation_type"],
            created_at=row["created_at"],
            weight=row["weight"],
            source_episode_ids=_json_load(
                row["source_episode_ids_json"],
                [],
            ),
        )

    def _fetch_receipt_refs_conn(
        self,
        conn: sqlite3.Connection,
        owner_type: str,
        owner_id: str,
    ) -> list[MemoryReceiptRef]:
        rows = conn.execute(
            (
                "SELECT * FROM receipt_refs WHERE owner_type = ? "
                "AND owner_id = ? ORDER BY created_at ASC"
            ),
            (owner_type, owner_id),
        ).fetchall()
        return [self._row_to_receipt_ref(row) for row in rows]

    def _row_to_receipt_ref(self, row: sqlite3.Row) -> MemoryReceiptRef:
        return MemoryReceiptRef(
            receipt_id=row["receipt_id"],
            event_kind_or_path=row["event_kind_or_path"],
            receipt_hash=row["receipt_hash"],
            classification=ClassificationTier(row["classification"]),
            policy_fingerprint=row["policy_fingerprint"],
            event_offset=row["event_offset"],
            sealed_mode_ref=row["sealed_mode_ref"],
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
