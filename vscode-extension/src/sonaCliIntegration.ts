// VS Code Extension Integration for Sona v1.0.0 CLI
// Provides full VS Code integration with local Sona CLI installation

import * as vscode from 'vscode';
import { spawn, exec, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

interface SonaConfig {
    pythonPath: string;
    timeout: number;
    autoSetup: boolean;
}

interface CommandResult {
    success: boolean;
    output: string;
    error?: string;
    exitCode?: number;
}

type UserProfile = 'neurotypical' | 'adhd' | 'dyslexia';

export class SonaCliIntegration {
    private config: SonaConfig;
    private outputChannel: vscode.OutputChannel;
    private statusBarItem: vscode.StatusBarItem;
    private userProfile: UserProfile;
    private context: vscode.ExtensionContext | undefined;
    private terminal: vscode.Terminal | undefined;

    constructor(context?: vscode.ExtensionContext) {
        this.config = this.loadConfiguration();
        this.outputChannel = vscode.window.createOutputChannel('Sona');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.context = context;
        this.userProfile = this.loadUserProfile();
        this.initializeStatusBar();
        this.registerCommands();
        this.checkSonaInstallation();
    }

    private loadConfiguration(): SonaConfig {
        const config = vscode.workspace.getConfiguration('sona');
        return {
            pythonPath: config.get('cli.pythonPath', 'python'),
            timeout: config.get('cli.timeout', 30000),
            autoSetup: config.get('ai.autoSetup', true)
        };
    }

    private loadUserProfile(): UserProfile {
        if (this.context) {
            const stored = this.context.globalState.get<UserProfile>('sonaUserProfile');
            if (stored) return stored;
        }
        const config = vscode.workspace.getConfiguration('sona');
        return config.get('userProfile', 'neurotypical') as UserProfile;
    }

    private initializeStatusBar(): void {
        this.statusBarItem.text = '$(rocket) Sona';
        this.statusBarItem.tooltip = 'Sona Language Support - Click for info';
        this.statusBarItem.command = 'sona.info';
        this.statusBarItem.show();
    }

    private async checkSonaInstallation(): Promise<void> {
        try {
            const result = await this.runSonaCommand(['--version']);
            if (result.success) {
                this.statusBarItem.text = '$(rocket) Sona ✓';
                this.statusBarItem.tooltip = `Sona CLI Available - ${result.output.trim()}`;
                this.outputChannel.appendLine(`✅ Sona CLI detected: ${result.output.trim()}`);
            } else {
                this.statusBarItem.text = '$(alert) Sona';
                this.statusBarItem.tooltip = 'Sona CLI not found - Click to install';
                this.statusBarItem.command = 'sona.welcome';
                this.outputChannel.appendLine('⚠️ Sona CLI not found. Please install Sona first.');
            }
        } catch (error) {
            this.statusBarItem.text = '$(alert) Sona';
            this.statusBarItem.tooltip = 'Sona CLI error - Click for help';
            this.statusBarItem.command = 'sona.help';
            this.outputChannel.appendLine(`❌ Error checking Sona: ${error}`);
        }
    }

    private async runSonaCommand(args: string[], input?: string): Promise<CommandResult> {
        return new Promise((resolve) => {
            const command = `${this.config.pythonPath} -m sona.cli ${args.join(' ')}`;
            this.outputChannel.appendLine(`Running: ${command}`);

            const process = exec(command, {
                timeout: this.config.timeout,
                encoding: 'utf8'
            }, (error, stdout, stderr) => {
                if (error) {
                    const result: CommandResult = {
                        success: false,
                        output: stdout || '',
                        error: stderr || error.message,
                        exitCode: error.code || -1
                    };
                    this.outputChannel.appendLine(`❌ Command failed: ${result.error}`);
                    resolve(result);
                } else {
                    const result: CommandResult = {
                        success: true,
                        output: stdout || '',
                        exitCode: 0
                    };
                    this.outputChannel.appendLine(`✅ Command succeeded`);
                    resolve(result);
                }
            });

            if (input && process.stdin) {
                process.stdin.write(input);
                process.stdin.end();
            }
        });
    }

    private registerCommands(): void {
        if (!this.context) return;

        // Welcome and Setup Commands
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.welcome', () => this.showWelcome())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.setup.azure', () => this.setupAzure())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.setup.manual', () => this.setupManual())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.selectUserProfile', () => this.selectUserProfile())
        );

        // Core CLI Commands
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.run', () => this.runCurrentFile())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.transpile', () => this.transpileCurrentFile())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.repl', () => this.startRepl())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.check', () => this.checkCurrentFile())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.format', () => this.formatCurrentFile())
        );

        // AI Commands
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.explain', () => this.explainSelection())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.suggest', () => this.getSuggestions())
        );

        // Performance Commands
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.profile', () => this.profileCurrentFile())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.benchmark', () => this.benchmarkCurrentFile())
        );

        // Info Commands
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.info', () => this.showInfo())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.help', () => this.showHelp())
        );

        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.checkAIConnection', () => this.checkAIConnection())
        );

        // Capability feature commands (0.9.3)
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.aiPlanSelection', () => this.planSelection())
        );
        this.context.subscriptions.push(
            vscode.commands.registerCommand('sona.aiReviewSelection', () => this.reviewSelection())
        );
    }

    // Command Implementations

    private async showWelcome(): Promise<void> {
        const panel = vscode.window.createWebviewPanel(
            'sonaWelcome',
            'Welcome to Sona',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        panel.webview.html = this.getWelcomeHtml();
        
        panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'setupAzure':
                        await this.setupAzure();
                        break;
                    case 'setupManual':
                        await this.setupManual();
                        break;
                    case 'selectProfile':
                        await this.selectUserProfile();
                        break;
                }
            },
            undefined,
            this.context?.subscriptions
        );
    }

    private async setupAzure(): Promise<void> {
        const result = await this.runSonaCommand(['setup', 'azure']);
        if (result.success) {
            vscode.window.showInformationMessage('Azure OpenAI setup completed successfully!');
        } else {
            vscode.window.showErrorMessage(`Azure setup failed: ${result.error}`);
        }
    }

    private async setupManual(): Promise<void> {
        const result = await this.runSonaCommand(['setup', 'manual']);
        if (result.success) {
            vscode.window.showInformationMessage('Manual AI setup completed successfully!');
        } else {
            vscode.window.showErrorMessage(`Manual setup failed: ${result.error}`);
        }
    }

    private async selectUserProfile(): Promise<void> {
        const profiles = [
            { label: 'Neurotypical', description: 'Standard UI/UX for typical users', value: 'neurotypical' },
            { label: 'ADHD', description: 'High-contrast, minimal distractions', value: 'adhd' },
            { label: 'Dyslexia', description: 'Dyslexia-friendly fonts and enhanced readability', value: 'dyslexia' }
        ];

        const selected = await vscode.window.showQuickPick(profiles, {
            placeHolder: 'Select your cognitive profile for optimized experience'
        });

        if (selected && this.context) {
            this.userProfile = selected.value as UserProfile;
            await this.context.globalState.update('sonaUserProfile', this.userProfile);
            vscode.window.showInformationMessage(`Profile set to: ${selected.label}`);
        }
    }

    private async runCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'sona') {
            vscode.window.showErrorMessage('Please open a .sona file to run');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.fileName;
        
        const result = await this.runSonaCommand(['run', filePath]);
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine('\n--- Sona Run Output ---');
            this.outputChannel.appendLine(result.output);
        } else {
            vscode.window.showErrorMessage(`Run failed: ${result.error}`);
        }
    }

    private async transpileCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'sona') {
            vscode.window.showErrorMessage('Please open a .sona file to transpile');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.fileName;
        const outputPath = filePath.replace('.sona', '.py');
        
        const result = await this.runSonaCommand(['transpile', filePath, outputPath]);
        if (result.success) {
            vscode.window.showInformationMessage(`Transpiled to: ${outputPath}`);
            const doc = await vscode.workspace.openTextDocument(outputPath);
            await vscode.window.showTextDocument(doc);
        } else {
            vscode.window.showErrorMessage(`Transpilation failed: ${result.error}`);
        }
    }

    private async startRepl(): Promise<void> {
        if (!this.terminal || this.terminal.exitStatus) {
            this.terminal = vscode.window.createTerminal({
                name: 'Sona REPL',
                shellPath: this.config.pythonPath,
                shellArgs: ['-m', 'sona.cli', 'repl']
            });
        }
        this.terminal.show();
    }

    private async checkCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'sona') {
            vscode.window.showErrorMessage('Please open a .sona file to check');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.fileName;
        
        const result = await this.runSonaCommand(['check', filePath]);
        if (result.success) {
            vscode.window.showInformationMessage('Syntax check passed!');
        } else {
            vscode.window.showErrorMessage(`Syntax errors found: ${result.error}`);
        }
    }

    private async formatCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'sona') {
            vscode.window.showErrorMessage('Please open a .sona file to format');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.fileName;
        
        const result = await this.runSonaCommand(['format', filePath]);
        if (result.success) {
            vscode.window.showInformationMessage('File formatted successfully!');
            // Reload the file to show formatting changes
            await vscode.commands.executeCommand('workbench.action.files.revert');
        } else {
            vscode.window.showErrorMessage(`Formatting failed: ${result.error}`);
        }
    }

    private async explainSelection(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || !editor.selection || editor.selection.isEmpty) {
            vscode.window.showErrorMessage('Please select code to explain');
            return;
        }

        const selectedText = editor.document.getText(editor.selection);
        const result = await this.runSonaCommand(['explain'], selectedText);
        
        if (result.success) {
            const panel = vscode.window.createWebviewPanel(
                'sonaExplanation',
                'Code Explanation',
                vscode.ViewColumn.Beside,
                {}
            );
            panel.webview.html = this.getExplanationHtml(selectedText, result.output);
        } else {
            vscode.window.showErrorMessage(`Explanation failed: ${result.error || 'AI service not configured'}`);
        }
    }

    private async getSuggestions(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('Please open a file to get suggestions');
            return;
        }

        const prompt = await vscode.window.showInputBox({
            placeHolder: 'Describe what you want to implement...',
            prompt: 'AI will suggest code based on your description'
        });

        if (!prompt) return;

        const result = await this.runSonaCommand(['suggest'], prompt);
        
        if (result.success) {
            const panel = vscode.window.createWebviewPanel(
                'sonaSuggestions',
                'AI Suggestions',
                vscode.ViewColumn.Beside,
                { enableScripts: true }
            );
            panel.webview.html = this.getSuggestionsHtml(prompt, result.output);
        } else {
            vscode.window.showErrorMessage(`Suggestions failed: ${result.error || 'AI service not configured'}`);
        }
    }

    private async planSelection(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showErrorMessage('Select text to create a plan');
            return;
        }
        const text = editor.document.getText(editor.selection).slice(0, 4000);
        const result = await this.runSonaCommand(['ai-plan', JSON.stringify(text)]);
        if (result.success) {
            this.showJsonPanel('AI Plan', result.output);
        } else {
            vscode.window.showErrorMessage(`Plan failed: ${result.error}`);
        }
    }

    private async reviewSelection(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showErrorMessage('Select text to review');
            return;
        }
        const text = editor.document.getText(editor.selection).slice(0, 6000);
        // For review we pipe content via stdin to keep args short
        const tmp = await this.runSonaCommand(['ai-review', '-'], text);
        if (tmp.success) {
            this.showJsonPanel('AI Review', tmp.output);
        } else {
            vscode.window.showErrorMessage(`Review failed: ${tmp.error}`);
        }
    }

    private showJsonPanel(title: string, raw: string): void {
        const panel = vscode.window.createWebviewPanel(
            'sonaJson', title, vscode.ViewColumn.Beside, {}
        );
        let body = raw.trim();
        if (!body.startsWith('{') && !body.startsWith('[')) {
            body = JSON.stringify({ raw: body });
        }
        panel.webview.html = `<html><body><pre>${body.replace(/</g, '&lt;')}</pre></body></html>`;
    }

    private async profileCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'sona') {
            vscode.window.showErrorMessage('Please open a .sona file to profile');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.fileName;
        
        const result = await this.runSonaCommand(['profile', filePath]);
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine('\n--- Performance Profile ---');
            this.outputChannel.appendLine(result.output);
        } else {
            vscode.window.showErrorMessage(`Profiling failed: ${result.error}`);
        }
    }

    private async benchmarkCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'sona') {
            vscode.window.showErrorMessage('Please open a .sona file to benchmark');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.fileName;
        
        const result = await this.runSonaCommand(['benchmark', filePath]);
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine('\n--- Benchmark Results ---');
            this.outputChannel.appendLine(result.output);
        } else {
            vscode.window.showErrorMessage(`Benchmarking failed: ${result.error}`);
        }
    }

    private async showInfo(): Promise<void> {
        const result = await this.runSonaCommand(['info']);
        if (result.success) {
            vscode.window.showInformationMessage(result.output, { modal: false });
            this.outputChannel.show();
            this.outputChannel.appendLine('\n--- Sona System Info ---');
            this.outputChannel.appendLine(result.output);
        } else {
            vscode.window.showErrorMessage(`Info failed: ${result.error}`);
        }
    }

    private async showHelp(): Promise<void> {
        const result = await this.runSonaCommand(['--help']);
        if (result.success) {
            this.outputChannel.show();
            this.outputChannel.appendLine('\n--- Sona Help ---');
            this.outputChannel.appendLine(result.output);
        } else {
            vscode.window.showErrorMessage(`Help failed: ${result.error}`);
        }
    }

    private async checkAIConnection(): Promise<void> {
        // Try to use an AI command to test connection
        const result = await this.runSonaCommand(['explain'], 'test connection');
        
        if (result.success && !result.output.includes('Error')) {
            vscode.window.showInformationMessage('✅ AI connection is working!');
        } else {
            const setupChoice = await vscode.window.showWarningMessage(
                '⚠️ AI connection not configured or not working',
                'Setup Azure',
                'Manual Setup',
                'Help'
            );
            
            switch (setupChoice) {
                case 'Setup Azure':
                    await this.setupAzure();
                    break;
                case 'Manual Setup':
                    await this.setupManual();
                    break;
                case 'Help':
                    await this.showHelp();
                    break;
            }
        }
    }

    // HTML Generation Methods

    private getWelcomeHtml(): string {
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
                <h1>🚀 Welcome to Sona v1.0.0</h1>
                <p>The AI-native programming language with cognitive accessibility features</p>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🤖 AI Integration</h3>
                    <p>Set up AI-powered code assistance with Azure OpenAI</p>
                    <button class="btn" onclick="vscode.postMessage({command: 'setupAzure'})">Setup Azure</button>
                    <button class="btn" onclick="vscode.postMessage({command: 'setupManual'})">Manual Setup</button>
                </div>
                
                <div class="feature-card">
                    <h3>👤 User Profile</h3>
                    <p>Optimize your experience for your cognitive needs</p>
                    <button class="btn" onclick="vscode.postMessage({command: 'selectProfile'})">Select Profile</button>
                </div>
                
                <div class="feature-card">
                    <h3>📚 Getting Started</h3>
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

    private getExplanationHtml(code: string, explanation: string): string {
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

    private getSuggestionsHtml(prompt: string, suggestions: string): string {
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

    public dispose(): void {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
        if (this.terminal) {
            this.terminal.dispose();
        }
    }
}

// Export activation functions
export function activate(context: vscode.ExtensionContext) {
    const sonaIntegration = new SonaCliIntegration(context);
    context.subscriptions.push({
        dispose: () => sonaIntegration.dispose()
    });
}

export function deactivate() {
    // Cleanup handled by dispose methods
}
