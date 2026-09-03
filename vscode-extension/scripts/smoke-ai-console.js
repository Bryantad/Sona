const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { EventEmitter } = require("events");
const { PassThrough } = require("stream");

const root = path.resolve(__dirname, "..");
const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));

async function main() {
  assertCommand("sona.aiConsole.focus");
  assertCommand("sona.aiConsole.clear");
  assertCommand("sona.aiConsole.selectAgent");

  assert(packageJson.contributes.viewsContainers.activitybar.some(container => container.id === "sona"));
  assert(packageJson.contributes.views.sona.some(view => view.id === "sona.aiConsole"));
  assert(packageJson.activationEvents.includes("onView:sona.aiConsole"));
  assert(packageJson.contributes.views.sona.some(view => view.id === "sona.proofModeExplorer"));
  assert(packageJson.activationEvents.includes("onView:sona.proofModeExplorer"));
  for (const command of [
    "sona.proofMode.run",
    "sona.proofMode.verifyReceipt",
    "sona.proofMode.inspectReceipt",
    "sona.proofMode.openReceipt",
    "sona.proofMode.refresh",
    "sona.proofMode.explainWithGuardian"
  ]) {
    assertCommand(command);
  }

  const registry = require(path.join(root, "out", "aiConsole", "agentRegistry.js"));
  const providers = require(path.join(root, "out", "aiConsole", "providers.js"));
  const backendTransport = require(path.join(root, "out", "aiConsole", "backendTransport.js"));
  const proofModeModel = require(path.join(root, "out", "proofModeModel.js"));

  const agents = registry.getAgents();
  assert.deepStrictEqual(
    agents.map(agent => agent.id),
    ["sona", "qwen", "claude", "codex", "local"]
  );

  const baseConfig = {
    qwenEnabled: false,
    qwenModel: "qwen2.5-coder:7b",
    ollamaUrl: "http://127.0.0.1:11434",
    claudeEnabled: false,
    codexEnabled: false,
    workspaceFolderPaths: [],
    transport: {
      async execute(request, providerId) {
        if (providerId) {
          return { agentId: request.agentId, status: "not_configured", text: `${providerId} unavailable` };
        }
        return { agentId: request.agentId, status: "ok", text: "Governed deterministic response. No external provider was called." };
      }
    }
  };

  const sonaRequest = {
    agentId: "sona",
    prompt: "Explain this file",
    context: {
      currentFile: "example.sona",
      workspaceName: "SonaMinimal"
    }
  };
  const sonaA = await providers.routeAgentRequest(sonaRequest, baseConfig);
  const sonaB = await providers.routeAgentRequest(sonaRequest, baseConfig);
  assert.strictEqual(sonaA.status, "ok");
  assert.strictEqual(sonaA.text, sonaB.text);
  assert(sonaA.text.includes("No external provider was called."));

  for (const agentId of ["qwen", "claude", "codex"]) {
    const response = await providers.routeAgentRequest(
      {
        agentId,
        prompt: "hello",
        context: {}
      },
      baseConfig
    );
    assert.strictEqual(response.status, "not_configured", `${agentId} should be not_configured`);
  }

  const transport = new backendTransport.CliDeveloperIntelligenceTransport("python", root, 1000);
  const unsupported = await transport.execute({ agentId: "sona", prompt: "hello, how are you?", context: {} });
  assert.strictEqual(unsupported.status, "error");
  assert(unsupported.text.includes("Unsupported task"));

  await assertBackendFailureHandling(backendTransport, sonaRequest, root);
  assertProofModeModel(proofModeModel);

  const viewSource = fs.readFileSync(path.join(root, "src", "aiConsole", "sonaAiConsoleView.ts"), "utf8");
  assert(viewSource.includes("Content-Security-Policy"));
  assert(viewSource.includes("nonce"));
  assert(viewSource.includes("registerWebviewViewProvider") || fs.readFileSync(path.join(root, "src", "extension.ts"), "utf8").includes("registerWebviewViewProvider"));
  const transportSource = fs.readFileSync(path.join(root, "src", "aiConsole", "backendTransport.ts"), "utf8");
  assert(transportSource.includes("Unsupported task"));
  assert(transportSource.includes('"-m", "sona", "ai", "task"'));
  assert(!transportSource.includes("/api/generate"));

  const cliSource = fs.readFileSync(path.join(root, "src", "sonaCliIntegration.ts"), "utf8");
  const proofModelSource = fs.readFileSync(path.join(root, "src", "proofModeModel.ts"), "utf8");
  assert(cliSource.includes('const commandArgs = ["-P", "-m", "sona", ...args]'));
  assert(cliSource.includes("delete env.PYTHONPATH"));
  assert(cliSource.includes('"proof", "inspect"') || cliSource.includes('"proof",\n      "inspect"'));
  assert(cliSource.includes("requireTrustedWorkspace"));
  assert(!proofModelSource.includes("createHash"));
  assert(!proofModelSource.includes("canonicalJson"));
  assert(!proofModelSource.includes("canonical_json"));
  assert(!proofModelSource.includes("Sona Proof"));

  assertNoHardcodedSecrets([
    path.join(root, "src", "aiConsole"),
    path.join(root, "media")
  ]);

  console.log("Sona extension smoke checks passed.");
}

