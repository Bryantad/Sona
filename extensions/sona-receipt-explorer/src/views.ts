import * as path from 'path';
import * as vscode from 'vscode';
import {
    ReceiptFile,
    ParsedReceipt,
    ExecutionReceipt,
    DirectoryReceipt
} from './models';

// ---------------------------------------------------------------------------
// HTML helpers
// ---------------------------------------------------------------------------

export function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

export function describeSignature(data: import('./models').BaseReceipt): string {
    if (!data.signature) {
        return 'unsigned';
    }
    const keyId = data.signature.key_id ? ` (${data.signature.key_id})` : '';
    return `${data.signature.algorithm}${keyId}`;
}

export function describeRedaction(data: import('./models').BaseReceipt): string {
    if (!data.redaction) {
        return 'none';
    }
    const parts = [data.redaction.profile, data.redaction.mode, data.redaction.token_strategy].filter(
        (v): v is string => Boolean(v)
    );
    return parts.length > 0 ? parts.join(' | ') : 'configured';
}

// ---------------------------------------------------------------------------
// CSS shared across all detail panels
// ---------------------------------------------------------------------------

const panelCss = `
body {
    font-family: var(--vscode-font-family);
    color: var(--vscode-foreground);
    background: var(--vscode-editor-background);
    padding: 20px;
    line-height: 1.6;
}
.header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--vscode-panel-border);
}
.header h1 {
    margin: 0;
    font-size: 1.4em;
}
.status {
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 0.9em;
}
.status.success {
    background: var(--vscode-testing-iconPassed);
    color: #fff;
}
.status.error {
    background: var(--vscode-testing-iconFailed);
    color: #fff;
}
.status.info {
    background: var(--vscode-badge-background);
    color: var(--vscode-badge-foreground);
}
.section {
    margin-bottom: 20px;
}
.section h2 {
    font-size: 1.05em;
    margin-bottom: 10px;
    color: var(--vscode-textPreformat-foreground);
}
.grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px;
}
.label {
    color: var(--vscode-descriptionForeground);
    font-weight: 500;
}
.value {
    font-family: var(--vscode-editor-font-family);
    word-break: break-all;
}
.code-block {
    background: var(--vscode-textBlockQuote-background);
    border: 1px solid var(--vscode-panel-border);
    border-radius: 4px;
    padding: 12px;
    font-family: var(--vscode-editor-font-family);
    font-size: 0.9em;
    white-space: pre-wrap;
}
.metric {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    background: var(--vscode-badge-background);
    color: var(--vscode-badge-foreground);
    border-radius: 4px;
    margin-right: 8px;
    margin-bottom: 8px;
}
.metric-value {
    font-weight: 700;
}
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    text-align: left;
    padding: 8px;
    border-bottom: 1px solid var(--vscode-panel-border);
    font-family: var(--vscode-editor-font-family);
}
th {
    color: var(--vscode-descriptionForeground);
    font-family: var(--vscode-font-family);
}
`;

