import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

function explicitConfigurationValue(
  configuration: vscode.WorkspaceConfiguration,
  key: string
): string | undefined {
  const inspected = configuration.inspect<string>(key);
  return inspected?.workspaceFolderValue
    ?? inspected?.workspaceValue
    ?? inspected?.globalValue;
}

export function resolveSonaPythonPath(resource?: vscode.Uri): string {
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

  return configuration.get<string>("cli.pythonPath")?.trim() || "python";
}
