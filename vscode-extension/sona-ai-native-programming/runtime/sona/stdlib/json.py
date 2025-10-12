"""Advanced JSON helpers backing the Sona ``json`` standard library module."""

from __future__ import annotations

import copy
import json as _json
import pathlib
import re
from typing import (
    Any,
    Callable,
    Iterable,
    MutableMapping,
    MutableSequence,
    Optional,
)
import warnings


_SINGLE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)
_MULTI_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(?=\s*?[\]}])")

_POINTER_PART_ESCAPE = re.compile(r"~[01]")
_DEFAULT_INDENT = 2
_DEFAULT_ENCODING = "utf-8"


def _strip_comments(payload: str) -> str:
    return _MULTI_COMMENT_RE.sub("", _SINGLE_COMMENT_RE.sub("", payload))


def _strip_trailing_commas(payload: str) -> str:
    return _TRAILING_COMMA_RE.sub("", payload)


def _prepare_text(
    text: str,
    *,
    allow_comments: bool,
    allow_trailing_commas: bool,
) -> str:
    candidate = text
    if allow_comments:
        candidate = _strip_comments(candidate)
    if allow_trailing_commas:
        candidate = _strip_trailing_commas(candidate)
    return candidate


def loads(
    text: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
    strict: bool = True,
) -> Any:
    """Parse *text* into Python objects with optional leniency flags."""

    try:
        prepared = _prepare_text(
            text,
            allow_comments=allow_comments,
            allow_trailing_commas=allow_trailing_commas,
        )
        return _json.loads(prepared, strict=strict)
    except _json.JSONDecodeError as exc:  # pragma: no cover - via tests
        message = (
            f"Invalid JSON: {exc.msg} at line {exc.lineno} "
            f"column {exc.colno}"
        )
        raise ValueError(message) from exc


def load(
    path: str | pathlib.Path,
    *,
    encoding: str = _DEFAULT_ENCODING,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
    strict: bool = True,
) -> Any:
    """Read JSON from *path* and parse it with :func:`loads` semantics."""

    file_path = pathlib.Path(path)
    payload = file_path.read_text(encoding=encoding)
    return loads(
        payload,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
        strict=strict,
    )


def dumps(
    obj: Any,
    *,
    indent: Optional[int] = None,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    default: Optional[Callable[[Any], Any]] = None,
    trailing_newline: bool = False,
) -> str:
    """Serialise *obj* to a JSON string with sensible defaults."""

    try:
        rendered = _json.dumps(
            obj,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            default=default,
        )
    except (TypeError, ValueError) as exc:  # pragma: no cover
        raise TypeError(f"JSON encode error: {exc}") from exc
    if trailing_newline and not rendered.endswith("\n"):
        rendered = f"{rendered}\n"
    return rendered


def dump(
    obj: Any,
    path: str | pathlib.Path,
    *,
    indent: int = _DEFAULT_INDENT,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    encoding: str = _DEFAULT_ENCODING,
    newline: str = "\n",
    trailing_newline: bool = True,
) -> None:
    """Serialise *obj* and write it to *path* with the requested formatting."""

    file_path = pathlib.Path(path)
    text = dumps(
        obj,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        trailing_newline=trailing_newline,
    )
    file_path.write_text(text.replace("\n", newline), encoding=encoding)


def pretty(
    obj: Any,
    *,
    indent: int = _DEFAULT_INDENT,
    sort_keys: bool = True,
) -> str:
    """Return a prettified JSON string with deterministic key ordering."""

    return dumps(
        obj,
        indent=indent,
        sort_keys=sort_keys,
        trailing_newline=True,
    )


def normalize(
    value: Any,
    *,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
) -> str:
    """Return a compact canonical JSON string for *value*."""

    return dumps(
        value,
        indent=None,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
    )


def is_valid(
    text: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
) -> bool:
    """Return ``True`` if *text* parses successfully using these options."""

    return validate(
        text,
        allow_comments=allow_comments,
        allow_trailing_commas=allow_trailing_commas,
    )["valid"]


