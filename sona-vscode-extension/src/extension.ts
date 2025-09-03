import * as vscode from 'vscode';
import { exec } from 'child_process';

// Cognitive Profile Types
type CognitiveProfile = 'ADHD' | 'Autism' | 'Dyslexia' | 'Neurotypical' | 'Auto';
type AccessibilityLevel = 'Basic' | 'Enhanced' | 'Maximum';

// Flow State Monitoring
class FlowStateMonitor {
    private keystrokePattern: number[] = [];
    private lastKeystroke: number = 0;
    private flowStateActive: boolean = false;
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'sona.flowStateInfo';
        this.updateStatusBar();
        this.statusBarItem.show();
    }

    public recordKeystroke() {
        const now = Date.now();
        if (this.lastKeystroke > 0) {
            const interval = now - this.lastKeystroke;
            this.keystrokePattern.push(interval);
            
            // Keep only last 20 keystrokes for analysis
            if (this.keystrokePattern.length > 20) {
                this.keystrokePattern.shift();
            }
            
            this.analyzeFlowState();
        }
        this.lastKeystroke = now;
    }

    private analyzeFlowState() {
        if (this.keystrokePattern.length < 10) {
            return;
        }

        // Calculate variance in keystroke timing
        const avg = this.keystrokePattern.reduce((a, b) => a + b, 0) / this.keystrokePattern.length;
        const variance = this.keystrokePattern.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / this.keystrokePattern.length;
        
        // Flow state indicators: consistent timing (low variance) and moderate speed
        const isInFlow = variance < 10000 && avg > 50 && avg < 500;
        
        if (isInFlow !== this.flowStateActive) {
            this.flowStateActive = isInFlow;
            this.updateStatusBar();
            this.notifyFlowStateChange();
        }
    }

    private updateStatusBar() {
        if (this.flowStateActive) {
            this.statusBarItem.text = "$(pulse) Flow State";
            this.statusBarItem.tooltip = "You're in flow state! 🧠✨";
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
        } else {
            this.statusBarItem.text = "$(eye) Sona";
            this.statusBarItem.tooltip = "Sona is monitoring your coding flow";
            this.statusBarItem.backgroundColor = undefined;
        }
    }

    private notifyFlowStateChange() {
        if (this.flowStateActive) {
            vscode.window.showInformationMessage('🧠 Flow state detected! Keep going!', 'Dismiss');
        }
    }

    dispose() {
        this.statusBarItem.dispose();
    }
}

// Accessibility Manager
class AccessibilityManager {
    private cognitiveProfile: CognitiveProfile;
    private decorationType: vscode.TextEditorDecorationType | undefined;

    constructor() {
        this.cognitiveProfile = this.loadCognitiveProfile();
        this.applyAccessibilitySettings();
    }

    private loadCognitiveProfile(): CognitiveProfile {
        const config = vscode.workspace.getConfiguration('sona');
        return config.get('cognitiveProfile', 'Auto') as CognitiveProfile;
    }

    private applyAccessibilitySettings() {
        const config = vscode.workspace.getConfiguration('sona');
        const level = config.get<AccessibilityLevel>('accessibilityLevel', 'Enhanced');
        
        if (level === 'Maximum' || this.cognitiveProfile === 'Dyslexia') {
            this.applyDyslexiaFriendlySettings();
        }
        
        if (this.cognitiveProfile === 'ADHD' || level === 'Enhanced') {
            this.applyADHDSettings();
        }
    }

    private applyDyslexiaFriendlySettings() {
        // Apply dyslexia-friendly font and spacing recommendations
        vscode.workspace.getConfiguration().update('editor.fontFamily', 
            'OpenDyslexic, Consolas, "Courier New", monospace', vscode.ConfigurationTarget.Global);
        vscode.workspace.getConfiguration().update('editor.lineHeight', 1.6, vscode.ConfigurationTarget.Global);
        vscode.workspace.getConfiguration().update('editor.letterSpacing', 0.5, vscode.ConfigurationTarget.Global);
    }

