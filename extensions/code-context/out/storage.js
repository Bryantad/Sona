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
exports.ContextNotesStorage = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
class ContextNotesStorage {
    context;
    notes = new Map();
    workspaceRoot;
    constructor(context) {
        this.context = context;
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }
    async load() {
        const config = vscode.workspace.getConfiguration('codeContext');
        const syncWithGit = config.get('syncWithGit', false);
        if (syncWithGit && this.workspaceRoot) {
            const filePath = path.join(this.workspaceRoot, '.code-context.json');
            if (fs.existsSync(filePath)) {
                try {
                    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                    this.indexNotes(data.notes);
                }
                catch (error) {
                    console.error('Failed to load .code-context.json:', error);
                }
            }
            return;
        }
        const data = this.context.workspaceState.get('codeContextNotes');
        if (data?.notes) {
            this.indexNotes(data.notes);
        }
    }
    async save() {
        const storage = {
            version: '1.0',
            notes: this.getAllNotesUnsorted()
        };
        const config = vscode.workspace.getConfiguration('codeContext');
        const syncWithGit = config.get('syncWithGit', false);
        if (syncWithGit && this.workspaceRoot) {
            const filePath = path.join(this.workspaceRoot, '.code-context.json');
            fs.writeFileSync(filePath, JSON.stringify(storage, null, 2));
            return;
        }
        await this.context.workspaceState.update('codeContextNotes', storage);
    }
    getNotesForFile(filePath) {
        const key = this.normalizeFilePath(filePath);
        return this.notes.get(key) || [];
    }
    getNoteAtLine(filePath, line) {
        const notes = this.getNotesForFile(filePath);
        return notes.find((note) => line >= note.lineStart && line <= note.lineEnd);
    }
    getAllNotes() {
        return this.getAllNotesUnsorted().sort((left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime());
    }
    addNote(note) {
        const key = this.normalizeFilePath(note.filePath);
        const existing = this.notes.get(key) || [];
        existing.push(note);
        this.notes.set(key, existing);
        void this.save();
    }
    updateNote(note) {
        const key = this.normalizeFilePath(note.filePath);
        const existing = this.notes.get(key) || [];
        const index = existing.findIndex((entry) => entry.id === note.id);
        if (index >= 0) {
            existing[index] = note;
            this.notes.set(key, existing);
            void this.save();
        }
    }
    deleteNote(noteId) {
        for (const [key, notes] of this.notes.entries()) {
            const index = notes.findIndex((note) => note.id === noteId);
            if (index >= 0) {
                notes.splice(index, 1);
                this.notes.set(key, notes);
                void this.save();
                return;
            }
        }
    }
    getStaleNotes(days) {
        if (days <= 0) {
            return [];
        }
        const threshold = Date.now() - days * 24 * 60 * 60 * 1000;
        return this.getAllNotes().filter((note) => new Date(note.createdAt).getTime() < threshold);
    }
    normalizeFilePath(filePath) {
        if (this.workspaceRoot && filePath.startsWith(this.workspaceRoot)) {
            return filePath.substring(this.workspaceRoot.length + 1).replace(/\\/g, '/');
        }
        return filePath.replace(/\\/g, '/');
    }
    indexNotes(notes) {
        this.notes.clear();
        for (const note of notes) {
            const key = this.normalizeFilePath(note.filePath);
            const existing = this.notes.get(key) || [];
            existing.push(note);
            this.notes.set(key, existing);
        }
    }
    getAllNotesUnsorted() {
        const allNotes = [];
        for (const notes of this.notes.values()) {
            allNotes.push(...notes);
        }
        return allNotes;
    }
}
exports.ContextNotesStorage = ContextNotesStorage;
//# sourceMappingURL=storage.js.map