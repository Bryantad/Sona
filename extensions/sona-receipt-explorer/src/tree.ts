import * as path from 'path';
import * as vscode from 'vscode';
import {
    ReceiptFile,
    ParsedReceipt,
    DateBucket,
    ExecutionReceipt,
    DirectoryReceipt
} from './models';
import { parseReceipt } from './parse';

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

export function getDateBucket(timestamp: string): DateBucket {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return { key: 'unknown', label: 'Unknown Date', order: -1 };
    }

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const diffDays = Math.floor((today.getTime() - target.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) {
        return { key: 'today', label: 'Today', order: 0 };
    }
    if (diffDays === 1) {
        return { key: 'yesterday', label: 'Yesterday', order: 1 };
    }
    if (diffDays < 7) {
        return { key: `days-${diffDays}`, label: `${diffDays} days ago`, order: 2 + diffDays };
    }

    return {
        key: `date-${target.getTime()}`,
        label: date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }),
        order: 1000000 - target.getTime()
    };
}

function describeStatus(parsed: ParsedReceipt): string {
    if (parsed.kind === 'execution') {
        const exec = (parsed.data as ExecutionReceipt).execution;
        return exec.exit_code === 0 ? 'OK' : 'ERR';
    }
    return parsed.kind;
}

function describeSignatureShort(parsed: ParsedReceipt): string {
    const sig = parsed.data.signature;
    return sig ? 'sig' : 'no-sig';
}

// ---------------------------------------------------------------------------
// Tree item
// ---------------------------------------------------------------------------

export class ReceiptTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly receiptFile?: ReceiptFile,
        public readonly isGroup = false,
        public readonly groupKey?: string
    ) {
        super(label, collapsibleState);

        if (receiptFile && !isGroup) {
            this.contextValue = 'receipt';
            this.tooltip = this.buildTooltip(receiptFile.parsed);
            this.description = this.buildDescription(receiptFile.parsed);
            this.iconPath = this.getIcon(receiptFile.parsed);
            this.command = {
                command: 'sonaReceipts.openReceipt',
                title: 'Open Receipt',
                arguments: [receiptFile]
            };
        } else if (isGroup) {
            this.contextValue = 'group';
            this.iconPath = new vscode.ThemeIcon('folder');
        }
    }

    // -- tooltip ----------------------------------------------------------

    private buildTooltip(parsed: ParsedReceipt): vscode.MarkdownString {
        const md = new vscode.MarkdownString();
        md.appendMarkdown(`**${parsed.displayLabel}**\n\n`);
        md.appendMarkdown(`- **Kind**: ${parsed.kind}\n`);
        md.appendMarkdown(`- **Sona**: ${parsed.data.sona_version}\n`);

        if (parsed.kind === 'execution') {
            const exec = (parsed.data as ExecutionReceipt).execution;
            md.appendMarkdown(`- **Exit Code**: ${exec.exit_code}\n`);
            md.appendMarkdown(`- **Duration**: ${exec.duration_ms}ms\n`);
        }

        if (parsed.kind === 'directory') {
            const dir = parsed.data as DirectoryReceipt;
            md.appendMarkdown(`- **Root**: ${dir.root_path}\n`);
            md.appendMarkdown(`- **Files**: ${dir.total_files}\n`);
            md.appendMarkdown(`- **Tree Hash**: \`${dir.tree_hash.slice(0, 12)}…\`\n`);
        }

        if (parsed.data.receipt_hash) {
            md.appendMarkdown(`- **Receipt Hash**: \`${parsed.data.receipt_hash.slice(0, 12)}…\`\n`);
        }
        if (parsed.data.policy_fingerprint) {
            md.appendMarkdown(`- **Policy**: \`${parsed.data.policy_fingerprint.slice(0, 12)}…\`\n`);
        }
        if (parsed.data.signature) {
            const keyId = parsed.data.signature.key_id ? ` (${parsed.data.signature.key_id})` : '';
            md.appendMarkdown(`- **Signature**: ${parsed.data.signature.algorithm}${keyId}\n`);
        } else {
            md.appendMarkdown(`- **Signature**: unsigned\n`);
        }
        if (parsed.data.redaction?.profile) {
            md.appendMarkdown(`- **Redaction**: profile=${parsed.data.redaction.profile}\n`);
        }

        if (parsed.kind === 'execution') {
            const git = (parsed.data as ExecutionReceipt).git;
            if (git) {
                md.appendMarkdown(
                    `- **Git**: ${git.branch}@${git.commit.slice(0, 7)}${git.dirty ? ' (dirty)' : ''}\n`
                );
            }
        }

        if (parsed.timestamp) {
            md.appendMarkdown(`\n*${parsed.timestamp}*`);
        }
        return md;
    }

    // -- description (inline text) ----------------------------------------

    private buildDescription(parsed: ParsedReceipt): string {
        const config = vscode.workspace.getConfiguration('sonaReceipts');
        const showTimestamps = config.get<boolean>('showTimestamps', true);

        const status = describeStatus(parsed);
        const sig = describeSignatureShort(parsed);

        let duration = '';
        if (parsed.kind === 'execution') {
            duration = `${(parsed.data as ExecutionReceipt).execution.duration_ms}ms`;
        }

        const parts = [status];
        if (duration) {
            parts.push(duration);
        }

        if (showTimestamps && parsed.timestamp) {
            const date = new Date(parsed.timestamp);
            const time = Number.isNaN(date.getTime())
                ? 'unknown'
                : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            parts.push(time);
        }

        parts.push(sig);
        return parts.join(' | ');
    }

    // -- icon -------------------------------------------------------------

    private getIcon(parsed: ParsedReceipt): vscode.ThemeIcon {
        switch (parsed.kind) {
            case 'execution': {
                const exitCode = (parsed.data as ExecutionReceipt).execution.exit_code;
                return exitCode === 0
                    ? new vscode.ThemeIcon('pass', new vscode.ThemeColor('testing.iconPassed'))
                    : new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
            }
            case 'directory':
                return new vscode.ThemeIcon('file-directory', new vscode.ThemeColor('charts.blue'));
            case 'bundle':
                return new vscode.ThemeIcon('package', new vscode.ThemeColor('charts.purple'));
            case 'chain':
                return new vscode.ThemeIcon('link', new vscode.ThemeColor('charts.orange'));
            case 'redaction':
                return new vscode.ThemeIcon('eye-closed', new vscode.ThemeColor('charts.yellow'));
            default:
                return new vscode.ThemeIcon('question', new vscode.ThemeColor('descriptionForeground'));
        }
    }
}

