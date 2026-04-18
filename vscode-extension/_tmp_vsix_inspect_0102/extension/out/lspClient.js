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
const fs = require("fs");
const path = require("path");
let client;
let outputChannel;
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
    const pythonPath = resolvePythonPath();
    if (!outputChannel) {
        outputChannel = vscode.window.createOutputChannel('Sona LSP');
    }
    outputChannel.appendLine(`[sona-lsp] starting: ${pythonPath} -m sona.lsp_server --stdio`);
    const serverOptions = {
        command: pythonPath,
        args: ['-m', 'sona.lsp_server', '--stdio']
    };
    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'sona' }],
        outputChannel
    };
    client = new node_1.LanguageClient('sona-lsp', 'Sona Language Server', serverOptions, clientOptions);
    client.start();
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
        yield toStop.stop();
    });
}
exports.stopSonaLsp = stopSonaLsp;
//# sourceMappingURL=lspClient.js.map