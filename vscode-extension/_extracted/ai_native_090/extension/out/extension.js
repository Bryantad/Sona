"use strict";
// Main extension entry point for Sona VS Code Extension
// Handles activation and provides comprehensive AI-powered development support
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const aiIntegration_1 = require("./aiIntegration");
function activate(context) {
    console.log('🚀 Sona v0.9.0 Extension is now active!');
    // Activate AI integration
    (0, aiIntegration_1.activate)(context);
    // Show welcome message for first-time users
    const hasShownWelcome = context.globalState.get('sonaWelcomeShown');
    if (!hasShownWelcome) {
        setTimeout(() => {
            vscode.window.showInformationMessage('🎉 Welcome to Sona v0.9.0! The AI-native programming language with cognitive accessibility features.', 'Get Started', 'Learn More').then(choice => {
                if (choice === 'Get Started') {
                    vscode.commands.executeCommand('sona.welcome');
                }
                else if (choice === 'Learn More') {
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
    (0, aiIntegration_1.deactivate)();
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map