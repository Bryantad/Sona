import { promisify } from 'util';
import { exec } from 'child_process';

const execAsync = promisify(exec);

function quote(arg: string): string {
    return `"${arg.replace(/"/g, '\\"')}"`;
}

export async function runSonaCommand(
    args: string[],
    cwd?: string
): Promise<{ stdout: string; stderr: string; cmd: string; exitCode: number }> {
    const cmd = `sona ${args.map(quote).join(' ')}`;
    try {
        const { stdout, stderr } = await execAsync(cmd, {
            cwd,
            env: process.env,
            windowsHide: true,
            encoding: 'utf8'
        });
        return { stdout, stderr, cmd, exitCode: 0 };
    } catch (error) {
        const execError = error as {
            stdout?: string;
            stderr?: string;
            code?: number;
            message?: string;
        };
        return {
            stdout: execError.stdout ?? '',
            stderr: execError.stderr ?? execError.message ?? String(error),
            cmd,
            exitCode: typeof execError.code === 'number' ? execError.code : 1
        };
    }
}
