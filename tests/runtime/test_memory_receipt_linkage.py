from sona.runtime.memory import Episode, MemoryReceiptRef
from sona.runtime.memory.advanced import SQLiteMemoryStore


def test_episode_receipt_refs_round_trip(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    episode = Episode(
        agent_id="orb.main",
        session_id="sess_104",
        kind="tool_result",
        source_type="tool",
        payload={"tool": "pytest", "exit_code": 0},
        receipt_refs=[
            MemoryReceiptRef(
                receipt_id="rcpt_9001",
                receipt_hash="sha256:abc123",
                event_kind_or_path="execution.events[4]",
            )
        ],
    )

    store.append_episode(episode)
    refs = store.get_receipt_refs("episode", episode.id)
    loaded = store.query_episodes(agent_id="orb.main", session_id="sess_104")

    assert len(refs) == 1
    assert refs[0].receipt_id == "rcpt_9001"
    assert (
        loaded[0].receipt_refs[0].event_kind_or_path
        == "execution.events[4]"
    )