// ---------------------------------------------------------------------------
// Tree data provider
// ---------------------------------------------------------------------------

export class ReceiptTreeDataProvider implements vscode.TreeDataProvider<ReceiptTreeItem> {
    private readonly _onDidChangeTreeData = new vscode.EventEmitter<ReceiptTreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private receipts: ReceiptFile[] = [];
    private watcher: vscode.FileSystemWatcher | undefined;
    private refreshTimer: NodeJS.Timeout | undefined;
    private loading: Promise<void> | undefined;

    constructor(private readonly output: vscode.OutputChannel) {
        this.setupWatcher();
    }

    private getConfig(): {
        maxReceipts: number;
        groupByDate: boolean;
        autoRefresh: boolean;
        receiptGlob: string;
        statusFilter: 'all' | 'success' | 'failed';
    } {
        const config = vscode.workspace.getConfiguration('sonaReceipts');
        return {
            maxReceipts: Math.max(1, config.get<number>('maxReceipts', 100)),
            groupByDate: config.get<boolean>('groupByDate', true),
            autoRefresh: config.get<boolean>('autoRefresh', true),
            receiptGlob: config.get<string>('receiptGlob', '**/*.receipt.json') || '**/*.receipt.json',
            statusFilter: config.get<'all' | 'success' | 'failed'>('statusFilter', 'all') || 'all'
        };
    }

    private setupWatcher(): void {
        const { autoRefresh, receiptGlob } = this.getConfig();
        if (!autoRefresh) {
            return;
        }

        this.watcher = vscode.workspace.createFileSystemWatcher(receiptGlob);
        const scheduleRefresh = (): void => {
            if (this.refreshTimer) {
                clearTimeout(this.refreshTimer);
            }
            this.refreshTimer = setTimeout(() => this.refresh(), 150);
        };

        this.watcher.onDidCreate(scheduleRefresh);
        this.watcher.onDidChange(scheduleRefresh);
        this.watcher.onDidDelete(scheduleRefresh);
    }

