import * as vscode from 'vscode';
import { createHoverContent } from './decorations';
import { ContextNotesStorage } from './storage';

export class ContextHoverProvider implements vscode.HoverProvider {
    constructor(private readonly storage: ContextNotesStorage) {}

    provideHover(document: vscode.TextDocument, position: vscode.Position): vscode.Hover | undefined {
        const config = vscode.workspace.getConfiguration('codeContext');
        if (!config.get<boolean>('showHoverNotes', true)) {
            return undefined;
        }

        const note = this.storage.getNoteAtLine(document.uri.fsPath, position.line);
        if (!note) {
            return undefined;
        }

        return new vscode.Hover(createHoverContent(note));
    }
}
