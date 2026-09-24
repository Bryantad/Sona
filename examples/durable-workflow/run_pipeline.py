"""Create, interrupt, explicitly recover, or finish a persisted local workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from sona.workflow import (
    RecoveryDecision,
    RetryMode,
    RetryPolicy,
    StepDefinition,
    StepState,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowJournalStore,
    WorkflowLedger,
    WorkflowState,
    new_step_id,
    new_task_id,
    new_workflow_id,
)


def _definition() -> WorkflowDefinition:
    build, test, package = new_step_id(), new_step_id(), new_step_id()
    retry = RetryPolicy(RetryMode.FIXED, maximum_attempts=2, delay_seconds=0)
    return WorkflowDefinition(
        new_workflow_id(),
        (
            TaskDefinition(
                new_task_id(),
                (
                    StepDefinition(build, "build", retry=retry),
                    StepDefinition(test, "test", depends_on=(build,), retry=retry),
                    StepDefinition(package, "package", depends_on=(test,), retry=retry),
                ),
            ),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".sona", help="Journal root (default: .sona)")
    parser.add_argument(
        "--interrupt",
        action="store_true",
        help="Persist a running step and exit to demonstrate inert recovery",
    )
    parser.add_argument(
        "--resume-interrupted",
        action="store_true",
        help="Explicitly retry an interrupted step from its beginning",
    )
    args = parser.parse_args()

    store = WorkflowJournalStore(Path(args.root))
    ledger = WorkflowLedger(store=store)
    persisted = store.load_latest()
    if not persisted:
        snapshot = ledger.create(_definition())
        snapshot = ledger.prepare(snapshot.definition.workflow_id)
    else:
        recovered = ledger.restore()
        if len(recovered) != 1:
            parser.error("example journal must contain exactly one workflow")
        snapshot = recovered[0]
        if snapshot.state is WorkflowState.CREATED:
            snapshot = ledger.prepare(snapshot.definition.workflow_id)

    workflow_id = snapshot.definition.workflow_id
    if args.interrupt:
        ready = next((step for step in snapshot.steps if step.state is StepState.READY), None)
        if ready is None:
            parser.error("no ready step is available to interrupt")
        ledger.start_step(workflow_id, ready.step_id)
        print(f"Interrupted after durable start: {workflow_id} / {ready.step_id}")
        print("Restart without --interrupt; the step will be blocked pending explicit recovery.")
        return 0

    snapshot = ledger.snapshot(workflow_id)
    if snapshot.state is WorkflowState.BLOCKED:
        interrupted = next(
            (
                step
                for step in snapshot.steps
                if step.failure_code == "SONA-WORKFLOW-RECOVERY-REQUIRED"
            ),
            None,
        )
        if interrupted is None:
            parser.error("workflow is blocked for a reason other than interrupted work")
        if not args.resume_interrupted:
            print("Recovery is inert. Re-run with --resume-interrupted to retry explicitly.")
            return 2
        snapshot = ledger.resume_step(
            workflow_id,
            interrupted.step_id,
            decision=RecoveryDecision.RETRY_FROM_START,
        )
    elif args.resume_interrupted:
        parser.error("--resume-interrupted requires an interrupted workflow")

    operations = {
        "build": "Built the local example artifact.",
        "test": "Validated the local example artifact.",
        "package": "Prepared the local package output.",
    }
    operation_by_step = {
        step.step_id: step.operation
        for task in snapshot.definition.tasks
        for step in task.steps
    }
    while snapshot.state is WorkflowState.READY:
        ready = next((step for step in snapshot.steps if step.state is StepState.READY), None)
        if ready is None:
            break
        snapshot = ledger.start_step(workflow_id, ready.step_id)
        print(operations[operation_by_step[ready.step_id]])
        snapshot = ledger.succeed_step(workflow_id, ready.step_id)
    print(
        f"Workflow {workflow_id}: {snapshot.state.value} "
        f"({snapshot.progress.completed_steps}/{snapshot.progress.total_steps} steps)"
    )
    return 0 if snapshot.state is WorkflowState.SUCCEEDED else 1


if __name__ == "__main__":
    raise SystemExit(main())
