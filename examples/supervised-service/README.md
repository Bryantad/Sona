# Example C — Supervised worker

Run the worker and observe its one bounded restart:

```powershell
python examples/supervised-service/run_worker.py
```

The first attempt reports healthy and then fails; the supervisor restarts only
that service once. The second attempt reports healthy and waits cooperatively
for shutdown. This is an in-process Python supervisor, not durable service
registration, process isolation, or cross-process service status.
