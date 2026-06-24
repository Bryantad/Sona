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
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.SonaAiConsoleViewProvider = void 0;
const vscode = __importStar(require("vscode"));
const agentRegistry_1 = require("./agentRegistry");
const contextCollector_1 = require("./contextCollector");
const providers_1 = require("./providers");
const DEFAULT_TOGGLES = {
    currentFile: true,
    selectedText: true,
    workspaceSummary: true,
    diagnostics: true
};
class SonaAiConsoleViewProvider {
    constructor(context) {
        this.context = context;
        this.activeAgent = this.getDefaultAgent();
    }
    resolveWebviewView(webviewView) {
        this.view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this.context.extensionUri, "media")
            ]
        };
        webviewView.webview.html = this.getHtml(webviewView.webview);
        webviewView.webview.onDidReceiveMessage(message => {
            void this.handleMessage(message);
        }, undefined, this.context.subscriptions);
        void this.postStatus();
    }
    async focus() {
        await vscode.commands.executeCommand("workbench.view.extension.sona");
    }
    clearChat() {
        void this.view?.webview.postMessage({ type: "clearChat" });
    }
    async selectAgent() {
        const status = (0, providers_1.getProviderStatus)(this.getProviderConfig());
        const picked = await vscode.window.showQuickPick(status.agents.map(agent => ({
            label: agent.label,
            description: agent.configured ? "configured" : "not configured",
            detail: agent.description,
            agentId: agent.id
        })), {
            placeHolder: "Select Sona AI Console agent",
            matchOnDescription: true,
            matchOnDetail: true
        });
        if (!picked) {
            return;
        }
        this.activeAgent = picked.agentId;
        void this.view?.webview.postMessage({
            type: "selectAgent",
            agentId: this.activeAgent
        });
    }
    async handleMessage(message) {
        if (!message || typeof message.type !== "string") {
            return;
        }
        switch (message.type) {
            case "selectAgent":
                this.activeAgent = (0, agentRegistry_1.normalizeAgentId)(message.agentId, this.activeAgent);
                await this.postStatus();
                break;
            case "sendPrompt":
                await this.handlePrompt(message);
                break;
            case "clearChat":
                this.clearChat();
                break;
            case "refreshStatus":
                await this.postStatus();
                break;
            default:
                break;
        }
    }
    async handlePrompt(message) {
        const prompt = typeof message.prompt === "string" ? message.prompt.trim() : "";
        if (!prompt) {
            await this.view?.webview.postMessage({
                type: "agentResponse",
                response: {
                    agentId: this.activeAgent,
                    status: "error",
                    text: "Enter a prompt before sending."
                }
            });
            return;
        }
        const agentId = (0, agentRegistry_1.normalizeAgentId)(message.agentId, this.activeAgent);
        this.activeAgent = agentId;
        const context = await (0, contextCollector_1.collectContext)({
            ...DEFAULT_TOGGLES,
            ...(message.contextToggles || {})
        });
        const request = {
            agentId,
            prompt,
            context
        };
        const response = await (0, providers_1.routeAgentRequest)(request, this.getProviderConfig());
        await this.view?.webview.postMessage({
            type: "agentResponse",
            response
        });
        await this.postStatus();
    }
    async postStatus() {
        const config = this.getProviderConfig();
        const status = (0, providers_1.getProviderStatus)(config);
        await this.view?.webview.postMessage({
            type: "providerStatus",
            activeAgent: this.activeAgent,
            defaultAgent: this.getDefaultAgent(),
            status
        });
    }
    getProviderConfig() {
        const cfg = vscode.workspace.getConfiguration("sona");
        return {
            qwenEnabled: cfg.get("ai.qwen.enabled", false),
            qwenModel: cfg.get("ai.qwen.model", "qwen2.5-coder:7b"),
            ollamaUrl: cfg.get("ai.ollama.url", "http://127.0.0.1:11434"),
            claudeEnabled: cfg.get("ai.claude.enabled", false),
            codexEnabled: cfg.get("ai.codex.enabled", false),
            workspaceFolderPaths: (vscode.workspace.workspaceFolders || []).map(folder => folder.uri.fsPath),
            timeoutMs: cfg.get("cli.timeout", 30000)
        };
    }
    getDefaultAgent() {
        const configured = vscode.workspace
            .getConfiguration("sona")
            .get("ai.defaultAgent", "sona");
        return (0, agentRegistry_1.normalizeAgentId)(configured, "sona");
    }
    getHtml(webview) {
        const nonce = getNonce();
        const cssUri = webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, "media", "sonaAiConsole.css"));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, "media", "sonaAiConsole.js"));
        const csp = [
            "default-src 'none'",
            `style-src ${webview.cspSource}`,
            `script-src 'nonce-${nonce}'`,
            `img-src ${webview.cspSource} https: data:`,
            `font-src ${webview.cspSource}`
        ].join("; ");
        const qwen = (0, providers_1.resolveQwenConfig)(this.getProviderConfig());
        const initialAgents = (0, agentRegistry_1.getAgents)({
            qwenConfigured: qwen.configured,
            claudeConfigured: false,
            codexConfigured: false
        });
        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="${csp}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="${cssUri}" rel="stylesheet">
  <title>Sona AI Console</title>
</head>
<body>
  <main class="console-shell">
    <header class="console-header">
      <h1>Sona AI Console</h1>
      <div id="providerStatus" class="provider-status" aria-live="polite">Loading providers...</div>
    </header>

    <section class="agent-section" aria-label="Agent selector">
      <div id="agentTabs" class="agent-tabs"></div>
      <div class="active-agent">Active agent: <strong id="activeAgentLabel">Sona</strong></div>
    </section>

    <section class="context-section" aria-label="Context toggles">
      <label><input id="toggleCurrentFile" type="checkbox" checked> current file</label>
      <label><input id="toggleSelection" type="checkbox" checked> selected text</label>
      <label><input id="toggleWorkspace" type="checkbox" checked> workspace summary</label>
      <label><input id="toggleDiagnostics" type="checkbox" checked> diagnostics</label>
    </section>

    <section id="messages" class="messages" aria-label="Chat messages" aria-live="polite"></section>

    <footer class="composer">
      <textarea id="promptInput" rows="3" placeholder="Ask Sona..." aria-label="Message"></textarea>
      <div class="composer-actions">
        <button id="clearButton" type="button" class="secondary">Clear chat</button>
        <button id="sendButton" type="button">Send</button>
      </div>
    </footer>
  </main>
  <script nonce="${nonce}" src="${scriptUri}" data-default-agent="${this.activeAgent}" data-agents="${encodeURIComponent(JSON.stringify(initialAgents))}"></script>
</body>
</html>`;
    }
}
exports.SonaAiConsoleViewProvider = SonaAiConsoleViewProvider;
SonaAiConsoleViewProvider.viewType = "sona.aiConsole";
function getNonce() {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let value = "";
    for (let i = 0; i < 32; i += 1) {
        value += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return value;
}
//# sourceMappingURL=sonaAiConsoleView.js.map