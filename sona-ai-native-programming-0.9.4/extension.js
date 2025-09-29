const vscode = require('vscode');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Sona AI-Native Programming Language extension is now active!');
    
    // Register a command
    let disposable = vscode.commands.registerCommand('sona.helloWorld', function () {
        vscode.window.showInformationMessage('Hello from Sona AI-Native Programming Language!');
    });
    
    context.subscriptions.push(disposable);
    
    // Language server features would be implemented here
    // For now, providing basic language support through package.json contributions
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};