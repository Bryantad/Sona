"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const axios_1 = require("axios");
const runtime_1 = require("./runtime");
const lspClient_1 = require("./lspClient");
// Version aligned with core project
const EXT_VERSION = '0.9.9';
let focusMode = false;
let statusBarItem = null;
function getConfig() {
    return vscode.workspace.getConfiguration('sona');
}
function safeRequest(url, timeout, retries) {
    return __awaiter(this, void 0, void 0, function* () {
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const res = yield axios_1.default.get(url, { timeout });
                return `AI Router OK (status ${res.status})`;
            }
            catch (err) {
                if (attempt === retries) {
                    return `AI Router Unreachable after ${retries + 1} attempts: ${err.message || err}`;
                }
                yield new Promise(r => setTimeout(r, 300 * (attempt + 1)));
            }
        }
        return 'Unknown error';
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
function selectUserProfile() {
    return __awaiter(this, void 0, void 0, function* () {
        const choice = yield vscode.window.showQuickPick(['neurotypical', 'adhd', 'dyslexia'], {
            placeHolder: 'Select cognitive accessibility profile'
        });
        if (choice) {
            yield getConfig().update('userProfile', choice, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage(`Sona profile set to ${choice}`);
        }
    });
}
function showWelcome() {
    vscode.window.showInformationMessage('🌟 Welcome to Sona 0.9.9 – AI-Native Programming with Cognitive Accessibility. Install sona-ai for advanced features: pip install sona-ai', 'View Docs', 'Install sona-ai').then(selection => {
        if (selection === 'View Docs') {
            vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona'));
        }
        else if (selection === 'Install sona-ai') {
            const terminal = vscode.window.createTerminal('Sona Setup');
            terminal.show();
            terminal.sendText('pip install sona-ai');
        }
    });
}
function showHelp() {
    vscode.window.showInformationMessage('Sona Commands: Generate, Refactor, Explain, Debug, Optimize, Focus Mode, AI Check.');
}
function checkAIConnection() {
    return __awaiter(this, void 0, void 0, function* () {
        const cfg = getConfig();
        const endpoint = cfg.get('aiRouter.endpoint');
        const timeout = cfg.get('aiRouter.timeout') || 30000;
        const retries = cfg.get('aiRouter.retryAttempts') || 3;
        const msg = yield safeRequest(endpoint, timeout, retries);
        vscode.window.showInformationMessage(msg);
    });
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
function activate(context) {
    ensureStatusBar();
    // Start Language Server (LSP) for .sona files
    (0, lspClient_1.startSonaLsp)(context);
    const registrations = [
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
        ['sona.verifyRuntime', runtime_1.verifyRuntime],
        ['sona.openRepl', runtime_1.openRepl]
    ];
    for (const [cmd, fn] of registrations) {
        context.subscriptions.push(vscode.commands.registerCommand(cmd, (...a) => fn(...a)));
    }
    if (getConfig().get('onboarding.showWelcome')) {
        setTimeout(() => showWelcome(), 800);
    }
    console.log(`Sona extension activated v${EXT_VERSION}`);
}
exports.activate = activate;
function deactivate() {
    statusBarItem === null || statusBarItem === void 0 ? void 0 : statusBarItem.dispose();
    void (0, lspClient_1.stopSonaLsp)();
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map