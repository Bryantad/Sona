import * as fs from "fs";
import * as path from "path";
import { spawnSync } from "child_process";
import * as vscode from "vscode";
import { LanguageClient } from "vscode-languageclient/node";

let client: LanguageClient | undefined;
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
  const installCmd = `${quoteForShell(pythonPath)} -m pip install pygls`;
  const message = "Sona LSP requires pygls in the selected Python environment. Install pygls, then reload VS Code.";
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
    const probe = spawnSync(pythonPath, ["-c", "import pygls"], {
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

function resolvePythonPath(): string {
  const cfg = vscode.workspace.getConfiguration("sona");
  const configured = cfg.get<string>("pythonPath") || cfg.get<string>("cli.pythonPath");
  if (configured && configured.trim()) {
    return configured.trim();
  }
  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (workspace) {
    const winCandidate = path.join(workspace, ".venv", "Scripts", "python.exe");
    const posixCandidate = path.join(workspace, ".venv", "bin", "python");
    if (process.platform === "win32" && fs.existsSync(winCandidate)) {
      return winCandidate;
    }
    if (process.platform !== "win32" && fs.existsSync(posixCandidate)) {
      return posixCandidate;
    }
  }
  return "python";
}

export function startSonaLsp(context: vscode.ExtensionContext): void {
  if (client) {
    return;
  }
  if (lspStartupBlocked) {
    appendOutput(`[sona-lsp] start skipped: ${lspBlockReason || "startup blocked"}`);
    return;
  }

  const pythonPath = resolvePythonPath();
  ensureOutputChannel();
  appendOutput(`[sona-lsp] resolved pythonPath: ${pythonPath}`);
  const preflight = runDependencyPreflight(pythonPath);
  if (!preflight.ok) {
    lspStartupBlocked = true;
    lspBlockReason = preflight.reason;
    showDependencyError(pythonPath, preflight.reason || "missing pygls dependency");
    return;
  }

  appendOutput(`[sona-lsp] starting: ${pythonPath} -m sona.lsp_server --stdio`);
  client = new LanguageClient(
    "sona-lsp",
    "Sona Language Server",
    { command: pythonPath, args: ["-m", "sona.lsp_server", "--stdio"] },
    {
      documentSelector: [{ scheme: "file", language: "sona" }],
      outputChannel: ensureOutputChannel()
    }
  );
  client.onDidChangeState(event => {
    appendOutput(`[sona-lsp] state: ${event.oldState} -> ${event.newState}`);
  });
  client.start().catch(err => {
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

export async function stopSonaLsp(): Promise<void> {
  if (!client) {
    return;
  }
  const toStop = client;
  client = undefined;
  try {
    await toStop.stop();
  } catch (err) {
    appendOutput(`[sona-lsp] stop failed: ${err instanceof Error ? err.message : String(err)}`);
  }
}
