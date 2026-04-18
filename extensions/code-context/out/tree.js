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
exports.ContextNotesTreeProvider = exports.FileNoteItem = exports.ContextNoteItem = void 0;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const decorations_1 = require("./decorations");
class ContextNoteItem extends vscode.TreeItem {
    note;
    constructor(note) {
        super(note.category, vscode.TreeItemCollapsibleState.None);
        this.note = note;
        const preview = note.note.length > 50 ? `${note.note.substring(0, 50)}...` : note.note;
        this.description = preview;
        this.tooltip = new vscode.MarkdownString(`**${note.category}**\n\n${note.note}\n\n---\n*${note.filePath}:${note.lineStart + 1}*`);
        this.command = {
            command: 'codeContext.goToNote',
            title: 'Go to Note',
            arguments: [note]
        };
        this.contextValue = (0, decorations_1.isStale)(note) ? 'staleNote' : 'note';
        this.iconPath = new vscode.ThemeIcon((0, decorations_1.isStale)(note) ? 'warning' : 'comment');
    }
}
exports.ContextNoteItem = ContextNoteItem;
class FileNoteItem extends vscode.TreeItem {
    filePath;
    notes;
    constructor(filePath, notes) {
        super(path.basename(filePath), vscode.TreeItemCollapsibleState.Expanded);
        this.filePath = filePath;
        this.notes = notes;
        this.description = `${notes.length} note${notes.length > 1 ? 's' : ''}`;
        this.tooltip = filePath;
        this.iconPath = vscode.ThemeIcon.File;
        this.resourceUri = vscode.Uri.file(filePath);
    }
}
exports.FileNoteItem = FileNoteItem;
class ContextNotesTreeProvider {
    storage;
    onDidChangeTreeDataEmitter = new vscode.EventEmitter();
    onDidChangeTreeData = this.onDidChangeTreeDataEmitter.event;
    constructor(storage) {
        this.storage = storage;
    }
    refresh() {
        this.onDidChangeTreeDataEmitter.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            const notesByFile = new Map();
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
exports.ContextNotesTreeProvider = ContextNotesTreeProvider;
//# sourceMappingURL=tree.js.map