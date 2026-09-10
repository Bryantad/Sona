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
exports.resolveSonaPythonPath = resolveSonaPythonPath;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
function explicitConfigurationValue(configuration, key) {
    const inspected = configuration.inspect(key);
    return inspected?.workspaceFolderValue
        ?? inspected?.workspaceValue
        ?? inspected?.globalValue;
}
function resolveSonaPythonPath(resource) {
    const configuration = vscode.workspace.getConfiguration("sona", resource);
    const configured = explicitConfigurationValue(configuration, "cli.pythonPath")
        || explicitConfigurationValue(configuration, "pythonPath");
    if (configured?.trim()) {
        return configured.trim();
    }
    const workspace = resource
        ? vscode.workspace.getWorkspaceFolder(resource)?.uri.fsPath
        : vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (workspace) {
        const windowsCandidate = path.join(workspace, ".venv", "Scripts", "python.exe");
        const posixCandidate = path.join(workspace, ".venv", "bin", "python");
        if (process.platform === "win32" && fs.existsSync(windowsCandidate)) {
            return windowsCandidate;
        }
        if (process.platform !== "win32" && fs.existsSync(posixCandidate)) {
            return posixCandidate;
        }
    }
    return configuration.get("cli.pythonPath")?.trim() || "python";
}
