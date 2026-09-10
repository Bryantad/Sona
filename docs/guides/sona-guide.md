# Sona Guide

Sona 0.15.6 provides deterministic explanations from the local Sona catalog.

## Explain a diagnostic

Use the exact identifier from the diagnostic:

```bash
sona why SONA-RUNTIME-003
sona why SONA-FS-005 --mode balanced
sona why SONA-RUNTIME-003 --mode expert
sona why PROOF-VERIFY-005 --style technical
sona why SONA-PARSE-003 --style visual --json
```

`guided` is the default: meaning, explanation, next step, example, and related
concepts. `balanced` shows the meaning and next step. `expert` gives a single
compact diagnostic line. The selected mode applies to this explanation; it
does not change ordinary run/check output or save a preference.

Styles are `simple`, `visual` (reviewed text diagrams), and `technical`.
Explanations come from the same catalog in every mode. No online model, Native
executable, project initialization, or runtime execution is needed.

An ID lookup is reference material. It does not establish what happened in a
particular run, verify a receipt, or grant a capability. Run `sona proof verify`
to verify a receipt and `sona guardian check` to check project state.

## Preview source fixes

`sona fix` runs reviewed deterministic fix rules. Preview is the default:

```bash
sona fix app.sona --diagnostic-id SONA-RUNTIME-003 --name quant --line 3 --column 21
sona fix app.sona --diagnostic-json diagnostic.json --json
sona fix app.sona --rule stdlib-api-migration
```

The command writes only when `--apply` is explicit:

```bash
sona fix app.sona --diagnostic-id SONA-RUNTIME-003 --name quant --line 3 --column 21 --apply
sona fix app.sona --rule stdlib-api-migration --apply
```

Every preview contains one or more `SourceEdit` records with the document,
one-based range, expected original text, replacement text, and rule identifier.
Application refuses stale files if the expected text no longer matches.

The first source rules are intentionally narrow:

- `guide.undefined-name.closest-binding` renames an undefined use only when the
  source location still contains that name and exactly one visible binding is
  the closest safe spelling match.
- `guide.stdlib-api-migration` reads the stdlib manifest and migrates bare
  `import io;` uses of `io.read_file` / `io.write_file` to `fs.read_text` /
  `fs.write_text`, adding `import fs;` when needed.

The rules ignore comments and strings, do not execute the program, do not call
AI providers, and do not change Sona syntax.

## Focus diagnostics

`sona focus` groups canonical diagnostics for presentation while preserving the
complete machine-readable sequence:

```bash
sona focus app.sona
sona focus app.sona --density focused
sona focus app.sona --density complete --json
sona focus --diagnostics-json diagnostics.json --density normal
```

Density controls only the presentation:

- `focused` shows one likely root issue and reports how many diagnostics are
  grouped.
- `normal` shows root issues and hides only reviewed cascade secondaries.
- `complete` shows every canonical diagnostic in original order.

The first reviewed cascade rule is deliberately small:

- `guide.cascade.unclosed-delimiter-downstream` can group later parse/name
  diagnostics in the same file under `SONA-PARSE-003`. It does not cross file
  boundaries, hide parser infrastructure failures, or claim compiler causality.

Focus output always includes the full canonical diagnostics list in JSON.
Grouping is a UI relationship, not a new compiler fact.

## Local learning profile

Sona Guide can read project-local preferences from `.sona/learning.json`.
Showing the effective profile is read-only and does not create project state:

```bash
sona guide profile
sona guide profile --json
```

Preferences are explicit:

```bash
sona guide profile set --mode balanced --density focused --style technical
sona guide profile set --quiet
sona guide profile set --no-quiet
sona guide profile reset
```

Concept familiarity is also explicit:

```bash
sona guide profile learn variables --familiarity comfortable
sona guide profile learn proof-mode --familiarity learning
```

Allowed familiarity values are `new`, `learning`, and `comfortable`.
The profile stores only:

- `guidance_mode`;
- `diagnostic_density`;
- `explanation_style`;
- `quiet`;
- a bounded map of concept identifiers to familiarity values.

It does not store source text, file paths, output bodies, credentials, runtime
receipts, or inferred medical state. Invalid, corrupt, oversized, or unsafe
profile state fails with Sona Guide diagnostics instead of Python tracebacks.

