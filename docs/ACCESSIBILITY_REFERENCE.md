# Sona Accessibility Reference

Sona `0.15.0` includes local cognitive-accessibility modules for explicit,
user-selected support. These modules are not medical tools, do not diagnose
users, do not infer a profile automatically, and do not send telemetry.

Experimental modules are importable and runtime-backed, but persistent,
adaptive, or session-history behavior remains disabled unless the caller opts
in locally with:

```json
{
  "experimental_accessibility": true
}
```

## Profile Presets

`profile` selects local support presets. Preset state is process-local and
`profile.current()` reports `local_only: true` and `persistent: false`.

- `profile.activate("cross-profile")` applies guided pacing and conservative
  flow thresholds.
- `profile.activate("adhd")` applies guided pacing, focused noise filtering,
  and lower flow-switch tolerance.
- `profile.activate("dyslexia")` applies guided pacing, 72-character line
  width, and shorter identifier readability checks.
- `profile.activate("autism")` applies guided pacing, strict checks, and
  sensory text transformation.
- `profile.activate("low-stimulation")` applies low-stimulation pacing,
  minimal noise, and sensory text transformation.
- `profile.activate("custom")` applies no automatic preset changes.

`profile.configure(options)` preserves unknown options for compatibility, but
only validated runtime keys change behavior.

## Stable Modules

| Module | Current Behavior | Limitations |
| ------ | ---------------- | ----------- |
| `profile` | Local support presets for runtime-backed accessibility modules. | Explicit user selection only; no diagnosis or persistence. |
| `simplify` | Deterministic plain-language message and error simplification. | No AI rewriting or medical adaptation. |
| `breadcrumb` | In-memory workflow breadcrumb trail. | No disk history by default. |
| `flow` | Explainable local flow scoring and suggestions. | Heuristic thresholds only. |
| `explain` | Deterministic value, error, module, function, and step explanations. | Curated runtime explanations only. |
| `pace` | Compact, balanced, guided, and low-stimulation text pacing. | Process-local formatting preference only. |
| `affirm` | Factual success and milestone messages. | No motivational or therapeutic claims. |
| `chunk` | Chunk lists, text, steps, and checkpoints. | Checkpoints are in memory only. |
| `timer` | Monotonic local focus timer helpers. | No background service. |
| `noise` | Local event noise filtering. | Caller-provided events only. |
| `tone` | Deterministic neutral/direct/supportive message normalization. | Text transformation only. |
| `readability` | Text and identifier readability heuristics. | Heuristic checks, not accessibility certification. |
| `linewidth` | Line-width wrapping and checks. | Local text only. |
| `mirror` | Similar-symbol pairs and explanations. | Curated symbol list only. |
| `chunk_read` | Chunked reading navigation. | In-memory navigation only. |
| `contract` | Explicit runtime contract checks. | Caller-defined checks only. |
| `boundary` | Local permission boundary helpers. | In-memory boundaries only. |
| `routine` | Routine definitions and checklist state. | In-memory routine state only. |
| `strict` | Opt-in strict runtime checks. | Not a full policy engine. |
| `certainty` | Local assumptions and uncertainty notes. | In-memory notes only. |
| `sensory` | Low-stimulation text transformations. | Text transformation only. |

## Experimental Modules

| Module | Current Behavior | Limitations |
| ------ | ---------------- | ----------- |
| `interrupt` | Experimental interrupt capture and review helpers. | Queueing requires explicit opt-in. |
| `hyperfocus` | Experimental boundary checks for focused work sessions. | Heuristic checks only. |
| `priority` | Experimental priority ranking helpers. | Sorts caller-provided priority data only. |
| `drift` | Experimental drift scoring and reset prompts. | Heuristic event scoring only. |
| `scaffold` | Experimental task step scaffolding. | Template step generation only. |
| `reentry` | Experimental re-entry cards. | Local card generation only. |
| `reward` | Experimental local reward token helpers. | History requires explicit opt-in. |
| `context` | Experimental local context packs. | Context storage requires explicit opt-in. |
| `momentum` | Experimental momentum checks. | Progress math only. |
| `rotate` | Experimental task rotation. | Stateless list rotation only. |
| `start` | Experimental tiny-start prompts. | Prompt scaffolding only. |
| `alias` | Experimental explicit replacement maps. | Caller-provided mappings only. |
| `phonetic` | Experimental phonetic spelling helpers. | Simple heuristic grouping only. |
| `visual` | Experimental visual position and spacing helpers. | Text-position helpers only. |
| `symbol` | Experimental symbol explanations. | Curated dictionary only. |
| `sequence` | Experimental sequence review helpers. | Ordering and duplicate checks only. |
| `memory` | Experimental local memory/glossary helpers. | Session memory requires explicit opt-in. |
| `contrast` | Experimental hex color contrast ratio helpers. | Hex colors only. |
| `template` | Experimental structured template helpers. | String replacement templates only. |
| `spoken` | Experimental spoken-script chunking. | Text chunking only. |
| `pattern` | Experimental repeated-pattern checks. | Simple repeated-pattern checks only. |
| `trace` | Experimental event trace formatting. | In-memory formatting only. |
| `transition` | Experimental transition planning. | Static transition plans only. |
| `detail` | Experimental detail expansion. | Explicit detail maps only. |
| `anchor` | Experimental local anchor helpers. | Anchor storage requires explicit opt-in. |
| `overload` | Experimental overload checks. | Heuristic signal counts only. |
| `mono` | Experimental monotropic focus framing. | Focus framing only. |
| `system` | Experimental system mapping helpers. | Explicit component maps only. |
| `mastery` | Experimental mastery planning. | Practice-plan scaffolding only. |
| `shutdown` | Experimental shutdown planning. | History requires explicit opt-in. |
| `energy` | Experimental energy budgeting. | Budgeting math only. |
| `narrative` | Experimental narrative framing prompts. | Static framing only. |
| `journal` | Experimental local journal helpers. | Journal history requires explicit opt-in. |
| `adapt` | Experimental adaptation preference helpers. | Preference storage requires explicit opt-in; no background adaptation. |

## Safety

Public imports are side-effect safe. Importing these modules must not write
files, create directories, make network requests, sleep, mutate user
configuration, start background watchers, or initialize persistent storage.

