const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const extensionRoot = path.resolve(__dirname, "..");
const repositoryRoot = path.resolve(extensionRoot, "..");
const manifest = JSON.parse(fs.readFileSync(path.join(extensionRoot, "package.json"), "utf8"));
const bundle = fs.readFileSync(path.join(extensionRoot, "out", "extension.js"), "utf8");
const python = process.env.SONA_TEST_PYTHON || path.join(
  repositoryRoot,
  ".venv",
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python"
);

assert(manifest.contributes.views.sona.some(view => view.id === "sona.runtimeView"));
assert(manifest.contributes.commands.some(command => command.command === "sona.runtime.refresh"));
assert(bundle.includes("sona.runtimeView"));
assert(bundle.includes('"runtime"') && bundle.includes('"status"'));

const result = spawnSync(
  python,
  ["-m", "sona", "runtime", "status", "--format", "json"],
  {
    cwd: repositoryRoot,
    env: { ...process.env, PYTHONPATH: repositoryRoot },
    encoding: "utf8",
    timeout: 15000,
    windowsHide: true,
    shell: false
  }
);
assert.equal(result.status, 0, result.stderr);
const runtime = JSON.parse(result.stdout);
assert.equal(runtime.schema_version, 1);
assert.equal(runtime.status, "ok");
assert.equal(runtime.services.status, "process_local");
assert.equal(runtime.proof.receipt_schema, "schema-1");
console.log("Sona Runtime CLI/view contract checks passed.");
