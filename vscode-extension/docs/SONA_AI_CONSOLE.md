# Sona AI Console

Sona AI Console adds a local Sona-owned chat surface with selectable agent modes and provider-ready routing.

This is a preview/developer feature. It is designed to open safely without Claude, Codex, Ollama, Qwen, or Azure credentials.

## How To Open

Use one of these paths:

- Command Palette: `Sona: Open AI Console`
- Sona activity bar container: `Sona AI Console`

The view ID is `sona.aiConsole`.

## Agents

The console shows these agent tabs:

- `Sona`
- `Qwen`
- `Claude`
- `Codex`
- `Local`

Clicking a tab changes only the active Sona AI Console agent state. It does not control external extensions.

## Implemented Providers

`Sona` is implemented as a deterministic local response provider. It does not make network calls.

`Local` is implemented as a deterministic local response provider. It does not make network calls.

The deterministic providers summarize the prompt plus the safe context selected in the webview toggles.

## Provider-Ready Routing

The extension host receives webview messages and routes them through an internal provider abstraction:

- `selectAgent`
- `sendPrompt`
- `clearChat`
- `refreshStatus`

Provider requests include:

- active agent ID
- prompt
- current file path when enabled
- selected text when enabled
- workspace name when enabled
- diagnostics for the active editor when enabled
- visible editor language ID when current file context is enabled

The console does not send full workspace content by default.

## Qwen And Ollama

`Qwen` is wired only to a configured local Ollama endpoint.

The provider is considered configured when either:

- `sona.ai.qwen.enabled` is `true`, with `sona.ai.qwen.model` and `sona.ai.ollama.url` set; or
- the workspace `.env` contains an Ollama backend from Sona manual setup, for example:

```env
SONA_AI_BACKEND=ollama
SONA_OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_HOST=http://localhost:11434
```

If Qwen/Ollama is not configured, the console returns a `not_configured` response instead of failing.

## Placeholder Providers

`Claude` is placeholder-only in this version. It returns:

`Claude provider is not configured yet. Add configuration before using this agent.`

`Codex` is placeholder-only in this version. Sona AI Console does not control the Codex extension or any other external extension.

Future credential-backed providers should use VS Code SecretStorage. API keys should not be stored in plaintext settings.

## Settings

Relevant settings:

```json
{
  "sona.ai.defaultAgent": "sona",
  "sona.ai.qwen.enabled": false,
  "sona.ai.qwen.model": "qwen2.5-coder:7b",
  "sona.ai.ollama.url": "http://127.0.0.1:11434",
  "sona.ai.claude.enabled": false,
  "sona.ai.codex.enabled": false
}
```

`sona.ai.claude.enabled` and `sona.ai.codex.enabled` are reserved for future provider integrations. They do not enable working Claude or Codex integration in this preview.

## Not Yet Implemented

- Claude API calls
- Codex API calls
- control of external AI extensions
- workspace-wide content indexing
- persistent server-side conversation memory
- credential storage flows

## Manual Test

1. Open the Sona extension development host.
2. Run `Sona: Open AI Console`.
3. Confirm the `Sona AI Console` view opens under the Sona activity bar container.
4. Click each agent tab and confirm the active agent label changes.
5. Send a prompt with `Sona` selected and confirm a deterministic local response.
6. Send a prompt with `Claude` or `Codex` selected and confirm a `not_configured` response.
7. If Ollama/Qwen is configured, select `Qwen` and send a prompt. Otherwise confirm the `not_configured` state.
8. Toggle current file, selected text, workspace summary, and diagnostics, then send another prompt to confirm context routing.
