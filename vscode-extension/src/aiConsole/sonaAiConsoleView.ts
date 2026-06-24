import * as vscode from "vscode";

import {
  SonaAgentId,
  getAgents,
  normalizeAgentId
} from "./agentRegistry";
import {
  ContextToggles,
  collectContext
} from "./contextCollector";
import {
  AgentRequest,
  ProviderConfig,
  getProviderStatus,
  resolveQwenConfig,
  routeAgentRequest
} from "./providers";

type WebviewMessage =
  | { type: "selectAgent"; agentId: unknown }
  | { type: "sendPrompt"; agentId: unknown; prompt: unknown; contextToggles?: Partial<ContextToggles> }
  | { type: "clearChat" }
  | { type: "refreshStatus" };

const DEFAULT_TOGGLES: ContextToggles = {
  currentFile: true,
  selectedText: true,
  workspaceSummary: true,
  diagnostics: true
};

export class SonaAiConsoleViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "sona.aiConsole";

  private view?: vscode.WebviewView;
  private activeAgent: SonaAgentId;

  public constructor(private readonly context: vscode.ExtensionContext) {
    this.activeAgent = this.getDefaultAgent();
  }

  public resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(this.context.extensionUri, "media")
      ]
    };

    webviewView.webview.html = this.getHtml(webviewView.webview);
    webviewView.webview.onDidReceiveMessage(
      message => {
        void this.handleMessage(message as WebviewMessage);
      },
      undefined,
      this.context.subscriptions
    );

    void this.postStatus();
  }

  public async focus(): Promise<void> {
    await vscode.commands.executeCommand("workbench.view.extension.sona");
  }

  public clearChat(): void {
    void this.view?.webview.postMessage({ type: "clearChat" });
  }

  public async selectAgent(): Promise<void> {
    const status = getProviderStatus(this.getProviderConfig());
    const picked = await vscode.window.showQuickPick(
      status.agents.map(agent => ({
        label: agent.label,
        description: agent.configured ? "configured" : "not configured",
        detail: agent.description,
        agentId: agent.id
      })),
      {
        placeHolder: "Select Sona AI Console agent",
        matchOnDescription: true,
        matchOnDetail: true
      }
    );

    if (!picked) {
      return;
    }
    this.activeAgent = picked.agentId;
    void this.view?.webview.postMessage({
      type: "selectAgent",
      agentId: this.activeAgent
    });
  }

  private async handleMessage(message: WebviewMessage): Promise<void> {
    if (!message || typeof message.type !== "string") {
      return;
    }

    switch (message.type) {
      case "selectAgent":
        this.activeAgent = normalizeAgentId(message.agentId, this.activeAgent);
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

  private async handlePrompt(message: Extract<WebviewMessage, { type: "sendPrompt" }>): Promise<void> {
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

    const agentId = normalizeAgentId(message.agentId, this.activeAgent);
    this.activeAgent = agentId;
    const context = await collectContext({
      ...DEFAULT_TOGGLES,
      ...(message.contextToggles || {})
    });
    const request: AgentRequest = {
      agentId,
      prompt,
      context
    };
    const response = await routeAgentRequest(request, this.getProviderConfig());
    await this.view?.webview.postMessage({
      type: "agentResponse",
      response
    });
    await this.postStatus();
  }

  private async postStatus(): Promise<void> {
    const config = this.getProviderConfig();
    const status = getProviderStatus(config);
    await this.view?.webview.postMessage({
      type: "providerStatus",
      activeAgent: this.activeAgent,
      defaultAgent: this.getDefaultAgent(),
      status
    });
  }

  private getProviderConfig(): ProviderConfig {
    const cfg = vscode.workspace.getConfiguration("sona");
    return {
      qwenEnabled: cfg.get<boolean>("ai.qwen.enabled", false),
      qwenModel: cfg.get<string>("ai.qwen.model", "qwen2.5-coder:7b"),
      ollamaUrl: cfg.get<string>("ai.ollama.url", "http://127.0.0.1:11434"),
      claudeEnabled: cfg.get<boolean>("ai.claude.enabled", false),
      codexEnabled: cfg.get<boolean>("ai.codex.enabled", false),
      workspaceFolderPaths: (vscode.workspace.workspaceFolders || []).map(folder => folder.uri.fsPath),
      timeoutMs: cfg.get<number>("cli.timeout", 30000)
    };
  }

  private getDefaultAgent(): SonaAgentId {
    const configured = vscode.workspace
      .getConfiguration("sona")
      .get<string>("ai.defaultAgent", "sona");
    return normalizeAgentId(configured, "sona");
  }

  private getHtml(webview: vscode.Webview): string {
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
    const qwen = resolveQwenConfig(this.getProviderConfig());
    const initialAgents = getAgents({
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

function getNonce(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let value = "";
  for (let i = 0; i < 32; i += 1) {
    value += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return value;
}
