"""Sona stdlib module scaffolding generator.

Create skeletons for Phase A modules.
Usage:
    python tools/new_stdlib_module.py fs --category core/files
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ERRORS = ["EINVAL", "ENOTFOUND", "EIO"]


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate scaffolding for a stdlib module",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "module",
        help="Module name such as 'fs' or 'web.router'",
    )
    parser.add_argument(
        "--category",
        default="core",
        help="Category path for grouping (e.g. 'core/files')",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Optional module summary inserted into docs",
    )
    parser.add_argument(
        "--error-codes",
        default=",".join(DEFAULT_ERRORS),
        help="Comma-separated error codes for the template header",
    )
    parser.add_argument(
        "--with-bridge",
        dest="with_bridge",
        action="store_true",
        help="Generate a Python bridge under sona/stdlib",
    )
    parser.add_argument(
        "--no-bridge",
        dest="with_bridge",
        action="store_false",
        help="Skip bridge generation",
    )
    parser.set_defaults(with_bridge=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files if they already exist",
    )
    return parser.parse_args(argv)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    return value.strip("_") or "misc"


def split_category(raw: str) -> List[str]:
    raw = raw.replace("\\", "/")
    parts = re.split(r"[/.]", raw)
    return [slugify(part) for part in parts if part]


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_package(base: Path, parts: List[str]) -> Path:
    current = base
    for part in parts:
        current = current / part
        current.mkdir(parents=True, exist_ok=True)
        init_path = current / "__init__.py"
        if not init_path.exists():
            init_path.write_text(
                '"""Stdlib package placeholder."""\n',
                encoding="utf-8",
            )
    return current


def write_file(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        print(f"[skip] {path.relative_to(REPO_ROOT)} exists")
        return
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")
    print(f"[write] {path.relative_to(REPO_ROOT)}")


def build_header(
    module: str,
    category_display: str,
    errors: Iterable[str],
    description: str,
) -> str:
    rows = "\n".join(
        f"# | {code} | TODO describe scenario | TODO remediation |"
        for code in errors
    )
    summary = description or "TODO fill in module purpose."
    return dedent(
        f"""
        # ---
        # Module: {module}
        # Category: {category_display}
        # Purpose: {summary}
        # Inputs: TODO list primary inputs.
        # Outputs: TODO describe return values.
        # Errors:
        # | Code | Scenario | Notes |
        {rows}
        # ---
        """
    ).strip()


def smod_template(
    module: str,
    category_display: str,
    errors: Iterable[str],
    description: str,
) -> str:
    header = build_header(module, category_display, errors, description)
    body = dedent(
        f"""
        # TODO: remove placeholder once implemented.
        func init_module() {{
            # Placeholder export keeps the module linkable.
            return "{module}::unimplemented"
        }}
        """
    ).strip()
    return f"{header}\n\n{body}\n"


def bridge_template(
    module: str,
    category_display: str,
    errors: Iterable[str],
) -> str:
    error_line = ", ".join(errors)
    return (
        dedent(
            f'''"""Python bridge for stdlib module '{module}'.
Category: {category_display}.
"""

from __future__ import annotations

from typing import Any

from sona.core import ErrorCode, Result, err


def unimplemented(*_args: Any, **_kwargs: Any) -> Result[Any]:
    """Temporary placeholder until the bridge is implemented."""
    return err(
        ErrorCode.EUNSUPPORTED,
        "{module} bridge not implemented",
        details={{
            "module": "{module}",
            "category": "{category_display}",
        }},
    )


# TODO: replace `unimplemented` with real bridge functions.
EXPORTS = {{
    "example": unimplemented,
}}

# Expected error codes: {error_line}
'''
        ).strip()
        + "\n"
    )


def test_template(module: str, category_display: str) -> str:
    return dedent(
        f"""
        # stdlib {module} tests ({category_display})
        import stdlib::{module} as {module}
        import stdlib::result as result

        test "{module} happy path placeholder" {{
            let outcome = result.ok("placeholder")
            expect outcome.is_ok()
        }}

        test "{module} error propagation placeholder" {{
            let failure = result.err("EUNSUPPORTED", "TODO implement")
            expect failure.is_err()
        }}
        """
    ).strip() + "\n"


def docs_template(
    module: str,
    category_display: str,
    description: str,
    errors: Iterable[str],
    example_ref: str,
) -> str:
    error_rows = "\n".join(
        f"| {code} | TODO describe scenario | TODO mitigation |"
        for code in errors
    )
    overview = description or "TODO provide a concise summary."
    return dedent(
        f"""
        # {module.title()} Module ({category_display})

    _Status: Draft - generated skeleton._

        ## Overview

        {overview}

        ## Quickstart

        ```sona
        import stdlib::{module} as {module}

        let outcome = {module}.init_module()
        print(outcome)
        ```

        ## API Surface (Draft)

        | API | Description | Result |
        | --- | ----------- | ------ |
    | `init_module()` | Placeholder export to replace. | Returns placeholder. |

        ## Error Codes

        | Code | Scenario | Notes |
        | ---- | -------- | ----- |
        {error_rows}

        ## Testing Requirements

        - Achieve ≥ 90% coverage within `/tests/smod`.
        - Add property tests for critical parsing or validation logic.
        - Use deterministic seeds via the shared test harness utilities.

        ## Examples

        - `{example_ref}`
        """
    ).strip() + "\n"


def example_template(module: str) -> str:
    return dedent(
        f"""
        # Example usage for stdlib::{module}

        import stdlib::{module} as {module}

        print("Running {module} demo")
        let placeholder = {module}.init_module()
        print(placeholder)
        """
    ).strip() + "\n"


def unique(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value:
            normal = value.upper()
            if normal not in seen:
                seen.add(normal)
                ordered.append(normal)
    return ordered


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    module_slug = slugify(args.module)
    category_parts = split_category(args.category)
    category_display = (
        " / ".join(part.replace("_", " ").title() for part in category_parts)
        or "Core"
    )

    error_values = [
        slugify(code).upper()
        for code in args.error_codes.split(",")
    ]
    error_codes = unique(error_values) or list(DEFAULT_ERRORS)

    smod_rel = Path("smod") / Path(*category_parts) / f"{module_slug}.smod"
    test_rel = (
        Path("tests")
        / "smod"
        / Path(*category_parts)
        / f"test_{module_slug}.sona"
    )
    docs_rel = (
        Path("docs") / "stdlib" / Path(*category_parts) / f"{module_slug}.md"
    )
    examples_rel = (
        Path("examples")
        / "stdlib"
        / Path(*category_parts)
        / f"{module_slug}_demo.sona"
    )
    bridge_base = REPO_ROOT / "sona" / "stdlib"

    example_ref = examples_rel.as_posix()

    write_file(
        REPO_ROOT / smod_rel,
        smod_template(
            module_slug,
            category_display,
            error_codes,
            args.description,
        ),
        force=args.force,
    )
    write_file(
        REPO_ROOT / test_rel,
        test_template(module_slug, category_display),
        force=args.force,
    )
    write_file(
        REPO_ROOT / docs_rel,
        docs_template(
            module_slug,
            category_display,
            args.description,
            error_codes,
            example_ref,
        ),
        force=args.force,
    )
    write_file(
        REPO_ROOT / examples_rel,
        example_template(module_slug),
        force=args.force,
    )

    if args.with_bridge:
        bridge_package = ensure_package(bridge_base, category_parts)
        bridge_path = bridge_package / f"{module_slug}.py"
        write_file(
            bridge_path,
            bridge_template(module_slug, category_display, error_codes),
            force=args.force,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
