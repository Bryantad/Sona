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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const STORAGE_KEY = 'decisionPointTracker.v1';
function genId() {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
function activate(context) {
    const iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'decision.svg');
    const deco = vscode.window.createTextEditorDecorationType({
        gutterIconPath: iconPath,
        gutterIconSize: 'contain',
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    });
    context.subscriptions.push(deco);
    const promptStatus = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
    promptStatus.text = '🧭 Decision point?';
    promptStatus.tooltip = 'Click to tag the last significant edit as a decision point';
    promptStatus.command = 'decisionPointTracker.confirmPending';
    context.subscriptions.push(promptStatus);
    let enabled = vscode.workspace.getConfiguration('decisionPointTracker').get('enabled', true);
    let points = context.workspaceState.get(STORAGE_KEY, []);
    let pending;
    let lastPromptAt = 0;
    function persist() {
        return context.workspaceState.update(STORAGE_KEY, points);
    }
    function render(editor) {
        if (!enabled) {
            for (const e of vscode.window.visibleTextEditors) {
                e.setDecorations(deco, []);
            }
            promptStatus.hide();
            return;
        }
        const editors = editor ? [editor] : vscode.window.visibleTextEditors;
        for (const e of editors) {
            const key = e.document.uri.toString();
            const related = points.filter(p => p.uri === key);
            e.setDecorations(deco, related.map(p => {
                const range = new vscode.Range(p.line, 0, p.line, e.document.lineAt(p.line).text.length);
                const hover = new vscode.MarkdownString([`**Decision Point**`, '', p.reason ?? '_No reason provided_', '', `Created: ${new Date(p.createdAt).toLocaleString()}`].join('\n'));
                return { range, hoverMessage: hover };
            }));
        }
        if (pending)
            promptStatus.show();
        else
            promptStatus.hide();
    }
    function maybeSetPending(doc, line, summary) {
        const now = Date.now();
        if (now - lastPromptAt < 15_000)
            return;
        lastPromptAt = now;
        pending = { uri: doc.uri.toString(), line, summary, createdAt: now };
        render(vscode.window.activeTextEditor);
    }
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('decisionPointTracker')) {
            const cfg = vscode.workspace.getConfiguration('decisionPointTracker');
            enabled = cfg.get('enabled', true);
            render();
        }
    }));
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(e => render(e ?? undefined)));
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(e => {
        if (!enabled)
            return;
        if (e.document.isUntitled)
            return;
        if (!vscode.window.activeTextEditor)
            return;
        if (vscode.window.activeTextEditor.document.uri.toString() !== e.document.uri.toString())
            return;
        const cfg = vscode.workspace.getConfiguration('decisionPointTracker');
        const minChars = cfg.get('minChangedChars', 80);
        const minLines = cfg.get('minChangedLines', 4);
        let changedChars = 0;
        let changedLines = 0;
        let firstLine = Number.MAX_SAFE_INTEGER;
        for (const c of e.contentChanges) {
            changedChars += c.text.length + c.rangeLength;
            changedLines += Math.abs(c.text.split(/\r\n|\r|\n/).length - 1 - (c.range.end.line - c.range.start.line));
            firstLine = Math.min(firstLine, c.range.start.line);
        }
        if (changedChars >= minChars || changedLines >= minLines) {
            const summary = `${changedChars} chars, ~${changedLines} line delta`;
            maybeSetPending(e.document, Math.max(0, firstLine), summary);
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('decisionPointTracker.toggleEnabled', async () => {
        const cfg = vscode.workspace.getConfiguration('decisionPointTracker');
        const current = cfg.get('enabled', true);
        await cfg.update('enabled', !current, vscode.ConfigurationTarget.Global);
    }));
    context.subscriptions.push(vscode.commands.registerCommand('decisionPointTracker.confirmPending', async () => {
        if (!pending)
            return;
        const choice = await vscode.window.showQuickPick([
            { label: 'Yes — this was a decision point', value: 'yes' },
            { label: 'No', value: 'no' },
            { label: 'Snooze', value: 'snooze' }
        ], { title: `Decision point? (${pending.summary})` });
        if (!choice)
            return;
        if (choice.value === 'no') {
            pending = undefined;
            render(vscode.window.activeTextEditor);
            return;
        }
        if (choice.value === 'snooze') {
            // keep pending; just hide temporarily
            promptStatus.hide();
            setTimeout(() => render(vscode.window.activeTextEditor), 30_000);
            return;
        }
        const reason = await vscode.window.showInputBox({
            title: 'Decision Point Reason (optional)',
            prompt: 'Why was this change important?',
            placeHolder: 'e.g., Simplified flow / Removed legacy path / Renamed for clarity'
        });
        points.push({
            id: genId(),
            uri: pending.uri,
            line: pending.line,
            reason: reason?.trim() || undefined,
            createdAt: Date.now()
        });
        pending = undefined;
        await persist();
        render(vscode.window.activeTextEditor);
    }));
    context.subscriptions.push(vscode.commands.registerCommand('decisionPointTracker.clearAtCursor', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const key = editor.document.uri.toString();
        const line = editor.selection.active.line;
        const before = points.length;
        points = points.filter(p => !(p.uri === key && p.line === line));
        if (points.length !== before) {
            await persist();
            render(editor);
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('decisionPointTracker.showAll', async () => {
        const items = points.map(p => ({
            label: p.reason ? `🧭 ${p.reason}` : '🧭 Decision Point',
            description: vscode.Uri.parse(p.uri).fsPath,
            detail: `Line ${p.line + 1} • ${new Date(p.createdAt).toLocaleString()}`,
            p
        }));
        const picked = await vscode.window.showQuickPick(items, { title: 'Decision Points' });
        if (!picked)
            return;
        const doc = await vscode.workspace.openTextDocument(vscode.Uri.parse(picked.p.uri));
        const editor = await vscode.window.showTextDocument(doc);
        const range = new vscode.Range(picked.p.line, 0, picked.p.line, editor.document.lineAt(picked.p.line).text.length);
        editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
        editor.selection = new vscode.Selection(range.start, range.end);
    }));
    render();
}
function deactivate() { }
//# sourceMappingURL=extension.js.map