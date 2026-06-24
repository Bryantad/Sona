"use strict";
// VS Code Extension Integration for Sona 0.15.1 CLI
// Provides full VS Code integration with local Sona CLI installation
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
exports.deactivate = exports.activate = exports.SonaCliIntegration = void 0;
const vscode = require("vscode");
const child_process_1 = require("child_process");
const path = require("path");
class SonaCliIntegration {
    constructor(context) {
        this.config = this.loadConfiguration();
        this.outputChannel = vscode.window.createOutputChannel('Sona');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.context = context;
        this.userProfile = this.loadUserProfile();
        this.initializeStatusBar();
        this.registerCommands();
        this.checkSonaInstallation();
    }
    loadConfiguration() {
        const config = vscode.workspace.getConfiguration('sona');
        return {
            pythonPath: config.get('cli.pythonPath', 'python'),
            timeout: config.get('cli.timeout', 30000),
            autoSetup: config.get('ai.autoSetup', true)
        };
    }
    loadUserProfile() {
        if (this.context) {
            const stored = this.context.globalState.get('sonaUserProfile');
            if (stored)
                return stored;
        }
        const config = vscode.workspace.getConfiguration('sona');
        return config.get('userProfile', 'neurotypical');
    }
    initializeStatusBar() {
        this.statusBarItem.text = '$(rocket) Sona';
        this.statusBarItem.tooltip = 'Sona Language Support - Click for info';
        this.statusBarItem.command = 'sona.info';
        this.statusBarItem.show();
    }
    checkSonaInstallation() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const result = yield this.runSonaCommand(['--version']);
                if (result.success) {
                    this.statusBarItem.text = '$(rocket) Sona $(check)';
                    this.statusBarItem.tooltip = `Sona CLI Available - ${result.output.trim()}`;
                    this.outputChannel.appendLine(`[OK] Sona CLI detected: ${result.output.trim()}`);
                }
                else {
                    this.statusBarItem.text = '$(alert) Sona';
                    this.statusBarItem.tooltip = 'Sona CLI not found - Click to install';
                    this.statusBarItem.command = 'sona.welcome';
                    this.outputChannel.appendLine('[WARN] Sona CLI not found. Please install Sona first.');
                }
            }
            catch (error) {
                this.statusBarItem.text = '$(alert) Sona';
                this.statusBarItem.tooltip = 'Sona CLI error - Click for help';
                this.statusBarItem.command = 'sona.help';
                this.outputChannel.appendLine(`[ERROR] Error checking Sona: ${error}`);
            }
        });
    }
    runSonaCommand(args, input) {
        return __awaiter(this, void 0, void 0, function* () {
            return new Promise((resolve) => {
                const commandArgs = ['-m', 'sona'].concat(args);
                this.outputChannel.appendLine(`Running: ${this.config.pythonPath} ${commandArgs.join(' ')}`);
                const cwd = this.getCommandCwd();
                const env = Object.assign({}, process.env);
                if (cwd) {
                    env.PYTHONPATH = cwd + (env.PYTHONPATH ? path.delimiter + env.PYTHONPATH : '');
                }
                const child = (0, child_process_1.spawn)(this.config.pythonPath, commandArgs, {
                    cwd,
                    env,
                    windowsHide: true
                });
                let stdout = '';
                let stderr = '';
                let finished = false;
                const finish = (result) => {
                    if (finished) {
                        return;
                    }
                    finished = true;
                    clearTimeout(timeoutHandle);
                    if (result.success) {
                        this.outputChannel.appendLine('Command succeeded');
                    }
                    else {
                        this.outputChannel.appendLine(`Command failed: ${result.error}`);
                    }
                    resolve(result);
                };
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
                if (child.stdout) {
                    child.stdout.on('data', chunk => {
                        stdout += chunk.toString();
                    });
                }
                if (child.stderr) {
                    child.stderr.on('data', chunk => {
                        stderr += chunk.toString();
                    });
                }
                child.on('error', error => {
                    finish({
                        success: false,
                        output: stdout,
                        error: error.message,
                        exitCode: -1
                    });
                });
                child.on('close', code => {
                    const success = code === 0;
                    finish({
                        success,
                        output: stdout,
                        error: success ? undefined : (stderr || stdout || `Command exited with code ${code}`),
                        exitCode: code === null ? -1 : code
                    });
                });
                if (input && child.stdin) {
                    child.stdin.write(input);
                    child.stdin.end();
                }
                else if (child.stdin) {
                    child.stdin.end();
                }
            });
        });
    }
    registerCommands() {
        if (!this.context)
            return;
        // Welcome and Setup Commands
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.welcome', () => this.showWelcome()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.setup.azure', () => this.setupAzure()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.setup.manual', () => this.setupManual()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.selectUserProfile', () => this.selectUserProfile()));
        // Core CLI Commands
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.run', () => this.runCurrentFile()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.transpile', () => this.transpileCurrentFile()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.repl', () => this.startRepl()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.check', () => this.checkCurrentFile()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.format', () => this.formatCurrentFile()));
        // AI Commands
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.explain', () => this.explainSelection()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.suggest', () => this.getSuggestions()));
        // Performance Commands
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.profile', () => this.profileCurrentFile()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.benchmark', () => this.benchmarkCurrentFile()));
        // Info Commands
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.info', () => this.showInfo()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.help', () => this.showHelp()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.checkAIConnection', () => this.checkAIConnection()));
        // Capability feature commands (0.9.3)
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.aiPlanSelection', () => this.planSelection()));
        this.context.subscriptions.push(vscode.commands.registerCommand('sona.aiReviewSelection', () => this.reviewSelection()));
    }
    // Command Implementations
    showWelcome() {
        var _a;
        return __awaiter(this, void 0, void 0, function* () {
            const panel = vscode.window.createWebviewPanel('sonaWelcome', 'Welcome to Sona', vscode.ViewColumn.One, { enableScripts: true });
            panel.webview.html = this.getWelcomeHtml();
            panel.webview.onDidReceiveMessage((message) => __awaiter(this, void 0, void 0, function* () {
                switch (message.command) {
                    case 'setupAzure':
                        yield this.setupAzure();
                        break;
                    case 'setupManual':
                        yield this.setupManual();
                        break;
                    case 'selectProfile':
                        yield this.selectUserProfile();
                        break;
                }
            }), undefined, (_a = this.context) === null || _a === void 0 ? void 0 : _a.subscriptions);
        });
    }
    resolveWorkspaceRoot() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            const folders = vscode.workspace.workspaceFolders;
            const active = (_a = vscode.window.activeTextEditor) === null || _a === void 0 ? void 0 : _a.document;
            if (active) {
                const activeFolder = vscode.workspace.getWorkspaceFolder(active.uri);
                if (activeFolder) {
                    return activeFolder.uri.fsPath;
                }
                if (active.uri && active.uri.scheme === 'file' && !active.isUntitled) {
                    return path.dirname(active.uri.fsPath);
                }
            }
            if (folders && folders.length > 0) {
                return folders[0].uri.fsPath;
            }
            const picked = yield vscode.window.showOpenDialog({
                canSelectFiles: false,
                canSelectFolders: true,
                canSelectMany: false,
                openLabel: 'Use Folder for Sona Setup',
                title: 'Choose where Sona should create or open .env'
            });
            if (picked && picked.length > 0) {
                return picked[0].fsPath;
            }
            vscode.window.showWarningMessage('Sona AI setup canceled. Open or choose a folder first.');
            return undefined;
        });
    }
    openWorkspaceEnvFile(workspaceRoot) {
        return __awaiter(this, void 0, void 0, function* () {
            const envUri = vscode.Uri.joinPath(vscode.Uri.file(workspaceRoot), '.env');
            const doc = yield vscode.workspace.openTextDocument(envUri);
            yield vscode.window.showTextDocument(doc);
        });
    }
    getCommandCwd() {
        var _a;
        const active = (_a = vscode.window.activeTextEditor) === null || _a === void 0 ? void 0 : _a.document;
        if (active) {
            const activeFolder = vscode.workspace.getWorkspaceFolder(active.uri);
            if (activeFolder) {
                return activeFolder.uri.fsPath;
            }
            if (active.uri && active.uri.scheme === 'file' && !active.isUntitled) {
                return path.dirname(active.uri.fsPath);
            }
        }
        const folders = vscode.workspace.workspaceFolders;
        if (folders && folders.length > 0) {
            return folders[0].uri.fsPath;
        }
        return undefined;
    }
    promptAzureSetupInput() {
        return __awaiter(this, void 0, void 0, function* () {
            const endpoint = yield vscode.window.showInputBox({
                prompt: 'Azure OpenAI endpoint',
                placeHolder: 'https://your-resource.openai.azure.com/',
                ignoreFocusOut: true
            });
            if (!endpoint) {
                return undefined;
            }
            const apiKey = yield vscode.window.showInputBox({
                prompt: 'Azure OpenAI API key',
                password: true,
                ignoreFocusOut: true
            });
            if (!apiKey) {
                return undefined;
            }
            const deployment = yield vscode.window.showInputBox({
                prompt: 'Azure OpenAI deployment name',
                placeHolder: 'gpt-4o-mini',
                value: 'gpt-4o-mini',
                ignoreFocusOut: true
            });
            return `${endpoint.trim()}\n${apiKey.trim()}\n${(deployment || 'gpt-4o-mini').trim()}\n`;
        });
    }
    promptManualSetupInput() {
        return __awaiter(this, void 0, void 0, function* () {
            const provider = yield vscode.window.showQuickPick([
                {
                    label: 'Local Ollama',
                    description: 'Use an installed Qwen coder model',
                    value: 'local'
                },
                {
                    label: 'Azure OpenAI',
                    description: 'Use endpoint, key, and deployment',
                    value: 'azure'
                }
            ], {
                placeHolder: 'Choose Sona AI provider',
                ignoreFocusOut: true
            });
            if (!provider) {
                return undefined;
            }
            if (provider.value === 'local') {
                const model = yield vscode.window.showInputBox({
                    prompt: 'Ollama model name (leave blank to auto-detect an installed Qwen model)',
                    placeHolder: 'qwen2.5:14b',
                    ignoreFocusOut: true
                });
                if (model === undefined) {
                    return undefined;
                }
                return `local\n${model.trim()}\n`;
            }
            const azureInput = yield this.promptAzureSetupInput();
            if (!azureInput) {
                return undefined;
            }
            return `azure\n${azureInput}`;
        });
    }
    setupAzure() {
        return __awaiter(this, void 0, void 0, function* () {
            const workspaceRoot = yield this.resolveWorkspaceRoot();
            if (!workspaceRoot) {
                return;
            }
            const setupInput = yield this.promptAzureSetupInput();
            if (!setupInput) {
                return;
            }
            const result = yield this.runSonaCommand(['setup', 'azure', '--manual', '--workspace', workspaceRoot], setupInput);
            if (result.success) {
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Sona AI Setup ---');
                this.outputChannel.appendLine(result.output);
                yield this.openWorkspaceEnvFile(workspaceRoot);
                vscode.window.showInformationMessage('Sona AI setup opened .env. Edit values, save, then run Sona: Check AI Connection.');
            }
            else {
                vscode.window.showErrorMessage(`Azure setup failed: ${result.error}`);
            }
        });
    }
    setupManual() {
        return __awaiter(this, void 0, void 0, function* () {
            const workspaceRoot = yield this.resolveWorkspaceRoot();
            if (!workspaceRoot) {
                return;
            }
            const setupInput = yield this.promptManualSetupInput();
            if (!setupInput) {
                return;
            }
            const result = yield this.runSonaCommand(['setup', 'manual', '--workspace', workspaceRoot], setupInput);
            if (result.success) {
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Sona Manual AI Setup ---');
                this.outputChannel.appendLine(result.output);
                yield this.openWorkspaceEnvFile(workspaceRoot);
                vscode.window.showInformationMessage('Manual AI setup opened .env. Edit values, save, then run Sona: Check AI Connection.');
            }
            else {
                vscode.window.showErrorMessage(`Manual setup failed: ${result.error}`);
            }
        });
    }
    selectUserProfile() {
        return __awaiter(this, void 0, void 0, function* () {
            const profiles = [
                { label: 'Neurotypical', description: 'Standard UI/UX for typical users', value: 'neurotypical' },
                { label: 'ADHD', description: 'High-contrast, minimal distractions', value: 'adhd' },
                { label: 'Dyslexia', description: 'Dyslexia-friendly fonts and enhanced readability', value: 'dyslexia' }
            ];
            const selected = yield vscode.window.showQuickPick(profiles, {
                placeHolder: 'Select your cognitive profile for optimized experience'
            });
            if (selected && this.context) {
                this.userProfile = selected.value;
                yield this.context.globalState.update('sonaUserProfile', this.userProfile);
                vscode.window.showInformationMessage(`Profile set to: ${selected.label}`);
            }
        });
    }
    runCurrentFile() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to run');
                return;
            }
            yield editor.document.save();
            const filePath = editor.document.fileName;
            const result = yield this.runSonaCommand(['run', filePath]);
            if (result.success) {
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Sona Run Output ---');
                this.outputChannel.appendLine(result.output);
            }
            else {
                vscode.window.showErrorMessage(`Run failed: ${result.error}`);
            }
        });
    }
    transpileCurrentFile() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to transpile');
                return;
            }
            yield editor.document.save();
            const filePath = editor.document.fileName;
            const outputPath = filePath.replace('.sona', '.py');
            const result = yield this.runSonaCommand(['transpile', filePath, outputPath]);
            if (result.success) {
                vscode.window.showInformationMessage(`Transpiled to: ${outputPath}`);
                const doc = yield vscode.workspace.openTextDocument(outputPath);
                yield vscode.window.showTextDocument(doc);
            }
            else {
                vscode.window.showErrorMessage(`Transpilation failed: ${result.error}`);
            }
        });
    }
    startRepl() {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.terminal || this.terminal.exitStatus) {
                this.terminal = vscode.window.createTerminal({
                    name: 'Sona REPL',
                    shellPath: this.config.pythonPath,
                    shellArgs: ['-m', 'sona', 'repl']
                });
            }
            this.terminal.show();
        });
    }
    checkCurrentFile() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to check');
                return;
            }
            yield editor.document.save();
            const filePath = editor.document.fileName;
            const result = yield this.runSonaCommand(['check', filePath]);
            if (result.success) {
                vscode.window.showInformationMessage('Syntax check passed!');
            }
            else {
                vscode.window.showErrorMessage(`Syntax errors found: ${result.error}`);
            }
        });
    }
    formatCurrentFile() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to format');
                return;
            }
            yield editor.document.save();
            const filePath = editor.document.fileName;
            const result = yield this.runSonaCommand(['format', filePath]);
            if (result.success) {
                vscode.window.showInformationMessage('File formatted successfully!');
                // Reload the file to show formatting changes
                yield vscode.commands.executeCommand('workbench.action.files.revert');
            }
            else {
                vscode.window.showErrorMessage(`Formatting failed: ${result.error}`);
            }
        });
    }
    explainSelection() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || !editor.selection || editor.selection.isEmpty) {
                vscode.window.showErrorMessage('Please select code to explain');
                return;
            }
            if (editor.document.isUntitled) {
                vscode.window.showErrorMessage('Save the file before explaining code');
                return;
            }
            yield editor.document.save();
            const selectedText = editor.document.getText(editor.selection);
            const result = yield this.runSonaCommand(['explain', editor.document.fileName]);
            if (result.success) {
                const panel = vscode.window.createWebviewPanel('sonaExplanation', 'Code Explanation', vscode.ViewColumn.Beside, {});
                panel.webview.html = this.getExplanationHtml(selectedText, result.output);
            }
            else {
                vscode.window.showErrorMessage(`Explanation failed: ${result.error || 'AI service not configured'}`);
            }
        });
    }
    getSuggestions() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('Please open a file to get suggestions');
                return;
            }
            if (editor.document.isUntitled) {
                vscode.window.showErrorMessage('Save the file before getting suggestions');
                return;
            }
            yield editor.document.save();
            const prompt = yield vscode.window.showInputBox({
                placeHolder: 'Describe what you want to implement...',
                prompt: 'AI will suggest code based on your description'
            });
            if (!prompt)
                return;
            const result = yield this.runSonaCommand(['suggest', editor.document.fileName]);
            if (result.success) {
                const panel = vscode.window.createWebviewPanel('sonaSuggestions', 'AI Suggestions', vscode.ViewColumn.Beside, { enableScripts: true });
                panel.webview.html = this.getSuggestionsHtml(prompt, result.output);
            }
            else {
                vscode.window.showErrorMessage(`Suggestions failed: ${result.error || 'AI service not configured'}`);
            }
        });
    }
    planSelection() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.selection.isEmpty) {
                vscode.window.showErrorMessage('Select text to create a plan');
                return;
            }
            const text = editor.document.getText(editor.selection).slice(0, 4000);
            const result = yield this.runSonaCommand(['ai-plan', JSON.stringify(text)]);
            if (result.success) {
                this.showJsonPanel('AI Plan', result.output);
            }
            else {
                vscode.window.showErrorMessage(`Plan failed: ${result.error}`);
            }
        });
    }
    reviewSelection() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.selection.isEmpty) {
                vscode.window.showErrorMessage('Select text to review');
                return;
            }
            const text = editor.document.getText(editor.selection).slice(0, 6000);
            // For review we pipe content via stdin to keep args short
            const tmp = yield this.runSonaCommand(['ai-review', '-'], text);
            if (tmp.success) {
                this.showJsonPanel('AI Review', tmp.output);
            }
            else {
                vscode.window.showErrorMessage(`Review failed: ${tmp.error}`);
            }
        });
    }
    showJsonPanel(title, raw) {
        const panel = vscode.window.createWebviewPanel('sonaJson', title, vscode.ViewColumn.Beside, {});
        let body = raw.trim();
        if (!body.startsWith('{') && !body.startsWith('[')) {
            body = JSON.stringify({ raw: body });
        }
        panel.webview.html = `<html><body><pre>${body.replace(/</g, '&lt;')}</pre></body></html>`;
    }
    profileCurrentFile() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to profile');
                return;
            }
            yield editor.document.save();
            const filePath = editor.document.fileName;
            const result = yield this.runSonaCommand(['profile', filePath]);
            if (result.success) {
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Performance Profile ---');
                this.outputChannel.appendLine(result.output);
            }
            else {
                vscode.window.showErrorMessage(`Profiling failed: ${result.error}`);
            }
        });
    }
    benchmarkCurrentFile() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to benchmark');
                return;
            }
            yield editor.document.save();
            const filePath = editor.document.fileName;
            const result = yield this.runSonaCommand(['benchmark', filePath]);
            if (result.success) {
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Benchmark Results ---');
                this.outputChannel.appendLine(result.output);
            }
            else {
                vscode.window.showErrorMessage(`Benchmarking failed: ${result.error}`);
            }
        });
    }
    showInfo() {
        return __awaiter(this, void 0, void 0, function* () {
            const result = yield this.runSonaCommand(['info']);
            if (result.success) {
                vscode.window.showInformationMessage(result.output, { modal: false });
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Sona System Info ---');
                this.outputChannel.appendLine(result.output);
            }
            else {
                vscode.window.showErrorMessage(`Info failed: ${result.error}`);
            }
        });
    }
    showHelp() {
        return __awaiter(this, void 0, void 0, function* () {
            const result = yield this.runSonaCommand(['--help']);
            if (result.success) {
                this.outputChannel.show();
                this.outputChannel.appendLine('\n--- Sona Help ---');
                this.outputChannel.appendLine(result.output);
            }
            else {
                vscode.window.showErrorMessage(`Help failed: ${result.error}`);
            }
        });
    }
    checkAIConnection() {
        return __awaiter(this, void 0, void 0, function* () {
            // Use a non-mutating command so this check does not require a file.
            const result = yield this.runSonaCommand(['ai-mode', 'status']);
            if (result.success && !result.output.includes('Error')) {
                vscode.window.showInformationMessage('[OK] AI connection is working!');
            }
            else {
                const setupChoice = yield vscode.window.showWarningMessage('[WARN] AI connection not configured or not working', 'Setup Azure', 'Manual Setup', 'Help');
                switch (setupChoice) {
                    case 'Setup Azure':
                        yield this.setupAzure();
                        break;
                    case 'Manual Setup':
                        yield this.setupManual();
                        break;
                    case 'Help':
                        yield this.showHelp();
                        break;
                }
            }
        });
    }
    // HTML Generation Methods
    getWelcomeHtml() {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
                .welcome-header { text-align: center; margin-bottom: 30px; }
                .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
                .feature-card { border: 1px solid #ccc; border-radius: 8px; padding: 20px; }
                .btn { background: #007acc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
                .btn:hover { background: #005a9e; }
            </style>
        </head>
        <body>
            <div class="welcome-header">
                <h1>Welcome to Sona 0.15.1</h1>
                <p>The AI-native programming language with cognitive accessibility features</p>
            </div>

            <div class="feature-grid">
                <div class="feature-card">
                    <h3>AI Integration</h3>
                    <p>Set up AI-powered code assistance with Azure OpenAI</p>
                    <button class="btn" onclick="vscode.postMessage({command: 'setupAzure'})">Setup Azure</button>
                    <button class="btn" onclick="vscode.postMessage({command: 'setupManual'})">Manual Setup</button>
                </div>

                <div class="feature-card">
                    <h3>User Profile</h3>
                    <p>Optimize your experience for your cognitive needs</p>
                    <button class="btn" onclick="vscode.postMessage({command: 'selectProfile'})">Select Profile</button>
                </div>

                <div class="feature-card">
                    <h3>Getting Started</h3>
                    <p>Learn about Sona's features and capabilities</p>
                    <button class="btn" onclick="window.open('https://github.com/Bryantad/Sona')">Documentation</button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
            </script>
        </body>
        </html>
        `;
    }
    getExplanationHtml(code, explanation) {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
                .code-block { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 10px 0; }
                .explanation { line-height: 1.6; }
            </style>
        </head>
        <body>
            <h2>Code Explanation</h2>

            <h3>Selected Code:</h3>
            <div class="code-block"><pre>${code}</pre></div>

            <h3>Explanation:</h3>
            <div class="explanation">${explanation.replace(/\n/g, '<br>')}</div>
        </body>
        </html>
        `;
    }
    getSuggestionsHtml(prompt, suggestions) {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
                .suggestion-block { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 10px 0; }
                .copy-btn { background: #007acc; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
            </style>
        </head>
        <body>
            <h2>AI Suggestions</h2>

            <h3>Your Request:</h3>
            <p><em>${prompt}</em></p>

            <h3>Suggested Code:</h3>
            <div class="suggestion-block">
                <pre id="suggestions">${suggestions}</pre>
                <button class="copy-btn" onclick="copyToClipboard()">Copy to Clipboard</button>
            </div>

            <script>
                function copyToClipboard() {
                    const text = document.getElementById('suggestions').textContent;
                    navigator.clipboard.writeText(text);
                }
            </script>
        </body>
        </html>
        `;
    }
    dispose() {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
        if (this.terminal) {
            this.terminal.dispose();
        }
    }
}
exports.SonaCliIntegration = SonaCliIntegration;
// Export activation functions
function activate(context) {
    const sonaIntegration = new SonaCliIntegration(context);
    context.subscriptions.push({
        dispose: () => sonaIntegration.dispose()
    });
}
exports.activate = activate;
function deactivate() {
    // Cleanup handled by dispose methods
}
exports.deactivate = deactivate;
//# sourceMappingURL=sonaCliIntegration.js.map