    refresh(): void {
        this.receipts = [];
        this.loading = undefined;
        this._onDidChangeTreeData.fire(undefined);
    }

    async ensureLoaded(): Promise<void> {
        if (this.receipts.length > 0) {
            return;
        }
        if (!this.loading) {
            this.loading = this.loadReceipts();
        }
        await this.loading;
    }

    async getChildren(element?: ReceiptTreeItem): Promise<ReceiptTreeItem[]> {
        if (!vscode.workspace.workspaceFolders) {
            return [];
        }

        await this.ensureLoaded();

        if (!element) {
            const { groupByDate } = this.getConfig();
            return groupByDate ? this.getGroupedItems() : this.getFlatItems();
        }

        if (!element.isGroup || !element.groupKey) {
            return [];
        }

        return this.receipts
            .filter((item) => {
                const ts = item.parsed.timestamp || '';
                return getDateBucket(ts).key === element.groupKey;
            })
            .sort((a, b) => b.mtime - a.mtime)
            .map(
                (item) =>
                    new ReceiptTreeItem(
                        item.parsed.displayLabel,
                        vscode.TreeItemCollapsibleState.None,
                        item
                    )
            );
    }

    private async loadReceipts(): Promise<void> {
        const { maxReceipts, receiptGlob, statusFilter } = this.getConfig();

        let files: vscode.Uri[] = [];
        try {
            files = await vscode.workspace.findFiles(receiptGlob, '**/node_modules/**', maxReceipts * 4);
        } catch (err) {
            this.output.appendLine(`findFiles failed: ${String(err)}`);
            this.receipts = [];
            return;
        }

        const loaded: ReceiptFile[] = [];
        let invalidCount = 0;

        for (const uri of files) {
            try {
                const content = await vscode.workspace.fs.readFile(uri);
                const parsed = parseReceipt(Buffer.from(content).toString('utf8'));
                if (!parsed) {
                    invalidCount += 1;
                    continue;
                }

                // Status filtering applies only to execution receipts
                if (parsed.kind === 'execution') {
                    const exitCode = (parsed.data as import('./models').ExecutionReceipt).execution.exit_code;
                    if (statusFilter === 'success' && exitCode !== 0) {
                        continue;
                    }
                    if (statusFilter === 'failed' && exitCode === 0) {
                        continue;
                    }
                }

                const stat = await vscode.workspace.fs.stat(uri);
                loaded.push({ uri, parsed, mtime: stat.mtime });
            } catch (err) {
                invalidCount += 1;
                this.output.appendLine(`Failed to load receipt ${uri.fsPath}: ${String(err)}`);
            }
        }

        if (invalidCount > 0) {
            this.output.appendLine(`Skipped ${invalidCount} invalid receipt file(s).`);
        }

        this.receipts = loaded.sort((a, b) => b.mtime - a.mtime).slice(0, maxReceipts);
    }

    private getGroupedItems(): ReceiptTreeItem[] {
        const groups = new Map<string, { label: string; order: number; count: number }>();

        for (const item of this.receipts) {
            const ts = item.parsed.timestamp || '';
            const bucket = getDateBucket(ts);
            const current = groups.get(bucket.key);
            if (current) {
                current.count += 1;
            } else {
                groups.set(bucket.key, { label: bucket.label, order: bucket.order, count: 1 });
            }
        }

        return [...groups.entries()]
            .sort((a, b) => a[1].order - b[1].order)
            .map(([key, group]) => {
                const item = new ReceiptTreeItem(
                    group.label,
                    vscode.TreeItemCollapsibleState.Expanded,
                    undefined,
                    true,
                    key
                );
                item.description = `${group.count} receipt${group.count === 1 ? '' : 's'}`;
                return item;
            });
    }

    private getFlatItems(): ReceiptTreeItem[] {
        return this.receipts.map(
            (item) =>
                new ReceiptTreeItem(
                    item.parsed.displayLabel,
                    vscode.TreeItemCollapsibleState.None,
                    item
                )
        );
    }

    getTreeItem(element: ReceiptTreeItem): vscode.TreeItem {
        return element;
    }

    getReceipts(): ReceiptFile[] {
        return [...this.receipts];
    }

    dispose(): void {
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }
        this.watcher?.dispose();
    }
}
