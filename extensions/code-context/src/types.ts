export interface ContextNote {
    id: string;
    filePath: string;
    lineStart: number;
    lineEnd: number;
    codeSnippet: string;
    note: string;
    category: string;
    reasonType?: ReasonType;
    nearCommit?: string;
    createdAt: string;
    updatedAt: string;
    author?: string;
}

export type ReasonType = 'TEMP' | 'WORKAROUND' | 'SECURITY' | 'PERFORMANCE' | 'LEGACY' | 'NONE';

export interface NotesStorage {
    version: string;
    notes: ContextNote[];
}
