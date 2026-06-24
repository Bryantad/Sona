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
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.collectContext = void 0;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const MAX_SELECTION_CHARS = 6000;
async function collectContext(toggles) {
    const editor = vscode.window.activeTextEditor;
    const context = {};
    if (toggles.workspaceSummary) {
        const workspaceFolder = editor
            ? vscode.workspace.getWorkspaceFolder(editor.document.uri)
            : vscode.workspace.workspaceFolders?.[0];
        context.workspaceName = workspaceFolder?.name;
    }
    if (!editor) {
        return context;
    }
    if (toggles.currentFile && editor.document.uri.scheme === "file") {
        context.currentFile = editor.document.uri.fsPath;
        context.languageId = editor.document.languageId;
    }
    else if (toggles.currentFile) {
        context.currentFile = editor.document.uri.toString(true);
        context.languageId = editor.document.languageId;
    }
    if (toggles.selectedText && !editor.selection.isEmpty) {
        context.selection = clip(editor.document.getText(editor.selection), MAX_SELECTION_CHARS);
    }
    if (toggles.diagnostics) {
        context.diagnostics = collectDiagnostics(editor);
    }
    return context;
}
exports.collectContext = collectContext;
function collectDiagnostics(editor) {
    return vscode.languages.getDiagnostics(editor.document.uri).map(diagnostic => ({
        message: diagnostic.message,
        severity: diagnostic.severity,
        source: diagnostic.source,
        code: normalizeDiagnosticCode(diagnostic.code),
        line: diagnostic.range.start.line + 1,
        character: diagnostic.range.start.character + 1,
        file: editor.document.uri.scheme === "file"
            ? path.basename(editor.document.uri.fsPath)
            : editor.document.uri.toString(true)
    }));
}
function normalizeDiagnosticCode(code) {
    if (typeof code === "string" || typeof code === "number") {
        return code;
    }
    return code?.value;
}
function clip(value, limit) {
    if (value.length <= limit) {
        return value;
    }
    return `${value.slice(0, Math.max(0, limit - 3))}...`;
}
//# sourceMappingURL=contextCollector.js.map