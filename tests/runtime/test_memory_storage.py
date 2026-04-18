from sona.runtime.memory import (
    AgentCheckpoint,
    Episode,
    Fact,
    Goal,
    GoalState,
    MemoryClaim,
    MemoryLink,
    Procedure,
    RetentionState,
)
from sona.runtime.memory.advanced import SQLiteMemoryStore


def test_append_and_query_episodes(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    episode = Episode(
        agent_id="orb.main",
        session_id="sess_100",
        kind="tool_result",
        source_type="tool",
        payload={"tool": "build", "ok": True},
    )

    store.append_episode(episode)
    results = store.query_episodes(agent_id="orb.main", session_id="sess_100")

    assert len(results) == 1
    assert results[0].payload["tool"] == "build"


def test_save_claim_fact_goal_procedure_and_link(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    episode = store.append_episode(
        Episode(
            agent_id="orb.main",
            session_id="sess_101",
            kind="verification",
            source_type="runtime",
            payload={"verified": True},
        )
    )
    claim = store.save_claim(
        MemoryClaim(
            statement="Verification succeeded",
            claim_type="verification_status",
            derived_from_episode_ids=[episode.id],
            agent_id="orb.main",
            session_id="sess_101",
        )
    )
    fact = store.save_fact(
        Fact(
            canonical_statement="Latest verification passed",
            supporting_claim_ids=[claim.id],
            supporting_episode_ids=[episode.id],
            agent_id="orb.main",
            session_id="sess_101",
        )
    )
    procedure = store.save_procedure(
        Procedure(
            title="Verify release",
            procedure_type="checklist",
            steps_or_pattern=["run tests", "inspect receipts"],
            supporting_fact_ids=[fact.id],
            agent_id="orb.main",
            session_id="sess_101",
        )
    )
    goal = store.save_goal(
        Goal(
            title="Ship release",
            status=GoalState.ACTIVE,
            agent_id="orb.main",
            session_id="sess_101",
            linked_episode_ids=[episode.id],
            linked_fact_ids=[fact.id],
            linked_procedure_ids=[procedure.id],
        )
    )
    link = store.add_link(
        MemoryLink(
            from_id=claim.id,
            to_id=fact.id,
            relation_type="supports",
            source_episode_ids=[episode.id],
        )
    )

    assert claim.id.startswith("claim_")
    assert fact.id.startswith("fact_")
    assert procedure.id.startswith("proc_")
    assert goal.status == GoalState.ACTIVE
    assert link.relation_type == "supports"


def test_retention_update_and_delete_record(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    episode = store.append_episode(
        Episode(
            agent_id="orb.main",
            session_id="sess_102",
            kind="user_input",
            source_type="chat",
            payload={"text": "temporary"},
        )
    )

    store.update_retention(
        "episode",
        episode.id,
        RetentionState.ARCHIVED.value,
    )
    archived = store.query_episodes(agent_id="orb.main", session_id="sess_102")
    assert archived[0].retention_state == RetentionState.ARCHIVED

    store.delete_record("episode", episode.id)
    assert (
        store.query_episodes(agent_id="orb.main", session_id="sess_102")
        == []
    )


def test_checkpoint_save_and_restore(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    checkpoint = AgentCheckpoint(
        agent_id="orb.main",
        session_id="sess_103",
        working_state_blob={"task": "continue release work"},
        active_goal_stack=["goal_a", "goal_b"],
        focus_stack=[{"name": "release"}],
        last_processed_episode_id="ep_last",
    )

    store.save_checkpoint(checkpoint)
    restored = store.get_latest_checkpoint("orb.main")

    assert restored is not None
    assert restored.working_state_blob["task"] == "continue release work"
    assert restored.active_goal_stack == ["goal_a", "goal_b"]


def test_goal_and_checkpoint_queries(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    active_goal = store.save_goal(
        Goal(
            title="Resume release",
            status=GoalState.ACTIVE,
            agent_id="orb.main",
            session_id="sess_104",
            opened_at="2026-03-14T10:00:00Z",
        )
    )
    store.save_goal(
        Goal(
            title="Completed release",
            status=GoalState.COMPLETED,
            agent_id="orb.main",
            session_id="sess_104",
            opened_at="2026-03-14T09:00:00Z",
        )
    )
    checkpoint_a = store.save_checkpoint(
        AgentCheckpoint(
            agent_id="orb.main",
            session_id="sess_104",
            created_at="2026-03-14T10:00:00Z",
            working_state_blob={"step": 1},
        )
    )
    checkpoint_b = store.save_checkpoint(
        AgentCheckpoint(
            agent_id="orb.main",
            session_id="sess_104",
            created_at="2026-03-14T11:00:00Z",
            working_state_blob={"step": 2},
        )
    )

    active_goals = store.query_goals(
        agent_id="orb.main",
        session_id="sess_104",
        statuses=[GoalState.ACTIVE.value],
    )
    checkpoints = store.query_checkpoints(
        agent_id="orb.main",
        session_id="sess_104",
    )

    assert [goal.id for goal in active_goals] == [active_goal.id]
    assert store.get_goal(active_goal.id) is not None
    assert store.get_checkpoint(checkpoint_a.id) is not None
    assert [checkpoint.id for checkpoint in checkpoints] == [
        checkpoint_b.id,
        checkpoint_a.id,
    ]


def test_query_links_for_returns_related_edges(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    link_a = store.add_link(
        MemoryLink(
            from_id="claim_a",
            to_id="fact_a",
            relation_type="supports",
        )
    )
    store.add_link(
        MemoryLink(
            from_id="fact_a",
            to_id="proc_a",
            relation_type="supports",
        )
    )

    links = store.query_links_for("fact_a")
    support_links = store.query_links_for("fact_a", relation_type="supports")

    assert len(links) == 2
    assert len(support_links) == 2
    assert any(link.id == link_a.id for link in links)