    private applyADHDSettings() {
        // Apply ADHD-friendly settings
        vscode.workspace.getConfiguration().update('editor.minimap.enabled', false, vscode.ConfigurationTarget.Global);
        vscode.workspace.getConfiguration().update('workbench.activityBar.location', 'hidden', vscode.ConfigurationTarget.Global);
    }

    public updateProfile(profile: CognitiveProfile) {
        this.cognitiveProfile = profile;
        const config = vscode.workspace.getConfiguration('sona');
        config.update('cognitiveProfile', profile, vscode.ConfigurationTarget.Global);
        this.applyAccessibilitySettings();
    }
}

// Sona CLI Interface
class SonaCLI {
    private pythonPath: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('sona');
        this.pythonPath = config.get('pythonPath', 'python');
    }

    async runCommand(command: string, args: string[] = [], workingDir?: string): Promise<{ stdout: string; stderr: string; code: number }> {
        return new Promise((resolve) => {
            const fullArgs = ['-m', 'sona.cli', command, ...args];
            const cwd = workingDir || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            
            exec(`"${this.pythonPath}" ${fullArgs.join(' ')}`, { cwd }, (error, stdout, stderr) => {
                resolve({
                    stdout,
                    stderr,
                    code: error?.code || 0
                });
            });
        });
    }

    async runFile(filePath: string): Promise<void> {
        const terminal = vscode.window.createTerminal('Sona');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli run "${filePath}"`);
    }

    async transpile(filePath: string, target: string): Promise<string> {
        const result = await this.runCommand('transpile', [filePath, '--target', target]);
        if (result.code !== 0) {
            throw new Error(result.stderr || 'Transpilation failed');
        }
        return result.stdout;
    }

    async formatFile(filePath: string): Promise<string> {
        const result = await this.runCommand('format', [filePath]);
        if (result.code !== 0) {
            throw new Error(result.stderr || 'Formatting failed');
        }
        return result.stdout;
    }

    async checkSyntax(filePath: string): Promise<{ valid: boolean; errors: string[] }> {
        const result = await this.runCommand('check', [filePath]);
        return {
            valid: result.code === 0,
            errors: result.stderr ? result.stderr.split('\n').filter(line => line.trim()) : []
        };
    }

    async getInfo(): Promise<string> {
        const result = await this.runCommand('info');
        return result.stdout;
    }

    async startREPL(): Promise<void> {
        const terminal = vscode.window.createTerminal('Sona REPL');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli repl`);
    }

    async profile(filePath: string): Promise<void> {
        const terminal = vscode.window.createTerminal('Sona Profile');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli profile "${filePath}"`);
    }

    async benchmark(filePath: string): Promise<void> {
        const terminal = vscode.window.createTerminal('Sona Benchmark');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli benchmark "${filePath}"`);
    }

    async setupEnvironment(): Promise<void> {
        const terminal = vscode.window.createTerminal('Sona Setup');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli setup manual`);
    }

    async explainCode(filePath: string): Promise<void> {
        const config = vscode.workspace.getConfiguration('sona');
        const aiEnabled = config.get('aiFeatures.enabled', false);
        
        if (!aiEnabled) {
            const result = await vscode.window.showInformationMessage(
                'AI features require setup. Would you like to configure them now?',
                'Setup AI', 'Cancel'
            );
            if (result === 'Setup AI') {
                await this.setupEnvironment();
            }
            return;
        }

        const terminal = vscode.window.createTerminal('Sona AI Explain');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli explain "${filePath}"`);
    }

    async suggestCode(filePath: string): Promise<void> {
        const config = vscode.workspace.getConfiguration('sona');
        const aiEnabled = config.get('aiFeatures.enabled', false);
        
        if (!aiEnabled) {
            const result = await vscode.window.showInformationMessage(
                'AI features require setup. Would you like to configure them now?',
                'Setup AI', 'Cancel'
            );
            if (result === 'Setup AI') {
                await this.setupEnvironment();
            }
            return;
        }

        const terminal = vscode.window.createTerminal('Sona AI Suggest');
        terminal.show();
        terminal.sendText(`"${this.pythonPath}" -m sona.cli suggest "${filePath}"`);
    }
}

// Focus Mode Manager
class FocusModeManager {
    private focusModeActive: boolean = false;
    private originalSettings: { [key: string]: any } = {};

