"""Typed resource-budget observations without implied enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .contracts import EnforcementStatus, ResourceBudget, ResourceUnit


@dataclass(frozen=True, slots=True)
class ResourceMeasurement:
    resource: str
    unit: ResourceUnit
    amount: int

    def __post_init__(self) -> None:
        if not isinstance(self.resource, str) or not self.resource:
            raise ValueError("resource must be non-empty")
        if not isinstance(self.unit, ResourceUnit):
            raise TypeError("unit must be a ResourceUnit")
        if isinstance(self.amount, bool) or not isinstance(self.amount, int) or self.amount < 0:
            raise ValueError("measurement amount must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ResourceLimitReport:
    resource: str
    unit: ResourceUnit
    configured_amount: int
    status: EnforcementStatus
    observed_amount: int | None
    exceeds_limit: bool | None


@dataclass(frozen=True, slots=True)
class ResourceBudgetReport:
    budget_id: str
    limits: tuple[ResourceLimitReport, ...]


class ResourceBudgetReporter:
    """Combine caller-supplied measurements with declared limit status.

    Reporting is observational. It neither samples resources nor enforces
    limits. Unsupported limits have no numeric threshold and report
    ``exceeds_limit=None`` even when an observation is supplied.
    """

    @staticmethod
    def report(
        budget: ResourceBudget,
        measurements: tuple[ResourceMeasurement, ...] = (),
    ) -> ResourceBudgetReport:
        if not isinstance(budget, ResourceBudget):
            raise TypeError("budget must be a ResourceBudget")
        if not isinstance(measurements, tuple) or any(
            not isinstance(item, ResourceMeasurement) for item in measurements
        ):
            raise TypeError("measurements must be a tuple of ResourceMeasurement values")
        observed: dict[tuple[str, ResourceUnit], int] = {}
        for item in measurements:
            key = (item.resource, item.unit)
            if key in observed:
                raise ValueError("measurements must be unique by resource and unit")
            observed[key] = item.amount

        allowed = {(limit.resource, limit.unit) for limit in budget.limits}
        if set(observed) - allowed:
            raise ValueError("measurement does not match a declared resource limit")

        entries = tuple(
            ResourceLimitReport(
                resource=limit.resource,
                unit=limit.unit,
                configured_amount=limit.amount,
                status=limit.status,
                observed_amount=observed.get((limit.resource, limit.unit)),
                exceeds_limit=(
                    observed[(limit.resource, limit.unit)] > limit.amount
                    if limit.status is not EnforcementStatus.UNSUPPORTED
                    and (limit.resource, limit.unit) in observed
                    else None
                ),
            )
            for limit in budget.limits
        )
        return ResourceBudgetReport(budget.budget_id, entries)
