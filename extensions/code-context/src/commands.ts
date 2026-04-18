import * as path from 'path';
import * as vscode from 'vscode';
import { getRelativeTime, updateDecorations, updateStatusBar } from './decorations';
import { getNearbyCommit } from './git';
import { ContextNotesStorage } from './storage';
import { ContextNotesTreeProvider } from './tree';
import { ContextNote, ReasonType } from './types';

function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

export async function addNote(
    storage: ContextNotesStorage,
    treeProvider: ContextNotesTreeProvider,
    statusBarItem: vscode.StatusBarItem
): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('Select code to add a context note');
        return;
    }

    const config = vscode.workspace.getConfiguration('codeContext');
    const categories = config.get<string[]>('noteCategories', [
        '💡 Decision',
        '🐛 Bug Fix',
        '⚠️ Temporary',
        '🔄 Refactor',
        '📝 Note'
    ]);

    const category = await vscode.window.showQuickPick(categories, {
        placeHolder: 'What type of context is this?'
    });
    if (!category) {
        return;
    }

    const reasonTypes: Array<{ label: string; value: ReasonType; description: string }> = [
        { label: '$(dash) None', value: 'NONE', description: 'No special classification' },
        { label: '$(clock) TEMP', value: 'TEMP', description: 'Temporary code to be removed' },
        { label: '$(tools) WORKAROUND', value: 'WORKAROUND', description: 'Workaround for a known issue' },
        { label: '$(shield) SECURITY', value: 'SECURITY', description: 'Security-related decision' },
        { label: '$(zap) PERFORMANCE', value: 'PERFORMANCE', description: 'Performance optimization' },
        { label: '$(archive) LEGACY', value: 'LEGACY', description: 'Legacy code kept for compatibility' }
    ];

    const reasonPick = await vscode.window.showQuickPick(reasonTypes, {
        placeHolder: 'Optional: Add a reason type (or press Escape to skip)'
    });

    const noteText = await vscode.window.showInputBox({
        prompt: 'Why does this code exist?',
        placeHolder: 'e.g., "Temporary fix for production bug #431"',
        validateInput: (value) => (value.trim() ? null : 'Note cannot be empty')
    });
    if (!noteText) {
        return;
    }

    const note: ContextNote = {
        id: generateId(),
        filePath: editor.document.uri.fsPath,
        lineStart: selection.start.line,
        lineEnd: selection.end.line,
        codeSnippet: editor.document.getText(selection).substring(0, 500),
        note: noteText,
        category,
        reasonType: reasonPick?.value || 'NONE',
        nearCommit: getNearbyCommit(editor.document.uri.fsPath, selection.start.line),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };

    storage.addNote(note);
    updateDecorations(editor, storage);
    treeProvider.refresh();
    updateStatusBar(storage, statusBarItem);
    vscode.window.showInformationMessage(`💭 Context note added: "${noteText.substring(0, 30)}..."`);
}

export async function editNote(
    storage: ContextNotesStorage,
    treeProvider: ContextNotesTreeProvider,
    noteId?: string
): Promise<void> {
    let note: ContextNote | undefined;

    if (noteId) {
        note = storage.getAllNotes().find((entry) => entry.id === noteId);
    } else {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            note = storage.getNoteAtLine(editor.document.uri.fsPath, editor.selection.active.line);
        }
    }

    if (!note) {
        vscode.window.showWarningMessage('No context note found at this location');
        return;
    }

    const newText = await vscode.window.showInputBox({
        prompt: 'Edit context note',
        value: note.note,
        validateInput: (value) => (value.trim() ? null : 'Note cannot be empty')
    });
    if (!newText) {
        return;
    }

    note.note = newText;
    note.updatedAt = new Date().toISOString();
    storage.updateNote(note);

    const editor = vscode.window.activeTextEditor;
    if (editor) {
        updateDecorations(editor, storage);
    }
    treeProvider.refresh();
    vscode.window.showInformationMessage('Context note updated');
}

export async function deleteNote(
    storage: ContextNotesStorage,
    treeProvider: ContextNotesTreeProvider,
    noteId?: string
): Promise<void> {
    let note: ContextNote | undefined;

    if (noteId) {
        note = storage.getAllNotes().find((entry) => entry.id === noteId);
    } else {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            note = storage.getNoteAtLine(editor.document.uri.fsPath, editor.selection.active.line);
        }
    }

    if (!note) {
        vscode.window.showWarningMessage('No context note found');
        return;
    }

    const confirm = await vscode.window.showWarningMessage(
        `Delete context note: "${note.note.substring(0, 50)}..."?`,
        { modal: true },
        'Delete'
    );
    if (confirm !== 'Delete') {
        return;
    }

    storage.deleteNote(note.id);

    const editor = vscode.window.activeTextEditor;
    if (editor) {
        updateDecorations(editor, storage);
    }
    treeProvider.refresh();
    vscode.window.showInformationMessage('Context note deleted');
}

export async function showAllNotes(storage: ContextNotesStorage): Promise<void> {
    const notes = storage.getAllNotes();
    if (notes.length === 0) {
        vscode.window.showInformationMessage('No context notes in this workspace');
        return;
    }

    const items = notes.map((note) => ({
        label: note.category,
        description: note.note.substring(0, 60),
        detail: `${path.basename(note.filePath)}:${note.lineStart + 1}`,
        note
    }));

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: `${notes.length} context note${notes.length > 1 ? 's' : ''} in workspace`
    });

    if (selected) {
        await goToNote(selected.note);
    }
}

