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
Object.defineProperty(exports, "__esModule", { value: true });
exports.startSonaLsp = startSonaLsp;
exports.stopSonaLsp = stopSonaLsp;
const vscode = __importStar(require("vscode"));
const node_js_1 = require("vscode-languageclient/node.js");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
let client;
let outputChannel;
function resolvePythonPath() {
    const cfg = vscode.workspace.getConfiguration('sona');
    const configured = cfg.get('pythonPath') || cfg.get('cli.pythonPath');
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
function startSonaLsp(context, channel) {
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
    const serverOptions = {
        command: pythonPath,
        args: ['-m', 'sona.lsp_server', '--stdio']
    };
    const clientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'sona' },
            { scheme: 'untitled', language: 'sona' }
        ],
        outputChannel
    };
    client = new node_js_1.LanguageClient('sona-lsp', 'Sona Language Server', serverOptions, clientOptions);
    client.start();
    context.subscriptions.push({
        dispose: () => {
            void stopSonaLsp();
        }
    });
}
async function stopSonaLsp() {
    if (!client)
        return;
    const toStop = client;
    client = undefined;
    await toStop.stop();
}
//# sourceMappingURL=lspClient.js.map