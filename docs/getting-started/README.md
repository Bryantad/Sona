# Get Started with Proof Mode

Estimated time: 10 minutes.

Sona is a simple programming language for software that can provide evidence
of what it did. **Proof Mode** creates privacy-conscious execution evidence
showing what Sona observed during one Native Core run: program identity,
runtime identity, capability grants, observed effects, output identity, and
the execution result.

A Proof Mode receipt supports deterministic integrity checking. It is not a
digital signature, proof of who ran the program, remote attestation, or proof
that an attacker could not replace and re-hash the entire receipt.

This walkthrough uses a new practice directory and local files. It does not
depend on examples from the source repository.

## Step 1: Install Sona and Native Core

Sona requires Python 3.11 or 3.12. Install the Python package and check the
user-facing CLI:

```bash
python -m pip install sona-lang
sona --version
```

Proof Mode execution also requires the Native Core archive for your operating
system and CPU. Download it with `SHA256SUMS.txt` from the same release and
verify its checksum before extraction. The complete artifact matrix and
checksum commands are in
[Platform Installation and Testing](../guides/platform-installation-and-testing.md).

On Windows x86-64, extract the archive and configure its executable for the
current PowerShell session:

```powershell
Expand-Archive `
  .\sona-native-0.15.6-windows-x86_64.zip `
  -DestinationPath .\sona-native

$env:SONA_NATIVE_BINARY = (Resolve-Path .\sona-native\sona.exe).Path
& $env:SONA_NATIVE_BINARY --version
```

On Linux or macOS, substitute the archive matching your platform and
architecture:

```bash
native_archive=sona-native-0.15.6-linux-x86_64-musl.tar.gz
mkdir -p ./sona-native
tar -xzf "$native_archive" -C ./sona-native
chmod 755 ./sona-native/sona
export SONA_NATIVE_BINARY="$(pwd)/sona-native/sona"
"$SONA_NATIVE_BINARY" --version
```

Apple Silicon uses `sona-native-0.15.6-macos-aarch64.tar.gz`; Intel macOS and
Linux ARM64 use the corresponding archive listed in the platform guide.

Expected Native Core version shape:

```text
Sona native 0.15.6
```

If Native Core is already installed as `sona-native` on `PATH`, you do not need
`SONA_NATIVE_BINARY`. The `sona proof` coordinator uses that command directly.
It never falls back to Python execution when Native Core is unavailable.

## Create a practice project

Create both tutorial programs before Guardian establishes its trusted
baseline.

Windows PowerShell:

```powershell
$project = Join-Path $env:TEMP `
  ("sona-proof-start-{0}" -f [guid]::NewGuid())
New-Item -ItemType Directory -Path $project | Out-Null
Set-Location $project

'print("Proof Mode is working");' |
  Set-Content -LiteralPath .\hello.sona -Encoding ascii

'import fs; fs.write_text("blocked.txt", "must not be written");' |
  Set-Content -LiteralPath .\denied-write.sona -Encoding ascii

New-Item -ItemType Directory -Path .\.sona\receipts | Out-Null
```

Linux or macOS:

```bash
project="$(mktemp -d "${TMPDIR:-/tmp}/sona-proof-start.XXXXXX")"
cd "$project"

printf '%s\n' 'print("Proof Mode is working");' > hello.sona
printf '%s\n' \
  'import fs; fs.write_text("blocked.txt", "must not be written");' \
  > denied-write.sona

mkdir -p .sona/receipts
```

Keep this terminal open: `SONA_NATIVE_BINARY` is configured only for the
current shell session.

## Step 2: Run a basic Sona program

```bash
sona run hello.sona
```

Expected output:

```text
Proof Mode is working
```

This is an ordinary compatibility-runtime run. It does not create Proof Mode
evidence.

## Step 3: Run with Proof Mode

```bash
sona proof hello.sona \
  --receipt .sona/receipts/hello.sproof \
  --engine native
```

In PowerShell, use backticks for multiline input or run the same command on one
line:

```powershell
sona proof .\hello.sona `
  --receipt .\.sona\receipts\hello.sproof `
  --engine native
