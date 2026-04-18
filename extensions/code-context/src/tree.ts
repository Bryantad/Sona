import * as path from 'path';
import * as vscode from 'vscode';
import { isStale } from './decorations';
import { ContextNotesStorage } from './storage';
import { ContextNote } from './types';

export class ContextNoteItem extends vscode.TreeItem {
    constructor(public readonly note: ContextNote) {
        super(note.category, vscode.TreeItemCollapsibleState.None);

        const preview = note.note.length > 50 ? `${note.note.substring(0, 50)}...` : note.note;
        this.description = preview;
        this.tooltip = new vscode.MarkdownString(`**${note.category}**\n\n${note.note}\n\n---\n*${note.filePath}:${note.lineStart + 1}*`);
        this.command = {
            command: 'codeContext.goToNote',
            title: 'Go to Note',
            arguments: [note]
        };
        this.contextValue = isStale(note) ? 'staleNote' : 'note';
        this.iconPath = new vscode.ThemeIcon(isStale(note) ? 'warning' : 'comment');
    }
}

export class FileNoteItem extends vscode.TreeItem {
    constructor(public readonly filePath: string, public readonly notes: ContextNote[]) {
        super(path.basename(filePath), vscode.TreeItemCollapsibleState.Expanded);
        this.description = `${notes.length} note${notes.length > 1 ? 's' : ''}`;
        this.tooltip = filePath;
        this.iconPath = vscode.ThemeIcon.File;
        this.resourceUri = vscode.Uri.file(filePath);
    }
}

export class ContextNotesTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private readonly onDidChangeTreeDataEmitter = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this.onDidChangeTreeDataEmitter.event;

    constructor(private readonly storage: ContextNotesStorage) {}

    refresh(): void {
        this.onDidChangeTreeDataEmitter.fire();
    }

    getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: vscode.TreeItem): vscode.TreeItem[] {
        if (!element) {
            const notesByFile = new Map<string, ContextNote[]>();
            for (const note of this.storage.getAllNotes()) {
                const existing = notesByFile.get(note.filePath) || [];
                existing.push(note);
                notesByFile.set(note.filePath, existing);
            }

            if (notesByFile.size === 0) {
                return [new vscode.TreeItem('No context notes yet', vscode.TreeItemCollapsibleState.None)];
            }

            return Array.from(notesByFile.entries()).map(([filePath, notes]) => new FileNoteItem(filePath, notes));
        }

        if (element instanceof FileNoteItem) {
            return element.notes.map((note) => new ContextNoteItem(note));
        }

        return [];
    }
}
