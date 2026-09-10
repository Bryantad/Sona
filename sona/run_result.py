"""Opt-in run transport, not Proof Mode evidence or an execution sandbox."""

from __future__ import annotations

import contextlib
import copy
import json
import tempfile

MAX_CAPTURE_CHARACTERS = 512 * 1024


def run_json(args, handler) -> int:
    delegated = copy.copy(args)
    delegated.json = False
    packet = {"schema_version": 1, "command": "run", "source_sha256": None,
              "source_mapping": "unavailable", "source_identity_format": "utf8-decoded-text-lf", "diagnostics": []}
    delegated._run_packet = packet
    # Temporary streams avoid unbounded in-memory capture. Only a bounded prefix
    # is serialized; ordinary execution limits are unchanged by this transport.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", newline="") as stdout, tempfile.TemporaryFile(mode="w+", encoding="utf-8", newline="") as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = handler(delegated)
        streams = {}
        truncated = {}
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            stream.seek(0)
            text = stream.read(MAX_CAPTURE_CHARACTERS + 1)
            truncated[name] = len(text) > MAX_CAPTURE_CHARACTERS
            streams[name] = text[:MAX_CAPTURE_CHARACTERS]
    packet.update(status="ok" if exit_code == 0 else "failed", exit_code=exit_code,
                  streams=streams, truncated=truncated,
                  diagnostic_status="reported" if packet["diagnostics"] else ("none" if exit_code == 0 else "unavailable"))
    print(json.dumps(packet, sort_keys=True))
    return exit_code
