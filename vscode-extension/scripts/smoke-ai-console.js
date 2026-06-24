const assert = require("assert");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));

async function main() {
  assertCommand("sona.aiConsole.focus");
  assertCommand("sona.aiConsole.clear");
  assertCommand("sona.aiConsole.selectAgent");

  assert(packageJson.contributes.viewsContainers.activitybar.some(container => container.id === "sona"));
  assert(packageJson.contributes.views.sona.some(view => view.id === "sona.aiConsole"));
  assert(packageJson.activationEvents.includes("onView:sona.aiConsole"));

  const registry = require(path.join(root, "out", "aiConsole", "agentRegistry.js"));
  const providers = require(path.join(root, "out", "aiConsole", "providers.js"));

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
    workspaceFolderPaths: []
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

  const viewSource = fs.readFileSync(path.join(root, "src", "aiConsole", "sonaAiConsoleView.ts"), "utf8");
  assert(viewSource.includes("Content-Security-Policy"));
  assert(viewSource.includes("nonce"));
  assert(viewSource.includes("registerWebviewViewProvider") || fs.readFileSync(path.join(root, "src", "extension.ts"), "utf8").includes("registerWebviewViewProvider"));

  assertNoHardcodedSecrets([
    path.join(root, "src", "aiConsole"),
    path.join(root, "media")
  ]);

  console.log("Sona AI Console smoke checks passed.");
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