`sona why` and `sona focus` use the profile when no explicit mode, style, or
density flag is supplied:

```bash
sona why SONA-RUNTIME-003
sona why SONA-RUNTIME-003 --mode expert
sona focus app.sona
sona focus app.sona --density complete
```

Explicit flags always win. `--no-profile` makes `why` and `focus` ignore
`.sona/learning.json` for that invocation.

`sona fix --apply` may update related concept familiarity to `learning` after a
deterministic stale-protected edit succeeds. Preview mode never writes the
profile, and `--no-profile-update` disables that follow-on update.

## Initial coverage

| Topic | Existing diagnostic identifiers |
| --- | --- |
| Undefined names | `SONA-RUNTIME-003`, `SONA-NATIVE-RUNTIME-003` |
| Unclosed delimiters | `SONA-PARSE-003` |
| Filesystem capability denial | `SONA-FS-005` |
| Receipt hash mismatch | `PROOF-VERIFY-005` |
| Guardian project/configuration/trusted state | `SONA-GUARD-001`, `SONA-GUARD-002`, `SONA-GUARD-004` |

The original diagnostic retains its identifier, severity, location, message,
hint, and runtime ownership. In particular, an unclosed-delimiter diagnostic
does not prove which closing token should be inserted. Guardian drift is also
a structured workflow status and must not be inferred from any of the three
infrastructure IDs above.

Unknown IDs produce `SONA-GUIDE-001`, exit code 1, and no guessed explanation.
Invalid presentation options produce CLI usage errors with exit code 2.

## Client contract

`sona/guide` contains pure request, response, catalog, explanation, and rendering
logic. JSON responses use `schema_version: 1`, separately from Proof Mode's
receipt schema. The response contains:

- the original diagnostic ID and requested mode/style/density;
- `basis: catalog-reference` for `sona why`, with `diagnostic: null`;
- `basis: reported-diagnostic` and the canonical diagnostic payload when a
  caller supplies a canonical `Diagnostic` through `GuideRequest`;
- structured explanation sections, related concept IDs, and catalog provenance;
- zero or more stale-protected fix previews.

Rendering controls detail. Canonical JSON diagnostic fields are preserved in
all modes. Text rendering escapes terminal control characters; canonical
diagnostic redaction continues to apply.

The API can explain a diagnostic already returned by the canonical frontend:

```python
from sona.developer_intelligence.frontend import analyze_frontend
from sona.guide import GuideRequest, explain, render_text

finding = analyze_frontend("let value = (1;", file="demo.sona")[0]
response = explain(GuideRequest(finding.diagnostic_id, finding, mode="guided"))
print(render_text(response))
```

## Remaining implementation

Real editor-host acceptance, final packaging, and platform certification still follow
the [0.15.6 contract](../plans/0.15.6-cognitive-developer-experience.md). Current
source fixes and profile updates are limited to the reviewed rules above.

The [learning and examples workflow](learning-and-examples.md) adds checked
installed examples and explicit practice using the real Python/Native runtimes.
Lesson explanations reuse the concept catalog; execution stays outside Guide.

## Editor workflow

The development extension exposes these Command Palette actions:

- **Sona Guide: Explain Diagnostic (Offline)** chooses a Sona diagnostic at the
  cursor, or offers the document's Sona diagnostics when there are several.
- **Sona Guide: Explain Selection (Offline)** describes reviewed grammar
  constructs in the selection, using the canonical parser. It does not execute
  the program, evaluate expressions, or claim to know its eventual output.
- **Sona Guide: Show Focused Diagnostics** shows the shared Focus rendering and
  offers **Open complete JSON**. The normal Problems list remains complete.
- **Sona Guide: Choose Guidance Detail** selects Guided, Balanced, or Expert.

Explanations open in read-only text documents. They use the editor's fonts,
keyboard navigation, themes, and zoom, with no animation or webview scripts.
The optional first-use setup prompt can be disabled with `sona.guide.showSetup`.
Existing accessibility presets do not select a guidance level.

Settings are `sona.guide.mode`, `.style`, `.density`, and `.quiet`. Explicit
editor settings override the project profile; unset settings preserve the
project defaults and familiarity-based scaffold reduction. In multi-root
workspaces, the language server selects the deepest containing workspace root.
Neither explanation requests nor editor fix application write learning state.
Use the profile CLI to record explicit familiarity.

