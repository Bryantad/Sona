import * as path from 'path';
import * as vscode from 'vscode';
import { ReceiptFile, ExecutionReceipt } from './models';
import { runSonaCommand } from './cli';
import { ReceiptTreeItem, ReceiptTreeDataProvider } from './tree';
import { ReceiptDetailPanel, formatReceiptForDiff, describeSignature } from './views';

interface ReceiptCommandResult {
    stdout: string;
    stderr: string;
    cmd: string;
    exitCode: number;
}

// ---------------------------------------------------------------------------
// Receipt resolution helper
// ---------------------------------------------------------------------------

export function resolveReceiptFile(
    candidate: unknown,
    treeView: vscode.TreeView<ReceiptTreeItem>
): ReceiptFile | undefined {
    if (candidate && typeof candidate === 'object') {
        const maybeReceiptFile = candidate as Partial<ReceiptFile>;
        if (maybeReceiptFile.parsed && maybeReceiptFile.uri) {
            return maybeReceiptFile as ReceiptFile;
        }

        const maybeTreeItem = candidate as Partial<ReceiptTreeItem>;
        if (maybeTreeItem.receiptFile) {
            return maybeTreeItem.receiptFile;
        }
    }

    const selected = treeView.selection[0];
    return selected?.receiptFile;
}

function getWorkspaceRoot(): string | undefined {
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function inferReceiptDirectory(
    treeDataProvider: ReceiptTreeDataProvider,
    receiptFile?: ReceiptFile
): string | undefined {
    if (receiptFile) {
        return path.dirname(receiptFile.uri.fsPath);
    }

    const receipts = treeDataProvider.getReceipts();
    if (receipts.length === 0) {
        const workspaceRoot = getWorkspaceRoot();
        return workspaceRoot ? path.join(workspaceRoot, '.sona', 'receipts') : undefined;
    }

    const firstDir = path.dirname(receipts[0].uri.fsPath);
    const allSameDir = receipts.every((item) => path.dirname(item.uri.fsPath) === firstDir);
    if (allSameDir) {
        return firstDir;
    }

    const workspaceRoot = getWorkspaceRoot();
    return workspaceRoot ? path.join(workspaceRoot, '.sona', 'receipts') : firstDir;
}

async function runReceiptCommand(
    args: string[],
    output: vscode.OutputChannel,
    cwd?: string
): Promise<ReceiptCommandResult> {
    const result = await runSonaCommand(args, cwd);
    output.appendLine(`$ ${result.cmd}`);
    if (result.stdout.trim()) {
        output.appendLine(result.stdout.trim());
    }
    if (result.stderr.trim()) {
        output.appendLine(result.stderr.trim());
    }
    return result;
}

// ---------------------------------------------------------------------------
// Command: verify signature
// ---------------------------------------------------------------------------

async function verifySignature(receiptFile: ReceiptFile, output: vscode.OutputChannel): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    try {
        const result = await runReceiptCommand(['receipt', 'verify-signature', receiptFile.uri.fsPath], output, workspaceRoot);
        if (result.exitCode !== 0) {
            throw new Error(result.stderr.trim() || result.stdout.trim() || 'signature verification failed');
        }
        vscode.window.showInformationMessage('Receipt signature verified.');
    } catch (err) {
        vscode.window.showErrorMessage(`Signature verification failed: ${String(err)}`);
        output.appendLine(String(err));
    }
}

// ---------------------------------------------------------------------------
// Command: redact receipt
// ---------------------------------------------------------------------------

async function redactReceipt(
    receiptFile: ReceiptFile,
    profile: string,
    outPath: string,
    output: vscode.OutputChannel
): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    try {
        const result = await runReceiptCommand(
            ['receipt', 'redact', receiptFile.uri.fsPath, '--profile', profile, '--out', outPath],
            output,
            workspaceRoot
        );
        if (result.exitCode !== 0) {
            throw new Error(result.stderr.trim() || result.stdout.trim() || 'redaction failed');
        }
        vscode.window.showInformationMessage(`Redacted receipt written to ${outPath}`);
    } catch (err) {
        vscode.window.showErrorMessage(`Redaction failed: ${String(err)}`);
        output.appendLine(String(err));
    }
}

