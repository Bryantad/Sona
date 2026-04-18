import * as vscode from 'vscode';
import { ContextNote, ReasonType } from './types';
import { ContextNotesStorage } from './storage';

const noteDecorationType = vscode.window.createTextEditorDecorationType({
    backgroundColor: new vscode.ThemeColor('codeContext.noteBackground'),
    isWholeLine: true,
    overviewRulerColor: '#FFD700',
    overviewRulerLane: vscode.OverviewRulerLane.Right
});

const markerDecorationType = vscode.window.createTextEditorDecorationType({
    after: {
        margin: '0 0 0 1em',
        color: new vscode.ThemeColor('editorCodeLens.foreground')
    }
});

export function createStatusBar(): vscode.StatusBarItem {
    const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    item.command = 'codeContext.showAllNotes';
    item.tooltip = 'Context notes in this file (click to view all)';
    return item;
}

export function updateStatusBar(storage: ContextNotesStorage, statusBarItem: vscode.StatusBarItem): void {
    const config = vscode.workspace.getConfiguration('codeContext');
    if (!config.get<boolean>('showStatusBarIndicator', true)) {
        statusBarItem.hide();
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        statusBarItem.hide();
        return;
    }

    const notes = storage.getNotesForFile(editor.document.uri.fsPath);
    const staleCount = notes.filter((note) => isStale(note)).length;

    if (notes.length === 0) {
        statusBarItem.hide();
        return;
    }

    let text = `💭 ${notes.length}`;
    if (staleCount > 0) {
        text += ` (⚠️ ${staleCount} stale)`;
    }

    statusBarItem.text = text;
    statusBarItem.tooltip = `${notes.length} context note${notes.length > 1 ? 's' : ''} in this file${staleCount > 0 ? ` (${staleCount} stale)` : ''}`;
    statusBarItem.show();
}

export function updateDecorations(editor: vscode.TextEditor, storage: ContextNotesStorage): void {
    const config = vscode.workspace.getConfiguration('codeContext');
    const showMarkers = config.get<boolean>('showInlineMarkers', true);
    const markerStyle = config.get<string>('markerStyle', 'emoji');
    const notes = storage.getNotesForFile(editor.document.uri.fsPath);

    if (notes.length === 0) {
        editor.setDecorations(noteDecorationType, []);
        editor.setDecorations(markerDecorationType, []);
        return;
    }

    const lineDecorations: vscode.DecorationOptions[] = [];
    const markerDecorations: vscode.DecorationOptions[] = [];

    for (const note of notes) {
        if (note.lineStart >= editor.document.lineCount) {
            continue;
        }

        const startLine = Math.min(note.lineStart, editor.document.lineCount - 1);
        const endLine = Math.min(note.lineEnd, editor.document.lineCount - 1);
        const range = new vscode.Range(startLine, 0, endLine, Number.MAX_VALUE);

        lineDecorations.push({
            range,
            hoverMessage: createHoverContent(note)
        });

        if (showMarkers) {
            markerDecorations.push({
                range: new vscode.Range(startLine, Number.MAX_VALUE, startLine, Number.MAX_VALUE),
                renderOptions: {
                    after: {
                        contentText: getMarkerText(markerStyle, note.category),
                        fontStyle: 'italic'
                    }
                }
            });
        }
    }

    editor.setDecorations(noteDecorationType, lineDecorations);
    editor.setDecorations(markerDecorationType, markerDecorations);
}

export function createHoverContent(note: ContextNote): vscode.MarkdownString {
    const md = new vscode.MarkdownString();
    md.isTrusted = true;
    md.supportHtml = true;

    const age = getRelativeTime(new Date(note.createdAt));
    const ageDays = getAgeDays(note);
    const reasonLabel = getReasonTypeLabel(note.reasonType);

    let staleWarning = '';
    if (isStale(note)) {
        staleWarning = `\n\n⚠️ *This decision is ${ageDays} days old*`;
    }

    md.appendMarkdown(`### ${note.category}\n\n`);
    if (reasonLabel) {
        md.appendMarkdown(`\`${reasonLabel}\`\n\n`);
    }
    md.appendMarkdown(`${note.note}\n\n`);
    md.appendMarkdown('---\n');

    let footer = `*Added ${age}*`;
    if (note.nearCommit) {
        footer += ` · near commit \`${note.nearCommit}\``;
    }
    md.appendMarkdown(`${footer}${staleWarning}\n\n`);
    md.appendMarkdown(`[Edit](command:codeContext.editNote?${encodeURIComponent(JSON.stringify(note.id))}) · `);
    md.appendMarkdown(`[Delete](command:codeContext.deleteNote?${encodeURIComponent(JSON.stringify(note.id))})`);

    return md;
}

function getMarkerText(style: string, category: string): string {
    switch (style) {
        case 'emoji':
            return `💭 ${category}`;
        case 'icon':
            return `[i] ${category}`;
        case 'subtle':
            return `· ${category}`;
        default:
            return `💭 ${category}`;
    }
}

export function getRelativeTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
        return 'today';
    }
    if (diffDays === 1) {
        return 'yesterday';
    }
    if (diffDays < 7) {
        return `${diffDays} days ago`;
    }
    if (diffDays < 30) {
        return `${Math.floor(diffDays / 7)} weeks ago`;
    }
    if (diffDays < 365) {
        return `${Math.floor(diffDays / 30)} months ago`;
    }
    return `${Math.floor(diffDays / 365)} years ago`;
}

export function isStale(note: ContextNote): boolean {
    const config = vscode.workspace.getConfiguration('codeContext');
    const staleDays = config.get<number>('staleAfterDays', 30);
    if (staleDays <= 0) {
        return false;
    }

    const threshold = Date.now() - staleDays * 24 * 60 * 60 * 1000;
    return new Date(note.createdAt).getTime() < threshold;
}

export function getAgeDays(note: ContextNote): number {
    const diffMs = Date.now() - new Date(note.createdAt).getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

export function getReasonTypeLabel(reasonType?: ReasonType): string {
    if (!reasonType || reasonType === 'NONE') {
        return '';
    }

    const labels: Record<ReasonType, string> = {
        TEMP: '⏳ TEMP',
        WORKAROUND: '🔧 WORKAROUND',
        SECURITY: '🔒 SECURITY',
        PERFORMANCE: '⚡ PERFORMANCE',
        LEGACY: '📦 LEGACY',
        NONE: ''
    };

    return labels[reasonType];
}
