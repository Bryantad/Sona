import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { ContextNote, NotesStorage } from './types';

export class ContextNotesStorage {
    private notes: Map<string, ContextNote[]> = new Map();
    private readonly workspaceRoot: string | undefined;

    constructor(private readonly context: vscode.ExtensionContext) {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }

    async load(): Promise<void> {
        const config = vscode.workspace.getConfiguration('codeContext');
        const syncWithGit = config.get<boolean>('syncWithGit', false);

        if (syncWithGit && this.workspaceRoot) {
            const filePath = path.join(this.workspaceRoot, '.code-context.json');
            if (fs.existsSync(filePath)) {
                try {
                    const data = JSON.parse(fs.readFileSync(filePath, 'utf8')) as NotesStorage;
                    this.indexNotes(data.notes);
                } catch (error) {
                    console.error('Failed to load .code-context.json:', error);
                }
            }
            return;
        }

        const data = this.context.workspaceState.get<NotesStorage>('codeContextNotes');
        if (data?.notes) {
            this.indexNotes(data.notes);
        }
    }

    async save(): Promise<void> {
        const storage: NotesStorage = {
            version: '1.0',
            notes: this.getAllNotesUnsorted()
        };

        const config = vscode.workspace.getConfiguration('codeContext');
        const syncWithGit = config.get<boolean>('syncWithGit', false);

        if (syncWithGit && this.workspaceRoot) {
            const filePath = path.join(this.workspaceRoot, '.code-context.json');
            fs.writeFileSync(filePath, JSON.stringify(storage, null, 2));
            return;
        }

        await this.context.workspaceState.update('codeContextNotes', storage);
    }

    getNotesForFile(filePath: string): ContextNote[] {
        const key = this.normalizeFilePath(filePath);
        return this.notes.get(key) || [];
    }

    getNoteAtLine(filePath: string, line: number): ContextNote | undefined {
        const notes = this.getNotesForFile(filePath);
        return notes.find((note) => line >= note.lineStart && line <= note.lineEnd);
    }

    getAllNotes(): ContextNote[] {
        return this.getAllNotesUnsorted().sort(
            (left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime()
        );
    }

    addNote(note: ContextNote): void {
        const key = this.normalizeFilePath(note.filePath);
        const existing = this.notes.get(key) || [];
        existing.push(note);
        this.notes.set(key, existing);
        void this.save();
    }

    updateNote(note: ContextNote): void {
        const key = this.normalizeFilePath(note.filePath);
        const existing = this.notes.get(key) || [];
        const index = existing.findIndex((entry) => entry.id === note.id);
        if (index >= 0) {
            existing[index] = note;
            this.notes.set(key, existing);
            void this.save();
        }
    }

    deleteNote(noteId: string): void {
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

    getStaleNotes(days: number): ContextNote[] {
        if (days <= 0) {
            return [];
        }

        const threshold = Date.now() - days * 24 * 60 * 60 * 1000;
        return this.getAllNotes().filter((note) => new Date(note.createdAt).getTime() < threshold);
    }

    normalizeFilePath(filePath: string): string {
        if (this.workspaceRoot && filePath.startsWith(this.workspaceRoot)) {
            return filePath.substring(this.workspaceRoot.length + 1).replace(/\\/g, '/');
        }
        return filePath.replace(/\\/g, '/');
    }

    private indexNotes(notes: ContextNote[]): void {
        this.notes.clear();
        for (const note of notes) {
            const key = this.normalizeFilePath(note.filePath);
            const existing = this.notes.get(key) || [];
            existing.push(note);
            this.notes.set(key, existing);
        }
    }

    private getAllNotesUnsorted(): ContextNote[] {
        const allNotes: ContextNote[] = [];
        for (const notes of this.notes.values()) {
            allNotes.push(...notes);
        }
        return allNotes;
    }
}
