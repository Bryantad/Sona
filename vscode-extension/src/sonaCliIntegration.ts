import * as fs from "fs";
import * as path from "path";
import { spawn } from "child_process";
import * as vscode from "vscode";

import { ProofModeExplorerProvider, ProofModeTreeItem } from "./proofModeExplorer";
import { parseProofModeCliOutput, ProofModeModel } from "./proofModeModel";
import { resolveSonaPythonPath } from "./pythonEnvironment";

interface SonaConfig {
  pythonPath: string;
  timeout: number;
  autoSetup: boolean;
}

interface CommandResult {
  success: boolean;
  output: string;
  error?: string;
  exitCode: number;
}

type TaskType = "explain" | "suggest" | "review";

export class SonaCliIntegration {
  private readonly context: vscode.ExtensionContext;
  private readonly config: SonaConfig;
  private readonly outputChannel: vscode.OutputChannel;
  private readonly statusBarItem: vscode.StatusBarItem;
  private readonly proofModeExplorer: ProofModeExplorerProvider;
  private terminal: vscode.Terminal | undefined;
  private userProfile: string;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.config = this.loadConfiguration();
    this.outputChannel = vscode.window.createOutputChannel("Sona");
    this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.proofModeExplorer = new ProofModeExplorerProvider();
    this.userProfile = this.loadUserProfile();
    this.initializeStatusBar();
    this.context.subscriptions.push(
      this.proofModeExplorer,
      vscode.window.registerTreeDataProvider(
        ProofModeExplorerProvider.viewType,
        this.proofModeExplorer
      )
    );
    this.registerCommands();
    void this.checkSonaInstallation();
  }

  private loadConfiguration(): SonaConfig {
    const config = vscode.workspace.getConfiguration("sona");
    return {
      pythonPath: resolveSonaPythonPath(),
      timeout: config.get<number>("cli.timeout", 30000),
      autoSetup: config.get<boolean>("ai.autoSetup", true)
    };
  }

  private loadUserProfile(): string {
    const stored = this.context.globalState.get<string>("sonaUserProfile");
    if (stored) {
      return stored;
    }
    return vscode.workspace.getConfiguration("sona").get<string>("userProfile", "neurotypical");
  }

  private initializeStatusBar(): void {
    this.statusBarItem.text = "$(rocket) Sona";
    this.statusBarItem.tooltip = "Sona Language Support - Click for info";
    this.statusBarItem.command = "sona.info";
    this.statusBarItem.show();
  }

  private async checkSonaInstallation(): Promise<void> {
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

  private getCommandCwd(): string | undefined {
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

  private runSonaCommand(args: string[], input?: string): Promise<CommandResult> {
    return new Promise(resolve => {
      const commandArgs = ["-P", "-m", "sona", ...args];
      this.outputChannel.appendLine(`Running: ${this.config.pythonPath} ${commandArgs.join(" ")}`);
      const cwd = this.getCommandCwd();
      const env = { ...process.env };
      delete env.PYTHONPATH;

      const child = spawn(this.config.pythonPath, commandArgs, {
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

      const finish = (result: CommandResult): void => {
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

  private registerCommands(): void {
    this.context.subscriptions.push(
      vscode.commands.registerCommand("sona.welcome", () => this.showWelcome()),
      vscode.commands.registerCommand("sona.setup.azure", () => this.setupAzure()),
      vscode.commands.registerCommand("sona.setup.manual", () => this.setupManual()),
      vscode.commands.registerCommand("sona.selectUserProfile", () => this.selectUserProfile()),
      vscode.commands.registerCommand("sona.run", () => this.runCurrentFile()),
      vscode.commands.registerCommand("sona.proofMode.run", () => this.runWithProofMode()),
      vscode.commands.registerCommand(
        "sona.proofMode.verifyReceipt",
        candidate => this.verifyProofModeReceipt(candidate)
      ),
      vscode.commands.registerCommand(
        "sona.proofMode.inspectReceipt",
        candidate => this.inspectProofModeReceipt(candidate)
      ),
      vscode.commands.registerCommand(
        "sona.proofMode.openReceipt",
        candidate => this.openProofModeReceipt(candidate)
      ),
      vscode.commands.registerCommand("sona.proofMode.refresh", () => this.refreshProofModeReceipt()),
      vscode.commands.registerCommand(
        "sona.proofMode.explainWithGuardian",
        candidate => this.explainProofModeWithGuardian(candidate)
      ),
      vscode.commands.registerCommand("sona.transpile", () => this.transpileCurrentFile()),
      vscode.commands.registerCommand("sona.repl", () => this.startRepl()),
      vscode.commands.registerCommand("sona.check", () => this.checkCurrentFile()),
      vscode.commands.registerCommand("sona.format", () => this.formatCurrentFile()),
      vscode.commands.registerCommand("sona.explain", () => this.explainSelection()),
      vscode.commands.registerCommand("sona.suggest", () => this.getSuggestions()),
      vscode.commands.registerCommand("sona.profile", () => this.profileCurrentFile()),
      vscode.commands.registerCommand("sona.benchmark", () => this.benchmarkCurrentFile()),
      vscode.commands.registerCommand("sona.info", () => this.showInfo()),
      vscode.commands.registerCommand("sona.help", () => this.showHelp()),
      vscode.commands.registerCommand("sona.checkAIConnection", () => this.checkAIConnection()),
      vscode.commands.registerCommand("sona.aiPlanSelection", () => this.planSelection()),
      vscode.commands.registerCommand("sona.aiReviewSelection", () => this.reviewSelection())
    );
  }

  private activeSavedFile(requiredLanguage?: string): vscode.TextDocument | undefined {
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

  private async resolveWorkspaceRoot(): Promise<string | undefined> {
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

  private async openWorkspaceEnvFile(workspaceRoot: string): Promise<void> {
    const envUri = vscode.Uri.joinPath(vscode.Uri.file(workspaceRoot), ".env");
    const doc = await vscode.workspace.openTextDocument(envUri);
    await vscode.window.showTextDocument(doc);
  }

  private async promptAzureSetupInput(): Promise<string | undefined> {
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

  private async promptManualSetupInput(): Promise<string | undefined> {
    const provider = await vscode.window.showQuickPick(
      [
        { label: "Local Ollama", description: "Use an installed Qwen coder model", value: "local" },
        { label: "Azure OpenAI", description: "Use endpoint, key, and deployment", value: "azure" }
      ],
      { placeHolder: "Choose Sona AI provider", ignoreFocusOut: true }
    );
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

  private async setupAzure(): Promise<void> {
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

  private async setupManual(): Promise<void> {
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

  private async selectUserProfile(): Promise<void> {
    const selected = await vscode.window.showQuickPick(
      [
        { label: "Neurotypical", description: "Standard UI/UX for typical users", value: "neurotypical" },
        { label: "ADHD", description: "High-contrast, minimal distractions", value: "adhd" },
        { label: "Dyslexia", description: "Dyslexia-friendly fonts and enhanced readability", value: "dyslexia" }
      ],
      { placeHolder: "Select your cognitive profile for optimized experience" }
    );
    if (selected) {
      this.userProfile = selected.value;
      await this.context.globalState.update("sonaUserProfile", this.userProfile);
      vscode.window.showInformationMessage(`Profile set to: ${selected.label}`);
    }
  }

  private async runCurrentFile(): Promise<void> {
    const doc = this.activeSavedFile("sona");
    if (!doc) {
      return;
    }
    await doc.save();
    const result = await this.runSonaCommand(["run", doc.fileName]);
    this.showCommandResult("Sona Run Output", result, "Run failed");
  }

  private requireTrustedWorkspace(action: string): boolean {
    if (vscode.workspace.isTrusted) {
      return true;
    }
    void vscode.window.showWarningMessage(
      `${action} is disabled until this workspace is trusted.`
    );
    return false;
  }

  private async pickProofModeReceipt(
    candidate: unknown,
    title: string
  ): Promise<vscode.Uri | undefined> {
    if (candidate instanceof vscode.Uri) {
      return candidate;
    }
    if (candidate instanceof ProofModeTreeItem && candidate.resourceUri) {
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

  private async revealProofModeExplorer(): Promise<void> {
    await vscode.commands.executeCommand(`${ProofModeExplorerProvider.viewType}.focus`);
  }

  private appendProofModeOutput(title: string, result: CommandResult): void {
    this.outputChannel.appendLine(`\n--- ${title} ---`);
    if (result.output.trim()) {
      this.outputChannel.appendLine(result.output.trimEnd());
    }
    if (result.error && result.error !== result.output) {
      this.outputChannel.appendLine(result.error.trimEnd());
    }
  }

  private showProofModeModel(
    receipt: vscode.Uri,
    model: ProofModeModel,
    programLabel?: string
  ): void {
    this.proofModeExplorer.showReceipt(receipt, model, programLabel);
    void this.revealProofModeExplorer();
  }

  private async inspectProofModeReceiptPath(
    receipt: vscode.Uri,
    programLabel?: string,
    announce = true
  ): Promise<ProofModeModel> {
    const result = await this.runSonaCommand([
      "proof",
      "inspect",
      receipt.fsPath,
      "--json"
    ]);
    this.appendProofModeOutput("Proof Mode Inspection", result);
    const model = parseProofModeCliOutput(result.output);
    this.showProofModeModel(receipt, model, programLabel);

    if (!announce) {
      return model;
    }
    if (model.state === "valid") {
      void vscode.window.showInformationMessage("Proof Mode receipt is valid and ready to inspect.");
    } else if (model.state === "invalid") {
      void vscode.window.showWarningMessage(
        `${model.diagnosticId || "Proof Mode verifier"}: receipt is invalid.`
      );
    } else {
      void vscode.window.showErrorMessage(
        "Proof Mode inspection output could not be displayed. Open the Sona output for details."
      );
    }
    return model;
  }

  private async runWithProofMode(): Promise<void> {
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
      void vscode.window.showWarningMessage(
        "Proof Mode will not overwrite an existing receipt. Choose a new receipt path."
      );
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
      void vscode.window.showErrorMessage(
        "Proof Mode execution failed. Open the Sona output for the diagnostic."
      );
      return;
    }

    const model = await this.inspectProofModeReceiptPath(receipt, programLabel, false);
    if (model.state === "valid") {
      void vscode.window.showInformationMessage(
        `Proof Mode completed for ${programLabel}. The receipt was verified.`
      );
    } else {
      void vscode.window.showWarningMessage(
        "Proof Mode execution completed, but the receipt did not pass shared verification."
      );
    }
  }

  private async verifyProofModeReceipt(candidate?: unknown): Promise<void> {
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
    const model = parseProofModeCliOutput(result.output);
    this.showProofModeModel(receipt, model);
    if (model.state === "valid") {
      void vscode.window.showInformationMessage("Proof Mode receipt verified.");
    } else if (model.state === "invalid") {
      void vscode.window.showWarningMessage(
        `${model.diagnosticId || "Proof Mode verifier"}: receipt verification failed.`
      );
    } else {
      void vscode.window.showErrorMessage(
        "Proof Mode verification output could not be displayed. Open the Sona output for details."
      );
    }
  }

  private async inspectProofModeReceipt(candidate?: unknown): Promise<void> {
    const receipt = await this.pickProofModeReceipt(candidate, "Inspect Receipt");
    if (receipt) {
      await this.inspectProofModeReceiptPath(receipt);
    }
  }

  private async openProofModeReceipt(candidate?: unknown): Promise<void> {
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
    } catch {
      void vscode.window.showErrorMessage("The Proof Mode receipt could not be opened.");
    }
  }

  private async refreshProofModeReceipt(): Promise<void> {
    const receipt = this.proofModeExplorer.getCurrentReceipt();
    if (receipt) {
      await this.inspectProofModeReceiptPath(receipt, undefined, false);
      return;
    }
    await this.inspectProofModeReceipt();
  }

  private async explainProofModeWithGuardian(candidate?: unknown): Promise<void> {
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
      void vscode.window.showInformationMessage(
        "Guardian explanation is available in the Sona output."
      );
    } else {
      void vscode.window.showWarningMessage(
        "Guardian could not explain this receipt. Open the Sona output for the governed result."
      );
    }
  }

  private async transpileCurrentFile(): Promise<void> {
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

  private startRepl(): void {
    if (!this.terminal || this.terminal.exitStatus) {
      this.terminal = vscode.window.createTerminal({
        name: "Sona REPL",
        shellPath: this.config.pythonPath,
        shellArgs: ["-m", "sona", "repl"]
      });
    }
    this.terminal.show();
  }

  private async checkCurrentFile(): Promise<void> {
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

  private async formatCurrentFile(): Promise<void> {
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

  private async runDeveloperTask(taskType: TaskType, instruction: string, selectedText?: string): Promise<CommandResult> {
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

  private async explainSelection(): Promise<void> {
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

  private async getSuggestions(): Promise<void> {
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

  private async planSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.selection.isEmpty) {
      vscode.window.showErrorMessage("Select text to create a plan.");
      return;
    }
    const text = editor.document.getText(editor.selection).slice(0, 4000);
    const result = await this.runDeveloperTask("suggest", "Create a development plan for the selected code.", text);
    this.showJsonResult("AI Plan", result);
  }

  private async reviewSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.selection.isEmpty) {
      vscode.window.showErrorMessage("Select text to review.");
      return;
    }
    const text = editor.document.getText(editor.selection).slice(0, 6000);
    const result = await this.runDeveloperTask("review", "Review the selected developer code.", text);
    this.showJsonResult("AI Review", result);
  }

  private async profileCurrentFile(): Promise<void> {
    const doc = this.activeSavedFile("sona");
    if (!doc) {
      return;
    }
    await doc.save();
    this.showCommandResult("Performance Profile", await this.runSonaCommand(["profile", doc.fileName]), "Profiling failed");
  }

  private async benchmarkCurrentFile(): Promise<void> {
    const doc = this.activeSavedFile("sona");
    if (!doc) {
      return;
    }
    await doc.save();
    this.showCommandResult("Benchmark Results", await this.runSonaCommand(["benchmark", doc.fileName]), "Benchmarking failed");
  }

  private async showInfo(): Promise<void> {
    const result = await this.runSonaCommand(["info"]);
    if (result.success) {
      vscode.window.showInformationMessage(result.output, { modal: false });
      this.showCommandResult("Sona System Info", result, "Info failed");
      return;
    }
    vscode.window.showErrorMessage(`Info failed: ${result.error}`);
  }

  private async showHelp(): Promise<void> {
    this.showCommandResult("Sona Help", await this.runSonaCommand(["--help"]), "Help failed");
  }

  private async checkAIConnection(): Promise<void> {
    const result = await this.runSonaCommand(["model", "health"]);
    if (result.success) {
      vscode.window.showInformationMessage("Sona model registry is reachable.");
      return;
    }
    const choice = await vscode.window.showWarningMessage(
      "Sona model registry check failed.",
      "Setup Azure",
      "Manual Setup",
      "Help"
    );
    if (choice === "Setup Azure") {
      await this.setupAzure();
    } else if (choice === "Manual Setup") {
      await this.setupManual();
    } else if (choice === "Help") {
      await this.showHelp();
    }
  }

  private showCommandResult(title: string, result: CommandResult, failurePrefix: string): void {
    if (result.success) {
      this.outputChannel.show();
      this.outputChannel.appendLine(`\n--- ${title} ---`);
      this.outputChannel.appendLine(result.output);
      return;
    }
    vscode.window.showErrorMessage(`${failurePrefix}: ${result.error}`);
  }

  private showJsonResult(title: string, result: CommandResult): void {
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

  private showHtmlPanel(title: string, html: string): void {
    const panel = vscode.window.createWebviewPanel("sonaResult", title, vscode.ViewColumn.Beside, {
      enableScripts: false
    });
    panel.webview.html = html;
  }

  private showWelcome(): void {
    const panel = vscode.window.createWebviewPanel("sonaWelcome", "Welcome to Sona", vscode.ViewColumn.One, {
      enableScripts: true
    });
    panel.webview.html = this.getWelcomeHtml();
    panel.webview.onDidReceiveMessage(async message => {
      if (message.command === "setupAzure") {
        await this.setupAzure();
      } else if (message.command === "setupManual") {
        await this.setupManual();
      } else if (message.command === "selectProfile") {
        await this.selectUserProfile();
      }
    }, undefined, this.context.subscriptions);
  }

  private escapeHtml(value: string): string {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  private getWelcomeHtml(): string {
    return `<!DOCTYPE html>
<html>
<body>
  <h1>Welcome to Sona 0.15.5</h1>
  <p>The AI-native programming language with cognitive accessibility features.</p>
  <button onclick="vscode.postMessage({command: 'setupAzure'})">Setup Azure</button>
  <button onclick="vscode.postMessage({command: 'setupManual'})">Manual Setup</button>
  <button onclick="vscode.postMessage({command: 'selectProfile'})">Select Profile</button>
  <script>const vscode = acquireVsCodeApi();</script>
</body>
</html>`;
  }

  private getExplanationHtml(code: string, explanation: string): string {
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

  private getSuggestionsHtml(prompt: string, suggestions: string): string {
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

  dispose(): void {
    this.statusBarItem.dispose();
    this.outputChannel.dispose();
    this.terminal?.dispose();
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const sonaIntegration = new SonaCliIntegration(context);
  context.subscriptions.push({ dispose: () => sonaIntegration.dispose() });
}

export function deactivate(): void {
  // Cleanup is handled by registered disposables.
}
