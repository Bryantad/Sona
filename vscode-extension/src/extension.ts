// Main extension entry point for Sona VS Code Extension v1.0.0
// Provides comprehensive integration with local Sona CLI installation

import * as vscode from 'vscode';
import { activate as activateCli, deactivate as deactivateCli } from './sonaCliIntegration';
import { startSonaLsp, stopSonaLsp } from './lspClient';

function shouldStartLsp(doc?: vscode.TextDocument): boolean {
    return !!doc && doc.languageId === 'sona';
}

export function activate(context: vscode.ExtensionContext) {
    console.log('🚀 Sona v1.0.0 Extension is now active!');
    
    // Activate CLI integration
    activateCli(context);

    // Start Language Server (LSP) lazily for .sona files
    const maybeStart = () => {
        const active = vscode.window.activeTextEditor?.document;
        if (shouldStartLsp(active)) {
            startSonaLsp(context);
        }
    };

    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => maybeStart()));
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(() => maybeStart()));
    maybeStart();
    
    // Show welcome message for first-time users
    const hasShownWelcome = context.globalState.get<boolean>('sonaWelcomeShown');
    if (!hasShownWelcome) {
        setTimeout(() => {
        vscode.window.showInformationMessage(
            '🎉 Welcome to Sona v1.0.0! The AI-native programming language is ready to use.',
                'Get Started',
                'Documentation'
            ).then(choice => {
                if (choice === 'Get Started') {
                    vscode.commands.executeCommand('sona.welcome');
                } else if (choice === 'Documentation') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/Bryantad/Sona'));
                }
            });
            
            context.globalState.update('sonaWelcomeShown', true);
        }, 1500);
    }
}

export function deactivate() {
    console.log('👋 Sona Extension deactivated');
    deactivateCli();
    void stopSonaLsp();
}
