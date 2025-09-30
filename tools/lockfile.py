import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import pathlib
import sys

DEFAULT_INCLUDE = [
    "**/*.py",
    "Github_release/0.9.4/**",
    "*.sona",
    "*.md",
    "*.json",
    ".vscode/**",
]
DEFAULT_EXCLUDE = [
    ".venv/**", "venv/**", ".git/**", "**/__pycache__/**", "**/*.pyc", "*.log"
]
DEFAULT_ALGO = "sha256"
DEFAULT_OUT = os.path.join("packaging", "sona.lock.json")
TOOL_VERSION = "0.1"

class LockError(Exception):
    pass

 
def posix_relpath(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()

 
def should_include(path: pathlib.Path, patterns):
    rel = path.as_posix()
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

 
def should_exclude(path: pathlib.Path, patterns):
    rel = path.as_posix()
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

 
def enumerate_files(root: pathlib.Path, include, exclude):
    files = set()
    for pat in include:
        patterns = [pat]
        if pat.endswith("/**") or pat.endswith("\\**"):
            patterns.append(pat + "/*")
        for eff in patterns:
            for p in root.glob(eff):
                if p.is_file():
                    rel = p.relative_to(root)
                    if should_exclude(rel, exclude):
                        continue
                    files.add(rel)
    return sorted(files, key=lambda p: p.as_posix())

 
def file_hash(path: pathlib.Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()

 
def generate(root: str, include, exclude, algorithm: str, out: str):
    root_p = pathlib.Path(root).resolve()
    file_list = enumerate_files(root_p, include, exclude)
    files_obj = {}
    for rel in file_list:
        files_obj[rel.as_posix()] = file_hash(root_p / rel, algorithm)
    data = {
        "version": "0.1",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "root": str(root_p),
        "algorithm": algorithm,
        "tool_version": TOOL_VERSION,
        "include": include,
        "exclude": exclude,
        "files": files_obj,
    }
    out_p = root_p / out
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with out_p.open("w", newline="\n", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write("\n")
    print(f"Wrote lockfile: {out_p}")
    return 0

 
def verify(root: str, lock_path: str):
    root_p = pathlib.Path(root).resolve()
    lock_p = root_p / lock_path
    debug = os.environ.get("SONA_LOCK_DEBUG")
    try:
        lock = json.loads(lock_p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Lockfile read error: {e}", file=sys.stderr)
        return 3

    algo = lock.get("algorithm", DEFAULT_ALGO)
    include = lock.get("include", DEFAULT_INCLUDE)
    exclude = lock.get("exclude", DEFAULT_EXCLUDE)
    files_locked = lock.get("files", {})

    if debug:
        print(f"[lock-debug] root={root_p}")
        print(f"[lock-debug] lock={lock_p}")
        print(f"[lock-debug] include={include}")
        print(f"[lock-debug] exclude={exclude}")

    files_now = enumerate_files(root_p, include, exclude)

    if debug:
        for pat in include:
            cnt = sum(1 for p in root_p.glob(pat) if p.is_file())
            print(
                f"[lock-debug] include_pat {pat!r} "
                f"(len={len(pat)}) -> {cnt} files"
            )
            if pat.startswith("Github_release") or pat.startswith(".vscode"):
                sample = [str(p) for p in list(root_p.glob(pat))[:3]]
                print(f"[lock-debug] sample for {pat!r}: {sample}")

    if debug:
        print(f"[lock-debug] enumerated_count={len(files_now)}")
    files_now_set = {p.as_posix() for p in files_now}
    locked_set = set(files_locked.keys())

    missing = sorted(locked_set - files_now_set)
    extra = sorted(files_now_set - locked_set)
    mismatched = []
    for rel in sorted(files_now_set & locked_set):
        h = file_hash(root_p / rel, algo)
        if h != files_locked.get(rel):
            mismatched.append(
                {
                    "path": rel,
                    "expected": files_locked.get(rel),
                    "actual": h,
                }
            )

    if debug:
        print(
            f"[lock-debug] missing_count={len(missing)} "
            f"extra_count={len(extra)} mismatched_count={len(mismatched)}"
        )

    if not missing and not extra and not mismatched:
        print("Lock verification OK")
        return 0

    print("Lock verification FAILED")
    if missing:
        print("Missing:")
        for p in missing:
            print(f"  - {p}")
    if extra:
        print("Extra:")
        for p in extra:
            print(f"  - {p}")
    if mismatched:
        print("Mismatched:")
        for m in mismatched:
            print(
                "  - {path}: expected {exp} actual {act}".format(
                    path=m["path"], exp=m["expected"], act=m["actual"]
                )
            )
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sona-lock")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_gen = sub.add_parser("generate")
    ap_gen.add_argument("--root", default=os.getcwd())
    ap_gen.add_argument("--include", nargs="*", default=DEFAULT_INCLUDE)
    ap_gen.add_argument("--exclude", nargs="*", default=DEFAULT_EXCLUDE)
    ap_gen.add_argument("--algorithm", default=DEFAULT_ALGO)
    ap_gen.add_argument("--out", default=DEFAULT_OUT)

    ap_ver = sub.add_parser("verify")
    ap_ver.add_argument("--root", default=os.getcwd())
    ap_ver.add_argument("--lock", default=DEFAULT_OUT)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "generate":
            return generate(
                args.root, args.include, args.exclude, args.algorithm, args.out
            )
        if args.cmd == "verify":
            return verify(args.root, args.lock)
        raise LockError("Unknown command")
    except LockError as e:
        print(str(e), file=sys.stderr)
        return 4

 
if __name__ == "__main__":
    sys.exit(main())
