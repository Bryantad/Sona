import * as path from "path";
import * as vscode from "vscode";

import { AgentContext } from "./providers";

export interface ContextToggles {
  currentFile: boolean;
  selectedText: boolean;
  workspaceSummary: boolean;
  diagnostics: boolean;
}

const MAX_SELECTION_CHARS = 6000;

export async function collectContext(toggles: ContextToggles): Promise<AgentContext> {
  const editor = vscode.window.activeTextEditor;
  const context: AgentContext = {};

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
  } else if (toggles.currentFile) {
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

function collectDiagnostics(editor: vscode.TextEditor): unknown[] {
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

function normalizeDiagnosticCode(code: vscode.Diagnostic["code"]): string | number | undefined {
  if (typeof code === "string" || typeof code === "number") {
    return code;
  }
  return code?.value;
}

function clip(value: string, limit: number): string {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, Math.max(0, limit - 3))}...`;
}
