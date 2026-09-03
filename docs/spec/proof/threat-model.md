# Proof Threat Model

Proof Mode provides local, redacted evidence about a Native Core execution.

It can show:

- the receipt content is internally consistent with its stored self-hash
- the receipt declares Native Core execution without Python fallback
- the source or source-backed bytecode identity recorded by the native runner
- the capability flags and observed effect records recorded by the native VM
- output body digests and byte counts, not output bodies

Effect evidence is intentionally bounded. It records calls through explicitly
instrumented Native host boundaries. Support labels describe that observation
coverage; they do not elevate an event into operating-system or hardware
evidence. In particular:

- absence of an effect does not prove the activity was impossible or did not
  occur outside the instrumented boundary
- `PARTIAL` means the observed event does not model every related sub-effect
- `UNAVAILABLE` records an attempted but unimplemented runtime operation
- `UNOBSERVED` names a vocabulary boundary for which no event may be inferred
- stdout/stderr hashes cover recorded process output bytes even when there is
  no one-to-one semantic output-effect record for every byte
- clock values, random values and seeds, stdin values, URLs, and raw paths are
  omitted rather than treated as evidence payloads

It does not show:

- that a party able to replace and re-seal a receipt left the original evidence
  unchanged
- who ran the program
- when it ran according to a trusted timestamping authority
- that the operating system was uncompromised
- that hardware was trusted
- that a remote party observed the run
- that uninstrumented operating-system, parent-process, library, or external
  activity is absent
- that Python and Native Core semantics are identical
- that Guardian constrained supported capability requests, unless the receipt
  has a verified policy-aware Guardian binding
- that Guardian approved the broader project or operator, even when Guardian
  verification and local attestation are separately performed
- that an AI request selected, caused, or performed the observed execution
- AI prompt, model, provider, or semantic agent-action provenance

AI review is advisory only. It can explain verified evidence but cannot create,
verify, sign, attest, or strengthen that evidence. Its provider packet includes
an explicit boundary stating that `AGENT.ACTION` is not represented and AI
request causality is not established.
