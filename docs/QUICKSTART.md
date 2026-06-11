# Sona Quickstart

This guide gets a new developer from install to a working `.sona` program in
5-10 minutes.

Estimated time: 5-10 minutes.

Documentation truth rule: if this page and runtime behavior disagree, runtime
behavior wins and this page must be corrected before release.

## 1. Install Sona

Use Python 3.11 or newer.

```bash
python -m pip install sona-lang
```

Check the CLI:

```bash
sona --version
```

Expected shape:

```text
Sona 0.15.0
```

## 2. Create `hello.sona`

Bash or macOS/Linux shell:

```bash
echo 'print("Hello, Sona!")' > hello.sona
```

Windows PowerShell:

```powershell
'print("Hello, Sona!")' | Out-File -Encoding utf8 hello.sona
```

## 3. Run the file

Run it with either CLI form:

```bash
sona run hello.sona
```

or:

```bash
sona hello.sona
```

Expected output:

```text
Hello, Sona!
```

## 4. Use one stdlib module

Create `math_demo.sona`:

```sona runnable
import math;

let total = math.add(2, 3);
print("2 + 3 = " + total);
```

Run it:

```bash
sona run math_demo.sona
```

## 5. Fix a simple error

Create this broken file:

```sona
print(total);
```

Run it:

```bash
sona run broken.sona
```

Sona should print a short diagnostic. The important part is the hint: define the
value before using it. See the full diagnostics contract in
[`docs/errors/v0.14-diagnostics.md`](errors/v0.14-diagnostics.md).

Corrected version:

```sona
let total = 5;
print(total);
```

## 6. Source-checkout examples

Official examples are source-repository examples. They are validated by release
tests, but installed packages are not required to include them.

From a source checkout:

```bash
sona run examples/hello.sona
```

To validate the full official example suite:

```bash
python tools/run_examples.py
```

## CLI behavior contract

- `sona --version` prints one line.
- `sona --help` is grouped and human-readable.
- `sona` with no arguments prints help to stderr and exits `1`.
- CLI errors print to stderr.
- CLI errors exit with a nonzero code.
- Stack traces are hidden unless explicitly requested.
