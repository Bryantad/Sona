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
exports.SonaCliIntegration = void 0;
exports.activate = activate;
exports.deactivate = deactivate;
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
const vscode = __importStar(require("vscode"));
class SonaCliIntegration {
    context;
    config;
    outputChannel;
    statusBarItem;
    terminal;
    userProfile;
    constructor(context) {
        this.context = context;
        this.config = this.loadConfiguration();
        this.outputChannel = vscode.window.createOutputChannel("Sona");
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.userProfile = this.loadUserProfile();
        this.initializeStatusBar();
        this.registerCommands();
        void this.checkSonaInstallation();
    }
    loadConfiguration() {
        const config = vscode.workspace.getConfiguration("sona");
        return {
            pythonPath: config.get("cli.pythonPath", "python"),
            timeout: config.get("cli.timeout", 30000),
            autoSetup: config.get("ai.autoSetup", true)
        };
    }
    loadUserProfile() {
        const stored = this.context.globalState.get("sonaUserProfile");
        if (stored) {
            return stored;
        }
        return vscode.workspace.getConfiguration("sona").get("userProfile", "neurotypical");
    }
    initializeStatusBar() {
        this.statusBarItem.text = "$(rocket) Sona";
        this.statusBarItem.tooltip = "Sona Language Support - Click for info";
        this.statusBarItem.command = "sona.info";
        this.statusBarItem.show();
    }
    async checkSonaInstallation() {
        const result = await this.runSonaCommand(["--version"]);
        if (result.success) {
            this.statusBarItem.text = "$(rocket) Sona $(check)";
            this.statusBarItem.tooltip = `Sona CLI Available - ${result.output.trim()}`;
            this.outputChannel.appendLine(`[OK] Sona CLI detected: ${result.output.trim()}`);
            return;
        }
        this.statusBarItem.text = "$(alert) Sona";
        this.statusBarItem.tooltip = "Sona CLI not found - Click for help";
        this.statusBarItem.command = "sona.help";
        this.outputChannel.appendLine(`[WARN] Sona CLI check failed: ${result.error || result.output}`);
    }
    getCommandCwd() {
        const active = vscode.window.activeTextEditor?.document;
        if (active) {
            const activeFolder = vscode.workspace.getWorkspaceFolder(active.uri);
            if (activeFolder) {
                return activeFolder.uri.fsPath;
            }
            if (active.uri.scheme === "file" && !active.isUntitled) {
                return path.dirname(active.uri.fsPath);
            }
        }
        return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }
    runSonaCommand(args, input) {
        return new Promise(resolve => {
            const commandArgs = ["-m", "sona", ...args];
            this.outputChannel.appendLine(`Running: ${this.config.pythonPath} ${commandArgs.join(" ")}`);
            const cwd = this.getCommandCwd();
            const env = { ...process.env };
            if (cwd) {
                env.PYTHONPATH = cwd + (env.PYTHONPATH ? path.delimiter + env.PYTHONPATH : "");
            }
            const child = (0, child_process_1.spawn)(this.config.pythonPath, commandArgs, {
                cwd,
                env,
                windowsHide: true
            });
            let stdout = "";
            let stderr = "";
            let finished = false;
            const timeoutHandle = setTimeout(() => {
                if (child.exitCode === null) {
                    child.kill();
                }
                finish({
                    success: false,
                    output: stdout,
                    error: `Command timed out after ${this.config.timeout}ms`,
                    exitCode: -1
                });
            }, this.config.timeout);
            const finish = (result) => {
                if (finished) {
                    return;
                }
                finished = true;
                clearTimeout(timeoutHandle);
                this.outputChannel.appendLine(result.success ? "Command succeeded" : `Command failed: ${result.error}`);
                resolve(result);
            };
            child.stdout?.on("data", chunk => {
                stdout += chunk.toString();
            });
            child.stderr?.on("data", chunk => {
                stderr += chunk.toString();
            });
            child.on("error", error => {
                finish({ success: false, output: stdout, error: error.message, exitCode: -1 });
            });
            child.on("close", code => {
                const success = code === 0;
                finish({
                    success,
                    output: stdout,
                    error: success ? undefined : stderr || stdout || `Command exited with code ${code}`,
                    exitCode: code === null ? -1 : code
                });
            });
            if (child.stdin) {
                if (input) {
                    child.stdin.write(input);
                }
                child.stdin.end();
            }
        });
    }
    registerCommands() {
        this.context.subscriptions.push(vscode.commands.registerCommand("sona.welcome", () => this.showWelcome()), vscode.commands.registerCommand("sona.setup.azure", () => this.setupAzure()), vscode.commands.registerCommand("sona.setup.manual", () => this.setupManual()), vscode.commands.registerCommand("sona.selectUserProfile", () => this.selectUserProfile()), vscode.commands.registerCommand("sona.run", () => this.runCurrentFile()), vscode.commands.registerCommand("sona.transpile", () => this.transpileCurrentFile()), vscode.commands.registerCommand("sona.repl", () => this.startRepl()), vscode.commands.registerCommand("sona.check", () => this.checkCurrentFile()), vscode.commands.registerCommand("sona.format", () => this.formatCurrentFile()), vscode.commands.registerCommand("sona.explain", () => this.explainSelection()), vscode.commands.registerCommand("sona.suggest", () => this.getSuggestions()), vscode.commands.registerCommand("sona.profile", () => this.profileCurrentFile()), vscode.commands.registerCommand("sona.benchmark", () => this.benchmarkCurrentFile()), vscode.commands.registerCommand("sona.info", () => this.showInfo()), vscode.commands.registerCommand("sona.help", () => this.showHelp()), vscode.commands.registerCommand("sona.checkAIConnection", () => this.checkAIConnection()), vscode.commands.registerCommand("sona.aiPlanSelection", () => this.planSelection()), vscode.commands.registerCommand("sona.aiReviewSelection", () => this.reviewSelection()));
    }
    activeSavedFile(requiredLanguage) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage("Open a file first.");
            return undefined;
        }
        if (requiredLanguage && editor.document.languageId !== requiredLanguage) {
            vscode.window.showErrorMessage(`Please open a .${requiredLanguage} file.`);
            return undefined;
        }
        if (editor.document.isUntitled) {
            vscode.window.showErrorMessage("Save the file before running this command.");
            return undefined;
        }
        return editor.document;
    }
    async resolveWorkspaceRoot() {
        const active = vscode.window.activeTextEditor?.document;
        if (active) {
            const activeFolder = vscode.workspace.getWorkspaceFolder(active.uri);
            if (activeFolder) {
                return activeFolder.uri.fsPath;
            }
            if (active.uri.scheme === "file" && !active.isUntitled) {
                return path.dirname(active.uri.fsPath);
            }
        }
        const firstFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (firstFolder) {
            return firstFolder;
        }
        const picked = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: "Use Folder for Sona Setup",
            title: "Choose where Sona should create or open .env"
        });
        return picked?.[0]?.fsPath;
    }
    async openWorkspaceEnvFile(workspaceRoot) {
        const envUri = vscode.Uri.joinPath(vscode.Uri.file(workspaceRoot), ".env");
        const doc = await vscode.workspace.openTextDocument(envUri);
        await vscode.window.showTextDocument(doc);
    }
    async promptAzureSetupInput() {
        const endpoint = await vscode.window.showInputBox({
            prompt: "Azure OpenAI endpoint",
            placeHolder: "https://your-resource.openai.azure.com/",
            ignoreFocusOut: true
        });
        if (!endpoint) {
            return undefined;
        }
        const apiKey = await vscode.window.showInputBox({
            prompt: "Azure OpenAI API key",
            password: true,
            ignoreFocusOut: true
        });
        if (!apiKey) {
            return undefined;
        }
        const deployment = await vscode.window.showInputBox({
            prompt: "Azure OpenAI deployment name",
            placeHolder: "gpt-4o-mini",
            value: "gpt-4o-mini",
            ignoreFocusOut: true
        });
        return `${endpoint.trim()}\n${apiKey.trim()}\n${(deployment || "gpt-4o-mini").trim()}\n`;
    }
    async promptManualSetupInput() {
        const provider = await vscode.window.showQuickPick([
            { label: "Local Ollama", description: "Use an installed Qwen coder model", value: "local" },
            { label: "Azure OpenAI", description: "Use endpoint, key, and deployment", value: "azure" }
        ], { placeHolder: "Choose Sona AI provider", ignoreFocusOut: true });
        if (!provider) {
            return undefined;
        }
        if (provider.value === "local") {
            const model = await vscode.window.showInputBox({
                prompt: "Ollama model name",
                placeHolder: "qwen2.5-coder:7b",
                ignoreFocusOut: true
            });
            return model === undefined ? undefined : `local\n${model.trim()}\n`;
        }
        return this.promptAzureSetupInput();
    }
    async setupAzure() {
        const workspaceRoot = await this.resolveWorkspaceRoot();
        const setupInput = workspaceRoot ? await this.promptAzureSetupInput() : undefined;
        if (!workspaceRoot || !setupInput) {
            return;
        }
        const result = await this.runSonaCommand(["setup", "azure", "--manual", "--workspace", workspaceRoot], setupInput);
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine("\n--- Sona AI Setup ---");
            this.outputChannel.appendLine(result.output);
            await this.openWorkspaceEnvFile(workspaceRoot);
            vscode.window.showInformationMessage("Sona AI setup opened .env. Edit values, save, then run Sona: Check AI Connection.");
            return;
        }
        vscode.window.showErrorMessage(`Azure setup failed: ${result.error}`);
    }
    async setupManual() {
        const workspaceRoot = await this.resolveWorkspaceRoot();
        const setupInput = workspaceRoot ? await this.promptManualSetupInput() : undefined;
        if (!workspaceRoot || !setupInput) {
            return;
        }
        const result = await this.runSonaCommand(["setup", "manual", "--workspace", workspaceRoot], setupInput);
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine("\n--- Sona Manual AI Setup ---");
            this.outputChannel.appendLine(result.output);
            await this.openWorkspaceEnvFile(workspaceRoot);
            vscode.window.showInformationMessage("Manual AI setup opened .env. Edit values, save, then run Sona: Check AI Connection.");
            return;
        }
        vscode.window.showErrorMessage(`Manual setup failed: ${result.error}`);
    }
    async selectUserProfile() {
        const selected = await vscode.window.showQuickPick([
            { label: "Neurotypical", description: "Standard UI/UX for typical users", value: "neurotypical" },
            { label: "ADHD", description: "High-contrast, minimal distractions", value: "adhd" },
            { label: "Dyslexia", description: "Dyslexia-friendly fonts and enhanced readability", value: "dyslexia" }
        ], { placeHolder: "Select your cognitive profile for optimized experience" });
        if (selected) {
            this.userProfile = selected.value;
            await this.context.globalState.update("sonaUserProfile", this.userProfile);
            vscode.window.showInformationMessage(`Profile set to: ${selected.label}`);
        }
    }
    async runCurrentFile() {
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        const result = await this.runSonaCommand(["run", doc.fileName]);
        this.showCommandResult("Sona Run Output", result, "Run failed");
    }
    async transpileCurrentFile() {
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        const outputPath = doc.fileName.replace(/\.sona$/i, ".py");
        const result = await this.runSonaCommand(["transpile", doc.fileName, outputPath]);
        if (result.success) {
            vscode.window.showInformationMessage(`Transpiled to: ${outputPath}`);
            const outDoc = await vscode.workspace.openTextDocument(outputPath);
            await vscode.window.showTextDocument(outDoc);
            return;
        }
        vscode.window.showErrorMessage(`Transpilation failed: ${result.error}`);
    }
    startRepl() {
        if (!this.terminal || this.terminal.exitStatus) {
            this.terminal = vscode.window.createTerminal({
                name: "Sona REPL",
                shellPath: this.config.pythonPath,
                shellArgs: ["-m", "sona", "repl"]
            });
        }
        this.terminal.show();
    }
    async checkCurrentFile() {
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        const result = await this.runSonaCommand(["check", doc.fileName]);
        if (result.success) {
            vscode.window.showInformationMessage("Syntax check passed.");
            return;
        }
        vscode.window.showErrorMessage(`Syntax errors found: ${result.error}`);
    }
    async formatCurrentFile() {
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        const result = await this.runSonaCommand(["format", doc.fileName]);
        if (result.success) {
            vscode.window.showInformationMessage("File formatted successfully.");
            await vscode.commands.executeCommand("workbench.action.files.revert");
            return;
        }
        vscode.window.showErrorMessage(`Formatting failed: ${result.error}`);
    }
    async runDeveloperTask(taskType, instruction, selectedText) {
        const doc = vscode.window.activeTextEditor?.document;
        const request = {
            schema_version: 1,
            task_type: taskType,
            instruction,
            target_files: doc && !doc.isUntitled ? [doc.fileName] : [],
            context: {
                active_file: doc && !doc.isUntitled ? doc.fileName : undefined,
                selected_text: selectedText,
                origin: "vscode"
            }
        };
        return this.runSonaCommand(["ai", "task", "--request", "-", "--format", "json"], JSON.stringify(request));
    }
    async explainSelection() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showErrorMessage("Please select code to explain.");
            return;
        }
        if (editor.document.isUntitled) {
            vscode.window.showErrorMessage("Save the file before explaining code.");
            return;
        }
        await editor.document.save();
        const selectedText = editor.document.getText(editor.selection);
        const result = await this.runDeveloperTask("explain", "Explain the selected developer code.", selectedText);
        if (result.success) {
            this.showHtmlPanel("Code Explanation", this.getExplanationHtml(selectedText, result.output));
            return;
        }
        vscode.window.showErrorMessage(`Explanation failed: ${result.error}`);
    }
    async getSuggestions() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.isUntitled) {
            vscode.window.showErrorMessage("Save a file before getting suggestions.");
            return;
        }
        await editor.document.save();
        const prompt = await vscode.window.showInputBox({
            placeHolder: "Describe the developer task...",
            prompt: "Sona will return governed developer-task suggestions."
        });
        if (!prompt) {
            return;
        }
        const result = await this.runDeveloperTask("suggest", prompt);
        if (result.success) {
            this.showHtmlPanel("AI Suggestions", this.getSuggestionsHtml(prompt, result.output));
            return;
        }
        vscode.window.showErrorMessage(`Suggestions failed: ${result.error}`);
    }
    async planSelection() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showErrorMessage("Select text to create a plan.");
            return;
        }
        const text = editor.document.getText(editor.selection).slice(0, 4000);
        const result = await this.runDeveloperTask("suggest", "Create a development plan for the selected code.", text);
        this.showJsonResult("AI Plan", result);
    }
    async reviewSelection() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showErrorMessage("Select text to review.");
            return;
        }
        const text = editor.document.getText(editor.selection).slice(0, 6000);
        const result = await this.runDeveloperTask("review", "Review the selected developer code.", text);
        this.showJsonResult("AI Review", result);
    }
    async profileCurrentFile() {
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        this.showCommandResult("Performance Profile", await this.runSonaCommand(["profile", doc.fileName]), "Profiling failed");
    }
    async benchmarkCurrentFile() {
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        this.showCommandResult("Benchmark Results", await this.runSonaCommand(["benchmark", doc.fileName]), "Benchmarking failed");
    }
    async showInfo() {
        const result = await this.runSonaCommand(["info"]);
        if (result.success) {
            vscode.window.showInformationMessage(result.output, { modal: false });
            this.showCommandResult("Sona System Info", result, "Info failed");
            return;
        }
        vscode.window.showErrorMessage(`Info failed: ${result.error}`);
    }
    async showHelp() {
        this.showCommandResult("Sona Help", await this.runSonaCommand(["--help"]), "Help failed");
    }
    async checkAIConnection() {
        const result = await this.runSonaCommand(["model", "health"]);
        if (result.success) {
            vscode.window.showInformationMessage("Sona model registry is reachable.");
            return;
        }
        const choice = await vscode.window.showWarningMessage("Sona model registry check failed.", "Setup Azure", "Manual Setup", "Help");
        if (choice === "Setup Azure") {
            await this.setupAzure();
        }
        else if (choice === "Manual Setup") {
            await this.setupManual();
        }
        else if (choice === "Help") {
            await this.showHelp();
        }
    }
    showCommandResult(title, result, failurePrefix) {
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine(`\n--- ${title} ---`);
            this.outputChannel.appendLine(result.output);
            return;
        }
        vscode.window.showErrorMessage(`${failurePrefix}: ${result.error}`);
    }
    showJsonResult(title, result) {
        if (!result.success) {
            vscode.window.showErrorMessage(`${title} failed: ${result.error}`);
            return;
        }
        let body = result.output.trim();
        if (!body.startsWith("{") && !body.startsWith("[")) {
            body = JSON.stringify({ raw: body }, null, 2);
        }
        this.showHtmlPanel(title, `<html><body><pre>${this.escapeHtml(body)}</pre></body></html>`);
    }
    showHtmlPanel(title, html) {
        const panel = vscode.window.createWebviewPanel("sonaResult", title, vscode.ViewColumn.Beside, {
            enableScripts: false
        });
        panel.webview.html = html;
    }
    showWelcome() {
        const panel = vscode.window.createWebviewPanel("sonaWelcome", "Welcome to Sona", vscode.ViewColumn.One, {
            enableScripts: true
        });
        panel.webview.html = this.getWelcomeHtml();
        panel.webview.onDidReceiveMessage(async (message) => {
            if (message.command === "setupAzure") {
                await this.setupAzure();
            }
            else if (message.command === "setupManual") {
                await this.setupManual();
            }
            else if (message.command === "selectProfile") {
                await this.selectUserProfile();
            }
        }, undefined, this.context.subscriptions);
    }
    escapeHtml(value) {
        return value
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }
    getWelcomeHtml() {
        return `<!DOCTYPE html>
<html>
<body>
  <h1>Welcome to Sona 0.15.4</h1>
  <p>The AI-native programming language with cognitive accessibility features.</p>
  <button onclick="vscode.postMessage({command: 'setupAzure'})">Setup Azure</button>
  <button onclick="vscode.postMessage({command: 'setupManual'})">Manual Setup</button>
  <button onclick="vscode.postMessage({command: 'selectProfile'})">Select Profile</button>
  <script>const vscode = acquireVsCodeApi();</script>
</body>
</html>`;
    }
    getExplanationHtml(code, explanation) {
        return `<!DOCTYPE html>
<html>
<body>
  <h2>Code Explanation</h2>
  <h3>Selected Code</h3>
  <pre>${this.escapeHtml(code)}</pre>
  <h3>Explanation</h3>
  <pre>${this.escapeHtml(explanation)}</pre>
</body>
</html>`;
    }
    getSuggestionsHtml(prompt, suggestions) {
        return `<!DOCTYPE html>
<html>
<body>
  <h2>AI Suggestions</h2>
  <h3>Your Request</h3>
  <p>${this.escapeHtml(prompt)}</p>
  <h3>Suggested Result</h3>
  <pre>${this.escapeHtml(suggestions)}</pre>
</body>
</html>`;
    }
    dispose() {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
        this.terminal?.dispose();
    }
}
exports.SonaCliIntegration = SonaCliIntegration;
function activate(context) {
    const sonaIntegration = new SonaCliIntegration(context);
    context.subscriptions.push({ dispose: () => sonaIntegration.dispose() });
}
function deactivate() {
    // Cleanup is handled by registered disposables.
}
