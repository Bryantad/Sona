import * as vscode from 'vscode';
import axios from 'axios';
import { verifyRuntime, openRepl } from './runtime';

// Version aligned with core project
const EXT_VERSION = '0.9.6';

let focusMode = false;
let statusBarItem: vscode.StatusBarItem | null = null;

function getConfig() {
  return vscode.workspace.getConfiguration('sona');
}

async function safeRequest(url: string, timeout: number, retries: number): Promise<string> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await axios.get(url, { timeout });
      return `AI Router OK (status ${res.status})`;
    } catch (err: any) {
      if (attempt === retries) {
        return `AI Router Unreachable after ${retries + 1} attempts: ${err.message || err}`;
      }
      await new Promise(r => setTimeout(r, 300 * (attempt + 1)));
    }
  }
  return 'Unknown error';
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
    '🌟 Welcome to Sona 0.9.6 – AI-Native Programming with Cognitive Accessibility. Install sona-ai for advanced features: pip install sona-ai',
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
  ensureStatusBar();

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
    ['sona.openRepl', openRepl]
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
}
