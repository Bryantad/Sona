"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.runSonaCommand = runSonaCommand;
const util_1 = require("util");
const child_process_1 = require("child_process");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
function quote(arg) {
    return `"${arg.replace(/"/g, '\\"')}"`;
}
async function runSonaCommand(args, cwd) {
    const cmd = `sona ${args.map(quote).join(' ')}`;
    try {
        const { stdout, stderr } = await execAsync(cmd, {
            cwd,
            env: process.env,
            windowsHide: true,
            encoding: 'utf8'
        });
        return { stdout, stderr, cmd, exitCode: 0 };
    }
    catch (error) {
        const execError = error;
        return {
            stdout: execError.stdout ?? '',
            stderr: execError.stderr ?? execError.message ?? String(error),
            cmd,
            exitCode: typeof execError.code === 'number' ? execError.code : 1
        };
    }
}
//# sourceMappingURL=cli.js.map