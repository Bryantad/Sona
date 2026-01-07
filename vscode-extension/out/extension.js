"use strict";
// Main extension entry point for Sona VS Code Extension v1.0.0
// Provides comprehensive integration with local Sona CLI installation
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const sonaCliIntegration_1 = require("./sonaCliIntegration");
const lspClient_1 = require("./lspClient");
function shouldStartLsp(doc) {
    return !!doc && doc.languageId === 'sona';
}
function activate(context) {
    console.log('🚀 Sona v1.0.0 Extension is now active!');
    // Activate CLI integration
    (0, sonaCliIntegration_1.activate)(context);
    // Start Language Server (LSP) lazily for .sona files
    const maybeStart = () => {
        var _a;
        const active = (_a = vscode.window.activeTextEditor) === null || _a === void 0 ? void 0 : _a.document;
        if (shouldStartLsp(active)) {
            (0, lspClient_1.startSonaLsp)(context);
        }
    };
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => maybeStart()));
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(() => maybeStart()));
    maybeStart();
    // Show welcome message for first-time users
    const hasShownWelcome = context.globalState.get('sonaWelcomeShown');
    if (!hasShownWelcome) {
        setTimeout(() => {
            vscode.window.showInformationMessage('🎉 Welcome to Sona v1.0.0! The AI-native programming language is ready to use.', 'Get Started', 'Documentation').then(choice => {
                if (choice === 'Get Started') {
                    vscode.commands.executeCommand('sona.welcome');
                }
                else if (choice === 'Documentation') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona'));
                }
            });
            context.globalState.update('sonaWelcomeShown', true);
        }, 1500);
    }
}
exports.activate = activate;
function deactivate() {
    console.log('👋 Sona Extension deactivated');
    (0, sonaCliIntegration_1.deactivate)();
    void (0, lspClient_1.stopSonaLsp)();
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map