import * as cp from "child_process";
import * as path from "path";
import * as vscode from "vscode";

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

  if (process.platform === "win32") {
    if (tryExec("py", ["-3", "-V"])) return "py";
    if (tryExec("python", ["-V"])) return "python";
  } else {
    if (tryExec("python3", ["-V"])) return "python3";
    if (tryExec("python", ["-V"])) return "python";
  }
  return process.platform === "win32" ? "python" : "python3";
}

function runtimeEnv(extPath: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env };
  const runtimeRoot = path.join(extPath, "runtime");
  const sep = process.platform === "win32" ? ";" : ":";
  env.PYTHONPATH = [runtimeRoot, process.env.PYTHONPATH || ""].filter(Boolean).join(sep);
  return env;
}

export async function verifyRuntime() {
  const ext = vscode.extensions.getExtension("Waycoreinc.sona-ai-native-programming");
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
  const ext = vscode.extensions.getExtension("Waycoreinc.sona-ai-native-programming");
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
