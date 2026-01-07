"""
Sona transpiler (core syntax) for v0.10.1.

This module converts Sona source into Python using the existing parser/AST.
Core syntax: variables, expressions, control flow, functions, lists/dicts,
and basic imports. Cognitive/AI constructs are emitted when enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sys
import re

from .parser_v090 import create_parser
from .ast_nodes import (
    AICompleteStatement,
    AIDebugStatement,
    AIExplainStatement,
    AIOptimizeStatement,
    BinaryOperatorExpression,
    BreakStatement,
    CallExpression,
    CatchClause,
    CognitiveCheckStatement,
    CognitiveScopeStatement,
    CognitiveTraceStatement,
    ContinueStatement,
    DictionaryExpression,
    DecisionStatement,
    ElifClause,
    EnhancedForLoop,
    EnhancedIfStatement,
    EnhancedTryStatement,
    EnhancedWhileLoop,
    ExplainStepStatement,
    ExportStatement,
    Expression,
    FocusBlockStatement,
    FocusModeStatement,
    FunctionCallExpression,
    FunctionDefinition,
    ImportFromStatement,
    ImportStatement,
    IndexExpression,
    IntentStatement,
    KeywordArgument,
    ListExpression,
    LiteralExpression,
    MethodCallExpression,
    PositionalArgument,
    ProfileStatement,
    PrintStatement,
    PropertyAccessExpression,
    ReturnStatement,
    SpreadArgument,
    UnaryOperatorExpression,
    VariableAssignment,
    VariableExpression,
    WorkingMemoryStatement,
)


@dataclass
class TranspileOptions:
    include_cognitive_blocks: bool = True
    emit_runtime_helpers: bool = True
    indent: str = "    "


@dataclass
class TranspileResult:
    code: str
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


class TranspileError(Exception):
    pass


def _read_text_safe(path: str) -> str:
    p = Path(path)
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeError:
            continue
        except FileNotFoundError:
            raise
        except Exception:
            continue
    return p.read_text(encoding="utf-8", errors="replace")


def _configure_console() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes  # type: ignore
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _preprocess_source(source: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    updated = source

    replacements = [
        (r"!\s+=", "!=", "Normalized spaced '!=' operator"),
        (r"<\s+=", "<=", "Normalized spaced '<=' operator"),
        (r">\s+=", ">=", "Normalized spaced '>=' operator"),
        (r"=\s+=", "==", "Normalized spaced '==' operator"),
    ]
    for pattern, repl, message in replacements:
        if re.search(pattern, updated):
            updated = re.sub(pattern, repl, updated)
            warnings.append(message)

    tuple_pattern = re.compile(r"=\s*\(([^()\n]*,[^()\n]*)\)")
    if tuple_pattern.search(updated):
        updated = tuple_pattern.sub(r"= [\1]", updated)
        warnings.append("Normalized tuple literals to list literals for core transpile")

    return updated, warnings


class SonaTranspiler:
    def __init__(self, options: TranspileOptions | None = None):
        self.options = options or TranspileOptions()

    def transpile_file(self, path: str) -> TranspileResult:
        source = _read_text_safe(path)
        return self.transpile_source(source, filename=path)

    def transpile_source(self, source: str, filename: str = "<string>") -> TranspileResult:
        _configure_console()
        source, preprocess_warnings = _preprocess_source(source)
        parser = create_parser()
        try:
            statements = parser.parse(source, filename)
        except Exception as exc:
            return TranspileResult("", [f"Parse error: {exc}"], preprocess_warnings)

        if not statements:
            return TranspileResult("", [f"Parse failed for {filename}"], preprocess_warnings)

        emitter = _PythonEmitter(self.options)
        emitter.emit_program(statements)
        code = emitter.render()
        warnings = preprocess_warnings + emitter.warnings
        return TranspileResult(code, emitter.errors, warnings)


class _PythonEmitter:
    def __init__(self, options: TranspileOptions):
        self.options = options
        self.lines: list[str] = []
        self.indent_level = 0
        self.used_helpers: set[str] = set()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self._temp_index = 0

    def emit_program(self, statements: list[Any]) -> None:
        for stmt in statements:
            self.emit_stmt(stmt)

    def emit_stmt(self, stmt: Any) -> None:
        if stmt is None:
            return
        if isinstance(stmt, list):
            for item in stmt:
                self.emit_stmt(item)
            return
        if isinstance(stmt, VariableAssignment):
            expr = self.emit_expr(stmt.value)
            self.emit_line(f"{stmt.name} = {expr}")
            return
        if isinstance(stmt, PrintStatement):
            if stmt.expression is None:
                self.emit_line("print()")
            else:
                expr = self.emit_expr(stmt.expression)
                self.emit_line(f"print({expr})")
            return
        if isinstance(stmt, EnhancedIfStatement):
            cond = self.emit_expr(stmt.condition)
            self.emit_line(f"if {cond}:")
            self.emit_block(stmt.if_body)
            for elif_clause in stmt.elif_clauses:
                self.emit_elif(elif_clause)
            if stmt.else_body is not None:
                self.emit_line("else:")
                self.emit_block(stmt.else_body)
            return
        if isinstance(stmt, EnhancedForLoop):
            iterable = self.emit_expr(stmt.iterable)
            self.emit_line(f"for {stmt.iterator_var} in {iterable}:")
            self.emit_block(stmt.body)
            return
        if isinstance(stmt, EnhancedWhileLoop):
            cond = self.emit_expr(stmt.condition)
            self.emit_line(f"while {cond}:")
            self.emit_block(stmt.body)
            return
        if isinstance(stmt, BreakStatement):
            self.emit_line("break")
            return
        if isinstance(stmt, ContinueStatement):
            self.emit_line("continue")
            return
        if isinstance(stmt, ReturnStatement):
            if stmt.expression is None:
                self.emit_line("return")
            else:
                expr = self.emit_expr(stmt.expression)
                self.emit_line(f"return {expr}")
            return
        if isinstance(stmt, FunctionDefinition):
            params = self.format_params(stmt)
            self.emit_line(f"def {stmt.name}({params}):")
            self.emit_block(stmt.body)
            return
        if isinstance(stmt, ImportStatement):
            line = self.format_import(stmt)
            self.emit_line(line)
            return
        if isinstance(stmt, ImportFromStatement):
            line = self.format_import_from(stmt)
            self.emit_line(line)
            return
        if isinstance(stmt, ExportStatement):
            self.emit_stmt(stmt.exported_item)
            self.warnings.append(
                self.format_warn(stmt, "export statement ignored in core transpiler")
            )
            return
        if isinstance(stmt, EnhancedTryStatement):
            self.emit_try(stmt)
            return
        if isinstance(stmt, CognitiveScopeStatement):
            if self.options.include_cognitive_blocks:
                self.emit_cognitive_scope(stmt)
            else:
                self.warnings.append(
                    self.format_warn(stmt, "cognitive_scope ignored (core syntax only)")
                )
                for item in stmt.body:
                    self.emit_stmt(item)
            return
        if isinstance(stmt, FocusBlockStatement):
            if self.options.include_cognitive_blocks:
                self.emit_focus_block(stmt)
            else:
                self.warnings.append(
                    self.format_warn(stmt, "focus block ignored (core syntax only)")
                )
                for item in stmt.body:
                    self.emit_stmt(item)
            return
        if isinstance(
            stmt,
            (
                CognitiveCheckStatement,
                FocusModeStatement,
                WorkingMemoryStatement,
                IntentStatement,
                DecisionStatement,
                CognitiveTraceStatement,
                ExplainStepStatement,
                ProfileStatement,
            ),
        ):
            if self.options.include_cognitive_blocks:
                self.emit_cognitive_call(stmt)
            else:
                self.warnings.append(
                    self.format_warn(stmt, "cognitive statement ignored (core syntax only)")
                )
            return
        if self.is_ai_statement(stmt):
            if self.options.include_cognitive_blocks:
                self.emit_ai_statement(stmt)
            else:
                self.warnings.append(
                    self.format_warn(stmt, "AI statement ignored (core syntax only)")
                )
            return
        if isinstance(stmt, Expression):
            expr = self.emit_expr(stmt)
            self.emit_line(expr)
            return

        self.errors.append(self.format_error(stmt, "Unsupported statement"))

    def emit_expr(self, expr: Any) -> str:
        if expr is None:
            return "None"
        if isinstance(expr, LiteralExpression):
            return repr(expr.value)
        if isinstance(expr, VariableExpression):
            return expr.name
        if isinstance(expr, BinaryOperatorExpression):
            left = self.emit_expr(expr.left)
            right = self.emit_expr(expr.right)
            op = str(expr.operator)
            if op == "&&" or op == "and":
                op = "and"
            elif op == "||" or op == "or":
                op = "or"
            if op == "+":
                self.used_helpers.add("sona_add")
                return f"sona_add({left}, {right})"
            return f"({left} {op} {right})"
        if isinstance(expr, UnaryOperatorExpression):
            operand = self.emit_expr(expr.operand)
            op = str(expr.operator)
            if op in ("!", "not"):
                return f"(not {operand})"
            return f"({op}{operand})"
        if isinstance(expr, ListExpression):
            items = ", ".join(self.emit_expr(item) for item in expr.elements)
            return f"[{items}]"
        if isinstance(expr, DictionaryExpression):
            pairs = []
            for key, value in expr.pairs:
                key_text = repr(key)
                value_text = self.emit_expr(value)
                pairs.append(f"{key_text}: {value_text}")
            return "{" + ", ".join(pairs) + "}"
        if isinstance(expr, FunctionCallExpression):
            func_name = getattr(expr, "name", None) or getattr(expr, "function_name", None)
            if not func_name:
                self.errors.append(self.format_error(expr, "Function call missing name"))
                func_name = "unknown_function"
            args = self.format_call_args(expr.arguments)
            return f"{func_name}({args})"
        if isinstance(expr, CallExpression):
            callee = self.emit_expr(expr.callee)
            args = self.format_call_args(expr.arguments)
            return f"{callee}({args})"
        if isinstance(expr, PropertyAccessExpression):
            obj = self.emit_expr(expr.object)
            self.used_helpers.add("sona_get_prop")
            return f"sona_get_prop({obj}, {repr(expr.property_name)})"
        if isinstance(expr, MethodCallExpression):
            obj = self.emit_expr(expr.object)
            args = self.format_call_args(expr.arguments)
            self.used_helpers.add("sona_call_method")
            if args:
                return f"sona_call_method({obj}, {repr(expr.method_name)}, {args})"
            return f"sona_call_method({obj}, {repr(expr.method_name)})"
        if isinstance(expr, IndexExpression):
            obj = self.emit_expr(expr.object)
            idx = self.emit_expr(expr.index)
            return f"{obj}[{idx}]"

        self.errors.append(self.format_error(expr, "Unsupported expression"))
        return "None"

    def emit_elif(self, clause: ElifClause) -> None:
        cond = self.emit_expr(clause.condition)
        self.emit_line(f"elif {cond}:")
        self.emit_block(clause.body)

    def emit_try(self, stmt: EnhancedTryStatement) -> None:
        self.emit_line("try:")
        self.emit_block(stmt.try_body)

        if not stmt.catch_clauses:
            self.warnings.append(self.format_warn(stmt, "try without catch"))
        for clause in stmt.catch_clauses:
            self.emit_catch(clause)

        if stmt.finally_body is not None:
            self.emit_line("finally:")
            self.emit_block(stmt.finally_body)

    def emit_catch(self, clause: CatchClause) -> None:
        exc_type = (clause.exception_type or "Exception").strip()
        if exc_type in ("", "_", "*"):
            exc_type = "Exception"
        if clause.var_name:
            self.emit_line(f"except {exc_type} as {clause.var_name}:")
        else:
            self.emit_line(f"except {exc_type}:")
        self.emit_block(clause.body)

    def emit_cognitive_call(self, stmt: Any) -> None:
        func_name = self.cognitive_function_name(stmt)
        args = self.format_mapping_kwargs(getattr(stmt, "body", {}) or {})
        self.used_helpers.add("sona_cognitive_runtime")
        if args:
            self.emit_line(f"{func_name}({args})")
        else:
            self.emit_line(f"{func_name}()")

    def emit_cognitive_scope(self, stmt: CognitiveScopeStatement) -> None:
        name_expr = self.format_value(stmt.name)
        meta = stmt.meta or {}
        meta_literal = self.format_mapping_literal(meta)
        needs_budget = any(
            key in meta for key in ("budget", "max_complexity", "max_statements")
        )
        complexity_arg = ""
        if needs_budget:
            complexity = self.estimate_complexity(stmt.body)
            complexity_arg = f", complexity={complexity}"
        self.used_helpers.add("sona_cognitive_runtime")
        self.emit_line(f"with sona_cognitive_scope({name_expr}, {meta_literal}{complexity_arg}):")
        self.emit_block(stmt.body)

    def emit_focus_block(self, stmt: FocusBlockStatement) -> None:
        meta = stmt.meta or {}
        meta_literal = self.format_mapping_literal(meta)
        self.used_helpers.add("sona_cognitive_runtime")
        self.emit_line(f"with sona_focus_block({meta_literal}):")
        self.emit_block(stmt.body)

    def emit_ai_statement(self, stmt: Any) -> None:
        self.used_helpers.add("sona_ai_runtime")
        if isinstance(stmt, AICompleteStatement):
            args = [self.format_ai_value(stmt.prompt)]
            args.extend(self.format_ai_value(opt) for opt in (stmt.options or []))
            self.emit_line(f"sona_ai_complete({', '.join(args)})")
            return
        if isinstance(stmt, AIExplainStatement):
            args = [self.format_ai_value(stmt.target)]
            args.extend(self.format_ai_value(opt) for opt in (stmt.options or []))
            self.emit_line(f"sona_ai_explain({', '.join(args)})")
            return
        if isinstance(stmt, AIDebugStatement):
            args = [self.format_ai_value(stmt.code)]
            args.extend(self.format_ai_value(opt) for opt in (stmt.options or []))
            self.emit_line(f"sona_ai_debug({', '.join(args)})")
            return
        if isinstance(stmt, AIOptimizeStatement):
            args = [self.format_ai_value(stmt.code)]
            args.extend(self.format_ai_value(opt) for opt in (stmt.options or []))
            self.emit_line(f"sona_ai_optimize({', '.join(args)})")
            return
        self.errors.append(self.format_error(stmt, "Unsupported AI statement"))

    def emit_block(self, statements: list[Any]) -> None:
        self.indent_level += 1
        if not statements:
            self.emit_line("pass")
        else:
            for stmt in statements:
                self.emit_stmt(stmt)
        self.indent_level -= 1

    def format_params(self, stmt: FunctionDefinition) -> str:
        params: list[str] = []
        for name in stmt.parameters or []:
            if name in stmt.default_values:
                default_expr = self.emit_expr(stmt.default_values[name])
                params.append(f"{name}={default_expr}")
            else:
                params.append(name)
        if stmt.varargs_param:
            params.append(f"*{stmt.varargs_param}")
        return ", ".join(params)

    def format_call_args(self, args: list[Any] | None) -> str:
        if not args:
            return ""
        rendered = []
        for arg in args:
            rendered.append(self.format_call_arg(arg))
        return ", ".join([item for item in rendered if item])

    def format_call_arg(self, arg: Any) -> str:
        if isinstance(arg, PositionalArgument):
            return self.emit_expr(arg.value)
        if isinstance(arg, KeywordArgument):
            return f"{arg.name}={self.emit_expr(arg.value)}"
        if isinstance(arg, SpreadArgument):
            expr = self.emit_expr(arg.value)
            if isinstance(arg.value, DictionaryExpression):
                return f"**{expr}"
            if isinstance(arg.value, ListExpression):
                return f"*{expr}"
            self.warnings.append(self.format_warn(arg, "spread argument emitted as * (type unknown)"))
            return f"*{expr}"
        if isinstance(arg, Expression):
            return self.emit_expr(arg)
        return repr(arg)

    def format_value(self, value: Any) -> str:
        if isinstance(value, Expression):
            return self.emit_expr(value)
        return repr(value)

    def format_mapping_kwargs(self, mapping: dict[str, Any]) -> str:
        if not mapping:
            return ""
        parts: list[str] = []
        extra_items: list[str] = []
        for key, value in mapping.items():
            value_text = self.format_value(value)
            if isinstance(key, str) and key.isidentifier():
                parts.append(f"{key}={value_text}")
            else:
                extra_items.append(f"{repr(key)}: {value_text}")
        if extra_items:
            parts.append("**{" + ", ".join(extra_items) + "}")
        return ", ".join(parts)

    def format_mapping_literal(self, mapping: dict[str, Any]) -> str:
        if not mapping:
            return "{}"
        items: list[str] = []
        for key, value in mapping.items():
            items.append(f"{repr(key)}: {self.format_value(value)}")
        return "{" + ", ".join(items) + "}"

    def format_ai_value(self, value: Any) -> str:
        return self.format_value(value)

    def cognitive_function_name(self, stmt: Any) -> str:
        if isinstance(stmt, CognitiveCheckStatement):
            return "sona_cognitive_check"
        if isinstance(stmt, FocusModeStatement):
            return "sona_focus_mode"
        if isinstance(stmt, WorkingMemoryStatement):
            return "sona_working_memory"
        if isinstance(stmt, IntentStatement):
            return "sona_intent"
        if isinstance(stmt, DecisionStatement):
            return "sona_decision"
        if isinstance(stmt, CognitiveTraceStatement):
            return "sona_cognitive_trace"
        if isinstance(stmt, ExplainStepStatement):
            return "sona_explain_step"
        if isinstance(stmt, ProfileStatement):
            return "sona_profile"
        return "sona_cognitive_unknown"

    def estimate_complexity(self, body: list[Any]) -> int:
        if not body:
            return 0
        total = 0
        for stmt in body:
            total += 1
            total += self.nested_complexity(stmt)
        return total

    def nested_complexity(self, stmt: Any) -> int:
        nested = 0
        for attr in ("body", "if_body", "else_body", "try_body", "finally_body"):
            block = getattr(stmt, attr, None)
            if isinstance(block, list):
                nested += len(block)
                for child in block:
                    nested += self.nested_complexity(child)
        for attr in ("elif_clauses", "catch_clauses"):
            block = getattr(stmt, attr, None)
            if isinstance(block, list):
                for child in block:
                    nested += self.nested_complexity(child)
        return nested

    def format_import(self, stmt: ImportStatement) -> str:
        module_path = stmt.module_path
        alias = stmt.alias
        if "." in module_path:
            parts = module_path.split(".")
            parent = ".".join(parts[:-1])
            leaf = parts[-1]
            alias_name = alias or module_path.replace(".", "_")
            if alias is None:
                self.warnings.append(
                    self.format_warn(stmt, f"import '{module_path}' mapped to '{alias_name}'")
                )
            return f"from sona.stdlib.{parent} import {leaf} as {alias_name}"
        if alias:
            return f"from sona.stdlib import {module_path} as {alias}"
        return f"from sona.stdlib import {module_path}"

    def format_import_from(self, stmt: ImportFromStatement) -> str:
        items = ", ".join(stmt.import_list)
        if not items:
            self.warnings.append(self.format_warn(stmt, "empty import-from list"))
            return f"from sona.stdlib.{stmt.module_path} import *"
        return f"from sona.stdlib.{stmt.module_path} import {items}"

    def render(self) -> str:
        helpers = []
        if self.options.emit_runtime_helpers:
            if "sona_cognitive_runtime" in self.used_helpers:
                helpers.append(self.helper_cognitive_runtime())
            if "sona_ai_runtime" in self.used_helpers:
                helpers.append(self.helper_ai_runtime())
            if "sona_add" in self.used_helpers:
                helpers.append(self.helper_add())
            if "sona_get_prop" in self.used_helpers:
                helpers.append(self.helper_get_prop())
            if "sona_call_method" in self.used_helpers:
                helpers.append(self.helper_call_method())

        header = []
        if helpers:
            header.extend(helpers)
        if header:
            header.append("")

        return "\n".join(header + self.lines) + "\n"

    def helper_cognitive_runtime(self) -> str:
        indent = self.options.indent
        indent2 = indent * 2
        indent3 = indent * 3
        indent4 = indent * 4
        lines = [
            "import time",
            "",
            "class _SonaCognitiveRuntime:",
            indent + "def __init__(self):",
            indent2 + "self.working_memory = {}",
            indent2 + "self.focus_sessions = []",
            indent2 + "self.intent_stack = []",
            indent2 + "self.decision_log = []",
            indent2 + "self.scope_stack = []",
            indent2 + "self.trace_enabled = False",
            indent2 + "self.trace_log = []",
            indent2 + "self.profile = None",
            indent2 + "self.last_analysis = None",
            indent2 + "self.lint_warnings = []",
            "",
            indent + "def _record_trace(self, event_type, payload):",
            indent2 + "if not self.trace_enabled:",
            indent3 + "return",
            indent2 + "self.trace_log.append({",
            indent3 + "'type': event_type,",
            indent3 + "'payload': payload,",
            indent3 + "'timestamp': time.time(),",
            indent2 + "})",
            "",
            indent + "def _basic_analysis(self, task, context):",
            indent2 + "context_text = str(context or \"\")",
            indent2 + "length = len(context_text)",
            indent2 + "if length < 200:",
            indent3 + "load = \"low\"",
            indent2 + "elif length < 800:",
            indent3 + "load = \"medium\"",
            indent2 + "else:",
            indent3 + "load = \"high\"",
            indent2 + "suggestions = []",
            indent2 + "if load != \"low\":",
            indent3 + "suggestions.append(\"Break work into smaller steps\")",
            indent2 + "if load == \"high\":",
            indent3 + "suggestions.append(\"Schedule a short break and resume with a plan\")",
            indent2 + "return {",
            indent3 + "'task': task or \"\",",
            indent3 + "'cognitive_load': load,",
            indent3 + "'context_preview': context_text[:160],",
            indent3 + "'suggestions': suggestions,",
            indent2 + "}",
            "",
            indent + "def _compute_intent_overlap(self, goal, activity):",
            indent2 + "if not goal or not activity:",
            indent3 + "return 1.0 if not goal else 0.0",
            indent2 + "goal_tokens = set(str(goal).lower().split())",
            indent2 + "act_tokens = set(str(activity).lower().split())",
            indent2 + "if not goal_tokens:",
            indent3 + "return 0.0",
            indent2 + "return len(goal_tokens & act_tokens) / len(goal_tokens)",
            "",
            indent + "def check_cognitive_load(self, params):",
            indent2 + "task = str(params.get('task') or params.get('arg0') or \"\")",
            indent2 + "context = params.get('context') or params.get('code') or params.get('arg1') or \"\"",
            indent2 + "analysis = self._basic_analysis(task, context)",
            indent2 + "intent = self.intent_stack[-1] if self.intent_stack else {}",
            indent2 + "goal = str(intent.get('goal') or intent.get('intent') or intent.get('arg0') or \"\")",
            indent2 + "drift_score = self._compute_intent_overlap(goal, str(task or context))",
            indent2 + "analysis['intent_goal'] = goal",
            indent2 + "analysis['intent_drift_score'] = drift_score",
            indent2 + "analysis['intent_drift'] = drift_score < 0.4 if goal else False",
            indent2 + "analysis['confidence'] = 'high' if analysis['cognitive_load'] == 'low' else 'medium'",
            indent2 + "self.last_analysis = analysis",
            indent2 + "self._record_trace('cognitive_check', analysis)",
            indent2 + "return analysis",
            "",
            indent + "def configure_focus_mode(self, params):",
            indent2 + "action = params.get('action', 'start')",
            indent2 + "description = str(params.get('task') or params.get('mode') or params.get('arg0') or 'focus')",
            indent2 + "minutes = params.get('minutes') or params.get('duration') or params.get('arg1') or 25",
            indent2 + "try:",
            indent3 + "minutes = int(minutes)",
            indent2 + "except Exception:",
            indent3 + "minutes = 25",
            indent2 + "if action == 'status':",
            indent3 + "return {",
            indent4 + "'status': 'ok',",
            indent4 + "'active_sessions': len(self.focus_sessions),",
            indent4 + "'last_session': self.focus_sessions[-1] if self.focus_sessions else None,",
            indent3 + "}",
            indent2 + "session = {",
            indent3 + "'description': description,",
            indent3 + "'minutes': minutes,",
            indent3 + "'state': 'active',",
            indent3 + "'started_at': time.time(),",
            indent2 + "}",
            indent2 + "self.focus_sessions.append(session)",
            indent2 + "self._record_trace('focus_mode', {'description': description, 'minutes': minutes})",
            indent2 + "return {",
            indent3 + "'status': 'ok',",
            indent3 + "'message': f'Focus mode started for {minutes} minutes',",
            indent3 + "'session': session,",
            indent2 + "}",
            "",
            indent + "def manage_working_memory(self, params):",
            indent2 + "action = (params.get('action') or '').lower() or 'store'",
            indent2 + "key = params.get('key') or params.get('name') or params.get('arg0')",
            indent2 + "value = params.get('value') if 'value' in params else params.get('arg1')",
            indent2 + "if action in ('store', 'remember'):",
            indent3 + "if key is None:",
            indent4 + "return {'status': 'error', 'message': 'working_memory: key is required for store'}",
            indent3 + "self.working_memory[str(key)] = value",
            indent3 + "return {'status': 'ok', 'stored': True, 'key': key, 'value': value}",
            indent2 + "if action in ('recall', 'get'):",
            indent3 + "if key is None:",
            indent4 + "return {'status': 'error', 'message': 'working_memory: key is required for recall'}",
            indent3 + "return {'status': 'ok', 'key': key, 'value': self.working_memory.get(str(key))}",
            indent2 + "if action in ('clear',):",
            indent3 + "self.working_memory.clear()",
            indent3 + "self._record_trace('working_memory', {'action': 'clear'})",
            indent3 + "return {'status': 'ok', 'cleared': True}",
            indent2 + "status = {",
            indent3 + "'status': 'ok',",
            indent3 + "'size': len(self.working_memory),",
            indent3 + "'keys': list(self.working_memory.keys())[:20],",
            indent2 + "}",
            indent2 + "self._record_trace('working_memory', status)",
            indent2 + "return status",
            "",
            indent + "def record_intent(self, params):",
            indent2 + "intent = {",
            indent3 + "'goal': params.get('goal') or params.get('arg0'),",
            indent3 + "'constraints': params.get('constraints'),",
            indent3 + "'success': params.get('success') or params.get('definition_of_done'),",
            indent3 + "'tags': params.get('tags'),",
            indent2 + "}",
            indent2 + "intent['meta'] = params",
            indent2 + "self.intent_stack.append(intent)",
            indent2 + "self._record_trace('intent', intent)",
            indent2 + "return {'status': 'ok', 'intent': intent, 'stack_depth': len(self.intent_stack)}",
            "",
            indent + "def record_decision(self, params):",
            indent2 + "decision = {",
            indent3 + "'label': params.get('label') or params.get('arg0'),",
            indent3 + "'rationale': params.get('rationale') or params.get('why') or params.get('arg1'),",
            indent3 + "'option': params.get('option'),",
            indent3 + "'timestamp': time.time(),",
            indent2 + "}",
            indent2 + "self.decision_log.append(decision)",
            indent2 + "self._record_trace('decision', decision)",
            indent2 + "return {'status': 'ok', 'decision': decision, 'count': len(self.decision_log)}",
            "",
            indent + "def toggle_trace(self, params):",
            indent2 + "if 'enabled' in params:",
            indent3 + "enabled = bool(params['enabled'])",
            indent2 + "elif 'arg0' in params:",
            indent3 + "enabled = str(params['arg0']).lower() in ('1', 'true', 'on', 'yes')",
            indent2 + "else:",
            indent3 + "enabled = True",
            indent2 + "self.trace_enabled = enabled",
            indent2 + "return {'status': 'ok', 'trace_enabled': self.trace_enabled}",
            "",
            indent + "def explain_step(self, params):",
            indent2 + "summary = {",
            indent3 + "'profile': self.profile,",
            indent3 + "'intents': self.intent_stack[-3:],",
            indent3 + "'decisions': self.decision_log[-5:],",
            indent3 + "'last_analysis': self.last_analysis,",
            indent3 + "'lint_warnings': self.lint_warnings[-3:],",
            indent3 + "'current_scope': self.scope_stack[-1] if self.scope_stack else None,",
            indent3 + "'trace_tail': self.trace_log[-10:] if self.trace_enabled else [],",
            indent2 + "}",
            indent2 + "self._record_trace('explain_step', {'requested': True})",
            indent2 + "return summary",
            "",
            indent + "def set_profile(self, params):",
            indent2 + "profile = params.get('profile') or params.get('arg0') or params.get('name')",
            indent2 + "if profile is None:",
            indent3 + "return {'status': 'error', 'message': 'profile name is required'}",
            indent2 + "self.profile = str(profile).lower()",
            indent2 + "self._record_trace('profile', {'profile': self.profile})",
            indent2 + "return {'status': 'ok', 'profile': self.profile}",
            "",
            indent + "def push_scope(self, name, meta, complexity=None):",
            indent2 + "meta = meta or {}",
            indent2 + "scope = {",
            indent3 + "'name': name or f'scope_{len(self.scope_stack)}',",
            indent3 + "'meta': meta,",
            indent2 + "}",
            indent2 + "warning = self._check_scope_budget(meta, complexity)",
            indent2 + "if warning:",
            indent3 + "scope['budget_warning'] = warning",
            indent3 + "self.lint_warnings.append({'warnings': [warning], 'warning_count': 1})",
            indent2 + "self.scope_stack.append(scope)",
            indent2 + "self._record_trace('scope_enter', scope)",
            indent2 + "return scope",
            "",
            indent + "def pop_scope(self):",
            indent2 + "if not self.scope_stack:",
            indent3 + "return None",
            indent2 + "scope = self.scope_stack.pop()",
            indent2 + "self._record_trace('scope_exit', scope)",
            indent2 + "return scope",
            "",
            indent + "def _check_scope_budget(self, meta, complexity):",
            indent2 + "budget = meta.get('budget') or meta.get('max_complexity') or meta.get('max_statements')",
            indent2 + "if budget is None or complexity is None:",
            indent3 + "return ''",
            indent2 + "try:",
            indent3 + "budget_val = int(budget)",
            indent2 + "except Exception:",
            indent3 + "return ''",
            indent2 + "if complexity <= budget_val:",
            indent3 + "return ''",
            indent2 + "return f'Scope complexity {complexity} exceeds budget {budget_val}'",
            "",
            "class _SonaFocusBlock:",
            indent + "def __init__(self, runtime, meta):",
            indent2 + "self.runtime = runtime",
            indent2 + "self.meta = meta or {}",
            indent2 + "self.prev_trace = None",
            "",
            indent + "def __enter__(self):",
            indent2 + "self.prev_trace = self.runtime.trace_enabled",
            indent2 + "self.runtime.trace_enabled = True",
            indent2 + "name = (",
            indent3 + "self.meta.get('task')",
            indent3 + "or self.meta.get('name')",
            indent3 + "or self.meta.get('goal')",
            indent3 + "or 'focus'",
            indent2 + ")",
            indent2 + "focus_meta = dict(self.meta)",
            indent2 + "focus_meta.setdefault('focus', True)",
            indent2 + "self.runtime.push_scope(name, focus_meta, complexity=None)",
            indent2 + "return self",
            "",
            indent + "def __exit__(self, exc_type, exc, tb):",
            indent2 + "self.runtime.pop_scope()",
            indent2 + "self.runtime.trace_enabled = self.prev_trace",
            indent2 + "return False",
            "",
            "class _SonaCognitiveScope:",
            indent + "def __init__(self, runtime, name, meta, complexity):",
            indent2 + "self.runtime = runtime",
            indent2 + "self.name = name",
            indent2 + "self.meta = meta or {}",
            indent2 + "self.complexity = complexity",
            indent + "def __enter__(self):",
            indent2 + "self.runtime.push_scope(self.name, self.meta, self.complexity)",
            indent2 + "return self",
            indent + "def __exit__(self, exc_type, exc, tb):",
            indent2 + "self.runtime.pop_scope()",
            indent2 + "return False",
            "",
            "_sona_cognitive_runtime = _SonaCognitiveRuntime()",
            "",
            "def sona_cognitive_check(**params):",
            indent + "return _sona_cognitive_runtime.check_cognitive_load(params)",
            "",
            "def sona_focus_mode(**params):",
            indent + "return _sona_cognitive_runtime.configure_focus_mode(params)",
            "",
            "def sona_working_memory(**params):",
            indent + "return _sona_cognitive_runtime.manage_working_memory(params)",
            "",
            "def sona_intent(**params):",
            indent + "return _sona_cognitive_runtime.record_intent(params)",
            "",
            "def sona_decision(**params):",
            indent + "return _sona_cognitive_runtime.record_decision(params)",
            "",
            "def sona_cognitive_trace(**params):",
            indent + "return _sona_cognitive_runtime.toggle_trace(params)",
            "",
            "def sona_explain_step(**params):",
            indent + "return _sona_cognitive_runtime.explain_step(params)",
            "",
            "def sona_profile(**params):",
            indent + "return _sona_cognitive_runtime.set_profile(params)",
            "",
            "def sona_focus_block(meta=None):",
            indent + "return _SonaFocusBlock(_sona_cognitive_runtime, meta)",
            "",
            "def sona_cognitive_scope(name, meta=None, complexity=None):",
            indent + "return _SonaCognitiveScope(_sona_cognitive_runtime, name, meta, complexity)",
        ]
        return "\n".join(lines)

    def helper_ai_runtime(self) -> str:
        indent = self.options.indent
        lines = [
            "def _sona_ai_stub(action, *args):",
            indent + "return {'status': 'unavailable', 'action': action, 'args': list(args)}",
            "",
            "def sona_ai_complete(prompt, *options):",
            indent + "return _sona_ai_stub('complete', prompt, *options)",
            "",
            "def sona_ai_explain(target, *options):",
            indent + "return _sona_ai_stub('explain', target, *options)",
            "",
            "def sona_ai_debug(code, *options):",
            indent + "return _sona_ai_stub('debug', code, *options)",
            "",
            "def sona_ai_optimize(code, *options):",
            indent + "return _sona_ai_stub('optimize', code, *options)",
        ]
        return "\n".join(lines)

    def helper_add(self) -> str:
        return "\n".join(
            [
                "def sona_add(left, right):",
                f"{self.options.indent}if isinstance(left, str) or isinstance(right, str):",
                f"{self.options.indent}{self.options.indent}return str(left) + str(right)",
                f"{self.options.indent}return left + right",
            ]
        )

    def helper_get_prop(self) -> str:
        return "\n".join(
            [
                "def sona_get_prop(obj, name):",
                f"{self.options.indent}if isinstance(obj, dict) and name in obj:",
                f"{self.options.indent}{self.options.indent}return obj[name]",
                f"{self.options.indent}return getattr(obj, name)",
            ]
        )

    def helper_call_method(self) -> str:
        return "\n".join(
            [
                "def sona_call_method(obj, name, *args, **kwargs):",
                f"{self.options.indent}if hasattr(obj, name):",
                f"{self.options.indent}{self.options.indent}method = getattr(obj, name)",
                f"{self.options.indent}{self.options.indent}return method(*args, **kwargs)",
                f"{self.options.indent}if isinstance(obj, dict) and name in obj and callable(obj[name]):",
                f"{self.options.indent}{self.options.indent}return obj[name](*args, **kwargs)",
                f"{self.options.indent}raise AttributeError(f\"Object has no method '{'{'}name{'}'}'\")",
            ]
        )

    def emit_line(self, text: str) -> None:
        indent = self.options.indent * self.indent_level
        self.lines.append(f"{indent}{text}")

    def format_error(self, node: Any, message: str) -> str:
        line = getattr(node, "line_number", None)
        if line:
            return f"{message} at line {line}"
        return message

    def format_warn(self, node: Any, message: str) -> str:
        line = getattr(node, "line_number", None)
        if line:
            return f"{message} at line {line}"
        return message

    def is_ai_statement(self, stmt: Any) -> bool:
        return isinstance(
            stmt,
            (
                AICompleteStatement,
                AIExplainStatement,
                AIDebugStatement,
                AIOptimizeStatement,
            ),
        )

    def format_ai_placeholder(self, stmt: Any) -> str:
        name = stmt.__class__.__name__
        return f"# {name} omitted by core transpiler"
