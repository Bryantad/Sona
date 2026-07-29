"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CliDeveloperIntelligenceTransport = void 0;
exports.isDeveloperTask = isDeveloperTask;
const child_process_1 = require("child_process");
class CliDeveloperIntelligenceTransport {
    pythonPath;
    workspacePath;
    timeoutMs;
    spawnProcess;
    constructor(pythonPath, workspacePath, timeoutMs = 30000, spawnProcess = child_process_1.spawn) {
        this.pythonPath = pythonPath;
        this.workspacePath = workspacePath;
        this.timeoutMs = timeoutMs;
        this.spawnProcess = spawnProcess;
    }
    execute(request, providerId) {
        if (!isDeveloperTask(request)) {
            return Promise.resolve({
                agentId: request.agentId,
                status: "error",
                text: "Unsupported task: Sona accepts developer-intelligence work, not general chat."
            });
        }
        return new Promise(resolve => {
            const payload = {
                schema_version: 1,
                task_type: "suggest",
                instruction: request.prompt,
                provider_id: providerId,
                target_files: request.context.currentFile ? [request.context.currentFile] : [],
                context: {
                    active_file: request.context.currentFile,
                    selected_text: request.context.selection,
                    diagnostics: request.context.diagnostics || [],
                    workspace_summary: request.context.workspaceName,
                    language_id: request.context.languageId,
                    origin: "vscode"
                },
                constraints: {
                    read_only: true,
                    allow_file_writes: false,
                    allow_shell: false,
                    allow_network: Boolean(providerId)
                }
            };
            const child = this.spawnProcess(this.pythonPath, ["-m", "sona", "ai", "task", "--request", "-", "--format", "json"], { cwd: this.workspacePath, windowsHide: true, shell: false });
            let stdout = "";
            let stderr = "";
            let finished = false;
            const finish = (response) => {
                if (finished)
                    return;
                finished = true;
                clearTimeout(timer);
                resolve(response);
            };
            const timer = setTimeout(() => {
                child.kill();
                finish({ agentId: request.agentId, status: "error", text: "Sona backend task timed out." });
            }, this.timeoutMs);
            child.stdout.on("data", value => { stdout += value.toString(); });
            child.stderr.on("data", value => { stderr += value.toString(); });
            child.on("error", error => finish({ agentId: request.agentId, status: "error", text: error.message }));
            child.on("close", code => {
                if (code !== 0) {
                    finish({
                        agentId: request.agentId,
                        status: "error",
                        text: stderr || `Sona backend exited with status ${code}.`
                    });
                    return;
                }
                try {
                    const data = JSON.parse(stdout);
                    const unavailable = data.status === "unavailable" || data.status === "approval_required";
                    finish({
                        agentId: request.agentId,
                        status: unavailable ? "not_configured" : data.status === "failed" || data.status === "denied" ? "error" : "ok",
                        text: data.summary || data.diagnostics?.[0]?.message || "Sona returned no task summary."
                    });
                }
                catch {
                    finish({ agentId: request.agentId, status: "error", text: stderr || stdout || "Invalid Sona backend response." });
                }
            });
            child.stdin.write(JSON.stringify(payload));
            child.stdin.end();
        });
    }
}
exports.CliDeveloperIntelligenceTransport = CliDeveloperIntelligenceTransport;
function isDeveloperTask(request) {
    if (request.context.currentFile || request.context.selection || (request.context.diagnostics || []).length) {
        return true;
    }
    return /\b(code|function|class|module|test|bug|error|diagnos|refactor|implement|sona|python|typescript|javascript|compile|runtime|parser|api|algorithm|recursion|stack|trace|lint|repository|file)\b/i.test(request.prompt);
}
