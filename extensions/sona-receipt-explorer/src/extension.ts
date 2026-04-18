import * as vscode from 'vscode';
import { ReceiptTreeDataProvider } from './tree';
import { registerCommands } from './commands';

export function activate(context: vscode.ExtensionContext): void {
    const output = vscode.window.createOutputChannel('Sona Receipt Explorer');
    const treeDataProvider = new ReceiptTreeDataProvider(output);
    const treeView = vscode.window.createTreeView('sonaReceipts', {
        treeDataProvider,
        showCollapseAll: true
    });

    context.subscriptions.push(output, treeView, treeDataProvider);

    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('sonaReceipts')) {
                treeDataProvider.refresh();
            }
        })
    );

    registerCommands(context, treeDataProvider, treeView, output);
}

export function deactivate(): void {
    // no-op
}