```

The program prints the same message and Native Core publishes
`.sona/receipts/hello.sproof`. Proof Mode never overwrites an existing receipt;
use a new filename if you repeat the run.

## Step 4: Inspect what happened

```bash
sona proof inspect .sona/receipts/hello.sproof
```

The first section should report:

```text
Receipt        VALID
Integrity      VALID
Execution      SUCCEEDED (exit 0)
Program        source
Engine         Native Core
Python         not involved in recorded execution
Fallback       false
```

The remaining sections show capability decisions, observed effects, and the
SHA-256 identities of the program, Native executable (for new 0.15.6
producers), stdout, stderr, and receipt. A build-supplied source revision is
shown when available. These are self-hashed correlation fields, not
authenticated runtime provenance. Output bodies, source text, and raw program
paths are not stored in the receipt.

## Step 5: Verify the receipt

```bash
sona proof verify .sona/receipts/hello.sproof
```

Verification checks canonical schema-1 structure and the receipt's self-hash,
then validates the recorded runtime, capabilities, execution, and effects.
You do not need to understand or manually re-create canonical JSON.

Use `--json` when another tool needs the machine-readable verified view:

```bash
sona proof verify .sona/receipts/hello.sproof --json
```

## Step 6: Enable Guardian policy

Guardian adds project-local policy and a trusted baseline around Native
execution. Initialize only a dedicated project you have reviewed:

```bash
sona guardian init --project-root . --format text
sona guardian check --project-root . --format text
sona guardian explain --project-root . --format text
```

The first initialization creates `sona.guard.json` only if it is absent. Its
deterministic default denies filesystem read, filesystem write, and network.
It also records a baseline containing the two tutorial programs. Repeating
`guardian init` does not overwrite the policy or baseline.

`guardian check` should report that policy, capabilities, baseline, and Proof
Mode support are ready. `guardian explain` lists the trusted allow/deny
decisions and the next action. Both commands are read-only.

## Step 7: Observe an intentional denial

The second program asks Native Core to create `blocked.txt`. Request the
filesystem-write capability while binding the run to Guardian:

Windows PowerShell:

```powershell
sona proof .\denied-write.sona `
  --receipt .\.sona\receipts\denied-write.sproof `
  --engine native `
  --guardian-root . `
  --allow-fs-write

$deniedExit = $LASTEXITCODE
if ($deniedExit -ne 1) {
  throw "Expected Guardian-bound execution to exit 1; received $deniedExit"
}
if (Test-Path -LiteralPath .\blocked.txt) {
  throw "Denied program created blocked.txt"
}
```

Linux or macOS:

```bash
denied_exit=0
sona proof denied-write.sona \
  --receipt .sona/receipts/denied-write.sproof \
  --engine native \
  --guardian-root . \
  --allow-fs-write || denied_exit=$?

test "$denied_exit" -eq 1
test ! -e blocked.txt
```

The nonzero exit is expected. Guardian's trusted policy denies the requested
grant, Native Core emits its existing `SONA-FS-005` capability diagnostic, and
the file is not created. Proof Mode still publishes evidence of that failed
execution.

Inspect and verify it:

```bash
sona proof inspect .sona/receipts/denied-write.sproof
sona proof verify .sona/receipts/denied-write.sproof
sona guardian proof verify \
  --project-root . \
  --receipt .sona/receipts/denied-write.sproof
```

The verified view should distinguish these facts:

```text
Receipt        VALID
Integrity      VALID
Execution      FAILED (exit 1)
Diagnostic     SONA-FS-005
- fs.write     denied
- FS.WRITE     denied (PARTIAL)
```

`Receipt VALID` means the stored evidence is structurally intact and
self-consistent. It does not turn the recorded failed execution into a
successful one. Guardian can verify the receipt's policy/baseline binding, but
it will not locally attest a failed execution as successful.

## What you established

You now have evidence that answers:

- which source content ran;
- whether execution succeeded or failed;
- which Sona and Native Core identity was recorded;
- whether Python or fallback participated in the recorded execution;
- which capabilities were granted or denied;
- which instrumented effects Sona observed; and
- which hashes identify program input and process output.

You did not establish signer identity, authenticated runtime provenance,
operating-system integrity, hardware trust, remote attestation, or proof that
unobserved external activity was impossible.

## Continue learning

- [Proof Mode Guide](../guides/proof-mode.md)
- [Guardian Guide](../guides/guardian.md)
- [Using Proof Mode and Guardian Together](../guides/proof-and-guardian.md)
- [Proof Mode Technical Reference](../reference/native-proof-mode.md)
- [Proof Mode Threat Model](../spec/proof/threat-model.md)
