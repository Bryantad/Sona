# Native Core command selection

Release contract for Sona 0.15.6 and later.

## Command ownership

| Host | Python package owns | Installed Native command | Existing archive member |
| --- | --- | --- | --- |
| Windows | `sona.exe` in the Python environment's Scripts directory | `sona-native.exe` | `sona.exe` |
| Linux | `sona` in the Python environment's bin directory | `sona-native` | `sona` |
| macOS | `sona` in the Python environment's bin directory | `sona-native` | `sona` |

Extract Native Core to its own versioned directory. Keep the Python launcher
in its Python environment. To use the existing archive without renaming it,
set `SONA_NATIVE_BINARY` to the extracted executable's absolute path. To install
a Native command on PATH, copy the extracted executable as `sona-native.exe`
on Windows or `sona-native` on Linux/macOS in a directory you manage. Never
overwrite the Python package's launcher with the archive member.

The archive's old member name remains compatible. Its operating system and
architecture must match the host; an executable rename is not a platform port.

## Resolution and version checking

Delegated `sona proof <program> --receipt <receipt>` uses this order:

1. If `SONA_NATIVE_BINARY` is set, resolve that explicit regular file. An invalid
   value fails; it does not fall through to PATH.
2. Otherwise resolve only `sona-native` on PATH. Generic `sona` is never searched.
3. Reject resolution back to the Python launcher. Windows `.cmd` and `.bat`
   wrappers are rejected because they can invoke a command shell.
4. Run the selected file with `--version` using no shell and closed stdin.
5. Require an exact `Sona native <version>` response matching the Python CLI
   version. Release/prerelease/build suffix differences are mismatches too.
6. Only after this check, launch Native Proof Mode with the original arguments,
   inherited program streams, and the existing recursion guard.

The probe allows five seconds and at most 4096 output bytes. Its stderr and
host exception text are never shown. A timeout or excessive response stops the
probe. Probe cleanup is bounded separately. A failure returns exit code 1 and
does not launch the Sona program or create its receipt.

Diagnostics identify whether the selection came from `SONA_NATIVE_BINARY` or
PATH. They omit raw absolute paths. Inspect the selection locally with these
shell commands if needed:

```powershell
# Windows PowerShell
Get-Command sona, sona-native -All
$env:SONA_NATIVE_BINARY
sona --version
sona-native --version
```

```bash
# Linux / macOS
command -v sona
command -v sona-native
printf '%s\n' "${SONA_NATIVE_BINARY-}"
sona --version
sona-native --version
```

| Diagnostic | Meaning |
| --- | --- |
| `SONA-NATIVE-LAUNCH-001` | Selected executable unavailable, points to the Python launcher, or cannot start |
| `SONA-NATIVE-LAUNCH-002` | Invalid/non-Native version response, excessive output, or Windows batch wrapper |
| `SONA-NATIVE-LAUNCH-003` | CLI/Native version mismatch |
| `SONA-NATIVE-LAUNCH-004` | Version probe timed out |
| `SONA-NATIVE-LAUNCH-005` | Delegation returned to the Python CLI |

Install the matching Native release and update the explicit setting or PATH
entry when a mismatch occurs. The preflight applies only to new delegated
executions. `sona proof verify` and `sona proof inspect` continue to accept
valid historical schema-1 receipts without any Native executable.

The version response establishes compatibility only. It cannot authenticate
an executable or prevent replacement between the check and launch. Use the
published archive checksums and a trusted installation location; Proof Mode's
existing assurance boundary remains in force.
