"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isRecord = isRecord;
exports.asString = asString;
exports.asNumber = asNumber;
exports.asBoolean = asBoolean;
exports.asStringArray = asStringArray;
exports.asStringRecord = asStringRecord;
exports.detectReceiptKind = detectReceiptKind;
exports.parseReceipt = parseReceipt;
// ---------------------------------------------------------------------------
// Type-guard / coercion helpers (unchanged from original)
// ---------------------------------------------------------------------------
function isRecord(value) {
    return typeof value === 'object' && value !== null;
}
function asString(value, fallback = '') {
    return typeof value === 'string' ? value : fallback;
}
function asNumber(value, fallback = 0) {
    return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}
function asBoolean(value, fallback = false) {
    return typeof value === 'boolean' ? value : fallback;
}
function asStringArray(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value.filter((entry) => typeof entry === 'string');
}
function asStringRecord(value) {
    if (!isRecord(value)) {
        return {};
    }
    const out = {};
    for (const [key, val] of Object.entries(value)) {
        out[key] = typeof val === 'string' ? val : String(val);
    }
    return out;
}
// ---------------------------------------------------------------------------
// Kind detection
// ---------------------------------------------------------------------------
/**
 * Detect the receipt family from raw parsed JSON.
 * Supports mixed root/header field layouts for backward compat.
 */
