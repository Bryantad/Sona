"""Abstract storage contract for persistent memory backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

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


class MemoryStore(ABC):
    """Backend contract for durable memory operations."""

    @abstractmethod
    def initialize(self) -> None:
        """Create or update backend schema."""

    @abstractmethod
    def append_episode(self, episode: Episode) -> Episode:
        """Persist an immutable episode."""

    @abstractmethod
    def query_episodes(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Episode]:
        """Return stored episodes in descending timestamp order."""
        pass

    @abstractmethod
    def get_episode(self, episode_id: str) -> Episode | None:
        """Return a single episode by id."""

    @abstractmethod
    def save_claim(self, claim: MemoryClaim) -> MemoryClaim:
        """Persist or update a claim."""

    @abstractmethod
    def query_claims(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryClaim]:
        """Return stored claims in descending creation order."""

    @abstractmethod
    def get_claim(self, claim_id: str) -> MemoryClaim | None:
        """Return a single claim by id."""

    @abstractmethod
    def save_fact(self, fact: Fact) -> Fact:
        """Persist or update a fact."""

    @abstractmethod
    def query_facts(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Fact]:
        """Return stored facts in descending creation order."""

    @abstractmethod
    def get_fact(self, fact_id: str) -> Fact | None:
        """Return a single fact by id."""

    @abstractmethod
    def save_procedure(self, procedure: Procedure) -> Procedure:
        """Persist or update a procedure."""

    @abstractmethod
    def query_procedures(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[Procedure]:
        """Return stored procedures in descending creation order."""

    @abstractmethod
    def get_procedure(self, procedure_id: str) -> Procedure | None:
        """Return a single procedure by id."""

    @abstractmethod
    def save_goal(self, goal: Goal) -> Goal:
        """Persist or update a goal."""

    @abstractmethod
    def query_goals(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        statuses: list[str] | None = None,
        limit: int = 50,
    ) -> list[Goal]:
        """Return stored goals in descending opened_at order."""

    @abstractmethod
    def get_goal(self, goal_id: str) -> Goal | None:
        """Return a single goal by id."""

    @abstractmethod
    def save_checkpoint(self, checkpoint: AgentCheckpoint) -> AgentCheckpoint:
        """Persist a checkpoint."""

    @abstractmethod
    def get_checkpoint(self, checkpoint_id: str) -> AgentCheckpoint | None:
        """Return a single checkpoint by id."""

    @abstractmethod
    def query_checkpoints(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentCheckpoint]:
        """Return stored checkpoints in descending created_at order."""

    @abstractmethod
    def get_latest_checkpoint(self, agent_id: str) -> AgentCheckpoint | None:
        """Return the newest checkpoint for an agent."""

    @abstractmethod
    def add_link(self, link: MemoryLink) -> MemoryLink:
        """Persist a relationship edge."""

    @abstractmethod
    def query_links_for(
        self,
        object_id: str,
        *,
        relation_type: str | None = None,
        limit: int = 200,
    ) -> list[MemoryLink]:
        """Return relationship edges that reference an object id."""

    @abstractmethod
    def get_receipt_refs(
        self,
        owner_type: str,
        owner_id: str,
    ) -> list[MemoryReceiptRef]:
        """Return receipt refs for a stored object."""

    @abstractmethod
    def update_retention(
        self,
        owner_type: str,
        owner_id: str,
        retention_state: str,
    ) -> None:
        """Update retention state for a stored object."""

    @abstractmethod
    def delete_record(self, owner_type: str, owner_id: str) -> None:
        """Delete a stored object and associated receipt refs."""
