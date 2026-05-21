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
exports.stopSonaLsp = exports.startSonaLsp = void 0;
const vscode = require("vscode");
const node_1 = require("vscode-languageclient/node");
const child_process_1 = require("child_process");
const fs = require("fs");
const path = require("path");
let client;
let outputChannel;
let lspStartupBlocked = false;
let lspBlockReason;
let dependencyPromptShown = false;
function ensureOutputChannel() {
    if (!outputChannel) {
        outputChannel = vscode.window.createOutputChannel('Sona LSP');
    }
    return outputChannel;
}
function appendOutput(line) {
    ensureOutputChannel().appendLine(line);
}
function quoteForShell(raw) {
    if (!raw) {
        return "python";
    }
    if (/\s/.test(raw)) {
        return `"${raw.replace(/"/g, '\\"')}"`;
    }
    return raw;
}
function showDependencyError(pythonPath, details) {
    if (dependencyPromptShown) {
        return;
    }
    dependencyPromptShown = true;
    const installCmd = `${quoteForShell(pythonPath)} -m pip install pygls`;
    const message = 'Sona LSP requires pygls in the selected Python environment. Install pygls, then reload VS Code.';
    void vscode.window
        .showErrorMessage(message, 'Copy install command', 'Open Sona LSP output')
        .then((choice) => {
        if (choice === 'Copy install command') {
            void vscode.env.clipboard.writeText(installCmd);
            void vscode.window.showInformationMessage('Copied install command for Sona LSP dependency.');
            return;
        }
        if (choice === 'Open Sona LSP output') {
            ensureOutputChannel().show(true);
        }
    });
    appendOutput(`[sona-lsp] dependency check failed: ${details}`);
    appendOutput(`[sona-lsp] install with: ${installCmd}`);
}
function runDependencyPreflight(pythonPath) {
    try {
        const probe = (0, child_process_1.spawnSync)(pythonPath, ['-c', 'import pygls'], {
            encoding: 'utf8',
            timeout: 5000,
            windowsHide: true
        });
        if (probe.error) {
            return { ok: false, reason: probe.error.message || String(probe.error) };
        }
        if (typeof probe.status === 'number' && probe.status !== 0) {
            const stderr = (probe.stderr || '').trim();
            const stdout = (probe.stdout || '').trim();
            const combined = [stderr, stdout].filter(Boolean).join(' | ');
            return { ok: false, reason: combined || `python exited with status ${probe.status}` };
        }
        return { ok: true };
    }
    catch (err) {
        return { ok: false, reason: err instanceof Error ? err.message : String(err) };
    }
}
function resolvePythonPath() {
    var _a, _b;
    const cfg = vscode.workspace.getConfiguration('sona');
    const configured = cfg.get('pythonPath') || cfg.get('cli.pythonPath');
    if (configured && configured.trim()) {
        return configured.trim();
    }
    const workspace = (_b = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.uri.fsPath;
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
function startSonaLsp(context) {
    if (client) {
        return;
    }
    if (lspStartupBlocked) {
        appendOutput(`[sona-lsp] start skipped: ${lspBlockReason || 'startup blocked'}`);
        return;
    }
    const pythonPath = resolvePythonPath();
    ensureOutputChannel();
    appendOutput(`[sona-lsp] resolved pythonPath: ${pythonPath}`);
    const preflight = runDependencyPreflight(pythonPath);
    if (!preflight.ok) {
        lspStartupBlocked = true;
        lspBlockReason = preflight.reason;
        showDependencyError(pythonPath, preflight.reason || 'missing pygls dependency');
        return;
    }
    appendOutput(`[sona-lsp] starting: ${pythonPath} -m sona.lsp_server --stdio`);
    const serverOptions = {
        command: pythonPath,
        args: ['-m', 'sona.lsp_server', '--stdio']
    };
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'sona' }],
        outputChannel: ensureOutputChannel()
    };
    client = new node_1.LanguageClient('sona-lsp', 'Sona Language Server', serverOptions, clientOptions);
    client.onDidChangeState((event) => {
        appendOutput(`[sona-lsp] state: ${event.oldState} -> ${event.newState}`);
    });
    client.start().catch((err) => {
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
exports.startSonaLsp = startSonaLsp;
function stopSonaLsp() {
    return __awaiter(this, void 0, void 0, function* () {
        if (!client)
            return;
        const toStop = client;
        client = undefined;
        try {
            yield toStop.stop();
        }
        catch (err) {
            appendOutput(`[sona-lsp] stop failed: ${err instanceof Error ? err.message : String(err)}`);
        }
    });
}
exports.stopSonaLsp = stopSonaLsp;
//# sourceMappingURL=lspClient.js.map
