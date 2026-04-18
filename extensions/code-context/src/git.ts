import * as path from 'path';
import * as vscode from 'vscode';
import { execSync } from 'child_process';

export function getNearbyCommit(filePath: string, line: number): string | undefined {
    const config = vscode.workspace.getConfiguration('codeContext');
    if (!config.get<boolean>('showGitBlameHint', true)) {
        return undefined;
    }

    try {
        const dir = path.dirname(filePath);
        const result = execSync(
            `git blame -L ${line + 1},${line + 1} --porcelain "${path.basename(filePath)}"`,
            { cwd: dir, encoding: 'utf8', timeout: 2000 }
        );
        const match = result.match(/^([a-f0-9]{40})/);
        if (match && match[1] && !match[1].startsWith('00000000')) {
            return match[1].substring(0, 7);
        }
    } catch {
        // Git not available or not a git repo.
    }

    return undefined;
}