Completion and hover documentation use the same concept catalog as selection
explanations. The initial concepts cover variables, conditions, loops,
functions, collections, modules, files, Guardian, and Proof Mode. Concept
reference text about Guardian or Proof Mode is not a policy check or receipt
verification result.

## Editor fix previews

Guide code actions reuse the CLI fix rules. The LSP emits versioned
`TextDocumentEdit` records with exact UTF-16 ranges, including zero-width import
insertions. Clients without versioned-edit support receive disabled actions.

The bundled VS Code client converts these actions into **Fix Preview** commands
because its generic code-action conversion discards document versions. The
command opens a before/after diff. **Apply fix** checks the current document
version, document identity, expected text, and non-overlapping edit ranges
again, then applies one undoable editor change. Changed or closed documents
require a fresh preview. Preview contents are held only in a bounded in-memory
document provider; they are not written to the project or learning profile.

The static language server does not execute code to discover runtime undefined
names. A name fix requires the original Sona runtime diagnostic supplied in
LSP action context. The stdlib migration can be requested directly as a source
action. Migration refuses shadowed `io`/`fs` bindings, nested-only imports, and
object-member lookalikes. Name fixes reject strings, comments, qualified members,
partial identifiers, and already-visible names.

## Quiet presentation

Quiet Mode uses canonical error severity as its initial blocker criterion; it
does not guess additional severity categories. Combine it with any density:

```bash
sona focus app.sona --quiet --json
sona focus app.sona --density complete --no-quiet
```

The JSON `diagnostics` array always contains every canonical item in original
order. `visible_indices`, `visible_diagnostics`, `quiet`, and `suppressed_count`
describe presentation only. To display all items, use complete density with
Quiet Mode off. Stored `quiet` preferences apply when no explicit flag is given.

## Shared JSON request transport

`sona guide request --json` reads a request from stdin. `sona/guide` is the LSP
method accepting the same JSON. Both delegate to `sona.guide.service` and return
the same schema-versioned payload and `text` renderer output. The CLI accepts
`--project-root` and `--no-profile` as well.

For example, pipe this JSON into `sona guide request --json --no-profile`:

```json
{
  "schema_version": 1,
  "action": "diagnostic",
  "diagnostic_id": "SONA-RUNTIME-003",
  "options": {"mode": "balanced", "style": "simple"}
}
```

Actions are `diagnostic`, `selection`, `focus`, and `concept`:

| Action | Input | Result |
| --- | --- | --- |
| `diagnostic` | Canonical `diagnostic` object or reference `diagnostic_id`; optional `source` and `document` | Shared explanation, unchanged canonical diagnostic, optional fix previews |
| `selection` | `source`; optional `document` and one-based code-point `selection` range | Reviewed concepts and complete frontend diagnostics; no execution |
| `focus` | Canonical `diagnostics` array or `source` | Shared Focus payload including every canonical diagnostic |
| `concept` | `concept_id` | Reviewed concept reference text with catalog provenance |

`options` supports `mode`, `style`, `density`, and `quiet`. Selection ranges use
`start_line`, `start_column`, `end_line`, and `end_column`, with an exclusive
end. The editor translates UTF-16 positions at the transport boundary.

The service limits requests to 1 MiB, source to 256 KiB, and supplied diagnostic
arrays to 1,000 items. The CLI rejects duplicate JSON keys. Malformed requests
return `status: unavailable` and a sanitized Guide diagnostic; the CLI exits 1.
Unknown diagnostic IDs retain `SONA-GUIDE-001`, with no invented explanation.
Ordinary frontend diagnostics are returned even when the selected syntax cannot
be explained. No request runs a program, calls a provider, or mutates project
state. The protocol adapters preserve related locations, metadata keys, and
Native/Python diagnostic identity fields.

## Explain checked Proof Mode and Guardian facts

```bash
sona guide proof receipt.sproof
sona guide proof receipt.sproof --mode balanced --json
sona guide proof receipt.sproof --mode expert --style technical
sona guide guardian --project-root .
sona guide guardian --project-root . --mode expert --no-profile
```

These read-only commands call the existing shared receipt verifier or Guardian
checker before explaining their results. They never execute a program, create
a receipt, initialize Guardian, repair drift, grant a capability, or update
learning state. Ordinary `sona proof inspect/verify` and `sona guardian
check/explain` output remains unchanged.

