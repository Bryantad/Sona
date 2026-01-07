import * as vscode from 'vscode';
import * as http from 'http';
import * as https from 'https';
import * as path from 'path';
import { verifyRuntime, openRepl, runFile, runFileInDebug, exportCognitiveReport } from './runtime';
import { startSonaLsp, stopSonaLsp } from './lspClient';

// Version aligned with core project
const EXT_VERSION = '0.10.0';

let focusMode = false;
let statusBarItem: vscode.StatusBarItem | null = null;
let lspOutputChannel: vscode.OutputChannel | null = null;
const seenProfileDocs = new Set<string>();

function shouldStartLsp(doc?: vscode.TextDocument): boolean {
  if (!doc) return false;
  if (doc.languageId === 'sona') return true;
  return doc.fileName.toLowerCase().endsWith('.sona');
}

function getConfig() {
  return vscode.workspace.getConfiguration('sona');
}

function extractProfileFromText(text: string): string | null {
  const patterns = [
    /profile\s*\(\s*["'](neurotypical|adhd|dyslexia)["']\s*\)/i,
    /#\s*profile\s*:\s*(neurotypical|adhd|dyslexia)/i,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      return match[1].toLowerCase();
    }
  }
  return null;
}

async function maybeApplyProfileFromDoc(doc?: vscode.TextDocument) {
  if (!doc || doc.languageId !== 'sona') return;
  const key = doc.uri.toString();
  if (seenProfileDocs.has(key)) return;

  const profile = extractProfileFromText(doc.getText());
  if (!profile) return;
  seenProfileDocs.add(key);

  const cfg = getConfig();
  const currentProfile = cfg.get<string>('userProfile');
  if (currentProfile === profile) return;

  const choice = await vscode.window.showInformationMessage(
    `Sona profile annotation detected: ${profile}. Apply for this workspace?`,
    'Apply', 'Ignore'
  );
  if (choice === 'Apply') {
    await cfg.update('userProfile', profile, vscode.ConfigurationTarget.Workspace);
    vscode.window.showInformationMessage(`Sona profile set to ${profile} for this workspace`);
  }
}

async function safeRequest(url: string, timeout: number, retries: number): Promise<string> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const status = await httpGetStatus(url, timeout);
      return `AI Router OK (status ${status})`;
    } catch (err: any) {
      if (attempt === retries) {
        return `AI Router Unreachable after ${retries + 1} attempts: ${err.message || err}`;
      }
      await new Promise(r => setTimeout(r, 300 * (attempt + 1)));
    }
  }
  return 'Unknown error';
}

function httpGetStatus(urlString: string, timeoutMs: number): Promise<number> {
  return new Promise((resolve, reject) => {
    let url: URL;
    try {
      url = new URL(urlString);
    } catch {
      reject(new Error(`Invalid URL: ${urlString}`));
      return;
    }

    const lib = url.protocol === 'https:' ? https : http;
    const req = lib.request(
      url,
      {
        method: 'GET',
        timeout: timeoutMs
      },
      (res) => {
        // Drain and close
        res.resume();
        resolve(res.statusCode ?? 0);
      }
    );

    req.on('timeout', () => {
      req.destroy(new Error('Request timed out'));
    });
    req.on('error', (e) => reject(e));
    req.end();
  });
}

function ensureStatusBar() {
  if (!statusBarItem) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'sona.toggleFocusMode';
  }
  statusBarItem.text = `Sona ${focusMode ? '$(eye-closed)' : '$(eye)'} ${focusMode ? 'Focus' : 'Ready'}`;
  statusBarItem.tooltip = 'Toggle Sona Focus Mode';
  statusBarItem.show();
}

async function selectUserProfile() {
  const choice = await vscode.window.showQuickPick(['neurotypical', 'adhd', 'dyslexia'], {
    placeHolder: 'Select cognitive accessibility profile'
  });
  if (choice) {
    await getConfig().update('userProfile', choice, vscode.ConfigurationTarget.Global);
    vscode.window.showInformationMessage(`Sona profile set to ${choice}`);
  }
}

function showWelcome() {
  vscode.window.showInformationMessage(
    '🌟 Welcome to Sona 0.10.0 – AI-Native Programming with Cognitive Accessibility. Install sona-ai for advanced features: pip install sona-ai',
    'View Docs', 'Install sona-ai'
  ).then(selection => {
    if (selection === 'View Docs') {
      vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona'));
    } else if (selection === 'Install sona-ai') {
      const terminal = vscode.window.createTerminal('Sona Setup');
      terminal.show();
      terminal.sendText('pip install sona-ai');
    }
  });
}

function showHelp() {
  vscode.window.showInformationMessage(
    'Sona Commands: Generate, Refactor, Explain, Debug, Optimize, Focus Mode, AI Check.'
  );
}

async function checkAIConnection() {
  const cfg = getConfig();
  const endpoint = cfg.get<string>('aiRouter.endpoint');
  const timeout = cfg.get<number>('aiRouter.timeout') || 30000;
  const retries = cfg.get<number>('aiRouter.retryAttempts') || 3;
  const msg = await safeRequest(endpoint!, timeout, retries);
  vscode.window.showInformationMessage(msg);
}

function generateCode() {
  vscode.window.showInformationMessage('Code generation placeholder (integrate with CLI/AI backend).');
}

function refactorCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.selection.isEmpty) {
    vscode.window.showWarningMessage('Select code to refactor.');
    return;
  }
  vscode.window.showInformationMessage('Refactor placeholder – selection length ' + editor.document.getText(editor.selection).length);
}

function explainCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.selection.isEmpty) {
    vscode.window.showWarningMessage('Select code to explain.');
    return;
  }
  vscode.window.showInformationMessage('Explain placeholder – sending selection to AI.');
}

function debugCode() {
  vscode.window.showInformationMessage('Debug placeholder – attach to Sona runtime.');
}

function optimizeCode() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.selection.isEmpty) {
    vscode.window.showWarningMessage('Select code to optimize.');
    return;
  }
  vscode.window.showInformationMessage('Optimize placeholder – analyzing selection.');
}

async function exportCognitiveReportCommand() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('No active editor. Open a .sona file first.');
    return;
  }

  const doc = editor.document;
  if (doc.languageId !== 'sona' && !doc.fileName.toLowerCase().endsWith('.sona')) {
    vscode.window.showWarningMessage('Current file is not a Sona file.');
    return;
  }

  if (doc.isDirty) {
    await doc.save();
  }

  const format = await vscode.window.showQuickPick(['md', 'json'], {
    placeHolder: 'Select cognitive report format'
  });
  if (!format) return;

  const workspace = vscode.workspace.getWorkspaceFolder(doc.uri) ?? vscode.workspace.workspaceFolders?.[0];
  if (!workspace) {
    vscode.window.showErrorMessage('Open a workspace folder to export reports.');
    return;
  }

  const filePath = doc.uri.fsPath;
  const baseName = path.basename(filePath, path.extname(filePath));
  const reportDir = path.join(workspace.uri.fsPath, '.sona', 'reports');
  const outPath = path.join(reportDir, `${baseName}.cognitive_report.${format}`);

  if (lspOutputChannel) {
    lspOutputChannel.appendLine(`[sona] export report -> ${outPath}`);
  }

  try {
    await exportCognitiveReport(filePath, format as 'md' | 'json', outPath, lspOutputChannel ?? undefined);
    const reportDoc = await vscode.workspace.openTextDocument(outPath);
    await vscode.window.showTextDocument(reportDoc, { preview: false });
  } catch (err: any) {
    const message = err?.message ? `Report export failed: ${err.message}` : 'Report export failed.';
    vscode.window.showErrorMessage(message);
  }
}

function toggleFocusMode() {
  focusMode = !focusMode;
  ensureStatusBar();
  vscode.window.showInformationMessage(focusMode ? 'Focus Mode Enabled' : 'Focus Mode Disabled');
}

function clearCognitiveMemory() {
  vscode.window.showInformationMessage('Cognitive memory cleared (placeholder).');
}

function showOnboarding() {
  vscode.commands.executeCommand('sona.welcome');
  vscode.window.showInformationMessage('Onboarding placeholder – open docs panel.');
}

export function activate(context: vscode.ExtensionContext) {
  if (!lspOutputChannel) {
    lspOutputChannel = vscode.window.createOutputChannel('Sona LSP');
    context.subscriptions.push(lspOutputChannel);
  }
  lspOutputChannel.appendLine(`[sona] activate v${EXT_VERSION}`);

  ensureStatusBar();

  // Start Language Server (LSP) lazily for .sona files
  const maybeStart = (doc?: vscode.TextDocument) => {
    const active = doc ?? vscode.window.activeTextEditor?.document;
    const lang = active?.languageId ?? '<none>';
    const file = active?.uri?.toString() ?? '<none>';
    lspOutputChannel?.appendLine(`[sona] maybeStart: lang=${lang} uri=${file}`);
    void maybeApplyProfileFromDoc(active);
    if (shouldStartLsp(active)) {
      lspOutputChannel?.appendLine('[sona] starting LSP...');
      startSonaLsp(context, lspOutputChannel ?? undefined);
    } else {
      lspOutputChannel?.appendLine('[sona] not starting LSP (not a .sona doc)');
    }
  };

  context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor((e) => maybeStart(e?.document)));
  context.subscriptions.push(vscode.workspace.onDidOpenTextDocument((d) => maybeStart(d)));
  maybeStart();

  const registrations: Array<[string, (...args: any[]) => any]> = [
    ['sona.selectUserProfile', selectUserProfile],
    ['sona.welcome', showWelcome],
    ['sona.help', showHelp],
    ['sona.checkAIConnection', checkAIConnection],
    ['sona.generateCode', generateCode],
    ['sona.refactorCode', refactorCode],
    ['sona.explainCode', explainCode],
    ['sona.debugCode', debugCode],
    ['sona.optimizeCode', optimizeCode],
    ['sona.toggleFocusMode', toggleFocusMode],
    ['sona.clearCognitiveMemory', clearCognitiveMemory],
    ['sona.showOnboarding', showOnboarding],
    ['sona.verifyRuntime', verifyRuntime],
    ['sona.openRepl', openRepl],
    ['sona.runFile', runFile],
    ['sona.runFileDebug', runFileInDebug],
    ['sona.exportCognitiveReport', exportCognitiveReportCommand]
  ];

  for (const [cmd, fn] of registrations) {
    context.subscriptions.push(vscode.commands.registerCommand(cmd, (...a) => fn(...a)));
  }

  if (getConfig().get<boolean>('onboarding.showWelcome')) {
    setTimeout(() => showWelcome(), 800);
  }

  console.log(`Sona extension activated v${EXT_VERSION}`);
}

export function deactivate() {
  statusBarItem?.dispose();
  void stopSonaLsp();
}

