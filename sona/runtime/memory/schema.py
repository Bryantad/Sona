"""SQLite schema definitions for the persistent memory subsystem."""

from __future__ import annotations


SCHEMA_VERSION = "0.1.0"

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS episodes (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        tenant_id TEXT,
        workspace_id TEXT,
        project_id TEXT,
        session_id TEXT NOT NULL,
        goal_id TEXT,
        trace_id TEXT,
        correlation_id TEXT,
        timestamp TEXT NOT NULL,
        kind TEXT NOT NULL,
        source_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        classification TEXT NOT NULL,
        trust_state TEXT NOT NULL,
        retention_state TEXT NOT NULL,
        privacy_scope TEXT,
        importance REAL,
        confidence REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS claims (
        id TEXT PRIMARY KEY,
        statement TEXT NOT NULL,
        claim_type TEXT NOT NULL,
        derived_from_episode_ids_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        agent_id TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        project_id TEXT,
        session_id TEXT,
        goal_id TEXT,
        privacy_scope TEXT,
        confidence REAL,
        trust_state TEXT NOT NULL,
        retention_state TEXT NOT NULL,
        contradicts_claim_ids_json TEXT NOT NULL,
        supports_claim_ids_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS facts (
        id TEXT PRIMARY KEY,
        canonical_statement TEXT NOT NULL,
        supporting_claim_ids_json TEXT NOT NULL,
        supporting_episode_ids_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        agent_id TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        project_id TEXT,
        session_id TEXT,
        goal_id TEXT,
        privacy_scope TEXT,
        trust_state TEXT NOT NULL,
        retention_state TEXT NOT NULL,
        validity_window_json TEXT,
        supersedes_fact_id TEXT,
        provenance_summary TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS procedures (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        procedure_type TEXT NOT NULL,
        steps_or_pattern_json TEXT NOT NULL,
        supporting_fact_ids_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        agent_id TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        project_id TEXT,
        session_id TEXT,
        goal_id TEXT,
        privacy_scope TEXT,
        trust_state TEXT NOT NULL,
        retention_state TEXT NOT NULL,
        success_evidence_ids_json TEXT NOT NULL,
        version INTEGER NOT NULL,
        review_state TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        opened_at TEXT NOT NULL,
        priority INTEGER,
        resumed_at TEXT,
        suspended_at TEXT,
        completed_at TEXT,
        agent_id TEXT,
        tenant_id TEXT,
        workspace_id TEXT,
        project_id TEXT,
        session_id TEXT,
        goal_id TEXT,
        privacy_scope TEXT,
        trust_state TEXT NOT NULL,
        retention_state TEXT NOT NULL,
        linked_episode_ids_json TEXT NOT NULL,
        linked_fact_ids_json TEXT NOT NULL,
        linked_procedure_ids_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS checkpoints (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        working_state_blob_json TEXT NOT NULL,
        last_processed_episode_id TEXT,
        created_at TEXT NOT NULL,
        session_id TEXT,
        trace_id TEXT,
        state TEXT NOT NULL,
        active_goal_stack_json TEXT NOT NULL,
        focus_stack_json TEXT NOT NULL,
        last_receipt_ref_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS links (
        id TEXT PRIMARY KEY,
        from_id TEXT NOT NULL,
        to_id TEXT NOT NULL,
        relation_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        weight REAL,
        source_episode_ids_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS receipt_refs (
        id TEXT PRIMARY KEY,
        owner_type TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        receipt_id TEXT NOT NULL,
        event_kind_or_path TEXT NOT NULL,
        receipt_hash TEXT,
        classification TEXT NOT NULL,
        policy_fingerprint TEXT,
        event_offset INTEGER,
        sealed_mode_ref TEXT,
        created_at TEXT NOT NULL
    )
    """,
    (
        "CREATE INDEX IF NOT EXISTS idx_episodes_agent_session "
        "ON episodes(agent_id, session_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_episodes_kind_timestamp "
        "ON episodes(kind, timestamp)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_episodes_scope "
        "ON episodes(workspace_id, project_id, goal_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_claims_scope "
        "ON claims(agent_id, workspace_id, project_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_facts_scope "
        "ON facts(agent_id, workspace_id, project_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_procedures_scope "
        "ON procedures(agent_id, workspace_id, project_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_goals_status_agent "
        "ON goals(status, agent_id)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_checkpoints_agent_created "
        "ON checkpoints(agent_id, created_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_receipt_refs_owner "
        "ON receipt_refs(owner_type, owner_id)"
    ),
]
