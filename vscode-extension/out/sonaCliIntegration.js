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
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
const crypto_1 = require("crypto");
const vscode = __importStar(require("vscode"));
const proofModeExplorer_1 = require("./proofModeExplorer");
const proofModeModel_1 = require("./proofModeModel");
const pythonEnvironment_1 = require("./pythonEnvironment");
const runtimeView_1 = require("./runtimeView");
class SonaCliIntegration {
    context;
    config;
    outputChannel;
    statusBarItem;
    proofModeExplorer;
    runtimeView;
    runtimeDiagnosticCollection;
    terminal;
    displayPreference;
    constructor(context) {
        this.context = context;
        this.config = this.loadConfiguration();
        this.outputChannel = vscode.window.createOutputChannel("Sona");
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.proofModeExplorer = new proofModeExplorer_1.ProofModeExplorerProvider();
        this.runtimeView = new runtimeView_1.RuntimeViewProvider(() => this.runSonaCommand(["runtime", "status", "--format", "json"]));
        this.runtimeDiagnosticCollection = vscode.languages.createDiagnosticCollection("sona-runtime");
        this.displayPreference = this.loadDisplayPreference();
        this.initializeStatusBar();
        this.context.subscriptions.push(this.runtimeDiagnosticCollection, this.proofModeExplorer, this.runtimeView, vscode.window.registerTreeDataProvider(proofModeExplorer_1.ProofModeExplorerProvider.viewType, this.proofModeExplorer), vscode.window.registerTreeDataProvider(runtimeView_1.RuntimeViewProvider.viewType, this.runtimeView));
        this.registerCommands();
        void this.runtimeView.refresh();
        this.registerRuntimeDiagnosticInvalidation();
        void this.checkSonaInstallation();
    }
    loadConfiguration() {
        const config = vscode.workspace.getConfiguration("sona");
        return {
            pythonPath: (0, pythonEnvironment_1.resolveSonaPythonPath)(),
            timeout: config.get("cli.timeout", 30000),
            autoSetup: config.get("ai.autoSetup", true)
        };
    }
    loadDisplayPreference() {
        const stored = this.context.globalState.get("sonaDisplayPreference")
            || this.context.globalState.get("sonaUserProfile");
        if (stored) {
            return this.normalizeDisplayPreference(stored);
        }
        const config = vscode.workspace.getConfiguration("sona");
        return this.normalizeDisplayPreference(config.get("displayPreference")
            || config.get("userProfile")
            || "standard");
    }
    normalizeDisplayPreference(value) {
        switch (value) {
            case "focused":
            case "adhd":
                return "focused";
            case "readable":
            case "dyslexia":
                return "readable";
            default:
                return "standard";
        }
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
            const commandArgs = ["-P", "-m", "sona", ...args];
            this.outputChannel.appendLine(`Running: ${this.config.pythonPath} ${commandArgs.join(" ")}`);
            const cwd = this.getCommandCwd();
            const env = { ...process.env };
            delete env.PYTHONPATH;
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
        this.context.subscriptions.push(vscode.commands.registerCommand("sona.welcome", () => this.showWelcome()), vscode.commands.registerCommand("sona.setup.azure", () => this.setupAzure()), vscode.commands.registerCommand("sona.setup.manual", () => this.setupManual()), vscode.commands.registerCommand("sona.selectUserProfile", () => this.selectDisplayPreference()), vscode.commands.registerCommand("sona.run", () => this.runCurrentFile()), vscode.commands.registerCommand("sona.proofMode.run", () => this.runWithProofMode()), vscode.commands.registerCommand("sona.proofMode.verifyReceipt", candidate => this.verifyProofModeReceipt(candidate)), vscode.commands.registerCommand("sona.proofMode.inspectReceipt", candidate => this.inspectProofModeReceipt(candidate)), vscode.commands.registerCommand("sona.proofMode.openReceipt", candidate => this.openProofModeReceipt(candidate)), vscode.commands.registerCommand("sona.proofMode.refresh", () => this.refreshProofModeReceipt()), vscode.commands.registerCommand("sona.runtime.refresh", () => this.runtimeView.refresh()), vscode.commands.registerCommand("sona.proofMode.explainWithGuardian", candidate => this.explainProofModeWithGuardian(candidate)), vscode.commands.registerCommand("sona.transpile", () => this.transpileCurrentFile()), vscode.commands.registerCommand("sona.repl", () => this.startRepl()), vscode.commands.registerCommand("sona.check", () => this.checkCurrentFile()), vscode.commands.registerCommand("sona.format", () => this.formatCurrentFile()), vscode.commands.registerCommand("sona.explain", () => this.explainSelection()), vscode.commands.registerCommand("sona.suggest", () => this.getSuggestions()), vscode.commands.registerCommand("sona.profile", () => this.profileCurrentFile()), vscode.commands.registerCommand("sona.benchmark", () => this.benchmarkCurrentFile()), vscode.commands.registerCommand("sona.info", () => this.showInfo()), vscode.commands.registerCommand("sona.help", () => this.showHelp()), vscode.commands.registerCommand("sona.checkAIConnection", () => this.checkAIConnection()), vscode.commands.registerCommand("sona.aiPlanSelection", () => this.planSelection()), vscode.commands.registerCommand("sona.aiReviewSelection", () => this.reviewSelection()));
    }
    registerRuntimeDiagnosticInvalidation() {
        this.context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(event => {
            this.runtimeDiagnosticCollection.delete(event.document.uri);
        }), vscode.workspace.onDidCloseTextDocument(document => {
            this.runtimeDiagnosticCollection.delete(document.uri);
        }));
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
    async selectDisplayPreference() {
        const selected = await vscode.window.showQuickPick([
            { label: "Standard", description: "Default editor presentation", value: "standard" },
            { label: "Focused", description: "Reduced visual noise and fewer interruptions", value: "focused" },
            { label: "Readable", description: "More spacious text-oriented presentation", value: "readable" }
        ], { placeHolder: "Select a Sona display preference" });
        if (selected) {
            this.displayPreference = selected.value;
            await this.context.globalState.update("sonaDisplayPreference", this.displayPreference);
            await this.context.globalState.update("sonaUserProfile", undefined);
            vscode.window.showInformationMessage(`Display preference set to: ${selected.label}`);
        }
    }
    async runCurrentFile() {
        if (!this.requireTrustedWorkspace("Run Sona")) {
            return;
        }
        const doc = this.activeSavedFile("sona");
        if (!doc) {
            return;
        }
        await doc.save();
        const version = doc.version;
        const text = doc.getText();
        const sourceSha256 = this.normalizedSourceSha256(text);
        const result = await this.runSonaCommand(["run", doc.fileName, "--json"]);
        const packet = this.parseRunPacket(result.output);
        if (!packet) {
            this.runtimeDiagnosticCollection.delete(doc.uri);
            this.showCommandResult("Sona Run Output", result, "Run failed");
            return;
        }
        this.showRunPacket(packet, result);
        this.publishRuntimeDiagnostics(doc, version, sourceSha256, packet);
        if (!result.success && (!packet.diagnostics || packet.diagnostics.length === 0)) {
            vscode.window.showErrorMessage("Run failed. Open the Sona output for details.");
        }
    }
    requireTrustedWorkspace(action) {
        if (vscode.workspace.isTrusted) {
            return true;
        }
        void vscode.window.showWarningMessage(`${action} is disabled until this workspace is trusted.`);
        return false;
    }
    async pickProofModeReceipt(candidate, title) {
        if (candidate instanceof vscode.Uri) {
            return candidate;
        }
        if (candidate instanceof proofModeExplorer_1.ProofModeTreeItem && candidate.resourceUri) {
            return candidate.resourceUri;
        }
        const picked = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: false,
            title,
            openLabel: title,
            filters: {
                "Proof Mode receipts": ["sproof", "json"],
                "All files": ["*"]
            }
        });
        return picked?.[0];
    }
    async revealProofModeExplorer() {
        await vscode.commands.executeCommand(`${proofModeExplorer_1.ProofModeExplorerProvider.viewType}.focus`);
    }
    appendProofModeOutput(title, result) {
        this.outputChannel.appendLine(`\n--- ${title} ---`);
        if (result.output.trim()) {
            this.outputChannel.appendLine(result.output.trimEnd());
        }
        if (result.error && result.error !== result.output) {
            this.outputChannel.appendLine(result.error.trimEnd());
        }
    }
    showProofModeModel(receipt, model, programLabel) {
        this.proofModeExplorer.showReceipt(receipt, model, programLabel);
        void this.revealProofModeExplorer();
    }
    async inspectProofModeReceiptPath(receipt, programLabel, announce = true) {
        const result = await this.runSonaCommand([
            "proof",
            "inspect",
            receipt.fsPath,
            "--json"
        ]);
        this.appendProofModeOutput("Proof Mode Inspection", result);
        const model = (0, proofModeModel_1.parseProofModeCliOutput)(result.output);
        this.showProofModeModel(receipt, model, programLabel);
        if (!announce) {
            return model;
        }
        if (model.state === "valid") {
            void vscode.window.showInformationMessage("Proof Mode receipt is valid and ready to inspect.");
        }
        else if (model.state === "invalid") {
            void vscode.window.showWarningMessage(`${model.diagnosticId || "Proof Mode verifier"}: receipt is invalid.`);
        }
        else {
            void vscode.window.showErrorMessage("Proof Mode inspection output could not be displayed. Open the Sona output for details.");
        }
        return model;
    }
    async runWithProofMode() {
        if (!this.requireTrustedWorkspace("Run with Proof Mode")) {
            return;
        }
        const document = this.activeSavedFile("sona");
        if (!document) {
            return;
        }
        await document.save();
        const parsed = path.parse(document.fileName);
        const receipt = await vscode.window.showSaveDialog({
            title: "Save Proof Mode Receipt",
            saveLabel: "Create Receipt",
            defaultUri: vscode.Uri.file(path.join(parsed.dir, `${parsed.name}.sproof`)),
            filters: { "Proof Mode receipt": ["sproof"] }
        });
        if (!receipt) {
            return;
        }
        if (fs.existsSync(receipt.fsPath)) {
            void vscode.window.showWarningMessage("Proof Mode will not overwrite an existing receipt. Choose a new receipt path.");
            return;
        }
        const programLabel = path.basename(document.fileName);
        this.proofModeExplorer.showRunning(programLabel);
        await this.revealProofModeExplorer();
        const result = await this.runSonaCommand([
            "proof",
            document.fileName,
            "--receipt",
            receipt.fsPath,
            "--engine",
            "native",
            "--summary"
        ]);
        this.appendProofModeOutput("Run with Proof Mode", result);
        if (!result.success) {
            this.proofModeExplorer.showError("Native Proof Mode execution failed safely.");
            void vscode.window.showErrorMessage("Proof Mode execution failed. Open the Sona output for the diagnostic.");
            return;
        }
        const model = await this.inspectProofModeReceiptPath(receipt, programLabel, false);
        if (model.state === "valid") {
            void vscode.window.showInformationMessage(`Proof Mode completed for ${programLabel}. The receipt was verified.`);
        }
        else {
            void vscode.window.showWarningMessage("Proof Mode execution completed, but the receipt did not pass shared verification.");
        }
    }
    async verifyProofModeReceipt(candidate) {
        const receipt = await this.pickProofModeReceipt(candidate, "Verify Receipt");
        if (!receipt) {
            return;
        }
        const result = await this.runSonaCommand([
            "proof",
            "verify",
            receipt.fsPath,
            "--json"
        ]);
        this.appendProofModeOutput("Proof Mode Verification", result);
        const model = (0, proofModeModel_1.parseProofModeCliOutput)(result.output);
        this.showProofModeModel(receipt, model);
        if (model.state === "valid") {
            void vscode.window.showInformationMessage("Proof Mode receipt verified.");
        }
        else if (model.state === "invalid") {
            void vscode.window.showWarningMessage(`${model.diagnosticId || "Proof Mode verifier"}: receipt verification failed.`);
        }
        else {
            void vscode.window.showErrorMessage("Proof Mode verification output could not be displayed. Open the Sona output for details.");
        }
    }
    async inspectProofModeReceipt(candidate) {
        const receipt = await this.pickProofModeReceipt(candidate, "Inspect Receipt");
        if (receipt) {
            await this.inspectProofModeReceiptPath(receipt);
        }
    }
    async openProofModeReceipt(candidate) {
        const receipt = candidate
            ? await this.pickProofModeReceipt(candidate, "Open Receipt")
            : this.proofModeExplorer.getCurrentReceipt()
                || await this.pickProofModeReceipt(undefined, "Open Receipt");
        if (!receipt) {
            return;
        }
        try {
            const document = await vscode.workspace.openTextDocument(receipt);
            await vscode.window.showTextDocument(document, { preview: true });
        }
        catch {
            void vscode.window.showErrorMessage("The Proof Mode receipt could not be opened.");
        }
    }
    async refreshProofModeReceipt() {
        const receipt = this.proofModeExplorer.getCurrentReceipt();
        if (receipt) {
            await this.inspectProofModeReceiptPath(receipt, undefined, false);
            return;
        }
        await this.inspectProofModeReceipt();
    }
    async explainProofModeWithGuardian(candidate) {
        if (!this.requireTrustedWorkspace("Explain with Guardian")) {
            return;
        }
        const receipt = candidate
            ? await this.pickProofModeReceipt(candidate, "Explain Receipt with Guardian")
            : this.proofModeExplorer.getCurrentReceipt()
                || await this.pickProofModeReceipt(undefined, "Explain Receipt with Guardian");
        if (!receipt) {
            return;
        }
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(receipt);
        const projectRoot = workspaceFolder?.uri.fsPath
            || this.getCommandCwd()
            || path.dirname(receipt.fsPath);
        const result = await this.runSonaCommand([
            "guardian",
            "proof",
            "review",
            "--project-root",
            projectRoot,
            "--receipt",
            receipt.fsPath
        ]);
        this.appendProofModeOutput("Guardian Proof Mode Explanation", result);
        this.outputChannel.show(true);
        if (result.success) {
            void vscode.window.showInformationMessage("Guardian explanation is available in the Sona output.");
        }
        else {
            void vscode.window.showWarningMessage("Guardian could not explain this receipt. Open the Sona output for the governed result.");
        }
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
    parseRunPacket(output) {
        try {
            const packet = JSON.parse(output);
            if (packet?.schema_version === 1 && packet.command === "run") {
                return packet;
            }
        }
        catch {
            return undefined;
        }
        return undefined;
    }
    normalizedSourceSha256(text) {
        const normalized = text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
        return `sha256:${(0, crypto_1.createHash)("sha256").update(normalized, "utf8").digest("hex")}`;
    }
    showRunPacket(packet, result) {
        this.outputChannel.show();
        this.outputChannel.appendLine("\n--- Sona Run Output ---");
        const stdout = packet.streams?.stdout || "";
        const stderr = packet.streams?.stderr || "";
        if (stdout) {
            this.outputChannel.append(stdout);
            if (!stdout.endsWith("\n")) {
                this.outputChannel.appendLine("");
            }
        }
        if (stderr) {
            this.outputChannel.append(stderr);
            if (!stderr.endsWith("\n")) {
                this.outputChannel.appendLine("");
            }
        }
        if (packet.truncated?.stdout || packet.truncated?.stderr) {
            this.outputChannel.appendLine("[WARN] Sona run output was truncated for the editor transport.");
        }
        if (packet.source_mapping && packet.source_mapping !== "original") {
            this.outputChannel.appendLine("[WARN] Runtime diagnostics were not published because this run used transformed source mapping.");
        }
        if (!result.success && !stderr && !stdout) {
            this.outputChannel.appendLine(result.error || `Command exited with code ${result.exitCode}`);
        }
    }
    publishRuntimeDiagnostics(document, version, sourceSha256, packet) {
        if (packet.source_mapping !== "original" || packet.source_sha256 !== sourceSha256 || document.version !== version) {
            this.runtimeDiagnosticCollection.delete(document.uri);
            return;
        }
        const diagnostics = Array.isArray(packet.diagnostics)
            ? packet.diagnostics.map(item => this.runtimeDiagnosticFromCanonical(document, item)).filter((item) => !!item)
            : [];
        this.runtimeDiagnosticCollection.set(document.uri, diagnostics);
    }
    runtimeDiagnosticFromCanonical(document, item) {
        if (!item || typeof item !== "object") {
            return undefined;
        }
        const diagnostic = item;
        const startLine = Number(diagnostic.start_line);
        const startColumn = Number(diagnostic.start_column);
        const endLine = Number(diagnostic.end_line || diagnostic.start_line);
        const endColumn = Number(diagnostic.end_column || diagnostic.start_column);
        if (![startLine, startColumn, endLine, endColumn].every(Number.isInteger)) {
            return undefined;
        }
        try {
            const range = new vscode.Range(this.positionFromCanonical(document, startLine, startColumn), this.positionFromCanonical(document, endLine, endColumn));
            const message = typeof diagnostic.message === "string" ? diagnostic.message : "Sona runtime diagnostic.";
            const rendered = new vscode.Diagnostic(range, message, this.diagnosticSeverity(diagnostic.severity));
            rendered.source = "sona";
            const identifier = typeof diagnostic.diagnostic_id === "string" ? diagnostic.diagnostic_id : "SONA-RUNTIME";
            rendered.code = identifier;
            rendered.data = diagnostic;
            return rendered;
        }
        catch {
            return undefined;
        }
    }
    positionFromCanonical(document, lineNumber, column) {
        if (lineNumber < 1 || lineNumber > document.lineCount || column < 1) {
            throw new Error("Runtime diagnostic range is outside the document.");
        }
        const line = document.lineAt(lineNumber - 1).text;
        const prefix = Array.from(line).slice(0, column - 1).join("");
        if (column > Array.from(line).length + 1) {
            throw new Error("Runtime diagnostic column is outside the line.");
        }
        return new vscode.Position(lineNumber - 1, prefix.length);
    }
    diagnosticSeverity(value) {
        switch (value) {
            case "warning":
                return vscode.DiagnosticSeverity.Warning;
            case "info":
                return vscode.DiagnosticSeverity.Information;
            case "hint":
                return vscode.DiagnosticSeverity.Hint;
            default:
                return vscode.DiagnosticSeverity.Error;
        }
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
                await this.selectDisplayPreference();
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
  <h1>Welcome to Sona 0.15.6</h1>
  <p>The AI-native programming language with deterministic Guide, Proof Mode, and Guardian workflows.</p>
  <button onclick="vscode.postMessage({command: 'setupAzure'})">Setup Azure</button>
  <button onclick="vscode.postMessage({command: 'setupManual'})">Manual Setup</button>
  <button onclick="vscode.postMessage({command: 'selectProfile'})">Display Preference</button>
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
        this.runtimeDiagnosticCollection.dispose();
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
