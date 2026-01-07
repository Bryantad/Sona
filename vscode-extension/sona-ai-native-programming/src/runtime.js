"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.openRepl = exports.verifyRuntime = void 0;
const cp = require("child_process");
const path = require("path");
const vscode = require("vscode");
function tryExec(cmd, args) {
    try {
        cp.execFileSync(cmd, args, { stdio: "ignore" });
        return true;
    }
    catch (_a) {
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
    const env = Object.assign({}, process.env);
    const runtimeRoot = path.join(extPath, "runtime");
    const sep = process.platform === "win32" ? ";" : ":";
    env.PYTHONPATH = [runtimeRoot, process.env.PYTHONPATH || ""].filter(Boolean).join(sep);
    return env;
}
function verifyRuntime() {
    return __awaiter(this, void 0, void 0, function* () {
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
    });
}
exports.verifyRuntime = verifyRuntime;
function openRepl() {
    return __awaiter(this, void 0, void 0, function* () {
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
    });
}
exports.openRepl = openRepl;
//# sourceMappingURL=runtime.js.map