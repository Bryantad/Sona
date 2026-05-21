import * as vscode from 'vscode';

// ---------------------------------------------------------------------------
// Receipt kind discriminator — the architectural pivot for 0.12.x
// ---------------------------------------------------------------------------

export type ReceiptKind =
    | 'execution'
    | 'directory'
    | 'bundle'
    | 'chain'
    | 'redaction'
    | 'unknown';

// ---------------------------------------------------------------------------
// Normalized receipt interfaces
// ---------------------------------------------------------------------------

/** Fields shared by every receipt family. */
export interface BaseReceipt {
    sona_version: string;
    receipt_version: string;
    timestamp_utc: string;
    receipt_hash?: string;
    prev_receipt_hash?: string;
    policy_fingerprint?: string;
    engine_policy_fingerprint?: string;
    redaction?: {
        profile?: string;
        mode?: string;
        token_strategy?: string;
    };
    signature?: {
        algorithm: string;
        value: string;
        key_id?: string;
        signed_at_utc?: string;
    };
}

/** Execution receipt — the original receipt family. */
export interface ExecutionReceipt extends BaseReceipt {
    code: {
        source_file: string;
        source_sha256: string;
        source_size_bytes: number;
    };
    dependencies: {
        lockfile_sha256: string | null;
        python_version: string;
    };
    inputs: {
        args: string[];
        env_allowlist: Record<string, string>;
    };
    execution: {
        exit_code: number;
        duration_ms: number;
        error?: string;
    };
    reproduce: {
        command: string;
    };
    git?: {
        commit: string;
        branch: string;
        dirty: boolean;
    };
}

/** Directory receipt — added in Sona 0.13.x receipt families. */
export interface DirectoryReceipt extends BaseReceipt {
    root_path: string;
    mode: string;
    total_files: number;
    total_bytes: number;
    tree_hash: string;
    entries: Array<{
        path: string;
        sha256: string;
        size_bytes: number;
    }>;
}

// ---------------------------------------------------------------------------
// Parsed wrapper used by tree loading, detail panels, and command dispatch
// ---------------------------------------------------------------------------

export interface ParsedReceipt {
    kind: ReceiptKind;
    id?: string;
    timestamp?: string;
    displayLabel: string;
    raw: unknown;
    data: BaseReceipt;
}

/** File-level wrapper associating a parsed receipt with its workspace URI. */
export interface ReceiptFile {
    uri: vscode.Uri;
    parsed: ParsedReceipt;
    mtime: number;
}

/** Helper for date-based grouping in the tree. */
export interface DateBucket {
    key: string;
    label: string;
    order: number;
}
