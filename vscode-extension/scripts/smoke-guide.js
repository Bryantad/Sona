const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const Module = require("node:module");
const os = require("node:os");
const { requestCheckedFacts, checkedFactArguments } = require("../out/guideFacts.js");

const root = path.resolve(__dirname, "../..");
const model = require("../out/guideModel.js");
const python = process.env.SONA_TEST_PYTHON || path.join(root, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const uri = "file:///guide-preview.sona";
const source = "let quantity = 3;\nprint(quant);\n";

function cli(request, extra) {
  const result = spawnSync(python, ["-m", "sona", ...(extra || ["guide", "request", "--json", "--no-profile"])], {
    input: request ? JSON.stringify(request) : undefined, encoding: "utf8", cwd: root,
    env: { ...process.env, PYTHONPATH: root }, timeout: 15000, windowsHide: true, shell: false
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

async function main() {
  const project = fs.mkdtempSync(path.join(os.tmpdir(), "sona-guide-facts-"));
  try {
    const receipt = path.join(root, "tests/proof/fixtures/0.15.4-native-hello.json");
    for (const mode of ["guided", "balanced", "expert"]) {
      const result = await requestCheckedFacts(python, "proof", project, { mode }, receipt);
      const expected = cli(null, ["guide", "proof", receipt, "--project-root", project, "--mode", mode, "--json"]);
      assert.deepEqual(result, expected);
      assert.equal(model.guideText(result), expected.text);
    }
    const invalid = await requestCheckedFacts(python, "proof", project, {}, path.join(project, "missing.sproof"));
    assert.equal(invalid.facts.status, "invalid");
    assert(invalid.text.includes("PROOF-VERIFY-002"));
    const guardian = await requestCheckedFacts(python, "guardian", project, {});
    assert.equal(guardian.facts.status, "uninitialized");
    assert.equal(fs.readdirSync(project).length, 0);
    const args = checkedFactArguments("proof", project, { mode: "expert" }, receipt);
    assert.deepEqual(args.slice(0, 5), ["-P", "-m", "sona", "guide", "proof"]);
    await assert.rejects(requestCheckedFacts(path.join(project, "secret-missing.exe"), "guardian", project, {}), error => {
      assert(!error.message.includes("secret-missing"));
      return true;
    });
  } finally {
    assert.equal(path.dirname(path.resolve(project)), path.resolve(os.tmpdir()));
    fs.rmSync(project, { recursive: true, force: true });
  }
  const canonical = {
    diagnostic_id: "SONA-RUNTIME-003", category: "runtime", message: "Name 'quant' is not defined.",
    severity: "error", hint: "", file: uri, start_line: 2, start_column: 7, end_line: 2, end_column: 12,
    node_type: null, source: "sona", related_locations: [], metadata: { name: "quant", "rule-id": "original" }, legacy_code: null
  };
  const item = { data: canonical, code: "SONA-RUNTIME-003", severity: 0, message: canonical.message,
    range: { start: { line: 1, character: 6 }, end: { line: 1, character: 11 } } };
  let response;
  for (const mode of ["guided", "balanced", "expert"]) {
    const request = model.diagnosticRequest(source, uri, item, { mode });
    response = cli(request);
    assert.deepEqual(response.diagnostic, canonical);
    assert.equal(response.mode, mode);
    assert.equal(model.guideText(response), response.text);
    const reference = cli({ schema_version: 1, action: "diagnostic", diagnostic_id: item.code, options: { mode } });
    const why = cli(null, ["why", item.code, "--mode", mode, "--json", "--no-profile"]);
    const { text, ...json } = reference;
    assert.deepEqual(json, why);
  }
  const unicode = 'print("😀"); let values = [1, 2];\r\n';
  const start = unicode.indexOf("let");
  const request = model.selectionRequest(unicode, uri, {
    start: { line: 0, character: start }, end: { line: 0, character: unicode.split("\r\n")[0].length }
  }, {});
  assert.equal(request.selection.start_column, Array.from(unicode.slice(0, start)).length + 1);
  const selection = cli(request);
  assert(selection.concepts.some(concept => concept.id === "collections"));
  assert(selection.text.includes("no program was executed"));
  assert.throws(() => model.guideText({ schema_version: 2 }), /contract/);

  const data = { schema_version: 1, source: "sona-guide", document_version: 4, fix: response.fixes[0] };
  const expected = "let quantity = 3;\nprint(quantity);\n";
  assert.equal(model.checkedFix(source, uri, 4, data).text, expected);
  assert.throws(() => model.checkedFix(source, uri, 5, data), /SONA-GUIDE-003/);
  assert.throws(() => model.checkedFix(source.replace("quant)", "other)"), uri, 4, data), /SONA-GUIDE-003/);
  assert.throws(() => model.checkedFix(source, "file:///different.sona", 4, data), /document/);

  const registered = new Map();
  const disposable = { dispose() {} };
  const errors = [];
  let text = source, version = 4, editsApplied = 0, staleAtConfirmation = false;
  let provider;
  const document = {
    uri: { toString: () => uri }, languageId: "sona", isClosed: false,
    get version() { return version; }, getText: () => text, positionAt: offset => ({ offset })
  };
  const editor = { document, async edit(callback) {
    const edits = [];
    callback({ replace: (range, replacement) => edits.push({ start: range.start.offset, end: range.end.offset, replacement }) });
    for (const edit of edits.sort((a, b) => b.start - a.start)) text = text.slice(0, edit.start) + edit.replacement + text.slice(edit.end);
    version++; editsApplied++;
    return true;
  } };
  const fakeVscode = {
    Uri: { parse: value => ({ toString: () => value }) },
    Range: class { constructor(start, end) { this.start = start; this.end = end; } },
    ViewColumn: { Beside: 2 }, ConfigurationTarget: { Global: 1 },
    workspace: {
      textDocuments: [document],
      getConfiguration: () => ({ inspect: () => undefined, get: () => false }),
      registerTextDocumentContentProvider: (_, value) => { provider = value; return disposable; },
      onDidChangeConfiguration: () => disposable,
      openTextDocument: async value => ({ uri: value, getText: () => provider.provideTextDocumentContent(value) })
    },
    window: {
      activeTextEditor: undefined,
      onDidChangeActiveTextEditor: () => disposable,
      showTextDocument: async () => editor,
      showInformationMessage: async () => { if (staleAtConfirmation) version++; return "Apply fix"; },
      showErrorMessage: message => { errors.push(message); }
    },
    commands: {
      registerCommand: (name, handler) => { registered.set(name, handler); return disposable; },
      executeCommand: async (name, before, after) => {
        assert.equal(name, "vscode.diff");
        assert.equal(provider.provideTextDocumentContent(before), source);
        assert.equal(provider.provideTextDocumentContent(after), expected);
      }
    }
  };
  const originalLoad = Module._load;
  Module._load = function(name, parent, isMain) {
    if (name === "vscode") return fakeVscode;
    if (name === "./lspClient" && parent.filename.endsWith(`${path.sep}guide.js`)) {
      return { requestSonaGuide: async (_, payload) => cli(payload), updateGuideOptions: async () => {} };
    }
    return originalLoad.call(this, name, parent, isMain);
  };
  let guide;
  try { guide = require("../out/guide.js"); } finally { Module._load = originalLoad; }
  const subscriptions = [];
  guide.activateGuide({ subscriptions, globalState: { get: () => true, update: async () => {} } });
  const action = { data, edit: { dangerousIfUngated: true } };
  guide.guardCodeActions([action], uri);
  assert.equal(action.edit, undefined);
  assert.equal(action.command.command, "sona.guide.previewFix");
  staleAtConfirmation = true;
  await registered.get(action.command.command)(...action.command.arguments);
  assert.equal(editsApplied, 0);
  assert.equal(text, source);
  assert(errors.at(-1).includes("SONA-GUIDE-003"));
  staleAtConfirmation = false; version = 4;
  await registered.get(action.command.command)(...action.command.arguments);
  assert.equal(editsApplied, 1);
  assert.equal(text, expected);
  for (const subscription of subscriptions) subscription.dispose();
  const packageJson = JSON.parse(fs.readFileSync(path.join(root, "vscode-extension/package.json"), "utf8"));
  for (const command of ["explainDiagnostic", "explainSelection", "focus", "setup", "explainProof", "explainGuardian"]) {
    assert(registered.has(`sona.guide.${command}`));
    assert(packageJson.contributes.commands.some(item => item.command === `sona.guide.${command}`));
  }
  fakeVscode.workspace.isTrusted = false;
  await registered.get("sona.guide.explainProof")();
  assert(errors.at(-1).includes("trusted workspace"));
  fakeVscode.workspace.isTrusted = true;
  fakeVscode.window.showOpenDialog = async () => undefined;
  const beforeCancel = errors.length;
  await registered.get("sona.guide.explainProof")();
  assert.equal(errors.length, beforeCancel);
  const selectedResource = { scheme: "file", fsPath: path.join(root, "second-workspace") };
  fakeVscode.workspace.getConfiguration = (section, resource) => ({
    inspect: key => ({ workspaceFolderValue: resource === selectedResource && key === "cli.pythonPath" ? "selected-python" : undefined }),
    get: () => "default-python"
  });
  assert.equal(require("../out/pythonEnvironment.js").resolveSonaPythonPath(selectedResource), "selected-python");
  console.log("Sona Guide CLI/editor parity, preview, and stale-edit checks passed.");
}

main().catch(error => { console.error(error); process.exitCode = 1; });
