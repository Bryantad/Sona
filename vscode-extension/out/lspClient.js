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
const child_process_1 = require("child_process");
const vscode = __importStar(require("vscode"));
const node_1 = require("vscode-languageclient/node");
const pythonEnvironment_1 = require("./pythonEnvironment");
let client;
let outputChannel;
let lspStartupBlocked = false;
let lspBlockReason;
let dependencyPromptShown = false;
function ensureOutputChannel() {
    if (!outputChannel) {
        outputChannel = vscode.window.createOutputChannel("Sona LSP", { log: true });
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
function runDependencyPreflight(pythonPath) {
    try {
        const probe = (0, child_process_1.spawnSync)(pythonPath, ["-P", "-c", "import pygls, sona.lsp_server"], {
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
    }
    catch (err) {
        return { ok: false, reason: err instanceof Error ? err.message : String(err) };
    }
}
function startSonaLsp(context) {
    if (client) {
        return;
    }
    if (lspStartupBlocked) {
        appendOutput(`[sona-lsp] start skipped: ${lspBlockReason || "startup blocked"}`);
        return;
    }
    const pythonPath = (0, pythonEnvironment_1.resolveSonaPythonPath)();
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
    client = new node_1.LanguageClient("sona-lsp", "Sona Language Server", { command: pythonPath, args: ["-P", "-m", "sona.lsp_server", "--stdio"] }, {
        documentSelector: [{ scheme: "file", language: "sona" }],
        outputChannel: ensureOutputChannel()
    });
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
async function stopSonaLsp() {
    if (!client) {
        return;
    }
    const toStop = client;
    client = undefined;
    try {
        await toStop.stop();
    }
    catch (err) {
        appendOutput(`[sona-lsp] stop failed: ${err instanceof Error ? err.message : String(err)}`);
    }
}
