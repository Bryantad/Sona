"""Demonstrate a service-local bounded restart and cooperative shutdown."""

from __future__ import annotations

import threading

from sona.runtime import RestartMode, RestartPolicy, ServiceDefinition, ServiceSupervisor


def main() -> int:
    attempts = 0
    attempt_lock = threading.Lock()
    recovered = threading.Event()

    def worker(context) -> None:
        nonlocal attempts
        with attempt_lock:
            attempts += 1
            attempt = attempts
        if attempt == 1:
            context.mark_healthy()
            raise RuntimeError("demonstration failure")
        context.mark_healthy()
        recovered.set()
        context.wait_cancelled(timeout=10)

    supervisor = ServiceSupervisor()
    supervisor.register(
        ServiceDefinition(
            "example.indexer",
            RestartPolicy(RestartMode.BOUNDED, maximum_restarts=1, delay_seconds=0.05),
        ),
        worker,
    )
    try:
        supervisor.start("example.indexer")
        if not recovered.wait(5):
            print("Worker did not recover within the bounded restart window.")
            return 1
        snapshot = supervisor.snapshot("example.indexer")
        print(
            f"{snapshot.service_id}: {snapshot.state.value}; "
            f"attempts={snapshot.attempts}; restarts={snapshot.restarts}"
        )
        stopped = supervisor.stop("example.indexer", timeout=2)
        print(f"Cooperative stop: {'completed' if stopped else 'still stopping'}")
        return 0 if stopped and snapshot.restarts == 1 else 1
    finally:
        supervisor.close(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