async function verifyReceiptChain(
    treeDataProvider: ReceiptTreeDataProvider,
    treeView: vscode.TreeView<ReceiptTreeItem>,
    output: vscode.OutputChannel,
    arg?: unknown
): Promise<void> {
    const receiptFile = resolveReceiptFile(arg, treeView);
    const receiptDir = inferReceiptDirectory(treeDataProvider, receiptFile);
    const workspaceRoot = getWorkspaceRoot();

    if (!receiptDir) {
        vscode.window.showWarningMessage('No receipt directory could be determined.');
        return;
    }

    const result = await runReceiptCommand(['receipt', 'verify-chain', '--dir', receiptDir], output, workspaceRoot);
    if (result.exitCode === 0) {
        vscode.window.showInformationMessage(`Receipt chain verified for ${receiptDir}`);
        return;
    }

    vscode.window.showErrorMessage('Receipt chain verification failed. See Sona Receipt Explorer output for details.');
}

async function exportReceiptBundle(
    treeDataProvider: ReceiptTreeDataProvider,
    treeView: vscode.TreeView<ReceiptTreeItem>,
    output: vscode.OutputChannel,
    arg?: unknown
): Promise<void> {
    const receiptFile = resolveReceiptFile(arg, treeView);
    const receiptDir = inferReceiptDirectory(treeDataProvider, receiptFile);
    const workspaceRoot = getWorkspaceRoot();

    if (!receiptDir) {
        vscode.window.showWarningMessage('No receipt directory could be determined.');
        return;
    }

    const defaultOutput = path.join(receiptDir, 'receipt-bundle.json');
    const outputPath = await vscode.window.showInputBox({
        prompt: 'Output path for the receipt bundle',
        value: defaultOutput,
        ignoreFocusOut: true
    });
    if (!outputPath) {
        return;
    }

    const includeLockChoice = await vscode.window.showQuickPick(
        [
            { label: 'No lockfile payload', value: false },
            { label: 'Include workspace lockfile payload', value: true }
        ],
        {
            placeHolder: 'Choose whether to include workspace lockfile payload',
            ignoreFocusOut: true
        }
    );
    if (!includeLockChoice) {
        return;
    }

    const args = ['receipt', 'export', '--dir', receiptDir, '--output', outputPath];
    if (includeLockChoice.value) {
        args.push('--include-lock');
        if (workspaceRoot) {
            args.push('--workspace', workspaceRoot);
        }
    }

    const result = await runReceiptCommand(args, output, workspaceRoot);
    if (result.exitCode !== 0) {
        vscode.window.showErrorMessage('Receipt bundle export failed. See Sona Receipt Explorer output for details.');
        return;
    }

    vscode.window.showInformationMessage(`Receipt bundle exported to ${outputPath}`);
    try {
        const document = await vscode.workspace.openTextDocument(outputPath);
        await vscode.window.showTextDocument(document, { preview: true });
    } catch {
        // Best effort only.
    }
}

// ---------------------------------------------------------------------------
// Diff helper
// ---------------------------------------------------------------------------

async function showReceiptDiff(receipt1: ReceiptFile, receipt2: ReceiptFile): Promise<void> {
    const doc1 = await vscode.workspace.openTextDocument({
        content: formatReceiptForDiff(receipt1.parsed),
        language: 'markdown'
    });
    const doc2 = await vscode.workspace.openTextDocument({
        content: formatReceiptForDiff(receipt2.parsed),
        language: 'markdown'
    });

    const title = `Receipt Comparison: ${path.basename(receipt1.uri.fsPath)} <-> ${path.basename(receipt2.uri.fsPath)}`;
    await vscode.commands.executeCommand('vscode.diff', doc1.uri, doc2.uri, title);
}

// ---------------------------------------------------------------------------
// Describe status for compare picker
// ---------------------------------------------------------------------------