    public toggleFocusMode() {
        if (this.focusModeActive) {
            this.disableFocusMode();
        } else {
            this.enableFocusMode();
        }
    }

    private enableFocusMode() {
        // Store original settings
        const config = vscode.workspace.getConfiguration();
        this.originalSettings = {
            'workbench.activityBar.visible': config.get('workbench.activityBar.visible'),
            'workbench.statusBar.visible': config.get('workbench.statusBar.visible'),
            'workbench.sidebar.location': config.get('workbench.sidebar.location'),
            'editor.minimap.enabled': config.get('editor.minimap.enabled'),
            'breadcrumbs.enabled': config.get('breadcrumbs.enabled')
        };

        // Apply focus mode settings
        config.update('workbench.activityBar.visible', false, vscode.ConfigurationTarget.Global);
        config.update('workbench.statusBar.visible', false, vscode.ConfigurationTarget.Global);
        config.update('editor.minimap.enabled', false, vscode.ConfigurationTarget.Global);
        config.update('breadcrumbs.enabled', false, vscode.ConfigurationTarget.Global);

        this.focusModeActive = true;
        vscode.window.showInformationMessage('🎯 Focus Mode Enabled');
    }

    private disableFocusMode() {
        // Restore original settings
        const config = vscode.workspace.getConfiguration();
        Object.entries(this.originalSettings).forEach(([key, value]) => {
            config.update(key, value, vscode.ConfigurationTarget.Global);
        });

        this.focusModeActive = false;
        vscode.window.showInformationMessage('👁️ Focus Mode Disabled');
    }
}

// Main Extension Variables
let flowStateMonitor: FlowStateMonitor;
let accessibilityManager: AccessibilityManager;
let sonaCLI: SonaCLI;
let focusModeManager: FocusModeManager;

