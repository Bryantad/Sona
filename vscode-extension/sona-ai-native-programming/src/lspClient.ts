import * as vscode from 'vscode';
import { LanguageClient, LanguageClientOptions, ServerOptions } from 'vscode-languageclient/node.js';
import * as fs from 'fs';
import * as path from 'path';

let client: LanguageClient | undefined;
let outputChannel: vscode.OutputChannel | undefined;

function resolvePythonPath(): string {
  const cfg = vscode.workspace.getConfiguration('sona');
  const configured = cfg.get<string>('pythonPath') || cfg.get<string>('cli.pythonPath');
  if (configured && configured.trim()) {
    return configured.trim();
  }

  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (workspace) {
    const winCandidate = path.join(workspace, '.venv', 'Scripts', 'python.exe');
    const posixCandidate = path.join(workspace, '.venv', 'bin', 'python');
    if (process.platform === 'win32' && fs.existsSync(winCandidate)) {
      return winCandidate;
    }
    if (process.platform !== 'win32' && fs.existsSync(posixCandidate)) {
      return posixCandidate;
    }
  }

  return 'python';
}

export function startSonaLsp(context: vscode.ExtensionContext, channel?: vscode.OutputChannel) {
  if (channel) {
    outputChannel = channel;
  }
  if (client) {
    outputChannel?.appendLine('[sona-lsp] client already running, skipping start');
    return;
  }

  const pythonPath = resolvePythonPath();
  outputChannel?.appendLine(`[sona-lsp] resolved pythonPath: ${pythonPath}`);

  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel('Sona LSP');
  }
  outputChannel.appendLine(`[sona-lsp] starting: ${pythonPath} -m sona.lsp_server --stdio`);

  const serverOptions: ServerOptions = {
    command: pythonPath,
    args: ['-m', 'sona.lsp_server', '--stdio']
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: 'file', language: 'sona' },
      { scheme: 'untitled', language: 'sona' }
    ],
    outputChannel
  };

  client = new LanguageClient('sona-lsp', 'Sona Language Server', serverOptions, clientOptions);
  client.start();
  context.subscriptions.push({
    dispose: () => {
      void stopSonaLsp();
    }
  });
}

export async function stopSonaLsp() {
  if (!client) return;
  const toStop = client;
  client = undefined;
  await toStop.stop();
}
