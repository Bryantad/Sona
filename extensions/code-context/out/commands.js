"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.addNote = addNote;
exports.editNote = editNote;
exports.deleteNote = deleteNote;
exports.showAllNotes = showAllNotes;
exports.goToNote = goToNote;
exports.exportNotes = exportNotes;
exports.clearStaleNotes = clearStaleNotes;
exports.registerCommands = registerCommands;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const decorations_1 = require("./decorations");
const git_1 = require("./git");
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}
async function addNote(storage, treeProvider, statusBarItem) {
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
    const categories = config.get('noteCategories', [
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
    const reasonTypes = [
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
    const note = {
        id: generateId(),
        filePath: editor.document.uri.fsPath,
        lineStart: selection.start.line,
        lineEnd: selection.end.line,
        codeSnippet: editor.document.getText(selection).substring(0, 500),
        note: noteText,
        category,
        reasonType: reasonPick?.value || 'NONE',
        nearCommit: (0, git_1.getNearbyCommit)(editor.document.uri.fsPath, selection.start.line),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    storage.addNote(note);
    (0, decorations_1.updateDecorations)(editor, storage);
    treeProvider.refresh();
    (0, decorations_1.updateStatusBar)(storage, statusBarItem);
    vscode.window.showInformationMessage(`💭 Context note added: "${noteText.substring(0, 30)}..."`);
}
async function editNote(storage, treeProvider, noteId) {
    let note;
    if (noteId) {
        note = storage.getAllNotes().find((entry) => entry.id === noteId);
    }
    else {
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
        (0, decorations_1.updateDecorations)(editor, storage);
    }
    treeProvider.refresh();
    vscode.window.showInformationMessage('Context note updated');
}
async function deleteNote(storage, treeProvider, noteId) {
    let note;
    if (noteId) {
        note = storage.getAllNotes().find((entry) => entry.id === noteId);
    }
    else {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            note = storage.getNoteAtLine(editor.document.uri.fsPath, editor.selection.active.line);
        }
    }
    if (!note) {
        vscode.window.showWarningMessage('No context note found');
        return;
    }
    const confirm = await vscode.window.showWarningMessage(`Delete context note: "${note.note.substring(0, 50)}..."?`, { modal: true }, 'Delete');
    if (confirm !== 'Delete') {
        return;
    }
    storage.deleteNote(note.id);
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        (0, decorations_1.updateDecorations)(editor, storage);
    }
    treeProvider.refresh();
    vscode.window.showInformationMessage('Context note deleted');
}
async function showAllNotes(storage) {
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
async function goToNote(note) {
    const uri = vscode.Uri.file(note.filePath);
    const document = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(document);
    const line = Math.min(note.lineStart, document.lineCount - 1);
    const range = new vscode.Range(line, 0, line, 0);
    editor.selection = new vscode.Selection(range.start, range.end);
    editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
}
async function exportNotes(storage) {
    const notes = storage.getAllNotes();
    if (notes.length === 0) {
        vscode.window.showInformationMessage('No context notes to export');
        return;
    }
    let markdown = '# Code Context Notes\n\n';
    markdown += `*Exported on ${new Date().toLocaleDateString()}*\n\n`;
    markdown += '---\n\n';
    const byFile = new Map();
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
async function clearStaleNotes(storage, treeProvider) {
    const config = vscode.workspace.getConfiguration('codeContext');
    const staleDays = config.get('staleAfterDays', 30);
    const staleNotes = storage.getStaleNotes(staleDays);
    if (staleNotes.length === 0) {
        vscode.window.showInformationMessage('No stale notes found');
        return;
    }
    const confirm = await vscode.window.showWarningMessage(`Delete ${staleNotes.length} stale note${staleNotes.length > 1 ? 's' : ''} (older than ${staleDays} days)?`, { modal: true }, 'Delete All', 'Review First');
    if (confirm === 'Review First') {
        const items = staleNotes.map((note) => ({
            label: note.category,
            description: note.note.substring(0, 60),
            detail: `${path.basename(note.filePath)} - ${(0, decorations_1.getRelativeTime)(new Date(note.createdAt))}`,
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
function registerCommands(context, storage, treeProvider, statusBarItem) {
    context.subscriptions.push(vscode.commands.registerCommand('codeContext.addNote', () => addNote(storage, treeProvider, statusBarItem)), vscode.commands.registerCommand('codeContext.viewNote', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }
        const note = storage.getNoteAtLine(editor.document.uri.fsPath, editor.selection.active.line);
        if (note) {
            void vscode.window.showInformationMessage(`${note.category}: ${note.note}`);
        }
        else {
            void vscode.window.showInformationMessage('No context note at this line');
        }
    }), vscode.commands.registerCommand('codeContext.editNote', (noteId) => editNote(storage, treeProvider, noteId)), vscode.commands.registerCommand('codeContext.deleteNote', (noteId) => deleteNote(storage, treeProvider, noteId)), vscode.commands.registerCommand('codeContext.showAllNotes', () => showAllNotes(storage)), vscode.commands.registerCommand('codeContext.goToNote', (note) => goToNote(note)), vscode.commands.registerCommand('codeContext.exportNotes', () => exportNotes(storage)), vscode.commands.registerCommand('codeContext.clearStaleNotes', () => clearStaleNotes(storage, treeProvider)));
}
//# sourceMappingURL=commands.js.map