function assertProofModeModel(proofModeModel) {
  const payload = {
    status: "valid",
    schema_id: "sona.native-proof.schema-1",
    sona_version: "0.15.5",
    receipt_hash: `sha256:${"a".repeat(64)}`,
    generated_at_utc: "2026-08-24T12:00:00Z",
    guardian_bound: false,
    engine: {
      label: "Native Core",
      python_required: false,
      python_embedded: false,
      fallback_used: false,
      runtime_identity: {
        native_binary: {
          bytes: 456,
          sha256: `sha256:${"4".repeat(64)}`
        },
        source_revision: `git:${"5".repeat(40)}`
      }
    },
    execution: {
      status: "ok",
      exit_code: 0,
      duration_ms: 2,
      stdout: { bytes: 3, sha256: `sha256:${"b".repeat(64)}` },
      stderr: { bytes: 0, sha256: `sha256:${"c".repeat(64)}` },
      diagnostic: null
    },
    program: {
      kind: "source",
      source: { bytes: 14, sha256: `sha256:${"d".repeat(64)}` }
    },
    capabilities: {
      console: true,
      filesystem_read: true,
      filesystem_write: false,
      network: false,
      process: false,
      environment: false
    },
    effects: [
      { sequence: 1, scope: "filesystem", operation: "fs.read_text", outcome: "allowed", effect: "FS.READ", support: "SUPPORTED" },
      { sequence: 2, scope: "filesystem", operation: "fs.read_text", outcome: "allowed", effect: "FS.READ", support: "SUPPORTED" },
      { sequence: 3, scope: "console", operation: "print", outcome: "allowed", effect: "STDOUT.WRITE", support: "PARTIAL" }
    ]
  };

  const valid = proofModeModel.parseProofModeCliOutput(JSON.stringify(payload));
  assert.strictEqual(valid.state, "valid");
  assert.strictEqual(valid.engineLabel, "Native Core");
  assert.strictEqual(valid.pythonInvolved, false);
  assert.strictEqual(valid.fallbackUsed, false);
  assert.strictEqual(valid.sourceRevision, `git:${"5".repeat(40)}`);
  assert.ok(valid.identities.some(identity => identity.label === "native binary"));
  assert.strictEqual(valid.effects.find(effect => effect.effect === "FS.READ").count, 2);
  assert.strictEqual(valid.capabilities.find(capability => capability.label === "fs.write").granted, false);

  const invalid = proofModeModel.parseProofModeCliOutput(JSON.stringify({
    status: "invalid",
    diagnostic: {
      diagnostic_id: "PROOF-VERIFY-005",
      message: "Receipt hash mismatch."
    }
  }));
  assert.strictEqual(invalid.state, "invalid");
  assert.strictEqual(invalid.diagnosticId, "PROOF-VERIFY-005");

  const unavailable = proofModeModel.parseProofModeCliOutput("not-json");
  assert.strictEqual(unavailable.state, "unavailable");
}

async function assertBackendFailureHandling(backendTransport, request, root) {
  function fakeSpawn({ stdout = "", stderr = "", code = 0, neverClose = false } = {}, capture = {}) {
    return (command, args, options) => {
      capture.command = command;
      capture.args = args;
      capture.options = options;
      const child = new EventEmitter();
      child.stdout = new PassThrough();
      child.stderr = new PassThrough();
      child.stdin = new PassThrough();
      child.killed = false;
      child.kill = () => { child.killed = true; return true; };
      process.nextTick(() => {
        if (stdout) child.stdout.write(stdout);
        if (stderr) child.stderr.write(stderr);
        child.stdout.end();
        child.stderr.end();
        if (!neverClose) child.emit("close", code);
      });
      capture.child = child;
      return child;
    };
  }

  const invalid = new backendTransport.CliDeveloperIntelligenceTransport(
    "python with spaces", path.join(root, "workspace with spaces"), 1000,
    fakeSpawn({ stdout: "not-json" })
  );
  const invalidResult = await invalid.execute(request);
  assert.strictEqual(invalidResult.status, "error");

  const nonzeroCapture = {};
  const nonzero = new backendTransport.CliDeveloperIntelligenceTransport(
    "python", root, 1000, fakeSpawn({ stderr: "sanitized failure", code: 7 }, nonzeroCapture)
  );
  const nonzeroResult = await nonzero.execute(request);
  assert.strictEqual(nonzeroResult.status, "error");
  assert.strictEqual(nonzeroResult.text, "sanitized failure");
  assert.strictEqual(nonzeroCapture.options.shell, false);
  assert.strictEqual(nonzeroCapture.options.cwd, root);
  assert.deepStrictEqual(nonzeroCapture.args.slice(0, 4), ["-m", "sona", "ai", "task"]);

  const timeoutCapture = {};
  const timeout = new backendTransport.CliDeveloperIntelligenceTransport(
    "python", root, 5, fakeSpawn({ neverClose: true }, timeoutCapture)
  );
  const timeoutResult = await timeout.execute(request);
  assert.strictEqual(timeoutResult.status, "error");
  assert(timeoutResult.text.includes("timed out"));
  assert.strictEqual(timeoutCapture.child.killed, true);
}

function assertCommand(command) {
  assert(
    packageJson.contributes.commands.some(entry => entry.command === command),
    `Missing command ${command}`
  );
}

function assertNoHardcodedSecrets(paths) {
  const files = [];
  for (const target of paths) {
    collectFiles(target, files);
  }

  const secretPatterns = [
    /sk-[A-Za-z0-9]{16,}/,
    /api[_-]?key\s*[:=]\s*["'][^"']+["']/i,
    /authorization\s*[:=]\s*["'][^"']+["']/i
  ];

  for (const file of files) {
    const content = fs.readFileSync(file, "utf8");
    for (const pattern of secretPatterns) {
      assert(!pattern.test(content), `Possible hardcoded secret in ${file}`);
    }
  }
}

function collectFiles(target, output) {
  if (!fs.existsSync(target)) {
    return;
  }
  const stat = fs.statSync(target);
  if (stat.isFile()) {
    output.push(target);
    return;
  }
  for (const child of fs.readdirSync(target)) {
    collectFiles(path.join(target, child), output);
  }
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
