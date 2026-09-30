const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const Module = require("node:module");
const os = require("node:os");
const { createHash } = require("node:crypto");
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
  assert.equal(model.parseEditProposal('{"replacement":"let value = 1;"}'), "let value = 1;");
  assert.equal(model.parseEditProposal('{"replacement":""}'), "");
  assert.throws(() => model.parseEditProposal("```sona\\nlet x = 1;\\n```"), /parse/);
  assert.throws(() => model.parseEditProposal('{"replacement":"x","approved":true}'), /one replacement/);
  assert.throws(() => model.parseEditProposal('{"replacement":"x","capability":"self-minted"}'), /one replacement/);
  assert.throws(() => model.parseEditProposal(JSON.stringify({ replacement: "x".repeat(65 * 1024) })), /64 KiB/);

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
  let staleDuringAuthorization = false;
  let selectionChangesDuringAuthorization = false;
  let selectionStart = source.indexOf("quant)"), selectionEnd = selectionStart + "quant".length;
  let confirmationAction = "Apply fix";
  let proposalText = '{"replacement":"3"}';
  let proposalDiffs = 0, localInferenceCalls = 0;
  let authorizationCalls = 0, consumeCalls = 0, authorizationDecision = "authorized";
  let localModelSetting = "test-local-model";
  let sourceEditorPinned = false, sourceDocumentClosed = false;
  let localModelResponse = {
    schema_version: 1, status: "ok", provider_id: "local", runtime_id: "llama-cpp",
    model_id: "test-local-model", proposal: proposalText
  };
  let expectedProposalSelection = "quantity";
  let expectedProposalBefore = expected;
  let expectedProposalAfter = expected.replace("print(quantity)", "print(3)");
  let changeSelectionDuringPrompt = false;
  let provider;
  const positionAt = offset => {
    const prefix = text.slice(0, offset);
    const parts = prefix.split("\n");
    return { offset, line: parts.length - 1, character: parts.at(-1).length };
  };
  const document = {
    uri: { scheme: "file", fsPath: "/workspace/guide-preview.sona", path: "/guide-preview.sona", toString: () => uri },
    languageId: "sona", get isClosed() { return sourceDocumentClosed; },
    get version() { return version; },
    getText: range => range ? text.slice(range.start.offset, range.end.offset) : text,
    positionAt, offsetAt: position => position.offset
  };
  const editor = { document, get selection() {
    return { isEmpty: selectionStart === selectionEnd, start: positionAt(selectionStart), end: positionAt(selectionEnd) };
  }, async edit(callback) {
    const edits = [];
    callback({ replace: (range, replacement) => edits.push({ start: range.start.offset, end: range.end.offset, replacement }) });
    if (!edits.length) return false;
    for (const edit of edits.sort((a, b) => b.start - a.start)) text = text.slice(0, edit.start) + edit.replacement + text.slice(edit.end);
    version++; editsApplied++;
    return true;
  } };
  const fakeVscode = {
    Uri: { parse: value => ({ toString: () => value }) },
    Range: class { constructor(start, end) { this.start = start; this.end = end; } },
    ViewColumn: { Beside: 2 }, ConfigurationTarget: { Global: 1 },
    workspace: {
      isTrusted: true,
      workspaceFolders: [{ name: "workspace", uri: { scheme: "file", fsPath: root } }],
      textDocuments: [document],
      getConfiguration: () => ({ inspect: () => undefined, get: (key, fallback) => key === "localModelId" ? localModelSetting : key === "ai.qwen.enabled" ? true : fallback }),
      getWorkspaceFolder: () => ({ name: "workspace", uri: { scheme: "file", fsPath: root } }),
      registerTextDocumentContentProvider: (_, value) => { provider = value; return disposable; },
      onDidChangeConfiguration: () => disposable,
      openTextDocument: async value => ({ uri: value, getText: () => provider.provideTextDocumentContent(value) })
    },
    window: {
      activeTextEditor: editor,
      onDidChangeActiveTextEditor: () => disposable,
      showTextDocument: async (value, options) => {
        if (value === document && options?.preview === false) sourceEditorPinned = true;
        return editor;
      },
      showInputBox: async () => {
        if (changeSelectionDuringPrompt) { selectionStart = 0; selectionEnd = 1; }
        return "replace the selected expression with its computed value";
      },
      showInformationMessage: async () => { if (staleAtConfirmation) version++; return confirmationAction; },
      showErrorMessage: message => { errors.push(message); }
    },
    commands: {
      registerCommand: (name, handler) => { registered.set(name, handler); return disposable; },
      executeCommand: async (name, before, after, title) => {
        assert.equal(name, "vscode.diff");
        if (title === "Sona Guide: Local AI Edit Proposal") {
          if (!sourceEditorPinned) sourceDocumentClosed = true;
          proposalDiffs++;
          assert.equal(provider.provideTextDocumentContent(before), expectedProposalBefore);
          assert.equal(provider.provideTextDocumentContent(after), expectedProposalAfter);
        } else {
          assert.equal(provider.provideTextDocumentContent(before), source);
          assert.equal(provider.provideTextDocumentContent(after), expected);
        }
      }
    }
  };
  const originalLoad = Module._load;
  Module._load = function(name, parent, isMain) {
    if (name === "vscode") return fakeVscode;
    if (name === "./lspClient" && parent.filename.endsWith(`${path.sep}guide.js`)) {
      return {
        requestSonaGuide: async (_, payload) => cli(payload),
        requestSonaLocalModelEdit: async (_, payload) => {
          localInferenceCalls++;
          assert.equal(payload.action, "local_model_proposal");
          assert.equal(payload.source, expectedProposalSelection);
          assert.equal(payload.instruction, "replace the selected expression with its computed value");
          assert.equal(payload.model_id, localModelSetting);
          return { ...localModelResponse, proposal: proposalText };
        },
        prepareSonaGuideBufferEdit: async (_, payload) => {
          authorizationCalls++;
          if (staleAtConfirmation) {
            return {
              schema_version: 1, status: "denied", diagnostic_id: "SONA-GUIDE-003",
              message: "The document changed before Guardian authorization."
            };
          }
          if (authorizationDecision === "no-capability") {
            return {
              schema_version: 1, status: "authorized", effect: "EDITOR.BUFFER_REPLACE",
              source_sha256: `sha256:${createHash("sha256").update(text).digest("hex")}`,
              proposed_sha256: `sha256:${createHash("sha256").update(payload.proposed_source).digest("hex")}`,
              replacement_sha256: `sha256:${createHash("sha256").update(payload.replacement).digest("hex")}`
            };
          }
          if (authorizationDecision !== "authorized") {
            return {
              schema_version: 1, status: "denied", diagnostic_id: "SONA-GUIDE-AUTH-DENIED",
              message: "Guardian did not authorize this editor-buffer change."
            };
          }
          assert.equal(payload.document, uri);
          assert.equal(payload.document_version, version);
          assert.equal(payload.expected_source_sha256, createHash("sha256").update(text).digest("hex"));
          return {
            schema_version: 1, status: "prepared", handle: `one-shot-${authorizationCalls}`, effect: "EDITOR.BUFFER_REPLACE",
            source_sha256: `sha256:${createHash("sha256").update(text).digest("hex")}`,
            proposed_sha256: `sha256:${createHash("sha256").update(payload.proposed_source).digest("hex")}`,
            replacement_sha256: `sha256:${createHash("sha256").update(payload.replacement).digest("hex")}`
          };
        },
        consumeSonaGuideBufferEdit: async (_, payload) => {
          consumeCalls++;
          assert.equal(payload.handle, `one-shot-${authorizationCalls}`);
          if (staleDuringAuthorization) version++;
          if (selectionChangesDuringAuthorization) { selectionStart = 0; selectionEnd = 1; }
          return {
            schema_version: 1, status: "authorized", effect: "EDITOR.BUFFER_REPLACE",
            source_sha256: `sha256:${createHash("sha256").update(text).digest("hex")}`,
            proposed_sha256: `sha256:${createHash("sha256").update(payload.proposed_source).digest("hex")}`,
            replacement_sha256: `sha256:${createHash("sha256").update(payload.replacement).digest("hex")}`
          };
        },
        updateGuideOptions: async () => {}
      };
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
  assert(errors.at(-1).includes("SONA-GUIDE-003"), errors.at(-1));
  staleAtConfirmation = false; version = 4;
  await registered.get(action.command.command)(...action.command.arguments);
  assert.equal(editsApplied, 1);
  assert.equal(text, expected);
  selectionStart = text.indexOf("quantity", text.indexOf("print("));
  selectionEnd = selectionStart + "quantity".length;
  confirmationAction = "Apply proposal";
  changeSelectionDuringPrompt = true;
  await registered.get("sona.guide.proposeEdit")();
  changeSelectionDuringPrompt = false;
  assert.equal(editsApplied, 1, "a changed selection must prevent the buffer edit");
  assert(errors.at(-1).includes("selection changed"), errors.at(-1));
  selectionStart = text.indexOf("quantity", text.indexOf("print("));
  selectionEnd = selectionStart + "quantity".length;
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, 2);
  assert.equal(text, expected.replace("print(quantity)", "print(3)"));
  selectionStart = text.indexOf("3", text.indexOf("print("));
  selectionEnd = selectionStart + 1;
  expectedProposalSelection = "3";
  expectedProposalBefore = text;
  expectedProposalAfter = text.replace("print(3)", "print(4)");
  const callsBeforeCancel = authorizationCalls;
  const consumesBeforeCancel = consumeCalls;
  confirmationAction = "Cancel";
  proposalText = '{"replacement":"4"}';
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(authorizationCalls, callsBeforeCancel, "cancelling the diff must not ask Guardian for a grant");
  assert.equal(consumeCalls, consumesBeforeCancel, "cancelling the diff must not consume a capability");
  confirmationAction = "Apply proposal";
  const appliedText = text, editsBeforeRejectedProposal = editsApplied;
  selectionStart = text.indexOf("3", text.indexOf("print("));
  selectionEnd = selectionStart + 1;
  expectedProposalSelection = "3";
  proposalText = '{"replacement":"("}';
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, editsBeforeRejectedProposal);
  assert.equal(text, appliedText);
  assert.equal(proposalDiffs, 3);
  assert(errors.at(-1).includes("SONA-PROPOSAL-VALIDATION-FAILED"));
  proposalText = '{"replacement":"4"}';
  expectedProposalBefore = appliedText;
  expectedProposalAfter = appliedText.replace("print(3)", "print(4)");
  staleAtConfirmation = true;
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, editsBeforeRejectedProposal);
  assert.equal(text, appliedText);
  assert(errors.at(-1).includes("SONA-GUIDE-003"), errors.at(-1));
  staleAtConfirmation = false;
  version = 4;
  staleDuringAuthorization = true;
  proposalText = '{"replacement":"4"}';
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, editsBeforeRejectedProposal);
  assert.equal(text, appliedText);
  assert(errors.at(-1).includes("SONA-GUIDE-003"), errors.at(-1));
  staleDuringAuthorization = false;
  version = 4;
  selectionChangesDuringAuthorization = true;
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, editsBeforeRejectedProposal);
  assert.equal(text, appliedText);
  assert(errors.at(-1).includes("selection changed after authorization"), errors.at(-1));
  selectionChangesDuringAuthorization = false;
  selectionStart = text.indexOf("3", text.indexOf("print("));
  selectionEnd = selectionStart + 1;
  authorizationDecision = "denied";
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, editsBeforeRejectedProposal);
  assert.equal(text, appliedText);
  assert(errors.at(-1).includes("SONA-GUIDE-AUTH-DENIED"), errors.at(-1));
  assert.equal(proposalDiffs, 7);
  authorizationDecision = "no-capability";
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(editsApplied, editsBeforeRejectedProposal, "approval without a minted capability must not apply");
  assert.equal(text, appliedText);
  assert(errors.at(-1).includes("SONA-GUIDE-AUTH-DENIED"), errors.at(-1));
  assert.equal(proposalDiffs, 8);
  authorizationDecision = "authorized";
  proposalText = '{"replacement":"("}';
  const callsBeforeRejectedProvider = localInferenceCalls;
  localModelResponse = { ...localModelResponse, provider_id: "remote", runtime_id: "https" };
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(localInferenceCalls, callsBeforeRejectedProvider + 1);
  assert.equal(proposalDiffs, 8);
  assert(errors.at(-1).includes("no provider fallback"));
  for (const subscription of subscriptions) subscription.dispose();
  const packageJson = JSON.parse(fs.readFileSync(path.join(root, "vscode-extension/package.json"), "utf8"));
  for (const command of ["explainDiagnostic", "explainSelection", "proposeEdit", "focus", "setup", "explainProof", "explainGuardian"]) {
    assert(registered.has(`sona.guide.${command}`));
    assert(packageJson.contributes.commands.some(item => item.command === `sona.guide.${command}`));
  }
  fakeVscode.workspace.isTrusted = false;
  const callsBeforeUntrustedProposal = localInferenceCalls;
  await registered.get("sona.guide.proposeEdit")();
  assert.equal(localInferenceCalls, callsBeforeUntrustedProposal);
  assert(errors.at(-1).includes("trusted workspace"));
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
