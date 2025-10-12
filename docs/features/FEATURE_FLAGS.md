# Sona Feature Flags (0.9.3)

All infrastructure / resilience features ship **disabled by default** to guarantee 0.9.2 parity. Enable explicitly via environment variables.

| Category        | Flag                | Env Var                  | Type                       | Default             | Description                                             |
| --------------- | ------------------- | ------------------------ | -------------------------- | ------------------- | ------------------------------------------------------- |
| Cache           | enable_cache        | SONA_ENABLE_CACHE        | bool ("1"/"0")             | 0                   | Enable LRU+TTL in‑memory cache                          |
| Cache           | cache_ttl_seconds   | SONA_CACHE_TTL           | duration (e.g. `60s`,`5m`) | 0                   | Time-to-live for cache entries (0 = no TTL enforcement) |
| Cache           | cache_max_entries   | SONA_CACHE_MAX           | int                        | 128                 | Max cache entries before LRU eviction                   |
| Batching        | enable_batching     | SONA_ENABLE_BATCH        | bool                       | 0                   | Enable micro-batching queue                             |
| Batching        | batch_window_ms     | SONA_BATCH_WINDOW_MS     | int                        | 25                  | Max window (ms) before batch flush                      |
| Circuit Breaker | enable_breaker      | SONA_ENABLE_BREAKER      | bool                       | 0                   | Enable circuit breaker around provider calls            |
| Circuit Breaker | breaker_error_rate  | SONA_BREAKER_ERR_RATE    | float (0..1)               | 0.3                 | Error-rate threshold to trip breaker (after min calls)  |
| AI Capabilities | enable_capabilities | SONA_ENABLE_CAPABILITIES | bool                       | 1                   | Enable deterministic ai-plan / ai-review commands       |
| Streaming       | streaming_enabled   | SONA_ENABLE_STREAMING    | bool                       | 1                   | Enable (future) streaming output features               |
| Performance     | perf_logs           | SONA_PERF_LOGS           | bool                       | 0                   | Enable JSONL performance log emission                   |
| Performance     | perf_directory      | SONA_PERF_DIR            | path                       | `.sona/.perf`       | Directory for rotated perf logs                         |
| Policy          | policy_path         | SONA_POLICY_PATH         | path                       | `.sona-policy.json` | Policy file location                                    |

## Usage Examples

Enable cache + breaker in a shell (PowerShell example):

```powershell
$env:SONA_ENABLE_CACHE=1; $env:SONA_ENABLE_BREAKER=1; sona build-info
```

Temporary cache tuning (Unix shell):

```bash
export SONA_ENABLE_CACHE=1
export SONA_CACHE_TTL=120s
export SONA_CACHE_MAX=512
sona build-info
```

## Duration Parsing

`SONA_CACHE_TTL` accepts suffixes: `s` (seconds), `m` (minutes). Examples: `30s`, `5m`. If no suffix: interpreted as seconds.

## Safety Principles

- Flags default OFF to preserve baseline behavior.
- Turn on **one feature at a time** in production.
- Use `sona build-info` and `sona doctor` to confirm effective configuration.
- Combine cache + breaker cautiously; monitor error rates.

## Observability

If `SONA_PERF_LOGS=1`, logs rotate daily (`perf-YYYYMMDD.jsonl`) inside `SONA_PERF_DIR` (auto-created). Each line: JSON object with timestamp (`ts`), event name, and contextual fields.

## Recommended Progressive Rollout

1. Enable cache with conservative TTL (`30s`).
2. Introduce circuit breaker (e.g., error rate 0.25).
3. Enable batching (small window: 15–25ms).
4. Activate perf logs and tune.
5. Harden policy patterns.

## Troubleshooting

| Symptom                                   | Possible Cause               | Resolution                                         |
| ----------------------------------------- | ---------------------------- | -------------------------------------------------- |
| `build-info` shows feature still disabled | Session not sourced          | Re-export flag or check shell profile              |
| High cache misses                         | TTL too low / capacity small | Increase `SONA_CACHE_TTL` / `SONA_CACHE_MAX`       |
| Breaker open too often                    | Threshold too aggressive     | Raise `SONA_BREAKER_ERR_RATE` (e.g., 0.5)          |
| Missing perf logs                         | Flag off or dir not writable | Set `SONA_PERF_LOGS=1` and ensure path permissions |
| Policy not applied                        | Wrong path                   | Set `SONA_POLICY_PATH` to correct file             |

## Programmatic Access

Access resolved flags in code:

```python
from sona.flags import get_flags
flags = get_flags()
if flags.enable_cache:
    # cache logic
    ...
```

## Security Note

Policy + breaker + caching combined can mask certain failure modes; always audit logs and set alerts on breaker open frequency.

---

Updated for Sona 0.9.3.
