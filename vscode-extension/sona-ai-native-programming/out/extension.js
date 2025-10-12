"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const axios_1 = __importDefault(require("axios"));
const runtime_1 = require("./runtime");
// Version aligned with core project
const EXT_VERSION = '0.9.6';
let focusMode = false;
let statusBarItem = null;
function getConfig() {
    return vscode.workspace.getConfiguration('sona');
}
async function safeRequest(url, timeout, retries) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const res = await axios_1.default.get(url, { timeout });
            return `AI Router OK (status ${res.status})`;
        }
        catch (err) {
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
    vscode.window.showInformationMessage('🌟 Welcome to Sona 0.9.6 – AI-Native Programming with Cognitive Accessibility. Install sona-ai for advanced features: pip install sona-ai', 'View Docs', 'Install sona-ai').then(selection => {
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
async function checkAIConnection() {
    const cfg = getConfig();
    const endpoint = cfg.get('aiRouter.endpoint');
    const timeout = cfg.get('aiRouter.timeout') || 30000;
    const retries = cfg.get('aiRouter.retryAttempts') || 3;
    const msg = await safeRequest(endpoint, timeout, retries);
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
function activate(context) {
    ensureStatusBar();
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
function deactivate() {
    statusBarItem?.dispose();
}
//# sourceMappingURL=extension.js.map