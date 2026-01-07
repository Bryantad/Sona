                     import * as cp from "child_process";
import * as path from "path";
import * as vscode from "vscode";
import * as fs from "fs";

function tryExec(cmd: string, args: string[]): boolean {
  try {
    cp.execFileSync(cmd, args, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function resolvePython(): string {
  const cfg = vscode.workspace.getConfiguration("sona");
  const user = cfg.get<string>("pythonPath");
  if (user) return user;

  // Check workspace .venv first
  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (workspace) {
    const winVenv = path.join(workspace, '.venv', 'Scripts', 'python.exe');
    const posixVenv = path.join(workspace, '.venv', 'bin', 'python');
    if (process.platform === 'win32' && fs.existsSync(winVenv)) return winVenv;
    if (process.platform !== 'win32' && fs.existsSync(posixVenv)) return posixVenv;
  }

  if (process.platform === "win32") {
    if (tryExec("py", ["-3", "-V"])) return "py";
    if (tryExec("python", ["-V"])) return "python";
  } else {
    if (tryExec("python3", ["-V"])) return "python3";
    if (tryExec("python", ["-V"])) return "python";
  }
  return process.platform === "win32" ? "python" : "python3";
}

function resolveDevRunnerPath(): string | null {
  const cfg = vscode.workspace.getConfiguration("sona");
  const configured = cfg.get<string>("runtime.devRunnerPath");
  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

  if (configured) {
    const candidate = path.isAbsolute(configured) || !workspace
      ? configured
      : path.join(workspace, configured);
    if (fs.existsSync(candidate)) return candidate;
  }

  if (!workspace) return null;
  const quickRun = path.join(workspace, "quick_run.py");
  if (fs.existsSync(quickRun)) return quickRun;
  const runSona = path.join(workspace, "run_sona.py");
  if (fs.existsSync(runSona)) return runSona;
  return null;
}

function buildPythonCommand(py: string, runnerPath: string, args: string[]) {
  if (py === "py") {
    return { command: "py", args: ["-3", runnerPath, ...args] };
  }
  return { command: py, args: [runnerPath, ...args] };
}

function runtimeEnv(extPath: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env };
  const runtimeRoot = path.join(extPath, "runtime");
  const sep = process.platform === "win32" ? ";" : ":";
  env.PYTHONPATH = [runtimeRoot, process.env.PYTHONPATH || ""].filter(Boolean).join(sep);
  return env;
}

export async function verifyRuntime() {
  const ext = vscode.extensions.getExtension("waycoreinc.sona-ai-native-programming");
  if (!ext) return vscode.window.showErrorMessage("Sona extension not found.");
  const env = runtimeEnv(ext.extensionPath);
  const py = resolvePython();
  const script = path.join(ext.extensionPath, "runtime", "sonactl.py");

  try {
    cp.execFileSync(py, [script, "--verify"], { env, stdio: "inherit" });
    vscode.window.showInformationMessage("Sona runtime verified.");
  } catch (e: any) {
    vscode.window.showErrorMessage("Sona runtime verification failed. Check Python availability or open Output.");
  }
}

export async function openRepl() {
  const ext = vscode.extensions.getExtension("waycoreinc.sona-ai-native-programming");
  if (!ext) return vscode.window.showErrorMessage("Sona extension not found.");
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

export async function runFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active editor. Open a .sona file first.");
    return;
  }

  const doc = editor.document;
  if (doc.languageId !== "sona" && !doc.fileName.toLowerCase().endsWith(".sona")) {
    vscode.window.showWarningMessage("Current file is not a Sona file.");
    return;
  }

  // Save if dirty
  if (doc.isDirty) {
    await doc.save();
  }

  const filePath = doc.uri.fsPath;
  const py = resolvePython();

  // Check if workspace has a dev runner (development mode)
  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const devRunner = resolveDevRunnerPath();
  const hasSonaDir = workspace ? fs.existsSync(path.join(workspace, "sona")) : false;

  const term = vscode.window.createTerminal({ name: "Sona Run" });
  term.show();

  const pyCmd = py === "py" ? "py -3" : py;
  const quotedFile = `"${filePath}"`;

  let cmd: string;
  if (devRunner) {
    // Development mode: use dev runner (run_sona.py or quick_run.py)
    const quotedScript = `"${devRunner}"`;
    cmd = `${pyCmd} ${quotedScript} ${quotedFile}`;
  } else if (hasSonaDir && workspace) {
    // Workspace has sona package: use python -m sona.cli run
    if (process.platform === "win32") {
      cmd = `$env:PYTHONPATH="${workspace}"; ${pyCmd} -m sona.cli run ${quotedFile}`;
    } else {
      cmd = `PYTHONPATH="${workspace}" ${pyCmd} -m sona.cli run ${quotedFile}`;
    }
  } else {
    // Installed sona: use python -m sona.cli run
    cmd = `${pyCmd} -m sona.cli run ${quotedFile}`;
  }

  term.sendText(cmd);
}

export async function runFileInDebug() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active editor. Open a .sona file first.");
    return;
  }

  const doc = editor.document;
  if (doc.languageId !== "sona" && !doc.fileName.toLowerCase().endsWith(".sona")) {
    vscode.window.showWarningMessage("Current file is not a Sona file.");
    return;
  }

  if (doc.isDirty) {
    await doc.save();
  }

  const filePath = doc.uri.fsPath;
  const py = resolvePython();
  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const devRunner = resolveDevRunnerPath();
  const hasSonaDir = workspace ? fs.existsSync(path.join(workspace, "sona")) : false;

  const term = vscode.window.createTerminal({ name: "Sona Debug" });
  term.show();

  const pyCmd = py === "py" ? "py -3" : py;
  const quotedFile = `"${filePath}"`;

  let cmd: string;
  if (devRunner) {
    // Development mode: use dev runner with --debug
    const quotedScript = `"${devRunner}"`;
    cmd = `${pyCmd} ${quotedScript} --debug ${quotedFile}`;
  } else if (hasSonaDir && workspace) {
    // Workspace has sona package: use python -m sona.cli run --debug
    if (process.platform === "win32") {
      cmd = `$env:PYTHONPATH="${workspace}"; ${pyCmd} -m sona.cli run --debug ${quotedFile}`;
    } else {
      cmd = `PYTHONPATH="${workspace}" ${pyCmd} -m sona.cli run --debug ${quotedFile}`;
    }
  } else {
    // Installed sona: use python -m sona.cli run --debug
    cmd = `${pyCmd} -m sona.cli run --debug ${quotedFile}`;
  }

  term.sendText(cmd);
}

export async function exportCognitiveReport(
  filePath: string,
  format: "md" | "json",
  outPath: string,
  outputChannel?: vscode.OutputChannel
) {
  const py = resolvePython();
  const devRunner = resolveDevRunnerPath();
  if (!devRunner) {
    vscode.window.showErrorMessage("Sona dev runner not found. Configure sona.runtime.devRunnerPath or add run_sona.py.");
    return;
  }

  const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const { command, args } = buildPythonCommand(py, devRunner, [
    "report",
    filePath,
    "--format",
    format,
    "--out",
    outPath,
  ]);

  outputChannel?.appendLine(`[sona] export report: ${command} ${args.join(" ")}`);

  await new Promise<void>((resolve, reject) => {
    cp.execFile(command, args, { cwd: workspace ?? undefined }, (err, stdout, stderr) => {
      if (stdout) outputChannel?.appendLine(stdout.trim());
      if (stderr) outputChannel?.appendLine(stderr.trim());
      if (err) {
        reject(err);
        return;
      }
      resolve();
    });
  });
}