function describeStatus(parsed: import('./models').ParsedReceipt): string {
    if (parsed.kind === 'execution') {
        const exec = (parsed.data as ExecutionReceipt).execution;
        return exec.exit_code === 0 ? 'OK' : 'ERR';
    }
    return parsed.kind;
}

// ---------------------------------------------------------------------------
// Register all commands
// ---------------------------------------------------------------------------

export function registerCommands(
    context: vscode.ExtensionContext,
    treeDataProvider: ReceiptTreeDataProvider,
    treeView: vscode.TreeView<ReceiptTreeItem>,
    output: vscode.OutputChannel
): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.refresh', () => {
            treeDataProvider.refresh();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.exploreReceipts', async () => {
            treeDataProvider.refresh();
            await vscode.commands.executeCommand('workbench.view.extension.sona-receipts');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.openReceipt', (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                void vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }
            ReceiptDetailPanel.show(receiptFile);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.openReceiptJson', async (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }
            try {
                const doc = await vscode.workspace.openTextDocument(receiptFile.uri);
                await vscode.window.showTextDocument(doc, { preview: true });
            } catch (err) {
                vscode.window.showErrorMessage(`Unable to open receipt JSON: ${String(err)}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.verifySignature', async (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }
            await verifySignature(receiptFile, output);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.redactReceipt', async (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }

            const profile = await vscode.window.showQuickPick(['prod', 'ci', 'dev'], {
                placeHolder: 'Choose redaction profile',
                ignoreFocusOut: true
            });
            if (!profile) {
                return;
            }

            const parsed = path.parse(receiptFile.uri.fsPath);
            const suggested = path.join(parsed.dir, `${parsed.name}.redacted${parsed.ext || '.json'}`);
            const outPath = await vscode.window.showInputBox({
                prompt: 'Output path for redacted receipt',
                value: suggested,
                ignoreFocusOut: true
            });
            if (!outPath) {
                return;
            }

            await redactReceipt(receiptFile, profile, outPath, output);
            treeDataProvider.refresh();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.compareReceipts', async () => {
            await treeDataProvider.ensureLoaded();
            const receipts = treeDataProvider.getReceipts();
            if (receipts.length < 2) {
                vscode.window.showWarningMessage('Need at least 2 receipts to compare.');
                return;
            }

            const items = receipts.map((r) => ({
                label: r.parsed.displayLabel,
                description: r.parsed.timestamp || '',
                detail: describeStatus(r.parsed),
                receipt: r
            }));

            const pick1 = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select first receipt'
            });
            if (!pick1) {
                return;
            }

            const pick2 = await vscode.window.showQuickPick(
                items.filter((item) => item.receipt !== pick1.receipt),
                { placeHolder: 'Select second receipt' }
            );
            if (!pick2) {
                return;
            }

            await showReceiptDiff(pick1.receipt, pick2.receipt);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.verifyReceiptChain', async (arg?: unknown) => {
            await treeDataProvider.ensureLoaded();
            await verifyReceiptChain(treeDataProvider, treeView, output, arg);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.exportReceiptBundle', async (arg?: unknown) => {
            await treeDataProvider.ensureLoaded();
            await exportReceiptBundle(treeDataProvider, treeView, output, arg);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.rerunFromReceipt', (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                void vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }

            if (receiptFile.parsed.kind !== 'execution') {
                vscode.window.showWarningMessage('Re-run is only available for execution receipts.');
                return;
            }

            const terminal = vscode.window.createTerminal('Sona Re-run');
            terminal.show();
            terminal.sendText((receiptFile.parsed.data as ExecutionReceipt).reproduce.command);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.copyReproduceCommand', async (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }

            if (receiptFile.parsed.kind !== 'execution') {
                vscode.window.showWarningMessage('Reproduce command is only available for execution receipts.');
                return;
            }

            await vscode.env.clipboard.writeText((receiptFile.parsed.data as ExecutionReceipt).reproduce.command);
            vscode.window.showInformationMessage('Reproduce command copied to clipboard.');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.deleteReceipt', async (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }

            const confirm = await vscode.window.showWarningMessage(
                `Delete receipt ${path.basename(receiptFile.uri.fsPath)}?`,
                { modal: true },
                'Delete'
            );

            if (confirm !== 'Delete') {
                return;
            }

            try {
                await vscode.workspace.fs.delete(receiptFile.uri);
                treeDataProvider.refresh();
                vscode.window.showInformationMessage('Receipt deleted.');
            } catch (err) {
                vscode.window.showErrorMessage(`Failed to delete receipt: ${String(err)}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sonaReceipts.exportReceipt', async (arg?: unknown) => {
            const receiptFile = resolveReceiptFile(arg, treeView);
            if (!receiptFile) {
                vscode.window.showWarningMessage('Select a receipt first.');
                return;
            }

            const md: string[] = [];
            const parsed = receiptFile.parsed;
            md.push(`# Receipt: ${parsed.displayLabel}`);
            md.push('');
            md.push(`**Kind**: ${parsed.kind}`);
            md.push(`**Timestamp**: ${parsed.timestamp || 'unknown'}`);
            md.push('');

            if (parsed.kind === 'execution') {
                const r = parsed.data as ExecutionReceipt;
                md.push(`**Status**: ${r.execution.exit_code === 0 ? 'Success' : 'Failed'}`);
                md.push('');
                md.push('## Execution');
                md.push(`- Duration: ${r.execution.duration_ms}ms`);
                md.push(`- Exit Code: ${r.execution.exit_code}`);
                if (r.execution.error) {
                    md.push(`- Error: \`${r.execution.error}\``);
                }
                md.push('');
                md.push('## Source');
                md.push(`- File: \`${r.code.source_file}\``);
                md.push(`- Size: ${r.code.source_size_bytes} bytes`);
                md.push(`- SHA-256: \`${r.code.source_sha256}\``);
                md.push('');
                md.push('## Environment');
                md.push(`- Sona: ${r.sona_version}`);
                md.push(`- Python: ${r.dependencies.python_version}`);
                md.push('');
                if (r.git) {
                    md.push('## Git');
                    md.push(`- Branch: ${r.git.branch}`);
                    md.push(`- Commit: \`${r.git.commit}\``);
                    md.push(`- Dirty: ${r.git.dirty ? 'Yes' : 'No'}`);
                    md.push('');
                }
                md.push('## Reproduce');
                md.push('```bash');
                md.push(r.reproduce.command);
                md.push('```');
                md.push('');
            }

            if (parsed.kind === 'directory') {
                const r = parsed.data as import('./models').DirectoryReceipt;
                md.push('## Directory');
                md.push(`- Root: \`${r.root_path}\``);
                md.push(`- Mode: ${r.mode}`);
                md.push(`- Files: ${r.total_files}`);
                md.push(`- Bytes: ${r.total_bytes}`);
                md.push(`- Tree Hash: \`${r.tree_hash}\``);
                md.push('');
            }

            md.push('## Trust & Governance');
            md.push(`- Receipt Version: ${parsed.data.receipt_version}`);
            md.push(`- Receipt Hash: ${parsed.data.receipt_hash ? `\`${parsed.data.receipt_hash}\`` : 'N/A'}`);
            md.push(`- Previous Receipt Hash: ${parsed.data.prev_receipt_hash ? `\`${parsed.data.prev_receipt_hash}\`` : 'N/A'}`);
            md.push(`- Policy Fingerprint: ${parsed.data.policy_fingerprint ? `\`${parsed.data.policy_fingerprint}\`` : 'N/A'}`);
            md.push(`- Engine Policy Fingerprint: ${parsed.data.engine_policy_fingerprint ? `\`${parsed.data.engine_policy_fingerprint}\`` : 'N/A'}`);
            md.push(`- Signature: ${describeSignature(parsed.data)}`);
            md.push(`- Signed At: ${parsed.data.signature?.signed_at_utc || 'N/A'}`);

            const doc = await vscode.workspace.openTextDocument({
                content: md.join('\n'),
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        })
    );
}