export async function goToNote(note: ContextNote): Promise<void> {
    const uri = vscode.Uri.file(note.filePath);
    const document = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(document);

    const line = Math.min(note.lineStart, document.lineCount - 1);
    const range = new vscode.Range(line, 0, line, 0);
    editor.selection = new vscode.Selection(range.start, range.end);
    editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
}

export async function exportNotes(storage: ContextNotesStorage): Promise<void> {
    const notes = storage.getAllNotes();
    if (notes.length === 0) {
        vscode.window.showInformationMessage('No context notes to export');
        return;
    }

    let markdown = '# Code Context Notes\n\n';
    markdown += `*Exported on ${new Date().toLocaleDateString()}*\n\n`;
    markdown += '---\n\n';

    const byFile = new Map<string, ContextNote[]>();
    for (const note of notes) {
        const existing = byFile.get(note.filePath) || [];
        existing.push(note);
        byFile.set(note.filePath, existing);
    }

    for (const [filePath, fileNotes] of byFile.entries()) {
        markdown += `## ${path.basename(filePath)}\n\n`;
        markdown += `*${filePath}*\n\n`;

        for (const note of fileNotes) {
            markdown += `### ${note.category} (Line ${note.lineStart + 1})\n\n`;
            markdown += `${note.note}\n\n`;
            markdown += '```\n';
            markdown += `${note.codeSnippet}\n`;
            markdown += '```\n\n';
            markdown += `*Added: ${new Date(note.createdAt).toLocaleDateString()}*\n\n`;
            markdown += '---\n\n';
        }
    }

    const uri = await vscode.window.showSaveDialog({
        defaultUri: vscode.Uri.file('code-context-notes.md'),
        filters: { Markdown: ['md'] }
    });
    if (!uri) {
        return;
    }

    await vscode.workspace.fs.writeFile(uri, Buffer.from(markdown, 'utf8'));
    vscode.window.showInformationMessage(`Exported ${notes.length} notes to ${path.basename(uri.fsPath)}`);
}

export async function clearStaleNotes(
    storage: ContextNotesStorage,
    treeProvider: ContextNotesTreeProvider
): Promise<void> {
    const config = vscode.workspace.getConfiguration('codeContext');
    const staleDays = config.get<number>('staleAfterDays', 30);
    const staleNotes = storage.getStaleNotes(staleDays);

    if (staleNotes.length === 0) {
        vscode.window.showInformationMessage('No stale notes found');
        return;
    }

    const confirm = await vscode.window.showWarningMessage(
        `Delete ${staleNotes.length} stale note${staleNotes.length > 1 ? 's' : ''} (older than ${staleDays} days)?`,
        { modal: true },
        'Delete All',
        'Review First'
    );

    if (confirm === 'Review First') {
        const items = staleNotes.map((note) => ({
            label: note.category,
            description: note.note.substring(0, 60),
            detail: `${path.basename(note.filePath)} - ${getRelativeTime(new Date(note.createdAt))}`,
            picked: true,
            note
        }));

        const selected = await vscode.window.showQuickPick(items, {
            canPickMany: true,
            placeHolder: 'Select notes to delete'
        });

        if (selected && selected.length > 0) {
            for (const item of selected) {
                storage.deleteNote(item.note.id);
            }
            treeProvider.refresh();
            vscode.window.showInformationMessage(`Deleted ${selected.length} stale note${selected.length > 1 ? 's' : ''}`);
        }
        return;
    }

    if (confirm === 'Delete All') {
        for (const note of staleNotes) {
            storage.deleteNote(note.id);
        }
        treeProvider.refresh();
        vscode.window.showInformationMessage(`Deleted ${staleNotes.length} stale note${staleNotes.length > 1 ? 's' : ''}`);
    }
}

export function registerCommands(
    context: vscode.ExtensionContext,
    storage: ContextNotesStorage,
    treeProvider: ContextNotesTreeProvider,
    statusBarItem: vscode.StatusBarItem
): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('codeContext.addNote', () => addNote(storage, treeProvider, statusBarItem)),
        vscode.commands.registerCommand('codeContext.viewNote', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            const note = storage.getNoteAtLine(editor.document.uri.fsPath, editor.selection.active.line);
            if (note) {
                void vscode.window.showInformationMessage(`${note.category}: ${note.note}`);
            } else {
                void vscode.window.showInformationMessage('No context note at this line');
            }
        }),
        vscode.commands.registerCommand('codeContext.editNote', (noteId?: string) => editNote(storage, treeProvider, noteId)),
        vscode.commands.registerCommand('codeContext.deleteNote', (noteId?: string) => deleteNote(storage, treeProvider, noteId)),
        vscode.commands.registerCommand('codeContext.showAllNotes', () => showAllNotes(storage)),
        vscode.commands.registerCommand('codeContext.goToNote', (note: ContextNote) => goToNote(note)),
        vscode.commands.registerCommand('codeContext.exportNotes', () => exportNotes(storage)),
        vscode.commands.registerCommand('codeContext.clearStaleNotes', () => clearStaleNotes(storage, treeProvider))
    );
}
