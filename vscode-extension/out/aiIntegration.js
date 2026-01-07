"use strict";
// VS Code Extension Integration for Sona v0.9.0 AI Router
// Connects the Sona VS Code extension to the enterprise AI routing infrastructure
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
exports.deactivate = exports.activate = exports.SonaAIIntegration = void 0;
const vscode = require("vscode");
const axios_1 = require("axios");
class SonaAIIntegration {
    constructor(context) {
        this.config = this.loadConfiguration();
        this.outputChannel = vscode.window.createOutputChannel('Sona AI Router');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.cognitiveMemory = {
            workingMemory: [],
            focusMode: false,
            cognitiveState: 'ready',
            timestamp: Date.now()
        };
        this.context = context;
        this.userProfile = this.loadUserProfile();
        this.initializeStatusBar();
        this.registerCommands();
        this.checkForOnboarding();
    }
    loadUserProfile() {
        if (this.context) {
            const stored = this.context.globalState.get('sonaUserProfile');
            if (stored)
                return stored;
        }
        return 'neurotypical';
    }
    checkForOnboarding() {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.context)
                return;
            const hasSeenOnboarding = this.context.globalState.get('sonaOnboardingComplete');
            if (!hasSeenOnboarding) {
                // Show onboarding after a brief delay to allow extension to fully load
                setTimeout(() => this.showOnboarding(), 2000);
            }
        });
    }
    showOnboarding() {
        return __awaiter(this, void 0, void 0, function* () {
            const choice = yield vscode.window.showInformationMessage('🚀 Welcome to Sona v0.9.0! Would you like to configure your UI profile for the best experience?', {
                modal: false,
                detail: 'Sona offers specialized UI modes for different cognitive needs:\n• Neurotypical (Default)\n• ADHD (High contrast, minimal distractions)\n• Dyslexia (Dyslexia-friendly fonts and layout)'
            }, 'Configure Now', 'Use Default', 'Remind Me Later');
            if (choice === 'Configure Now') {
                yield this.selectUserProfile();
                if (this.context) {
                    yield this.context.globalState.update('sonaOnboardingComplete', true);
                }
            }
            else if (choice === 'Use Default') {
                vscode.window.showInformationMessage('Sona will use the default neurotypical UI. You can change this anytime via "Sona: Select User Profile" in the command palette.');
                if (this.context) {
                    yield this.context.globalState.update('sonaOnboardingComplete', true);
                }
            }
            // If "Remind Me Later" is selected, onboarding will show again next time
        });
    }
    saveUserProfile(profile) {
        return __awaiter(this, void 0, void 0, function* () {
            this.userProfile = profile;
            if (this.context) {
                yield this.context.globalState.update('sonaUserProfile', profile);
            }
            this.updateStatusBarForProfile();
        });
    }
    loadConfiguration() {
        const config = vscode.workspace.getConfiguration('sona');
        return {
            aiRouterEndpoint: config.get('aiRouter.endpoint', 'http://localhost:8000'),
            fallbackProviders: config.get('aiRouter.fallbackProviders', ['openai', 'anthropic', 'azure-openai']),
            timeout: config.get('aiRouter.timeout', 30000),
            retryAttempts: config.get('aiRouter.retryAttempts', 3)
        };
    }
    initializeStatusBar() {
        this.updateStatusBarForProfile();
        this.statusBarItem.show();
    }
    updateStatusBarForProfile() {
        let icon = 'zap';
        let label = 'Sona AI: Ready';
        let tooltip = 'Sona AI Router Status - Click to check connection';
        if (this.userProfile === 'adhd') {
            icon = 'rocket';
            label = 'Sona AI: ADHD Mode';
            tooltip = 'Sona AI (ADHD UI) - Fast, high-contrast, minimal distractions';
        }
        else if (this.userProfile === 'dyslexia') {
            icon = 'book';
            label = 'Sona AI: Dyslexia Mode';
            tooltip = 'Sona AI (Dyslexia UI) - Dyslexia-friendly font and layout';
        }
        this.statusBarItem.text = `$(${icon}) ${label}`;
        this.statusBarItem.tooltip = tooltip + `\nCurrent profile: ${this.userProfile}\n\nRight-click to change profile`;
        // Add context menu for easy profile switching
        this.statusBarItem.command = {
            command: 'sona.statusBarClick',
            title: 'Sona Status Bar Click'
        };
    }
    registerCommands() {
        if (!this.context)
            return;
        const disposables = [
            vscode.commands.registerCommand('sona.checkAIConnection', () => this.checkAIConnection()),
            vscode.commands.registerCommand('sona.generateCode', () => this.generateCode()),
            vscode.commands.registerCommand('sona.refactorCode', () => this.refactorCode()),
            vscode.commands.registerCommand('sona.explainCode', () => this.explainCode()),
            vscode.commands.registerCommand('sona.debugCode', () => this.debugCode()),
            vscode.commands.registerCommand('sona.optimizeCode', () => this.optimizeCode()),
            vscode.commands.registerCommand('sona.toggleFocusMode', () => this.toggleFocusMode()),
            vscode.commands.registerCommand('sona.clearCognitiveMemory', () => this.clearCognitiveMemory()),
            vscode.commands.registerCommand('sona.selectUserProfile', () => this.selectUserProfile()),
            vscode.commands.registerCommand('sona.statusBarClick', () => this.handleStatusBarClick()),
            vscode.commands.registerCommand('sona.showOnboarding', () => this.showOnboarding())
        ];
        disposables.forEach(disposable => {
            this.context.subscriptions.push(disposable);
        });
    }
    handleStatusBarClick() {
        return __awaiter(this, void 0, void 0, function* () {
            const choice = yield vscode.window.showQuickPick([
                {
                    label: '$(pulse) Check AI Connection',
                    value: 'connection'
                },
                {
                    label: '$(person) Change UI Profile',
                    value: 'profile',
                    description: `Current: ${this.userProfile}`
                },
                {
                    label: '$(question) Show Onboarding',
                    value: 'onboarding'
                }
            ], {
                placeHolder: 'What would you like to do?'
            });
            switch (choice === null || choice === void 0 ? void 0 : choice.value) {
                case 'connection':
                    yield this.checkAIConnection();
                    break;
                case 'profile':
                    yield this.selectUserProfile();
                    break;
                case 'onboarding':
                    yield this.showOnboarding();
                    break;
            }
        });
    }
    selectUserProfile() {
        return __awaiter(this, void 0, void 0, function* () {
            const options = [
                {
                    label: '$(person) Neurotypical (Default)',
                    value: 'neurotypical',
                    description: 'Standard UI/UX with familiar design patterns',
                    detail: 'Best for users who prefer conventional interfaces'
                },
                {
                    label: '$(rocket) ADHD',
                    value: 'adhd',
                    description: 'High-contrast, minimal distractions, bold fonts',
                    detail: 'Optimized for focus and reduced cognitive load'
                },
                {
                    label: '$(book) Dyslexia',
                    value: 'dyslexia',
                    description: 'Dyslexia-friendly fonts and enhanced readability',
                    detail: 'Designed with OpenDyslexic font and improved spacing'
                }
            ];
            const pick = yield vscode.window.showQuickPick(options, {
                placeHolder: 'Select your preferred UI profile for optimal Sona experience',
                matchOnDescription: true,
                matchOnDetail: true
            });
            if (pick) {
                yield this.saveUserProfile(pick.value);
                // Show profile-specific welcome message
                let welcomeMessage = '';
                if (pick.value === 'adhd') {
                    welcomeMessage = '🚀 ADHD mode activated! UI optimized for focus with high contrast and minimal distractions.';
                }
                else if (pick.value === 'dyslexia') {
                    welcomeMessage = '📖 Dyslexia mode activated! UI enhanced with dyslexia-friendly fonts and improved readability.';
                }
                else {
                    welcomeMessage = '👤 Neurotypical mode activated! Standard UI for familiar development experience.';
                }
                vscode.window.showInformationMessage(welcomeMessage, 'Open Settings').then(choice => {
                    if (choice === 'Open Settings') {
                        vscode.commands.executeCommand('workbench.action.openSettings', 'sona');
                    }
                });
            }
        });
    }
    checkAIConnection() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                this.updateStatus("$(sync~spin) Checking connection...", "Checking AI Router connection");
                const response = yield this.makeAIRequest('/health', 'GET');
                if (response.success) {
                    this.updateStatus("$(check) Sona AI: Connected", `Connected to AI Router - Provider: ${response.provider}`);
                    vscode.window.showInformationMessage(`Sona AI Router connected successfully via ${response.provider}`);
                }
                else {
                    throw new Error(response.error || 'Unknown error');
                }
            }
            catch (error) {
                this.updateStatus("$(error) Sona AI: Disconnected", "Failed to connect to AI Router");
                vscode.window.showErrorMessage(`Sona AI Router connection failed: ${error}`);
            }
        });
    }
    generateCode() {
        return __awaiter(this, void 0, void 0, function* () {
            const prompt = yield vscode.window.showInputBox({
                prompt: 'Describe the code you want to generate',
                placeHolder: 'e.g., Create a function that sorts an array of objects by name'
            });
            if (!prompt)
                return;
            try {
                this.updateStatus("$(sync~spin) Generating code...", "AI is generating code");
                const editor = vscode.window.activeTextEditor;
                const languageId = (editor === null || editor === void 0 ? void 0 : editor.document.languageId) || 'python';
                const response = yield this.makeAIRequest('/generate-code', 'POST', {
                    prompt,
                    language: languageId,
                    context: yield this.getEditorContext(),
                    cognitive_memory: this.cognitiveMemory
                });
                if (response.success && response.data.code) {
                    yield this.insertCodeIntoEditor(response.data.code, response.data.explanation);
                    this.updateCognitiveMemory('code_generation', { prompt, language: languageId });
                    this.updateStatus("$(check) Code generated", "Code generation completed successfully");
                }
                else {
                    throw new Error(response.error || 'Code generation failed');
                }
            }
            catch (error) {
                vscode.window.showErrorMessage(`Code generation failed: ${error}`);
                this.updateStatus("$(error) Generation failed", "Code generation failed");
            }
        });
    }
    refactorCode() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }
            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);
            if (!selectedText) {
                vscode.window.showErrorMessage('Please select code to refactor');
                return;
            }
            try {
                this.updateStatus("$(sync~spin) Refactoring code...", "AI is refactoring selected code");
                const response = yield this.makeAIRequest('/refactor-code', 'POST', {
                    code: selectedText,
                    language: editor.document.languageId,
                    context: yield this.getEditorContext(),
                    cognitive_memory: this.cognitiveMemory
                });
                if (response.success && response.data.refactored_code) {
                    yield editor.edit(editBuilder => {
                        editBuilder.replace(selection, response.data.refactored_code);
                    });
                    if (response.data.explanation) {
                        vscode.window.showInformationMessage(response.data.explanation);
                    }
                    this.updateCognitiveMemory('code_refactoring', { original: selectedText, refactored: response.data.refactored_code });
                    this.updateStatus("$(check) Code refactored", "Code refactoring completed successfully");
                }
                else {
                    throw new Error(response.error || 'Code refactoring failed');
                }
            }
            catch (error) {
                vscode.window.showErrorMessage(`Code refactoring failed: ${error}`);
                this.updateStatus("$(error) Refactoring failed", "Code refactoring failed");
            }
        });
    }
    explainCode() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }
            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);
            if (!selectedText) {
                vscode.window.showErrorMessage('Please select code to explain');
                return;
            }
            try {
                this.updateStatus("$(sync~spin) Explaining code...", "AI is analyzing the selected code");
                const response = yield this.makeAIRequest('/explain-code', 'POST', {
                    code: selectedText,
                    language: editor.document.languageId,
                    context: yield this.getEditorContext(),
                    cognitive_memory: this.cognitiveMemory
                });
                if (response.success && response.data.explanation) {
                    const panel = vscode.window.createWebviewPanel('sonaExplanation', 'Sona Code Explanation', vscode.ViewColumn.Beside, { enableScripts: true });
                    panel.webview.html = this.getExplanationHTML(response.data.explanation, selectedText);
                    this.updateCognitiveMemory('code_explanation', { code: selectedText, explanation: response.data.explanation });
                    this.updateStatus("$(check) Code explained", "Code explanation completed successfully");
                }
                else {
                    throw new Error(response.error || 'Code explanation failed');
                }
            }
            catch (error) {
                vscode.window.showErrorMessage(`Code explanation failed: ${error}`);
                this.updateStatus("$(error) Explanation failed", "Code explanation failed");
            }
        });
    }
    debugCode() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }
            const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);
            if (diagnostics.length === 0) {
                vscode.window.showInformationMessage('No issues found in the current file');
                return;
            }
            try {
                this.updateStatus("$(sync~spin) Debugging code...", "AI is analyzing code issues");
                const response = yield this.makeAIRequest('/debug-code', 'POST', {
                    code: editor.document.getText(),
                    language: editor.document.languageId,
                    diagnostics: diagnostics.map(d => ({
                        message: d.message,
                        line: d.range.start.line,
                        column: d.range.start.character,
                        severity: d.severity
                    })),
                    context: yield this.getEditorContext(),
                    cognitive_memory: this.cognitiveMemory
                });
                if (response.success && response.data.debug_suggestions) {
                    const panel = vscode.window.createWebviewPanel('sonaDebug', 'Sona Debug Assistant', vscode.ViewColumn.Beside, { enableScripts: true });
                    panel.webview.html = this.getDebugHTML(response.data.debug_suggestions, diagnostics);
                    this.updateCognitiveMemory('code_debugging', { diagnostics: diagnostics.length, suggestions: response.data.debug_suggestions });
                    this.updateStatus("$(check) Debug complete", "Code debugging completed successfully");
                }
                else {
                    throw new Error(response.error || 'Code debugging failed');
                }
            }
            catch (error) {
                vscode.window.showErrorMessage(`Code debugging failed: ${error}`);
                this.updateStatus("$(error) Debug failed", "Code debugging failed");
            }
        });
    }
    optimizeCode() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }
            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);
            if (!selectedText) {
                vscode.window.showErrorMessage('Please select code to optimize');
                return;
            }
            try {
                this.updateStatus("$(sync~spin) Optimizing code...", "AI is optimizing selected code");
                const response = yield this.makeAIRequest('/optimize-code', 'POST', {
                    code: selectedText,
                    language: editor.document.languageId,
                    optimization_type: 'performance',
                    context: yield this.getEditorContext(),
                    cognitive_memory: this.cognitiveMemory
                });
                if (response.success && response.data.optimized_code) {
                    const choice = yield vscode.window.showInformationMessage('Code optimization completed. Apply changes?', 'Apply', 'Show Diff', 'Cancel');
                    if (choice === 'Apply') {
                        yield editor.edit(editBuilder => {
                            editBuilder.replace(selection, response.data.optimized_code);
                        });
                    }
                    else if (choice === 'Show Diff') {
                        const diffPanel = vscode.window.createWebviewPanel('sonaDiff', 'Sona Code Optimization Diff', vscode.ViewColumn.Beside, { enableScripts: true });
                        diffPanel.webview.html = this.getDiffHTML(selectedText, response.data.optimized_code, response.data.explanation);
                    }
                    this.updateCognitiveMemory('code_optimization', { original: selectedText, optimized: response.data.optimized_code });
                    this.updateStatus("$(check) Code optimized", "Code optimization completed successfully");
                }
                else {
                    throw new Error(response.error || 'Code optimization failed');
                }
            }
            catch (error) {
                vscode.window.showErrorMessage(`Code optimization failed: ${error}`);
                this.updateStatus("$(error) Optimization failed", "Code optimization failed");
            }
        });
    }
    toggleFocusMode() {
        return __awaiter(this, void 0, void 0, function* () {
            this.cognitiveMemory.focusMode = !this.cognitiveMemory.focusMode;
            try {
                yield this.saveCognitiveMemory();
                const status = this.cognitiveMemory.focusMode ? 'enabled' : 'disabled';
                this.updateStatus(`$(eye) Focus mode ${status}`, `Cognitive focus mode ${status}`);
                vscode.window.showInformationMessage(`Sona focus mode ${status}`);
            }
            catch (error) {
                vscode.window.showErrorMessage(`Failed to toggle focus mode: ${error}`);
            }
        });
    }
    clearCognitiveMemory() {
        return __awaiter(this, void 0, void 0, function* () {
            const choice = yield vscode.window.showWarningMessage('Clear all cognitive memory? This action cannot be undone.', 'Clear', 'Cancel');
            if (choice === 'Clear') {
                this.cognitiveMemory = {
                    workingMemory: [],
                    focusMode: false,
                    cognitiveState: 'ready',
                    timestamp: Date.now()
                };
                try {
                    yield this.saveCognitiveMemory();
                    vscode.window.showInformationMessage('Cognitive memory cleared successfully');
                    this.updateStatus("$(check) Memory cleared", "Cognitive memory cleared");
                }
                catch (error) {
                    vscode.window.showErrorMessage(`Failed to clear cognitive memory: ${error}`);
                }
            }
        });
    }
    makeAIRequest(endpoint, method, data) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            const startTime = Date.now();
            try {
                const response = yield (0, axios_1.default)({
                    method,
                    url: `${this.config.aiRouterEndpoint}${endpoint}`,
                    data,
                    timeout: this.config.timeout,
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'Sona-VSCode-Extension/0.9.0'
                    }
                });
                return {
                    success: true,
                    data: response.data,
                    provider: response.headers['x-ai-provider'],
                    responseTime: Date.now() - startTime
                };
            }
            catch (error) {
                this.outputChannel.appendLine(`AI Router request failed: ${error.message}`);
                return {
                    success: false,
                    error: ((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.error) || error.message,
                    responseTime: Date.now() - startTime
                };
            }
        });
    }
    getEditorContext() {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor)
                return {};
            return {
                fileName: editor.document.fileName,
                languageId: editor.document.languageId,
                lineCount: editor.document.lineCount,
                cursorPosition: editor.selection.start,
                visibleRange: editor.visibleRanges[0]
            };
        });
    }
    insertCodeIntoEditor(code, explanation) {
        return __awaiter(this, void 0, void 0, function* () {
            const editor = vscode.window.activeTextEditor;
            if (!editor)
                return;
            yield editor.edit(editBuilder => {
                editBuilder.insert(editor.selection.start, code);
            });
            if (explanation) {
                vscode.window.showInformationMessage(explanation);
            }
        });
    }
    updateCognitiveMemory(action, data) {
        this.cognitiveMemory.workingMemory.push({
            action,
            data,
            timestamp: Date.now()
        });
        // Keep only last 50 memory items
        if (this.cognitiveMemory.workingMemory.length > 50) {
            this.cognitiveMemory.workingMemory = this.cognitiveMemory.workingMemory.slice(-50);
        }
        this.cognitiveMemory.timestamp = Date.now();
        this.saveCognitiveMemory();
    }
    saveCognitiveMemory() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield this.makeAIRequest('/cognitive-memory', 'POST', {
                    user_id: vscode.env.machineId,
                    memory_data: this.cognitiveMemory
                });
            }
            catch (error) {
                this.outputChannel.appendLine(`Failed to save cognitive memory: ${error}`);
            }
        });
    }
    updateStatus(text, tooltip) {
        this.statusBarItem.text = text;
        this.statusBarItem.tooltip = tooltip;
    }
    getExplanationHTML(explanation, code) {
        // UI adaptation for profile
        let font = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        let bg = '#f5f5f5';
        let color = '#007acc';
        if (this.userProfile === 'adhd') {
            font = "'Arial Black', 'Segoe UI', sans-serif";
            bg = '#fffbe6';
            color = '#ff9800';
        }
        else if (this.userProfile === 'dyslexia') {
            font = "'OpenDyslexic', 'Arial', sans-serif";
            bg = '#eaf6ff';
            color = '#005fa3';
        }
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Sona Code Explanation</title>
            <style>
                body { font-family: ${font}; margin: 20px; }
                .code-block { background: ${bg}; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .explanation { line-height: 1.6; }
                .header { color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1 class="header">🧠 Sona Code Explanation</h1>
            <h3>Selected Code:</h3>
            <div class="code-block"><pre><code>${code}</code></pre></div>
            <h3>Explanation:</h3>
            <div class="explanation">${explanation.replace(/\n/g, '<br>')}</div>
        </body>
        </html>`;
    }
    getDebugHTML(suggestions, diagnostics) {
        let font = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        let issueBg = '#fff3cd';
        let suggBg = '#d4edda';
        let color = '#007acc';
        if (this.userProfile === 'adhd') {
            font = "'Arial Black', 'Segoe UI', sans-serif";
            issueBg = '#ffe0b2';
            suggBg = '#ffe082';
            color = '#ff9800';
        }
        else if (this.userProfile === 'dyslexia') {
            font = "'OpenDyslexic', 'Arial', sans-serif";
            issueBg = '#eaf6ff';
            suggBg = '#c8e6c9';
            color = '#005fa3';
        }
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Sona Debug Assistant</title>
            <style>
                body { font-family: ${font}; margin: 20px; }
                .issue { background: ${issueBg}; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .suggestion { background: ${suggBg}; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .header { color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1 class="header">🔧 Sona Debug Assistant</h1>
            <h3>Issues Found:</h3>
            ${diagnostics.map(d => `
                <div class="issue">
                    <strong>Line ${d.range.start.line + 1}:</strong> ${d.message}
                </div>
            `).join('')}
            <h3>AI Suggestions:</h3>
            ${suggestions.map(s => `
                <div class="suggestion">
                    <strong>${s.title}:</strong> ${s.description}
                </div>
            `).join('')}
        </body>
        </html>`;
    }
    getDiffHTML(original, optimized, explanation) {
        let font = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        let bg = '#f5f5f5';
        let origBorder = '#dc3545';
        let optBorder = '#28a745';
        let color = '#007acc';
        if (this.userProfile === 'adhd') {
            font = "'Arial Black', 'Segoe UI', sans-serif";
            bg = '#fffbe6';
            origBorder = '#ff9800';
            optBorder = '#00bcd4';
            color = '#ff9800';
        }
        else if (this.userProfile === 'dyslexia') {
            font = "'OpenDyslexic', 'Arial', sans-serif";
            bg = '#eaf6ff';
            origBorder = '#005fa3';
            optBorder = '#43a047';
            color = '#005fa3';
        }
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Sona Code Optimization</title>
            <style>
                body { font-family: ${font}; margin: 20px; }
                .code-block { background: ${bg}; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .original { border-left: 4px solid ${origBorder}; }
                .optimized { border-left: 4px solid ${optBorder}; }
                .header { color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1 class="header">⚡ Sona Code Optimization</h1>
            <h3>Original Code:</h3>
            <div class="code-block original"><pre><code>${original}</code></pre></div>
            <h3>Optimized Code:</h3>
            <div class="code-block optimized"><pre><code>${optimized}</code></pre></div>
            <h3>Optimization Explanation:</h3>
            <div>${explanation.replace(/\n/g, '<br>')}</div>
        </body>
        </html>`;
    }
    dispose() {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
    }
}
exports.SonaAIIntegration = SonaAIIntegration;
// Export for use in extension activation
function activate(context) {
    const sonaAI = new SonaAIIntegration(context);
    context.subscriptions.push(sonaAI);
    // Register additional commands for better discoverability
    context.subscriptions.push(vscode.commands.registerCommand('sona.welcome', () => sonaAI.selectUserProfile()), vscode.commands.registerCommand('sona.help', () => {
        vscode.window.showInformationMessage('Sona v0.9.0 Commands:\n• Generate Code\n• Refactor Code\n• Explain Code\n• Debug Code\n• Optimize Code\n• Toggle Focus Mode\n• Select UI Profile', 'Open Documentation', 'Change Profile').then(choice => {
            if (choice === 'Change Profile') {
                sonaAI.selectUserProfile();
            }
            else if (choice === 'Open Documentation') {
                vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona'));
            }
        });
    }));
}
exports.activate = activate;
function deactivate() {
    // Cleanup handled by dispose methods
}
exports.deactivate = deactivate;
//# sourceMappingURL=aiIntegration.js.map