function detectReceiptKind(raw) {
    // Execution receipts always have code + execution + reproduce
    if (isRecord(raw.code) && isRecord(raw.execution) && isRecord(raw.reproduce)) {
        return 'execution';
    }
    // Directory receipts have root_path + tree_hash (or entries array)
    if (typeof raw.root_path === 'string' && typeof raw.tree_hash === 'string') {
        return 'directory';
    }
    // Bundle manifests
    if (typeof raw.bundle_hash === 'string' || typeof raw.manifest_hash === 'string') {
        return 'bundle';
    }
    // Chain verification results
    if (typeof raw.chain_length === 'number' || typeof raw.integrity_score === 'number') {
        return 'chain';
    }
    // Redaction manifests
    if (typeof raw.source_receipt_hash === 'string' && Array.isArray(raw.redacted_fields)) {
        return 'redaction';
    }
    return 'unknown';
}
// ---------------------------------------------------------------------------
// Shared base-field extraction
// ---------------------------------------------------------------------------
function extractBase(raw) {
    const header = isRecord(raw.header) ? raw.header : {};
    const redactionSource = isRecord(raw.redaction)
        ? raw.redaction
        : isRecord(header.redaction)
            ? header.redaction
            : undefined;
    const signatureSource = isRecord(raw.signature)
        ? raw.signature
        : isRecord(header.signature)
            ? header.signature
            : undefined;
    return {
        sona_version: asString(raw.sona_version, 'unknown'),
        receipt_version: asString(raw.receipt_version, 'unknown'),
        timestamp_utc: asString(raw.timestamp_utc),
        receipt_hash: asString(raw.receipt_hash || header.receipt_hash || '', '') || undefined,
        prev_receipt_hash: asString(raw.prev_receipt_hash || header.prev_receipt_hash || '', '') || undefined,
        policy_fingerprint: asString(header.policy_fingerprint || raw.policy_fingerprint || '', '') || undefined,
        engine_policy_fingerprint: asString(header.engine_policy_fingerprint || raw.engine_policy_fingerprint || '', '') || undefined,
        redaction: redactionSource
            ? {
                profile: asString(redactionSource.profile, undefined),
                mode: asString(redactionSource.mode, undefined),
                token_strategy: asString(redactionSource.token_strategy, undefined)
            }
            : undefined,
        signature: signatureSource
            ? {
                algorithm: asString(signatureSource.algorithm, 'unknown'),
                value: asString(signatureSource.value, ''),
                key_id: asString(signatureSource.key_id, undefined),
                signed_at_utc: asString(signatureSource.signed_at_utc, undefined)
            }
            : undefined
    };
}
// ---------------------------------------------------------------------------
// Kind-specific parsers
// ---------------------------------------------------------------------------
function parseExecutionReceipt(raw) {
    const code = isRecord(raw.code) ? raw.code : {};
    const dependencies = isRecord(raw.dependencies) ? raw.dependencies : {};
    const inputs = isRecord(raw.inputs) ? raw.inputs : {};
    const execution = isRecord(raw.execution) ? raw.execution : {};
    const reproduce = isRecord(raw.reproduce) ? raw.reproduce : {};
    const git = isRecord(raw.git) ? raw.git : undefined;
    const sourceFile = asString(code.source_file);
    const timestamp = asString(raw.timestamp_utc);
    const reproduceCommand = asString(reproduce.command);
    if (!sourceFile || !timestamp || !reproduceCommand) {
        return undefined;
    }
    return {
        ...extractBase(raw),
        code: {
            source_file: sourceFile,
            source_sha256: asString(code.source_sha256, 'unknown'),
            source_size_bytes: asNumber(code.source_size_bytes, 0)
        },
        dependencies: {
            lockfile_sha256: dependencies.lockfile_sha256 === null ? null : asString(dependencies.lockfile_sha256, null),
            python_version: asString(dependencies.python_version, 'unknown')
        },
        inputs: {
            args: asStringArray(inputs.args),
            env_allowlist: asStringRecord(inputs.env_allowlist)
        },
        execution: {
            exit_code: asNumber(execution.exit_code, 1),
            duration_ms: asNumber(execution.duration_ms, 0),
            error: asString(execution.error, '') || undefined
        },
        reproduce: {
            command: reproduceCommand
        },
        git: git
            ? {
                commit: asString(git.commit, 'unknown'),
                branch: asString(git.branch, 'unknown'),
                dirty: asBoolean(git.dirty, false)
            }
            : undefined
    };
}
function parseDirectoryReceipt(raw) {
    const rootPath = asString(raw.root_path);
    const treeHash = asString(raw.tree_hash);
    if (!rootPath || !treeHash) {
        return undefined;
    }
    const rawEntries = Array.isArray(raw.entries) ? raw.entries : [];
    const entries = rawEntries
        .filter(isRecord)
        .map((e) => ({
        path: asString(e.path),
        sha256: asString(e.sha256),
        size_bytes: asNumber(e.size_bytes, 0)
    }));
    return {
        ...extractBase(raw),
        root_path: rootPath,
        mode: asString(raw.mode, 'unknown'),
        total_files: asNumber(raw.total_files, entries.length),
        total_bytes: asNumber(raw.total_bytes, 0),
        tree_hash: treeHash,
        entries
    };
}
// ---------------------------------------------------------------------------
// Top-level parser — returns a normalized ParsedReceipt or undefined
// ---------------------------------------------------------------------------
function parseReceipt(content) {
    let parsed;
    try {
        parsed = JSON.parse(content);
    }
    catch {
        return undefined;
    }
    if (!isRecord(parsed)) {
        return undefined;
    }
    const kind = detectReceiptKind(parsed);
    switch (kind) {
        case 'execution': {
            const data = parseExecutionReceipt(parsed);
            if (!data) {
                // Falls through to unknown rather than silently dropping
                break;
            }
            return {
                kind: 'execution',
                id: data.receipt_hash,
                timestamp: data.timestamp_utc,
                displayLabel: data.code.source_file
                    ? require('path').basename(data.code.source_file)
                    : 'Execution Receipt',
                raw: parsed,
                data
            };
        }
        case 'directory': {
            const data = parseDirectoryReceipt(parsed);
            if (!data) {
                break;
            }
            return {
                kind: 'directory',
                id: data.receipt_hash,
                timestamp: data.timestamp_utc,
                displayLabel: data.root_path
                    ? require('path').basename(data.root_path)
                    : 'Directory Receipt',
                raw: parsed,
                data
            };
        }
        default:
            break;
    }
    // For bundle, chain, redaction, or truly unknown JSON:
    // always load so it appears in the tree with safe rendering.
    const base = extractBase(parsed);
    const label = kind === 'unknown'
        ? 'Unknown Receipt'
        : `${kind.charAt(0).toUpperCase() + kind.slice(1)} Receipt`;
    return {
        kind,
        id: base.receipt_hash,
        timestamp: base.timestamp_utc || undefined,
        displayLabel: label,
        raw: parsed,
        data: base
    };
}
//# sourceMappingURL=parse.js.map