function wrapHtml(body: string): string {
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>${panelCss}</style>
</head>
<body>
${body}
</body>
</html>`;
}

// ---------------------------------------------------------------------------
// Kind-specific renderers
// ---------------------------------------------------------------------------

function renderGovernance(data: import('./models').BaseReceipt): string {
    const rows = [
        ['Receipt Hash', data.receipt_hash],
        ['Previous Receipt Hash', data.prev_receipt_hash],
        ['Policy Fingerprint', data.policy_fingerprint],
        ['Engine Policy Fingerprint', data.engine_policy_fingerprint],
        ['Signature', describeSignature(data)],
        ['Signed At', data.signature?.signed_at_utc],
        ['Redaction', describeRedaction(data)]
    ]
        .filter((entry): entry is [string, string] => Boolean(entry[1]))
        .map(
            ([label, value]) =>
                `<span class="label">${escapeHtml(label)}</span><span class="value">${escapeHtml(String(value))}</span>`
        )
        .join('');

    if (!rows) {
        return '';
    }
    return `<div class="section"><h2>Trust &amp; Governance</h2><div class="grid">${rows}</div></div>`;
}

function renderMetadata(parsed: ParsedReceipt, filePath: string): string {
    return `<div class="section">
    <h2>Metadata</h2>
    <div class="grid">
        <span class="label">Kind</span>
        <span class="value">${escapeHtml(parsed.kind)}</span>
        <span class="label">Timestamp</span>
        <span class="value">${escapeHtml(parsed.timestamp || 'unknown')}</span>
        <span class="label">Receipt Version</span>
        <span class="value">${escapeHtml(parsed.data.receipt_version)}</span>
        <span class="label">Receipt File</span>
        <span class="value">${escapeHtml(filePath)}</span>
    </div>
</div>`;
}

export function renderExecutionReceipt(receiptFile: ReceiptFile): string {
    const r = receiptFile.parsed.data as ExecutionReceipt;
    const statusText = r.execution.exit_code === 0 ? 'Success' : 'Failed';
    const statusClass = r.execution.exit_code === 0 ? 'success' : 'error';

    const envRows = Object.entries(r.inputs.env_allowlist)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => `<tr><td>${escapeHtml(k)}</td><td>${escapeHtml(v)}</td></tr>`)
        .join('');

    const body = `
    <div class="header">
        <h1>${escapeHtml(path.basename(r.code.source_file))}</h1>
        <span class="status ${statusClass}">${statusText}</span>
    </div>

    <div class="section">
        <div class="metric"><span>Duration</span><span class="metric-value">${r.execution.duration_ms}ms</span></div>
        <div class="metric"><span>Size</span><span class="metric-value">${r.code.source_size_bytes} bytes</span></div>
        <div class="metric"><span>Sona</span><span class="metric-value">${escapeHtml(r.sona_version)}</span></div>
        <div class="metric"><span>Python</span><span class="metric-value">${escapeHtml(r.dependencies.python_version)}</span></div>
        <div class="metric"><span>Signature</span><span class="metric-value">${escapeHtml(describeSignature(r))}</span></div>
    </div>

    <div class="section">
        <h2>Source</h2>
        <div class="grid">
            <span class="label">File</span>
            <span class="value">${escapeHtml(r.code.source_file)}</span>
            <span class="label">SHA-256</span>
            <span class="value">${escapeHtml(r.code.source_sha256)}</span>
        </div>
    </div>

    ${r.git
        ? `<div class="section">
            <h2>Git</h2>
            <div class="grid">
                <span class="label">Branch</span>
                <span class="value">${escapeHtml(r.git.branch)}</span>
                <span class="label">Commit</span>
                <span class="value">${escapeHtml(r.git.commit.slice(0, 7))}${r.git.dirty ? ' (dirty)' : ''}</span>
            </div>
        </div>`
        : ''}

    ${renderGovernance(r)}

    ${envRows
        ? `<div class="section">
            <h2>Environment</h2>
            <table>
                <thead><tr><th>Variable</th><th>Value</th></tr></thead>
                <tbody>${envRows}</tbody>
            </table>
        </div>`
        : ''}

    ${r.execution.error
        ? `<div class="section">
            <h2>Error</h2>
            <div class="code-block">${escapeHtml(r.execution.error)}</div>
        </div>`
        : ''}

    <div class="section">
        <h2>Reproduce</h2>
        <div class="code-block">${escapeHtml(r.reproduce.command)}</div>
    </div>

    ${renderMetadata(receiptFile.parsed, receiptFile.uri.fsPath)}`;

    return wrapHtml(body);
}

export function renderDirectoryReceipt(receiptFile: ReceiptFile): string {
    const r = receiptFile.parsed.data as DirectoryReceipt;

    const entryRows = r.entries
        .slice(0, 200)
        .map(
            (e) =>
                `<tr><td>${escapeHtml(e.path)}</td><td>${escapeHtml(e.sha256.slice(0, 12))}…</td><td>${e.size_bytes}</td></tr>`
        )
        .join('');

    const body = `
    <div class="header">
        <h1>${escapeHtml(path.basename(r.root_path))}</h1>
        <span class="status info">Directory</span>
    </div>

    <div class="section">
        <div class="metric"><span>Files</span><span class="metric-value">${r.total_files}</span></div>
        <div class="metric"><span>Bytes</span><span class="metric-value">${r.total_bytes}</span></div>
        <div class="metric"><span>Mode</span><span class="metric-value">${escapeHtml(r.mode)}</span></div>
        <div class="metric"><span>Sona</span><span class="metric-value">${escapeHtml(r.sona_version)}</span></div>
        <div class="metric"><span>Signature</span><span class="metric-value">${escapeHtml(describeSignature(r))}</span></div>
    </div>

    <div class="section">
        <h2>Integrity</h2>
        <div class="grid">
            <span class="label">Root Path</span>
            <span class="value">${escapeHtml(r.root_path)}</span>
            <span class="label">Tree Hash</span>
            <span class="value">${escapeHtml(r.tree_hash)}</span>
        </div>
    </div>

    ${renderGovernance(r)}

    ${entryRows
        ? `<div class="section">
            <h2>Entries${r.entries.length > 200 ? ` (showing 200 of ${r.entries.length})` : ''}</h2>
            <table>
                <thead><tr><th>Path</th><th>SHA-256</th><th>Size</th></tr></thead>
                <tbody>${entryRows}</tbody>
            </table>
        </div>`
        : ''}

    ${renderMetadata(receiptFile.parsed, receiptFile.uri.fsPath)}`;

    return wrapHtml(body);
}

export function renderUnknownReceipt(receiptFile: ReceiptFile): string {
    const raw = JSON.stringify(receiptFile.parsed.raw, null, 2);

    const body = `
    <div class="header">
        <h1>${escapeHtml(receiptFile.parsed.displayLabel)}</h1>
        <span class="status info">${escapeHtml(receiptFile.parsed.kind)}</span>
    </div>

    ${renderGovernance(receiptFile.parsed.data)}
    ${renderMetadata(receiptFile.parsed, receiptFile.uri.fsPath)}

    <div class="section">
        <h2>Raw Receipt</h2>
        <div class="code-block">${escapeHtml(raw)}</div>
    </div>`;

    return wrapHtml(body);
}

// ---------------------------------------------------------------------------
// Detail panel (singleton webview)
// ---------------------------------------------------------------------------

export class ReceiptDetailPanel {
    private static currentPanel: ReceiptDetailPanel | undefined;
    private readonly panel: vscode.WebviewPanel;
    private readonly disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel, receipt: ReceiptFile) {
        this.panel = panel;
        this.update(receipt);
        this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    }

    static show(receipt: ReceiptFile): void {
        const column = vscode.window.activeTextEditor?.viewColumn;

        if (ReceiptDetailPanel.currentPanel) {
            ReceiptDetailPanel.currentPanel.update(receipt);
            ReceiptDetailPanel.currentPanel.panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'sonaReceiptDetail',
            `Receipt: ${receipt.parsed.displayLabel}`,
            column ?? vscode.ViewColumn.One,
            { enableScripts: false }
        );

        ReceiptDetailPanel.currentPanel = new ReceiptDetailPanel(panel, receipt);
    }

    private update(receipt: ReceiptFile): void {
        this.panel.title = `Receipt: ${receipt.parsed.displayLabel}`;
        this.panel.webview.html = this.renderByKind(receipt);
    }

    private renderByKind(receipt: ReceiptFile): string {
        switch (receipt.parsed.kind) {
            case 'execution':
                return renderExecutionReceipt(receipt);
            case 'directory':
                return renderDirectoryReceipt(receipt);
            default:
                return renderUnknownReceipt(receipt);
        }
    }

    private dispose(): void {
        ReceiptDetailPanel.currentPanel = undefined;
        this.panel.dispose();
        this.disposables.forEach((d) => d.dispose());
    }
}

// ---------------------------------------------------------------------------
// Diff formatter
// ---------------------------------------------------------------------------

export function formatReceiptForDiff(parsed: ParsedReceipt): string {
    const lines: string[] = [];
    lines.push(`# Receipt: ${parsed.displayLabel}`);
    lines.push(`Kind: ${parsed.kind}`);
    lines.push(`Timestamp: ${parsed.timestamp || 'unknown'}`);
    lines.push(`Sona Version: ${parsed.data.sona_version}`);
    lines.push(`Receipt Version: ${parsed.data.receipt_version}`);
    lines.push('');

    if (parsed.kind === 'execution') {
        const r = parsed.data as ExecutionReceipt;
        lines.push('## Execution');
        lines.push(`Exit Code: ${r.execution.exit_code}`);
        lines.push(`Duration: ${r.execution.duration_ms}ms`);
        if (r.execution.error) {
            lines.push(`Error: ${r.execution.error}`);
        }
        lines.push('');
        lines.push('## Source');
        lines.push(`File: ${r.code.source_file}`);
        lines.push(`Size: ${r.code.source_size_bytes} bytes`);
        lines.push(`SHA-256: ${r.code.source_sha256}`);
        lines.push('');
        lines.push('## Dependencies');
        lines.push(`Python: ${r.dependencies.python_version}`);
        lines.push(`Lockfile SHA-256: ${r.dependencies.lockfile_sha256 || 'N/A'}`);
        lines.push('');

        if (r.git) {
            lines.push('## Git');
            lines.push(`Branch: ${r.git.branch}`);
            lines.push(`Commit: ${r.git.commit}`);
            lines.push(`Dirty: ${r.git.dirty}`);
            lines.push('');
        }

        lines.push('## Reproduce');
        lines.push(r.reproduce.command);
        lines.push('');
    }

    if (parsed.kind === 'directory') {
        const r = parsed.data as DirectoryReceipt;
        lines.push('## Directory');
        lines.push(`Root: ${r.root_path}`);
        lines.push(`Mode: ${r.mode}`);
        lines.push(`Files: ${r.total_files}`);
        lines.push(`Bytes: ${r.total_bytes}`);
        lines.push(`Tree Hash: ${r.tree_hash}`);
        lines.push('');
    }

    lines.push('## Trust');
    lines.push(`Receipt Hash: ${parsed.data.receipt_hash || 'N/A'}`);
    lines.push(`Previous Receipt Hash: ${parsed.data.prev_receipt_hash || 'N/A'}`);
    lines.push(`Policy Fingerprint: ${parsed.data.policy_fingerprint || 'N/A'}`);
    lines.push(`Engine Policy Fingerprint: ${parsed.data.engine_policy_fingerprint || 'N/A'}`);
    lines.push(`Signature: ${describeSignature(parsed.data)}`);
    lines.push(`Signed At: ${parsed.data.signature?.signed_at_utc || 'N/A'}`);
    lines.push(`Redaction: ${describeRedaction(parsed.data)}`);

    return lines.join('\n');
}
