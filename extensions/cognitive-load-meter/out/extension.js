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
function clamp01(value) {
    if (value < 0)
        return 0;
    if (value > 1)
        return 1;
    return value;
}
function toKey(uri) {
    return uri.toString();
}
function estimateBraceNesting(text) {
    let depth = 0;
    let maxDepth = 0;
    let inSingle = false;
    let inDouble = false;
    let inBacktick = false;
    let escape = false;
    for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (escape) {
            escape = false;
            continue;
        }
        if (ch === '\\') {
            escape = true;
            continue;
        }
        if (!inDouble && !inBacktick && ch === '\'') {
            inSingle = !inSingle;
            continue;
        }
        if (!inSingle && !inBacktick && ch === '"') {
            inDouble = !inDouble;
            continue;
        }
        if (!inSingle && !inDouble && ch === '`') {
            inBacktick = !inBacktick;
            continue;
        }
        if (inSingle || inDouble || inBacktick)
            continue;
        if (ch === '{' || ch === '(' || ch === '[') {
            depth++;
            if (depth > maxDepth)
                maxDepth = depth;
            continue;
        }
        if (ch === '}' || ch === ')' || ch === ']') {
            depth = Math.max(0, depth - 1);
        }
    }
    return maxDepth;
}
function estimateIndentNesting(document, maxLines) {
    const linesToScan = Math.min(document.lineCount, maxLines);
    let maxIndent = 0;
    for (let i = 0; i < linesToScan; i++) {
        const line = document.lineAt(i).text;
        if (line.trim().length === 0)
            continue;
        const match = line.match(/^(\s+)/);
        if (!match)
            continue;
        maxIndent = Math.max(maxIndent, match[1].replace(/\t/g, '    ').length);
    }
    return Math.floor(maxIndent / 4);
}
function debounce(fn, ms) {
    let timer;
    return () => {
        if (timer)
            clearTimeout(timer);
        timer = setTimeout(fn, ms);
    };
}
function activate(context) {
    const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    status.command = 'cognitiveLoadMeter.showDetails';
    context.subscriptions.push(status);
    const editHistory = new Map();
    function getConfig() {
        const cfg = vscode.workspace.getConfiguration('cognitiveLoadMeter');
        return {
            enabled: cfg.get('enabled', true),
            lookbackMinutes: cfg.get('lookbackMinutes', 10),
            debounceMs: cfg.get('debounceMs', 350),
            maxLinesForNesting: cfg.get('maxLinesForNesting', 2000)
        };
    }
    function pruneEdits(events, cutoff) {
        const firstKeep = events.findIndex(e => e.at >= cutoff);
        if (firstKeep === -1)
            return [];
        return events.slice(firstKeep);
    }
    function getActiveDocument() {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return undefined;
        return editor.document;
    }
    function computeLoad(document) {
        const cfg = getConfig();
        const now = Date.now();
        const cutoff = now - cfg.lookbackMinutes * 60_000;
        const key = toKey(document.uri);
        const events = pruneEdits(editHistory.get(key) ?? [], cutoff);
        editHistory.set(key, events);
        const lineCount = document.lineCount;
        const linesToScan = Math.min(document.lineCount, cfg.maxLinesForNesting);
        let nesting = 0;
        if (document.languageId === 'python' || document.languageId === 'sona' || document.languageId === 'yaml') {
            nesting = estimateIndentNesting(document, linesToScan);
        }
        else {
            const text = document.getText(new vscode.Range(0, 0, linesToScan - 1, document.lineAt(linesToScan - 1).text.length));
            nesting = estimateBraceNesting(text);
        }
        const recentEditCount = events.length;
        const recentEditsLast2Min = events.filter(e => e.at >= now - 2 * 60_000).length;
        const uniqueLineBuckets = new Set();
        const regionBuckets = new Set();
        for (const e of events) {
            const start = Math.max(0, Math.min(lineCount - 1, e.startLine));
            const end = Math.max(0, Math.min(lineCount - 1, e.endLine));
            for (let ln = start; ln <= end; ln++) {
                uniqueLineBuckets.add(ln);
                regionBuckets.add(Math.floor(ln / 50));
            }
        }
        const sizeScore = clamp01(lineCount / 800);
        const nestingScore = clamp01(nesting / 10);
        const conceptsScore = clamp01(regionBuckets.size / 8);
        const freqScore = clamp01(recentEditsLast2Min / 20);
        const score = clamp01(0.25 * sizeScore + 0.25 * nestingScore + 0.25 * conceptsScore + 0.25 * freqScore);
        const level = score < 0.33 ? 'Light' : score < 0.66 ? 'Moderate' : 'Heavy';
        const icon = score < 0.33 ? '🟢' : score < 0.66 ? '🟡' : '🔴';
        return {
            icon,
            level,
            score,
            lineCount,
            nesting,
            recentEditCount,
            uniqueEditedLines: uniqueLineBuckets.size,
            regionBuckets: regionBuckets.size,
            recentEditsLast2Min
        };
    }
    function updateStatus() {
        const cfg = getConfig();
        if (!cfg.enabled) {
            status.hide();
            return;
        }
        const doc = getActiveDocument();
        if (!doc) {
            status.hide();
            return;
        }
        const info = computeLoad(doc);
        status.text = `${info.icon} Load: ${info.level}`;
        status.tooltip = new vscode.MarkdownString([
            `**Cognitive Load Meter**`,
            ``,
            `Score: **${info.score.toFixed(2)}**`,
            ``,
            `- Lines: ${info.lineCount}`,
            `- Nesting estimate: ${info.nesting}`,
            `- Recent edits (${getConfig().lookbackMinutes}m): ${info.recentEditCount}`,
            `- Unique edited lines: ${info.uniqueEditedLines}`,
            `- Regions touched: ${info.regionBuckets}`,
            `- Edits (last 2m): ${info.recentEditsLast2Min}`
        ].join('\n'));
        status.show();
    }
    let debouncedUpdate = debounce(updateStatus, getConfig().debounceMs);
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('cognitiveLoadMeter')) {
            debouncedUpdate = debounce(updateStatus, getConfig().debounceMs);
            updateStatus();
        }
    }));
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(() => updateStatus()));
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(e => {
        const doc = e.document;
        if (doc.isUntitled)
            return;
        const key = toKey(doc.uri);
        const events = editHistory.get(key) ?? [];
        for (const c of e.contentChanges) {
            const insertedLineCount = c.text.split(/\r\n|\r|\n/).length - 1;
            const removedLineCount = c.range.end.line - c.range.start.line;
            events.push({
                at: Date.now(),
                startLine: c.range.start.line,
                endLine: c.range.end.line,
                insertedLineCount,
                removedLineCount
            });
        }
        editHistory.set(key, events);
        if (vscode.window.activeTextEditor?.document.uri.toString() === doc.uri.toString()) {
            debouncedUpdate();
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('cognitiveLoadMeter.toggleEnabled', async () => {
        const cfg = vscode.workspace.getConfiguration('cognitiveLoadMeter');
        const enabled = cfg.get('enabled', true);
        await cfg.update('enabled', !enabled, vscode.ConfigurationTarget.Global);
        updateStatus();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('cognitiveLoadMeter.showDetails', async () => {
        const doc = getActiveDocument();
        if (!doc)
            return;
        const info = computeLoad(doc);
        const msg = `Load: ${info.level} (score ${info.score.toFixed(2)}) — lines ${info.lineCount}, nesting ${info.nesting}, regions ${info.regionBuckets}, edits(last2m) ${info.recentEditsLast2Min}`;
        await vscode.window.showInformationMessage(msg);
    }));
    context.subscriptions.push(vscode.commands.registerCommand('cognitiveLoadMeter.resetHistory', async () => {
        editHistory.clear();
        updateStatus();
    }));
    updateStatus();
}
function deactivate() { }
//# sourceMappingURL=extension.js.map