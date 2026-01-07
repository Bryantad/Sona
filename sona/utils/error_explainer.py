"""Cognitive-first error explanations for Sona runtime."""

from __future__ import annotations

import re


_UNSUPPORTED_OPERAND_RE = re.compile(
    r"unsupported operand type\(s\) for (.+?): '([^']+)' and '([^']+)'"
)
_NOT_SUBSCRIPTABLE_RE = re.compile(r"'([^']+)' object is not subscriptable")
_NOT_CALLABLE_RE = re.compile(r"'([^']+)' object is not callable")
_MUST_BE_RE = re.compile(r"argument must be ([^,]+), not (\\S+)")
_NAME_ERROR_RE = re.compile(r"(?:name|Variable) '([^']+)' is not defined")
_ATTRIBUTE_ERROR_RE = re.compile(r"'([^']+)' object has no attribute '([^']+)'")
_LINE_COL_RE = re.compile(r"line (\\d+)(?:, column (\\d+))?", re.IGNORECASE)


def explain_error(
    exc: Exception,
    *,
    filename: str | None = None,
    source: str | None = None,
    intent: str | None = None,
    suppress_details: bool = False,
) -> str:
    """Return a human-first explanation for an exception."""
    cause = exc.__cause__ or exc
    message = str(cause) or str(exc) or "Unknown error"
    explanation, suggestions = _explain_message(message, cause)
    location = _extract_location(cause, message, filename, source)

    if not explanation:
        explanation = ["Sona hit a runtime error."]

    lines: list[str] = []
    lines.extend(explanation)

    if suggestions:
        lines.append("")
        lines.append("You may want:")
        for suggestion in suggestions:
            lines.append(f"- {suggestion}")

    if intent:
        lines.append("")
        lines.append(f"Intent: {intent}")

    if location:
        lines.append("")
        lines.append(f"Location: {location}")

    if not suppress_details:
        lines.append("")
        lines.append(f"Details: {message}")

    return "\n".join(lines).strip()


def _explain_message(message: str, exc: Exception) -> tuple[list[str], list[str]]:
    msg = message.strip()
    suggestions: list[str] = []
    explanation: list[str] = []

    if isinstance(exc, ZeroDivisionError) or "division by zero" in msg.lower():
        explanation = [
            "This operation tried to divide by zero.",
            "Division by zero is undefined and stops execution.",
        ]
        suggestions = [
            "Check that the divisor is not zero before dividing",
            "Add a guard like: if denom != 0",
        ]
        return explanation, suggestions

    name_match = _NAME_ERROR_RE.search(msg)
    if name_match:
        var_name = name_match.group(1)
        explanation = [
            f"The name '{var_name}' was used before it was defined.",
        ]
        suggestions = [
            f"Declare '{var_name}' earlier with let/const",
            "Check for typos in the variable name",
        ]
        return explanation, suggestions

    unsupported = _UNSUPPORTED_OPERAND_RE.search(msg)
    if unsupported:
        op = unsupported.group(1).strip()
        left = unsupported.group(2)
        right = unsupported.group(3)
        explanation = [
            f"This operation tried to apply '{op}' between a { _friendly_type(left) } and a { _friendly_type(right) }.",
            "Those types cannot be combined directly.",
        ]
        suggestions = _operand_suggestions(op, left, right)
        return explanation, suggestions

    not_subscriptable = _NOT_SUBSCRIPTABLE_RE.search(msg)
    if not_subscriptable:
        kind = not_subscriptable.group(1)
        explanation = [
            f"You tried to index a { _friendly_type(kind) }, which does not support [] access.",
        ]
        suggestions = [
            "If this is a function, call it with () before indexing",
            "If this is a dict, check that the key exists",
        ]
        return explanation, suggestions

    not_callable = _NOT_CALLABLE_RE.search(msg)
    if not_callable:
        kind = not_callable.group(1)
        explanation = [
            f"You tried to call a { _friendly_type(kind) } like a function.",
        ]
        suggestions = [
            "Remove the () if you intended to access a value",
            "Check that the variable holds a function",
        ]
        return explanation, suggestions

    must_be = _MUST_BE_RE.search(msg)
    if must_be:
        expected = must_be.group(1)
        got = must_be.group(2)
        explanation = [
            f"This call expected a { _friendly_type(expected) }, but received a { _friendly_type(got) }.",
        ]
        suggestions = [
            "Convert the input to the expected type",
            "Check the value you passed into the function",
        ]
        return explanation, suggestions

    if isinstance(exc, KeyError) or msg.startswith("KeyError"):
        explanation = [
            "A dictionary key was missing.",
        ]
        suggestions = [
            "Check the key spelling",
            "Use a default value when the key is missing",
        ]
        return explanation, suggestions

    if isinstance(exc, IndexError) or "index out of range" in msg.lower():
        explanation = [
            "An index was outside the valid range for this list.",
        ]
        suggestions = [
            "Check the list length before indexing",
            "Use list slicing to stay in bounds",
        ]
        return explanation, suggestions

    attr_match = _ATTRIBUTE_ERROR_RE.search(msg)
    if attr_match:
        obj_type = attr_match.group(1)
        attr = attr_match.group(2)
        explanation = [
            f"The { _friendly_type(obj_type) } does not have a '{attr}' property.",
        ]
        suggestions = [
            "Check the property name for typos",
            "Verify the object is the type you expect",
        ]
        return explanation, suggestions

    if isinstance(exc, SyntaxError) or "syntax error" in msg.lower():
        explanation = [
            "Sona could not parse this line due to a syntax error.",
        ]
        suggestions = [
            "Check for missing or extra punctuation",
            "Verify all brackets and parentheses are balanced",
        ]
        return explanation, suggestions

    if "Unexpected token" in msg:
        explanation = [
            "The parser found a token it did not expect at this position.",
        ]
        suggestions = [
            "Check for missing or extra punctuation",
            "Verify all brackets and parentheses are balanced",
        ]
        return explanation, suggestions

    return explanation, suggestions


