import { spawnSync } from "child_process";
import * as vscode from "vscode";
import { LanguageClient } from "vscode-languageclient/node";

import { resolveSonaPythonPath } from "./pythonEnvironment";
import { guardCodeActions, guideOptions } from "./guide";
import { GuideOptions } from "./guideModel";

let client: LanguageClient | undefined;
let started: Promise<void> | undefined;
let outputChannel: vscode.LogOutputChannel | undefined;
let lspStartupBlocked = false;
let lspBlockReason: string | undefined;
let dependencyPromptShown = false;

function ensureOutputChannel(): vscode.LogOutputChannel {
  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel("Sona LSP", { log: true });
  }
  return outputChannel;
}

function appendOutput(line: string): void {
  ensureOutputChannel().appendLine(line);
}

function quoteForShell(raw: string): string {
  if (!raw) {
    return "python";
  }
  if (/\s/.test(raw)) {
    return `"${raw.replace(/"/g, '\\"')}"`;
  }
  return raw;
}

function showDependencyError(pythonPath: string, details: string): void {
  if (dependencyPromptShown) {
    return;
  }
  dependencyPromptShown = true;
  const installCmd = `${quoteForShell(pythonPath)} -m pip install --upgrade sona-lang`;
  const message = "The selected Python environment cannot load the Sona language server. Install or upgrade sona-lang, then reload VS Code.";
  void vscode.window
    .showErrorMessage(message, "Copy install command", "Open Sona LSP output")
    .then(choice => {
      if (choice === "Copy install command") {
        void vscode.env.clipboard.writeText(installCmd);
        void vscode.window.showInformationMessage("Copied install command for Sona LSP dependency.");
        return;
      }
      if (choice === "Open Sona LSP output") {
        ensureOutputChannel().show(true);
      }
    });
  appendOutput(`[sona-lsp] dependency check failed: ${details}`);
  appendOutput(`[sona-lsp] install with: ${installCmd}`);
}

function runDependencyPreflight(pythonPath: string): { ok: boolean; reason?: string } {
  try {
    const probe = spawnSync(pythonPath, ["-P", "-c", "import pygls, sona.lsp_server"], {
      encoding: "utf8",
      timeout: 5000,
      windowsHide: true
    });
    if (probe.error) {
      return { ok: false, reason: probe.error.message || String(probe.error) };
    }
    if (typeof probe.status === "number" && probe.status !== 0) {
      const stderr = (probe.stderr || "").trim();
      const stdout = (probe.stdout || "").trim();
      const combined = [stderr, stdout].filter(Boolean).join(" | ");
      return { ok: false, reason: combined || `python exited with status ${probe.status}` };
    }
    return { ok: true };
  } catch (err) {
    return { ok: false, reason: err instanceof Error ? err.message : String(err) };
  }
}

export function startSonaLsp(context: vscode.ExtensionContext): void {
  if (client) {
    return;
  }
  if (lspStartupBlocked) {
    appendOutput(`[sona-lsp] start skipped: ${lspBlockReason || "startup blocked"}`);
    return;
  }

  const pythonPath = resolveSonaPythonPath();
  ensureOutputChannel();
  appendOutput(`[sona-lsp] resolved pythonPath: ${pythonPath}`);
  const preflight = runDependencyPreflight(pythonPath);
  if (!preflight.ok) {
    lspStartupBlocked = true;
    lspBlockReason = preflight.reason;
    showDependencyError(pythonPath, preflight.reason || "missing pygls dependency");
    return;
  }

  appendOutput(`[sona-lsp] starting: ${pythonPath} -P -m sona.lsp_server --stdio`);
  client = new LanguageClient(
    "sona-lsp",
    "Sona Language Server",
    { command: pythonPath, args: ["-P", "-m", "sona.lsp_server", "--stdio"] },
    {
      documentSelector: [{ scheme: "file", language: "sona" }],
      outputChannel: ensureOutputChannel(),
      middleware: {
        async provideCodeActions(document, range, actionContext, token, next) {
          return guardCodeActions(await next(document, range, actionContext, token), document.uri.toString());
        }
      }
    }
  );
  client.onDidChangeState(event => {
    appendOutput(`[sona-lsp] state: ${event.oldState} -> ${event.newState}`);
  });
  started = client.start();
  started.then(() => updateGuideOptions(guideOptions(vscode.window.activeTextEditor?.document.uri))).catch(err => {
    lspStartupBlocked = true;
    lspBlockReason = err instanceof Error ? err.message : String(err);
    appendOutput(`[sona-lsp] failed to start: ${lspBlockReason}`);
  });
  context.subscriptions.push({
    dispose: () => {
      void stopSonaLsp();
    }
  });
}

export async function requestSonaGuide(context: vscode.ExtensionContext, payload: unknown): Promise<any> {
  startSonaLsp(context);
  if (!client || !started || lspStartupBlocked) throw new Error("The Sona language server is unavailable. Check the Sona LSP output and selected Python runtime.");
  await started;
  try { return await client.sendRequest("sona/guide", payload); }
  catch { throw new Error("Sona Guide could not answer this request. Update the selected Sona runtime and reload VS Code."); }
}

export async function updateGuideOptions(options: GuideOptions): Promise<void> {
  if (client?.isRunning()) await client.sendNotification("workspace/didChangeConfiguration", { settings: { sona: { guide: options } } });
}

export async function stopSonaLsp(): Promise<void> {
  if (!client) {
    return;
  }
  const toStop = client;
  client = undefined;
  started = undefined;
  try {
    await toStop.stop();
  } catch (err) {
    appendOutput(`[sona-lsp] stop failed: ${err instanceof Error ? err.message : String(err)}`);
  }
}