def validate(
    text: str,
    *,
    allow_comments: bool = False,
    allow_trailing_commas: bool = False,
) -> dict[str, Any]:
    """Validate *text* returning a structured diagnostic map."""

    try:
        loads(
            text,
            allow_comments=allow_comments,
            allow_trailing_commas=allow_trailing_commas,
        )
        return {"valid": True, "error": None}
    except ValueError as exc:
        return {"valid": False, "error": str(exc)}


def merge(*objects: Any, deep: bool = True) -> Any:
    """Deep merge multiple mapping objects into a new structure."""

    if not objects:
        return {}

    def _merge_pair(left: Any, right: Any) -> Any:
        if isinstance(left, MutableMapping) and isinstance(
            right, MutableMapping
        ):
            result: MutableMapping[str, Any] = type(left)()
            result.update({k: copy.deepcopy(v) for k, v in left.items()})
            for key, value in right.items():
                if deep and key in result:
                    result[key] = _merge_pair(result[key], value)
                else:
                    result[key] = copy.deepcopy(value)
            return result
        if deep and isinstance(left, list) and isinstance(right, list):
            return [copy.deepcopy(item) for item in (*left, *right)]
        return copy.deepcopy(right)

    result = copy.deepcopy(objects[0])
    for candidate in objects[1:]:
        result = _merge_pair(result, candidate)
    return result


def merge_patch(target: Any, patch: Any) -> Any:
    """Apply a JSON Merge Patch (RFC 7396) and return a new value.

    Rules summary:
    - If patch is not a mapping (object), it replaces the target entirely.
    - If patch is a mapping:
      - For each key:
        - If value is null, remove the key from target if present.
        - Else recursively apply merge-patch to the member at that key.
    - Arrays are replaced (not element-wise merged) unless patch is not an object.
    """

    # Non-object patch replaces target entirely
    if not isinstance(patch, MutableMapping):
        return copy.deepcopy(patch)

    # Object patch: work on a deep copy of target (use {} if target not object)
    result: MutableMapping[str, Any]
    if isinstance(target, MutableMapping):
        result = copy.deepcopy(target)
    else:
        result = type(patch)()  # usually dict

    for key, pval in patch.items():
        if pval is None:
            # Remove key if present
            if key in result:
                del result[key]
            continue
        # If both target[key] and patch value are objects, recurse
        tval = result.get(key)
        if isinstance(tval, MutableMapping) and isinstance(pval, MutableMapping):
            result[key] = merge_patch(tval, pval)
        else:
            # Replace (arrays and scalars replaced by value)
            result[key] = copy.deepcopy(pval)

    return result