Guided, Balanced, and Expert vary detail, not evidence. The complete `facts`
object in schema-1 JSON is identical to the provider's machine output in every
mode. Guardian uses the same redaction boundary as its existing CLI. The
structured `sections`, `assurance_limits`, and `provenance` identify the shared
renderer. `fixes` is always empty. Simple presentation keeps hashes out of the
headline; technical style includes complete provider facts. Expert mode still
displays assurance limits and any execution/infrastructure diagnostic.

The summaries keep these distinctions explicit:

- Valid receipt integrity does not mean successful execution.
- A receipt's Guardian binding is not an independently checked baseline.
- Guardian readiness does not imply policy enforcement, particularly for legacy
  baselines. Working-policy drift does not silently replace the trusted policy.
- Recorded effects cover instrumentation only; not observed does not mean
  impossible. Self-consistency is not authentication, signatures, host integrity,
  or remote attestation.

Corrupt receipts retain their original `PROOF-VERIFY-*` diagnostic and receive
no success summary. Guardian failures retain their original diagnostic or drift
status. Exit code 0 requires a valid receipt or `ok` Guardian state and a readable
selected profile; invalid receipts, drift/uninitialized state, and infrastructure
or profile failures exit 1. A valid receipt with failed execution still exits 0,
matching the existing verifier's integrity contract.

Modes/styles honor project preferences with explicit flags taking precedence.
`--no-profile` disables profile reads. If preferences cannot be read, provider
facts are retained, `profile_diagnostic` reports the problem, and text explicitly
identifies default presentation; the command does not silently succeed.

Internally, `GuideRequest(fact_kind="proof" | "guardian", facts=...)` is an
exclusive alternative to the diagnostic variant. The pure `explain_facts`
renderer does not verify or authenticate arbitrary Python objects. Only the
outside `sona.fact_service` coordinator obtains checked facts. The general
stdin/LSP request endpoint deliberately does not accept caller-asserted
`status: valid` facts.

The development extension's **Sona Guide: Explain Proof Mode Receipt (Offline)**
and **Sona Guide: Explain Guardian State (Offline)** commands consume this same
checked CLI contract. They require a trusted workspace before starting Python.
Select a local receipt for Proof Mode; select the intended workspace when it
cannot be inferred. Cancellation starts no process. Python selection and Guide
preferences are scoped to that chosen workspace, including multi-root settings.

The process uses an argument array, no shell, closed stdin, Python safe-path
mode (`-P`), and no inherited `PYTHONPATH`. The transport bounds execution to
30 seconds and captured streams to 2 MiB each. Python-rendered explanation text
is shown verbatim in the read-only Guide view, with **Open complete JSON** on
request. An exit-1 invalid receipt, uninitialized/drifting Guardian state, or
profile error is displayed as its structured response, not fabricated success.
Transport failures use a sanitized message. No independent TypeScript receipt
verification or trust interpretation is performed. Real editor-host/visual
acceptance remains separate from the automated command and transport tests.

## Runtime diagnostic transport (development)

```bash
sona run app.sona --json
```

This opt-in command **executes the program** through the existing run handler.
It is not static explanation, a sandbox, or Proof Mode evidence. Ordinary run
output and exit codes are unchanged when the flag is omitted. The schema-1
response separates `streams.stdout`/`stderr` from original structured runtime
`diagnostics`; program output is not parsed to invent diagnostics. A failed run
without a structured runtime diagnostic says `diagnostic_status: unavailable`.

`source_sha256` identifies the decoded text used by the run handler, with a BOM
removed and CRLF normalized to LF (`source_identity_format:
utf8-decoded-text-lf`). It is not the original file-byte hash or authentication.
`source_mapping: transformed` marks extracted embedded-Python blocks; consumers
must not assume those locations address the original document. Unknown/unread
source has no hash and unavailable mapping. Each serialized stream retains at
most 512 Ki characters and reports truncation. Temporary capture avoids unbounded
memory, but this flag does not impose a new disk/time sandbox or change the
program's existing execution limits.

The current integration tests run the actual flagship typo program and feed its
original diagnostic into all three shared Guide modes to obtain the exact
`quant` -> `quantity` preview. Editor publication still needs source/version
checks and invalidation before this transport can drive live runtime fixes.