def _operand_suggestions(op: str, left: str, right: str) -> list[str]:
    types = {left, right}
    suggestions: list[str] = []
    if op == "+":
        if "list" in types and ("int" in types or "float" in types):
            suggestions.append("Use sum(the_list) if you want a total")
            suggestions.append("Append the number to the list instead of adding")
        if "str" in types and ("int" in types or "float" in types):
            suggestions.append("Convert the number to a string with str()")
            suggestions.append("Use an f-string for formatting")
    if op in ("-", "*", "/") and "str" in types:
        suggestions.append("Convert the string to a number before arithmetic")
    if not suggestions:
        suggestions.append("Convert values to compatible types before combining")
    return suggestions


def _friendly_type(type_name: str) -> str:
    mapping = {
        "int": "integer",
        "float": "number",
        "str": "string",
        "list": "list",
        "dict": "dictionary",
        "NoneType": "null",
        "function": "function",
        "builtin_function_or_method": "function",
    }
    return mapping.get(type_name, type_name)


def _extract_location(
    exc: Exception,
    message: str,
    filename: str | None,
    source: str | None,
) -> str | None:
    line = getattr(exc, "lineno", None)
    column = getattr(exc, "offset", None)
    if line is None:
        match = _LINE_COL_RE.search(message)
        if match:
            try:
                line = int(match.group(1))
            except Exception:
                line = None
            if match.group(2):
                try:
                    column = int(match.group(2))
                except Exception:
                    column = None

    if line is None:
        return None

    location = f"line {line}"
    if column:
        location = f"{location}, column {column}"
    if filename and filename not in ("<string>", "<repl>"):
        location = f"{filename} ({location})"
    if source:
        code_line = _line_from_source(source, line)
        if code_line:
            location = f"{location}: {code_line}"
    return location


def _line_from_source(source: str, line_no: int) -> str | None:
    if line_no <= 0:
        return None
    lines = source.splitlines()
    if line_no > len(lines):
        return None
    return lines[line_no - 1].strip()