def deep_update(
    target: Any,
    patch: Any,
    *,
    list_strategy: str = "replace",  # "replace" | "append" | "extend_unique"
    make_copy: bool = True,
    **_kwargs: Any,
) -> Any:
    """Deeply merge ``patch`` into ``target`` and return the result.

    Semantics:
    - If both are dicts: merge keys recursively. Keys in ``patch`` overwrite or merge.
    - If both are lists:
      - "replace" (default): result is a copy of ``patch``.
      - "append": ``target + patch`` (shallow append of items from ``patch``).
      - "extend_unique": like append, but only adds items not already present (``==`` comparison).
    - Else (scalars, or type conflict): result is a copy of ``patch``.

    Notes:
    - No deletion semantics: use :func:`merge_patch` with ``null`` to remove keys.
    - ``make_copy=True`` ensures ``target`` is not mutated. Set ``make_copy=False`` for in-place behaviour
      on dict/list branches where possible.

    Args:
        list_strategy: list merge behavior ("replace" | "append" | "extend_unique").
        make_copy:     if True (default), do not mutate ``target``.
        **_kwargs:     accepts legacy ``copy=``; emits DeprecationWarning and honours the value.
    """

    # Back-compat shim for legacy copy= kwarg
    if "copy" in _kwargs:
        warnings.warn(
            "deep_update(copy=...) is deprecated; use make_copy=... instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        make_copy = _kwargs["copy"]

    if list_strategy not in {"replace", "append", "extend_unique"}:
        raise ValueError(f"invalid list_strategy: {list_strategy!r}")

    base = copy.deepcopy(target) if make_copy else target
    return _deep_update_into(base, patch, list_strategy)


def _deep_update_into(t: Any, p: Any, list_strategy: str) -> Any:
    # dict ↔ dict: recursive
    if isinstance(t, MutableMapping) and isinstance(p, MutableMapping):
        for k, pv in p.items():
            if k in t:
                t[k] = _deep_update_into(t[k], pv, list_strategy)
            else:
                t[k] = copy.deepcopy(pv)
        return t

    # list ↔ list: strategy
    if isinstance(t, list) and isinstance(p, list):
        if list_strategy == "replace":
            return copy.deepcopy(p)
        if list_strategy == "append":
            return list(t) + [copy.deepcopy(x) for x in p]
        if list_strategy == "extend_unique":
            out = list(t)
            for x in p:
                if x not in out:
                    out.append(copy.deepcopy(x))
            return out

    # type conflict or scalars: replace with patch
    return copy.deepcopy(p)


def _decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _traverse_pointer(value: Any, pointer: str) -> Iterable[tuple[Any, str]]:
    if pointer == "":
        yield value, ""
        return
    parts = pointer.lstrip("/").split("/") if pointer else []
    current = value
    for raw in parts:
        key = _decode_pointer_token(raw)
        yield current, key
        if isinstance(current, MutableMapping):
            if key not in current:
                raise KeyError(f"Pointer segment {key!r} missing")
            current = current[key]
        elif isinstance(current, MutableSequence):
            index = int(key)
            current = current[index]
        else:
            raise KeyError(
                f"Cannot traverse pointer through {type(current).__name__}"
            )


def pointer_get(value: Any, pointer: str, default: Any = None) -> Any:
    """Retrieve the value at *pointer* or return *default* if missing."""

    if pointer == "":
        return value
    try:
        current = value
        for container, key in _traverse_pointer(value, pointer):
            if isinstance(container, MutableMapping):
                current = container[key]
            elif isinstance(container, MutableSequence):
                current = container[int(key)]
            else:  # pragma: no cover - guarded earlier
                raise KeyError
        return current
    except (KeyError, IndexError, ValueError):
        if default is not None:
            return default
        raise


def pointer_set(value: Any, pointer: str, new_value: Any) -> Any:
    """Return a copy of *value* with *pointer* updated to *new_value*."""

    if pointer == "":
        return copy.deepcopy(new_value)

    clone = copy.deepcopy(value)
    parts = pointer.lstrip("/").split("/") if pointer else []
    if not parts:
        return clone
    current = clone
    for raw in parts[:-1]:
        key = _decode_pointer_token(raw)
        if isinstance(current, MutableMapping):
            if key not in current or not isinstance(
                current[key], (MutableMapping, MutableSequence)
            ):
                current[key] = {}
            current = current[key]
        elif isinstance(current, MutableSequence):
            index = int(key)
            while index >= len(current):
                current.append({})
            if not isinstance(
                current[index], (MutableMapping, MutableSequence)
            ):
                current[index] = {}
            current = current[index]
        else:
            raise KeyError(
                f"Cannot set pointer through {type(current).__name__}"
            )

    last_token = _decode_pointer_token(parts[-1])
    if isinstance(current, MutableMapping):
        current[last_token] = copy.deepcopy(new_value)
    elif isinstance(current, MutableSequence):
        index = int(last_token)
        while index >= len(current):
            current.append(None)
        current[index] = copy.deepcopy(new_value)
    else:
        raise KeyError(f"Cannot apply pointer to {type(current).__name__}")
    return clone


__all__ = [
    "loads",
    "load",
    "dumps",
    "dump",
    "pretty",
    "normalize",
    "is_valid",
    "validate",
    "merge",
    "merge_patch",
    "deep_update",
    "pointer_get",
    "pointer_set",
]
