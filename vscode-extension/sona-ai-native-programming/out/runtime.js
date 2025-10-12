"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyRuntime = verifyRuntime;
exports.openRepl = openRepl;
const cp = __importStar(require("child_process"));
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
function tryExec(cmd, args) {
    try {
        cp.execFileSync(cmd, args, { stdio: "ignore" });
        return true;
    }
    catch {
        return false;
    }
}
function resolvePython() {
    const cfg = vscode.workspace.getConfiguration("sona");
    const user = cfg.get("pythonPath");
    if (user)
        return user;
    if (process.platform === "win32") {
        if (tryExec("py", ["-3", "-V"]))
            return "py";
        if (tryExec("python", ["-V"]))
            return "python";
    }
    else {
        if (tryExec("python3", ["-V"]))
            return "python3";
        if (tryExec("python", ["-V"]))
            return "python";
    }
    return process.platform === "win32" ? "python" : "python3";
}
function runtimeEnv(extPath) {
    const env = { ...process.env };
    const runtimeRoot = path.join(extPath, "runtime");
    const sep = process.platform === "win32" ? ";" : ":";
    env.PYTHONPATH = [runtimeRoot, process.env.PYTHONPATH || ""].filter(Boolean).join(sep);
    return env;
}
async function verifyRuntime() {
    const ext = vscode.extensions.getExtension("waycoreinc.sona-ai-native-programming");
    if (!ext)
        return vscode.window.showErrorMessage("Sona extension not found.");
    const env = runtimeEnv(ext.extensionPath);
    const py = resolvePython();
    const script = path.join(ext.extensionPath, "runtime", "sonactl.py");
    try {
        cp.execFileSync(py, [script, "--verify"], { env, stdio: "inherit" });
        vscode.window.showInformationMessage("Sona runtime verified.");
    }
    catch (e) {
        vscode.window.showErrorMessage("Sona runtime verification failed. Check Python availability or open Output.");
    }
}
async function openRepl() {
    const ext = vscode.extensions.getExtension("waycoreinc.sona-ai-native-programming");
    if (!ext)
        return vscode.window.showErrorMessage("Sona extension not found.");
    const env = runtimeEnv(ext.extensionPath);
    const py = resolvePython();
    const script = path.join(ext.extensionPath, "runtime", "sonactl.py");
    const term = vscode.window.createTerminal({ name: "Sona REPL" });
    term.show();
    const pyCmd = py === "py" ? "py -3" : py;
    const quotedScript = `"${script.replace(/\\/g, "\\\\")}"`;
    const exportCmd = process.platform === "win32"
        ? `$env:PYTHONPATH="${env.PYTHONPATH}"; ${pyCmd} ${quotedScript}`
        : `export PYTHONPATH="${env.PYTHONPATH}"; ${pyCmd} ${quotedScript}`;
    term.sendText(exportCmd);
}
//# sourceMappingURL=runtime.js.map