export function activate(context: vscode.ExtensionContext) {
    // Register commands first
    const commands = [
        vscode.commands.registerCommand('sona.run', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'sona') {
                await sonaCLI.runFile(activeEditor.document.uri.fsPath);
            } else {
                vscode.window.showErrorMessage('Please open a .sona file to run');
            }
        }),

        vscode.commands.registerCommand('sona.transpile', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (!activeEditor || activeEditor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to transpile');
                return;
            }

            const config = vscode.workspace.getConfiguration('sona');
            const defaultTarget = config.get('defaultTranspileTarget', 'python');
            
            const target = await vscode.window.showQuickPick(
                ['python', 'javascript', 'rust', 'go', 'cpp'],
                { placeHolder: `Select target language (default: ${defaultTarget})` }
            ) || defaultTarget;

            try {
                const result = await sonaCLI.transpile(activeEditor.document.uri.fsPath, target);
                
                // Show transpiled code in new editor
                const doc = await vscode.workspace.openTextDocument({
                    content: result,
                    language: target === 'cpp' ? 'cpp' : target === 'javascript' ? 'javascript' : target
                });
                await vscode.window.showTextDocument(doc);
                
                vscode.window.showInformationMessage(`✅ Transpiled to ${target.toUpperCase()}`);
            } catch (error) {
                vscode.window.showErrorMessage(`Transpilation failed: ${error}`);
            }
        }),

        vscode.commands.registerCommand('sona.format', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (!activeEditor || activeEditor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to format');
                return;
            }

            try {
                const result = await sonaCLI.formatFile(activeEditor.document.uri.fsPath);
                const edit = new vscode.WorkspaceEdit();
                const range = new vscode.Range(
                    activeEditor.document.positionAt(0),
                    activeEditor.document.positionAt(activeEditor.document.getText().length)
                );
                edit.replace(activeEditor.document.uri, range, result);
                await vscode.workspace.applyEdit(edit);
                vscode.window.showInformationMessage('✨ Code formatted successfully');
            } catch (error) {
                vscode.window.showErrorMessage(`Formatting failed: ${error}`);
            }
        }),

        vscode.commands.registerCommand('sona.checkSyntax', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (!activeEditor || activeEditor.document.languageId !== 'sona') {
                vscode.window.showErrorMessage('Please open a .sona file to check');
                return;
            }

            try {
                const result = await sonaCLI.checkSyntax(activeEditor.document.uri.fsPath);
                if (result.valid) {
                    vscode.window.showInformationMessage('✅ Syntax is valid');
                } else {
                    vscode.window.showErrorMessage(`❌ Syntax errors found:\n${result.errors.join('\n')}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Syntax check failed: ${error}`);
            }
        }),

        vscode.commands.registerCommand('sona.info', async () => {
            try {
                const info = await sonaCLI.getInfo();
                vscode.window.showInformationMessage(info, { modal: true });
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to get Sona info: ${error}`);
            }
        }),

        vscode.commands.registerCommand('sona.setup', async () => {
            await sonaCLI.setupEnvironment();
        }),

        vscode.commands.registerCommand('sona.repl', async () => {
            await sonaCLI.startREPL();
        }),

        vscode.commands.registerCommand('sona.profile', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'sona') {
                await sonaCLI.profile(activeEditor.document.uri.fsPath);
            } else {
                vscode.window.showErrorMessage('Please open a .sona file to profile');
            }
        }),

        vscode.commands.registerCommand('sona.benchmark', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'sona') {
                await sonaCLI.benchmark(activeEditor.document.uri.fsPath);
            } else {
                vscode.window.showErrorMessage('Please open a .sona file to benchmark');
            }
        }),

        vscode.commands.registerCommand('sona.explain', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'sona') {
                await sonaCLI.explainCode(activeEditor.document.uri.fsPath);
            } else {
                vscode.window.showErrorMessage('Please open a .sona file to explain');
            }
        }),

        vscode.commands.registerCommand('sona.suggest', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.languageId === 'sona') {
                await sonaCLI.suggestCode(activeEditor.document.uri.fsPath);
            } else {
                vscode.window.showErrorMessage('Please open a .sona file for suggestions');
            }
        }),

        vscode.commands.registerCommand('sona.docs', () => {
            vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona#readme'));
        }),

        vscode.commands.registerCommand('sona.cognitiveProfile', async () => {
            const profiles: CognitiveProfile[] = ['Auto', 'ADHD', 'Autism', 'Dyslexia', 'Neurotypical'];
            const selected = await vscode.window.showQuickPick(profiles, {
                placeHolder: 'Select your cognitive profile for personalized assistance'
            });
            if (selected) {
                accessibilityManager.updateProfile(selected as CognitiveProfile);
                vscode.window.showInformationMessage(`🧠 Cognitive profile set to: ${selected}`);
            }
        }),

        vscode.commands.registerCommand('sona.toggleFocusMode', () => {
            focusModeManager.toggleFocusMode();
        }),

        vscode.commands.registerCommand('sona.accessibilitySettings', async () => {
            const levels = ['Standard', 'Enhanced', 'Maximum'];
            const selected = await vscode.window.showQuickPick(levels, {
                placeHolder: 'Select accessibility enhancement level'
            });
            if (selected) {
                const config = vscode.workspace.getConfiguration('sona');
                await config.update('accessibilityLevel', selected, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage(`♿ Accessibility level set to: ${selected}`);
            }
        }),

        vscode.commands.registerCommand('sona.whatsNew', () => {
            const panel = vscode.window.createWebviewPanel(
                'sonaWhatsNew',
                'What\'s New in Sona v1.0.0',
                vscode.ViewColumn.One,
                { enableScripts: true }
            );

            panel.webview.html = getWhatsNewContent();
        }),

        // Flow State Info Command
        vscode.commands.registerCommand('sona.flowStateInfo', () => {
            vscode.window.showInformationMessage(
                'Flow State Monitor: Tracks your coding rhythm and focus patterns to help maintain optimal cognitive state.',
                'Learn More'
            ).then(selection => {
                if (selection === 'Learn More') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona#flow-state'));
                }
            });
        }),

        // Open Samples Command
        vscode.commands.registerCommand('sona.openSamples', async () => {
            const extensionPath = context.extensionPath;
            const samplesPath = vscode.Uri.file(extensionPath + '/samples');
            
            try {
                // Open the samples folder
                await vscode.commands.executeCommand('vscode.openFolder', samplesPath, { forceNewWindow: false });
            } catch {
                // If opening folder fails, show sample files in quick pick
                const sampleFiles = [
                    'hello_world.sona - Your first Sona program',
                    'cognitive_memory.sona - Memory system demo', 
                    'oop_example.sona - Object-oriented programming',
                    'performance_benchmark.sona - Performance testing',
                    'ai_integration.sona - AI features demo',
                    'cognitive_accessibility.sona - Neurodivergent features'
                ];
                
                const selected = await vscode.window.showQuickPick(sampleFiles, {
                    placeHolder: 'Choose a sample file to open'
                });
                
                if (selected) {
                    const fileName = selected.split(' - ')[0];
                    const filePath = vscode.Uri.file(extensionPath + '/samples/' + fileName);
                    const doc = await vscode.workspace.openTextDocument(filePath);
                    await vscode.window.showTextDocument(doc);
                }
            }
        })
    ];

    // Initialize managers after commands are registered
    flowStateMonitor = new FlowStateMonitor();
    accessibilityManager = new AccessibilityManager();
    sonaCLI = new SonaCLI();
    focusModeManager = new FocusModeManager();

    // Monitor keystrokes for flow state
    const keystrokeDisposable = vscode.workspace.onDidChangeTextDocument((event) => {
        if (event.document.languageId === 'sona') {
            flowStateMonitor.recordKeystroke();
        }
    });

    // Add all disposables
    context.subscriptions.push(...commands, keystrokeDisposable, flowStateMonitor);

    // Show welcome message on first activation
    const hasShownWelcome = context.globalState.get('hasShownWelcome', false);
    if (!hasShownWelcome) {
        vscode.window.showInformationMessage(
            '🎉 Welcome to Sona! A neurodivergent-first programming language.',
            'Get Started', 'What\'s New'
        ).then(selection => {
            if (selection === 'Get Started') {
                vscode.commands.executeCommand('sona.docs');
            } else if (selection === 'What\'s New') {
                vscode.commands.executeCommand('sona.whatsNew');
            }
        });
        context.globalState.update('hasShownWelcome', true);
    }
}

function getWhatsNewContent(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>What's New in Sona v1.0.0</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: var(--vscode-editor-foreground);
            background-color: var(--vscode-editor-background);
        }
        h1, h2 { color: var(--vscode-textLink-foreground); }
        .feature { margin: 20px 0; padding: 15px; border-left: 4px solid var(--vscode-textLink-foreground); }
        .emoji { font-size: 1.2em; }
        code { background-color: var(--vscode-textCodeBlock-background); padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🎉 What's New in Sona v1.0.0</h1>
    
    <div class="feature">
        <h2><span class="emoji">🧠</span> Enhanced Cognitive Support</h2>
        <p>Improved ADHD, Autism, and Dyslexia-friendly features with adaptive UI and flow state monitoring.</p>
    </div>
    
    <div class="feature">
        <h2><span class="emoji">🔄</span> Multi-Language Transpilation</h2>
        <p>Transpile Sona code to Python, JavaScript, Rust, Go, and C++ with a single command.</p>
    </div>
    
    <div class="feature">
        <h2><span class="emoji">🤖</span> AI-Native Programming</h2>
        <p>Built-in AI assistance for code explanation, suggestions, and debugging (setup required).</p>
    </div>
    
    <div class="feature">
        <h2><span class="emoji">⚡</span> Performance Improvements</h2>
        <p>Faster transpilation, improved syntax highlighting, and better error reporting.</p>
    </div>
    
    <div class="feature">
        <h2><span class="emoji">🎯</span> Focus Mode</h2>
        <p>Toggle distraction-free coding environment with <code>Ctrl+Shift+Alt+F</code>.</p>
    </div>
    
    <div class="feature">
        <h2><span class="emoji">🛠️</span> Improved Setup</h2>
        <p>Streamlined environment setup and configuration for all features.</p>
    </div>
    
    <p><strong>Get Started:</strong> Open a <code>.sona</code> file and press <code>Ctrl+F5</code> to run it!</p>
</body>
</html>`;
}

export function deactivate() {
    if (flowStateMonitor) {
        flowStateMonitor.dispose();
    }
}
