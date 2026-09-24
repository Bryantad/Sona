"""Data contracts for services, effects, capabilities, and resource budgets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ServiceState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"


class HealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RestartMode(StrEnum):
    NEVER = "never"
    ON_FAILURE = "on_failure"
    BOUNDED = "bounded"


@dataclass(frozen=True, slots=True)
class RestartPolicy:
    mode: RestartMode = RestartMode.NEVER
    maximum_restarts: int = 0
    delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.maximum_restarts < 0:
            raise ValueError("maximum_restarts cannot be negative")
        if self.delay_seconds < 0:
            raise ValueError("restart delay cannot be negative")
        if self.mode is RestartMode.NEVER and self.maximum_restarts != 0:
            raise ValueError("never restart policy requires maximum_restarts=0")
        if self.mode is not RestartMode.NEVER and self.maximum_restarts < 1:
            raise ValueError("restart policies require a finite positive maximum_restarts")


@dataclass(frozen=True, slots=True)
class ServiceDefinition:
    service_id: str
    restart_policy: RestartPolicy = RestartPolicy()
    resource_budget_id: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", self.service_id):
            raise ValueError("service_id must be a safe identifier")
        if self.schema_version != 1:
            raise ValueError("service definition requires schema_version 1")


class EnforcementStatus(StrEnum):
    ENFORCED = "enforced"
    OBSERVED = "observed"
    UNSUPPORTED = "unsupported"


class ResourceUnit(StrEnum):
    BYTES = "bytes"
    MILLI_CPUS = "milli_cpus"
    SECONDS = "seconds"
    ITEMS = "items"
    TOKENS = "tokens"


@dataclass(frozen=True, slots=True)
class ResourceLimit:
    """A configured value, or zero when status explicitly says unsupported."""

    resource: str
    amount: int
    unit: ResourceUnit
    status: EnforcementStatus

    def __post_init__(self) -> None:
        if not self.resource.strip():
            raise ValueError("resource name is required")
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise ValueError("resource amount must be an integer")
        if self.amount < 0 or (
            self.amount == 0 and self.status is not EnforcementStatus.UNSUPPORTED
        ):
            raise ValueError("resource amount must be positive unless unsupported")


@dataclass(frozen=True, slots=True)
class ResourceBudget:
    budget_id: str
    limits: tuple[ResourceLimit, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.budget_id.strip():
            raise ValueError("budget_id is required")
        if self.schema_version != 1:
            raise ValueError("resource budget requires schema_version 1")
        keys = [(item.resource, item.unit) for item in self.limits]
        if len(set(keys)) != len(keys):
            raise ValueError("resource limits must be unique by resource and unit")


class EffectClass(StrEnum):
    FS_READ = "FS.READ"
    FS_WRITE = "FS.WRITE"
    NETWORK_REQUEST = "NETWORK.REQUEST"
    PROCESS_EXECUTE = "PROCESS.EXECUTE"
    ENV_READ = "ENV.READ"
    MODEL_INFERENCE = "MODEL.INFERENCE"
    MESSAGE_SEND = "MESSAGE.SEND"
    EVENT_EMIT = "EVENT.EMIT"
    SERVICE_START = "SERVICE.START"
    SERVICE_STOP = "SERVICE.STOP"


class EffectOutcome(StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CapabilityScope:
    """Requested scope data only; possession here is not an authorization."""

    effect: EffectClass
    resource_pattern: str = "*"
    expires_at_utc: str | None = None

    def __post_init__(self) -> None:
        if not self.resource_pattern.strip():
            raise ValueError("resource_pattern is required")


class BackpressurePolicy(StrEnum):
    BLOCK = "block"
    REJECT = "reject"
    DROP_OLDEST = "drop_oldest"


class ChannelState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ChannelDefinition:
    channel_id: str
    message_type: str
    capacity: int
    backpressure: BackpressurePolicy = BackpressurePolicy.BLOCK
    schema_version: int = 1

    def __post_init__(self) -> None:
        identifier = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"
        if not isinstance(self.channel_id, str) or not re.fullmatch(identifier, self.channel_id):
            raise ValueError("channel_id must be a safe identifier")
        if not isinstance(self.message_type, str) or not re.fullmatch(
            identifier, self.message_type
        ):
            raise ValueError("message_type must be a safe identifier")
        if isinstance(self.capacity, bool) or not isinstance(self.capacity, int):
            raise ValueError("channel capacity must be an integer")
        if not 1 <= self.capacity <= 65_536:
            raise ValueError("channel capacity must be between 1 and 65536")
        if not isinstance(self.backpressure, BackpressurePolicy):
            raise ValueError("backpressure must be a BackpressurePolicy")
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version != 1
        ):
            raise ValueError("channel definition requires schema_version 1")
