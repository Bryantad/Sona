import * as vscode from 'vscode';
import { registerCommands } from './commands';
import { createStatusBar, updateDecorations, updateStatusBar } from './decorations';
import { ContextHoverProvider } from './hover';
import { ContextNotesStorage } from './storage';
import { ContextNotesTreeProvider } from './tree';

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    const storage = new ContextNotesStorage(context);
    await storage.load();

    const treeProvider = new ContextNotesTreeProvider(storage);
    const statusBarItem = createStatusBar();

    context.subscriptions.push(statusBarItem);
    context.subscriptions.push(vscode.window.registerTreeDataProvider('codeContextNotes', treeProvider));
    context.subscriptions.push(vscode.languages.registerHoverProvider({ scheme: 'file' }, new ContextHoverProvider(storage)));

    registerCommands(context, storage, treeProvider, statusBarItem);

    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor) {
                updateDecorations(editor, storage);
                updateStatusBar(storage, statusBarItem);
            } else {
                statusBarItem.hide();
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
            const editor = vscode.window.activeTextEditor;
            if (editor && event.document === editor.document) {
                setTimeout(() => {
                    updateDecorations(editor, storage);
                    updateStatusBar(storage, statusBarItem);
                }, 300);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('codeContext')) {
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    updateDecorations(editor, storage);
                    updateStatusBar(storage, statusBarItem);
                }
                treeProvider.refresh();
            }
        })
    );

    if (vscode.window.activeTextEditor) {
        updateDecorations(vscode.window.activeTextEditor, storage);
        updateStatusBar(storage, statusBarItem);
    }

    console.log('Code Context extension activated');
}

export function deactivate(): void {}