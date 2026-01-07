"""
Sona v0.10.1 - Enhanced Interpreter with Full Loop Support
========================================================

Production-grade interpreter with complete language feature support.
Includes all control flow constructs, module system, and cognitive features.

Features:
- Full control flow (if/else/elif, while, for, repeat)
- Break/continue statements
- Module system (import/export)
- AI integration statements
- Cognitive programming support
- Try/catch/finally exception handling
- Function definitions with parameters
- Class definitions and methods
- Complete expression evaluation
"""

import ast
import json
import sys
import time
import traceback
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any  # Ruff UP035: will migrate away from Dict/List


# Add current directory to path for imports
if str(Path(__file__).parent) not in sys.path:
    sys.path.append(str(Path(__file__).parent))

# Import parser
try:
    from .parser_v090 import SonaParserv090
except ImportError:
    try:
        from parser_v090 import SonaParserv090
    except ImportError:
        print("⚠️  Advanced parser not available, using basic mode")
        SonaParserv090 = None

# Import AST nodes
try:
    from .ast_nodes import (
        AICompleteStatement,
        AIDebugStatement,
        AIExplainStatement,
        AIOptimizeStatement,
        ReturnValue,
    )
except ImportError:
    try:
        from ast_nodes import (
            AICompleteStatement,
            AIDebugStatement,
            AIExplainStatement,
            AIOptimizeStatement,
            ReturnValue,
        )
    except ImportError:
        print("⚠️  AST nodes not available, using placeholder mode")
        # Create placeholder classes

        class AICompleteStatement:
            pass

        class AIExplainStatement:
            pass

        class AIDebugStatement:
            pass

        class AIOptimizeStatement:
            pass

# Import Cognitive Assistant
try:
    from .ai.cognitive_assistant import CognitiveAssistant
except ImportError:
    try:
        from ai.cognitive_assistant import CognitiveAssistant
    except ImportError:
        print("[WARN] CognitiveAssistant not available, using placeholder mode")

        class CognitiveAssistant:
            def __init__(self):
                pass

            def analyze_working_memory(self, *args, **kwargs):
                return {'cognitive_load': 'medium', 'suggestions': []}

            def detect_hyperfocus(self, *args, **kwargs):
                return {'hyperfocus_detected': False}

            def analyze_executive_function(self, *args, **kwargs):
                return {'task_breakdown': [], 'support_strategies': []}


# Import structured error system (v0.10.1)
from .errors import (
    SonaError,
    SonaSyntaxError,
    SonaImportError,
    SonaNameError,
    SonaTypeError,
    SonaValueError,
    SonaIndexError,
    SonaKeyError,
    SonaDivisionError,
    SourceLocation,
    ErrorCode,
    get_source_line,
    format_error_simple,
)


class SonaInterpreterError(Exception):
    """Base class for Sona interpreter errors (legacy compat)"""
    pass


class SonaRuntimeError(SonaError):
    """Runtime error in Sona interpretation (v0.10.1: extends SonaError)"""
    pass


class BreakException(Exception):
    """Exception for break statement flow control"""
    pass


class ContinueException(Exception):
    """Exception for continue statement flow control"""
    pass


class SimpleModuleSystem:
    """Simple module system for loading stdlib modules"""

    def __init__(self, interpreter, *, project_root: str | Path | None = None):
        self.interpreter = interpreter
        self.loaded_modules = {}
        self.loaded_by_path = {}
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.modules_path = self.project_root / ".sona_modules"
        self.stdlib_path = Path(__file__).parent / "stdlib"
        self.smod_path = Path(__file__).resolve().parents[1] / "stdlib"
        self.stdlib_namespace = SimpleNamespace()
        self.stdlib_errors = {}
        self._register_stdlib_root()

    def _register_stdlib_root(self) -> None:
        if "stdlib" in self.interpreter.memory.global_scope:
            return
        self.interpreter.memory.set_variable(
            "stdlib",
            self.stdlib_namespace,
            global_scope=True
        )

    def _expose_native_aliases(self, module_obj, module_name_for_prefix: str) -> None:
        prefix = f"{module_name_for_prefix}_"
        for attr_name in dir(module_obj):
            if not attr_name.startswith(prefix):
                continue
            alias_name = attr_name[len(prefix):]
            if not hasattr(module_obj, alias_name):
                try:
                    setattr(module_obj, alias_name, getattr(module_obj, attr_name))
                except Exception:
                    # If the module uses unusual descriptors, skip aliasing.
                    pass

    def _attach_cognitive_metadata(self, module_obj) -> None:
        monitor = getattr(self.interpreter, "cognitive_monitor", None)
        if not monitor:
            return
        try:
            setattr(module_obj, "__sona_profile__", monitor.profile)
            setattr(
                module_obj,
                "__sona_intent__",
                monitor.intent_stack[-1] if monitor.intent_stack else None
            )
            setattr(module_obj, "__sona_decisions__", monitor.decision_log[-5:])
        except Exception:
            pass

    def _load_module_from_file(
        self,
        module_id: str,
        module_file: Path,
        *,
        native_prefix: str | None = None
    ):
        if not module_file.exists():
            raise ImportError(f"Module file not found: {module_file}")

        import importlib.util

        spec = importlib.util.spec_from_file_location(module_id, module_file)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load module spec for {module_id}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if native_prefix:
            self._expose_native_aliases(module, native_prefix)

        self._attach_cognitive_metadata(module)
        return module

    def _resolve_smod_path(self, module_path: str) -> Path:
        parts = module_path.split(".")
        # Prefer project-local installed packages first.
        local = self.modules_path.joinpath(*parts).with_suffix(".smod")
        if local.exists():
            return local
        local_pkg = self.modules_path.joinpath(*parts) / "__init__.smod"
        if local_pkg.exists():
            return local_pkg

        return self.smod_path.joinpath(*parts).with_suffix(".smod")

    def _load_smod_module(
        self,
        module_path: str,
        module_file: Path,
        *,
        allow_missing_native: bool = False,
    ):
        if not module_file.exists():
            raise ImportError(f"Module file not found: {module_file}")

        from .stdlib.native_bridge import NativeBridge

        module_name = module_path.split(".")[-1]
        raw_source = module_file.read_text(encoding="utf-8-sig")
        source_lines = []
        for line in raw_source.splitlines():
            if line.lstrip().startswith("#"):
                continue
            source_lines.append(line)
        source = "\n".join(source_lines)

        original_globals = self.interpreter.memory.global_scope
        original_functions = self.interpreter.functions
        module_globals = dict(original_globals)

        class _NullNativeBridge:
            def __getattr__(self, name: str):
                raise AttributeError(name)

        try:
            native_bridge = NativeBridge(module_name)
        except Exception:
            if allow_missing_native:
                native_bridge = _NullNativeBridge()
            else:
                raise

        module_globals["__native__"] = native_bridge

        previous_context = getattr(self.interpreter, "_module_context", None)
        self.interpreter.memory.global_scope = module_globals
        self.interpreter.functions = dict(original_functions)
        self.interpreter._module_context = module_globals

        try:
            self.interpreter._execute_sona_code(source, filename=str(module_file))
        finally:
            self.interpreter._module_context = previous_context
            self.interpreter.memory.global_scope = original_globals
            self.interpreter.functions = original_functions

        exports = {
            name: value
            for name, value in module_globals.items()
            if name not in original_globals or original_globals[name] is not value
        }
        exports = {
            name: value
            for name, value in exports.items()
            if not name.startswith("__")
        }

        module = ModuleType(f"sona.smod.{module_path}")
        for name, value in exports.items():
            setattr(module, name, value)
        def _module_getattr(attr_name: str, _bridge=native_bridge):
            try:
                return getattr(_bridge, attr_name)
            except AttributeError as exc:
                raise AttributeError(attr_name) from exc

        setattr(module, "__getattr__", _module_getattr)
        return module

    def _load_module(self, module_path: str, *, force_smod: bool = False):
        if module_path in self.loaded_by_path:
            return self.loaded_by_path[module_path]

        parts = module_path.split(".")
        smod_file = self._resolve_smod_path(module_path)

        if module_path.startswith("native_"):
            module_file = self.stdlib_path / f"{module_path}.py"
            module = self._load_module_from_file(
                f"sona.stdlib.{module_path}",
                module_file
            )
        elif force_smod:
            allow_missing_native = False
            try:
                allow_missing_native = smod_file.is_relative_to(self.modules_path)
            except Exception:
                allow_missing_native = str(smod_file).startswith(str(self.modules_path))
            module = self._load_smod_module(module_path, smod_file, allow_missing_native=allow_missing_native)
        elif smod_file.exists():
            allow_missing_native = False
            try:
                allow_missing_native = smod_file.is_relative_to(self.modules_path)
            except Exception:
                allow_missing_native = str(smod_file).startswith(str(self.modules_path))
            module = self._load_smod_module(module_path, smod_file, allow_missing_native=allow_missing_native)
        elif len(parts) > 1:
            module_file = self.stdlib_path.joinpath(*parts).with_suffix(".py")
            module = self._load_module_from_file(
                f"sona.stdlib.{module_path}",
                module_file
            )
        else:
            native_module_path = self.stdlib_path / f"native_{module_path}.py"
            if native_module_path.exists():
                module = self._load_module_from_file(
                    f"sona.stdlib.native_{module_path}",
                    native_module_path,
                    native_prefix=module_path
                )
            else:
                regular_module_path = self.stdlib_path / f"{module_path}.py"
                module = self._load_module_from_file(
                    f"sona.stdlib.{module_path}",
                    regular_module_path
                )

        self.loaded_by_path[module_path] = module
        return module

    def _register_stdlib_namespace(self, module_path: str, module_obj) -> None:
        parts = module_path.split(".")
        root: Any = self.stdlib_namespace

        for part in parts[:-1]:
            child = getattr(root, part, None)
            if child is None:
                child = SimpleNamespace()
                setattr(root, part, child)
            root = child

        final_name = parts[-1]
        existing = getattr(root, final_name, None)
        if isinstance(existing, SimpleNamespace) and isinstance(module_obj, ModuleType):
            for key, value in existing.__dict__.items():
                setattr(module_obj, key, value)
        if isinstance(root, ModuleType):
            submodules = getattr(root, "__sona_submodules__", None)
            if submodules is None:
                submodules = {}
                setattr(root, "__sona_submodules__", submodules)
            submodules[final_name] = module_obj
        else:
            setattr(root, final_name, module_obj)

    def _expose_global_module(
        self,
        module_name: str,
        module_obj,
        *,
        force: bool = False
    ) -> bool:
        if not force:
            if "." in module_name:
                return False
            if module_name in self.interpreter.memory.global_scope:
                return False

        self.interpreter.memory.set_variable(
            module_name,
            module_obj,
            global_scope=True
        )
        self.interpreter.modules[module_name] = module_obj
        return True

    def _load_manifest_modules(self) -> list[str]:
        manifest_path = self.stdlib_path / "MANIFEST.json"
        if not manifest_path.exists():
            return []
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        modules = payload.get("modules", [])
        return [name for name in modules if isinstance(name, str)]

    def _scan_stdlib_modules(self) -> list[str]:
        modules: list[str] = []
        if not self.stdlib_path.exists():
            return modules
        for path in self.stdlib_path.rglob("*.py"):
            if path.name == "__init__.py":
                continue
            rel = path.relative_to(self.stdlib_path)
            if "__pycache__" in rel.parts:
                continue
            modules.append(".".join(rel.with_suffix("").parts))
        return modules

    def _sorted_stdlib_modules(self, modules: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for name in modules:
            if name in seen:
                continue
            seen.add(name)
            unique.append(name)
        unique.sort(key=lambda name: name.count("."))
        return unique

    def load_stdlib_modules(self) -> dict[str, Any]:
        modules = self._load_manifest_modules()
        if not modules:
            modules = self._scan_stdlib_modules()
        modules = self._sorted_stdlib_modules(modules)

        loaded: list[str] = []
        errors: dict[str, str] = {}

        for module_path in modules:
            try:
                module_obj = self._load_module(module_path)
            except Exception as exc:
                errors[module_path] = str(exc)
                continue

            self.loaded_modules.setdefault(module_path, module_obj)
            self._register_stdlib_namespace(module_path, module_obj)
            self._expose_global_module(module_path, module_obj, force=False)
            loaded.append(module_path)

        self.stdlib_errors = errors
        return {"loaded": loaded, "errors": errors}

    def import_module(self, module_path: str, alias: str | None = None):
        """Import a module and make it available in the interpreter

        Supports nested namespaces like 'collection.list':
        - collection.list -> sona/stdlib/collection/list.py
        - http -> sona/stdlib/http.py or native_http.py
        """
        force_smod = False
        if module_path.endswith(".smod"):
            module_path = module_path[:-5]
            force_smod = True

        module_name = alias if alias else module_path

        module_obj = self.loaded_by_path.get(module_path)
        if not module_obj:
            module_obj = self.loaded_modules.get(module_path)
        if not module_obj:
            module_obj = self._load_module(module_path, force_smod=force_smod)

        self.loaded_modules[module_name] = module_obj
        self.loaded_by_path[module_path] = module_obj
        self.loaded_modules.setdefault(module_path, module_obj)

        self._register_stdlib_namespace(module_path, module_obj)
        self._expose_global_module(module_name, module_obj, force=True)
        return module_obj


class SonaMemoryManager:
    """Manages memory and variable scoping for Sona interpreter"""

    def __init__(self):
        self.global_scope = {}
        self.local_scopes = []
        self.call_stack = []

    def push_scope(self, scope_name: str = "local"):
        """Push a new local scope"""
        self.local_scopes.append({})
        self.call_stack.append(scope_name)

    def pop_scope(self):
        """Pop the current local scope"""
        if self.local_scopes:
            self.local_scopes.pop()
            self.call_stack.pop()

    def set_variable(self, name: str, value: Any, global_scope: bool = False):
        """Set a variable in the appropriate scope"""
        if global_scope or not self.local_scopes:
            self.global_scope[name] = value
        else:
            self.local_scopes[-1][name] = value

    def get_variable(self, name: str) -> Any:
        """Get a variable from the appropriate scope"""
        # Check local scopes first (most recent first)
        for scope in reversed(self.local_scopes):
            if name in scope:
                return scope[name]

        # Check global scope
        if name in self.global_scope:
            return self.global_scope[name]

        raise NameError(f"Variable '{name}' is not defined")

    def has_variable(
        self,
        name: str
    ) -> bool:
        """Check if a variable exists in any scope"""
        try:
            self.get_variable(name)
            return True
        except NameError:
            return False


class CognitiveMonitor:
    """Lightweight cognitive runtime used by cognitive_* statements and helpers."""

    def __init__(self, interpreter, assistant=None):
        self.interpreter = interpreter
        self.assistant = assistant
        self.working_memory: dict[str, Any] = {}
        self.focus_sessions: list[dict[str, Any]] = []
        self.last_analysis: dict[str, Any] | None = None
        self.intent_stack: list[dict[str, Any]] = []
        self.scope_stack: list[dict[str, Any]] = []
        self.decision_log: list[dict[str, Any]] = []
        self.trace_enabled: bool = False
        self.trace_log: list[dict[str, Any]] = []
        self.lint_warnings: list[dict[str, Any]] = []
        self.profile: str | None = None
        self.last_attention_alerts: list[str] = []

    def _basic_analysis(self, task: str, context: str) -> dict[str, Any]:
        """Deterministic fallback cognitive load analysis (no AI required)."""
        context_text = str(context or "")
        length = len(context_text)
        if length < 200:
            load = "low"
        elif length < 800:
            load = "medium"
        else:
            load = "high"

        suggestions: list[str] = []
        if load != "low":
            suggestions.append("Break work into smaller steps")
        if load == "high":
            suggestions.append("Schedule a short break and resume with a plan")

        return {
            "task": task or "",
            "cognitive_load": load,
            "context_preview": context_text[:160],
            "suggestions": suggestions,
        }

    def check_cognitive_load(self, params: dict[str, Any]) -> dict[str, Any]:
        """Analyze current cognitive load using the assistant when available."""
        task = str(params.get('task') or params.get('arg0') or "")
        context = params.get('context') or params.get('code') or params.get('arg1') or ""

        if self.assistant and hasattr(self.assistant, 'analyze_working_memory'):
            try:
                analysis = self.assistant.analyze_working_memory(task, str(context))
            except Exception:
                analysis = self._basic_analysis(task, str(context))
        else:
            analysis = self._basic_analysis(task, str(context))

        # Intent drift heuristic
        intent = self.intent_stack[-1] if self.intent_stack else {}
        goal = str(intent.get("goal") or intent.get("intent") or intent.get("arg0") or "")
        drift_score = self._compute_intent_overlap(goal, str(task or context))
        analysis["intent_goal"] = goal
        analysis["intent_drift_score"] = drift_score
        analysis["intent_drift"] = drift_score < 0.4 if goal else False
        analysis["confidence"] = "high" if analysis["cognitive_load"] == "low" else "medium"
        analysis["attention_alerts"] = self._attention_alerts(analysis["cognitive_load"])

        self.last_analysis = analysis
        self._record_trace("cognitive_check", analysis)
        return analysis

    def configure_focus_mode(self, params: dict[str, Any]) -> dict[str, Any]:
        """Configure or check focus mode settings."""
        action = params.get('action', 'start')
        description = str(params.get('task') or params.get('mode') or params.get('arg0') or "focus")
        minutes = params.get('minutes') or params.get('duration') or params.get('arg1') or 25
        try:
            minutes = int(minutes)
        except Exception:
            minutes = 25

        if action == 'status':
            return {
                "status": "ok",
                "active_sessions": len(self.focus_sessions),
                "last_session": self.focus_sessions[-1] if self.focus_sessions else None,
            }

        session = {
            "description": description,
            "minutes": minutes,
            "state": "active",
            "started_at": time.time(),
        }
        self.focus_sessions.append(session)
        self._record_trace("focus_mode", {"description": description, "minutes": minutes})
        return {
            "status": "ok",
            "message": f"Focus mode started for {minutes} minutes",
            "session": session,
        }

    def manage_working_memory(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle working_memory(...) operations."""
        action = (params.get('action') or '').lower() or 'store'
        key = params.get('key') or params.get('name') or params.get('arg0')
        value = params.get('value') if 'value' in params else params.get('arg1')

        if action in ('store', 'remember'):
            if key is None:
                return {"status": "error", "message": "working_memory: key is required for store"}
            self.working_memory[str(key)] = value
            return {"status": "ok", "stored": True, "key": key, "value": value}

        if action in ('recall', 'get'):
            if key is None:
                return {"status": "error", "message": "working_memory: key is required for recall"}
            return {"status": "ok", "key": key, "value": self.working_memory.get(str(key))}

        if action in ('clear',):
            self.working_memory.clear()
            self._record_trace("working_memory", {"action": "clear"})
            return {"status": "ok", "cleared": True}

        # Default: status
        status = {
            "status": "ok",
            "size": len(self.working_memory),
            "keys": list(self.working_memory.keys())[:20],
        }
        self._record_trace("working_memory", status)
        return status

    def record_intent(self, params: dict[str, Any]) -> dict[str, Any]:
        """Record or update the current intent metadata."""
        intent = {
            "goal": params.get("goal") or params.get("arg0"),
            "constraints": params.get("constraints"),
            "success": params.get("success") or params.get("definition_of_done"),
            "tags": params.get("tags"),
        }
        # Keep raw params for completeness
        intent["meta"] = params
        self.intent_stack.append(intent)
        self._record_trace("intent", intent)
        return {"status": "ok", "intent": intent, "stack_depth": len(self.intent_stack)}

    def record_decision(self, params: dict[str, Any]) -> dict[str, Any]:
        """Record a decision for traceability."""
        decision = {
            "label": params.get("label") or params.get("arg0"),
            "rationale": params.get("rationale") or params.get("why") or params.get("arg1"),
            "option": params.get("option"),
            "timestamp": time.time(),
        }
        self.decision_log.append(decision)
        self._record_trace("decision", decision)
        return {"status": "ok", "decision": decision, "count": len(self.decision_log)}

    def set_profile(self, params: dict[str, Any]) -> dict[str, Any]:
        """Set the active cognitive accessibility profile."""
        profile = params.get("profile") or params.get("arg0") or params.get("name")
        if profile is None:
            return {"status": "error", "message": "profile name is required"}
        self.profile = str(profile).lower()
        self._record_trace("profile", {"profile": self.profile})
        return {"status": "ok", "profile": self.profile}

    def push_scope(self, name: str | None, meta: dict[str, Any]) -> None:
        """Enter a cognitive scope boundary."""
        scope = {"name": name or f"scope_{len(self.scope_stack)}", "meta": meta}
        self.scope_stack.append(scope)
        self._record_trace("scope_enter", scope)

    def pop_scope(self) -> None:
        """Exit the current cognitive scope boundary."""
        if self.scope_stack:
            scope = self.scope_stack.pop()
            self._record_trace("scope_exit", scope)

    def toggle_trace(self, params: dict[str, Any]) -> dict[str, Any]:
        """Turn reasoning trace on or off."""
        # Accept on/off/bool
        if "enabled" in params:
            enabled = bool(params["enabled"])
        elif "arg0" in params:
            enabled = str(params["arg0"]).lower() in ("1", "true", "on", "yes")
        else:
            enabled = True
        self.trace_enabled = enabled
        return {"status": "ok", "trace_enabled": self.trace_enabled}

    def explain_step(self, params: dict[str, Any]) -> dict[str, Any]:
        """Provide an explainability snapshot using recorded traces and intents."""
        summary = {
            "profile": self.profile,
            "intents": self.intent_stack[-3:],
            "decisions": self.decision_log[-5:],
            "last_analysis": self.last_analysis,
            "lint_warnings": self.lint_warnings[-3:],
            "current_scope": self.scope_stack[-1] if self.scope_stack else None,
            "trace_tail": self.trace_log[-10:] if self.trace_enabled else [],
        }
        self._record_trace("explain_step", {"requested": True})
        return summary

    def _compute_intent_overlap(self, goal: str, activity: str) -> float:
        """Simple token-overlap heuristic for intent drift detection."""
        if not goal or not activity:
            return 1.0 if not goal else 0.0
        goal_tokens = set(goal.lower().split())
        act_tokens = set(activity.lower().split())
        if not goal_tokens:
            return 0.0
        return len(goal_tokens & act_tokens) / len(goal_tokens)

    def _record_trace(self, event_type: str, payload: dict[str, Any]) -> None:
        """Record an event if tracing is enabled."""
        if not self.trace_enabled:
            return
        self.trace_log.append(
            {
                "type": event_type,
                "payload": payload,
                "timestamp": time.time(),
            }
        )

    def lint_context(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run deterministic cognitive lint checks on a provided context."""
        context = str(params.get("context") or params.get("code") or params.get("arg0") or "")
        warnings: list[str] = []

        if self.intent_stack and "cognitive_check(" not in context and "explain_step(" not in context:
            warnings.append("Intent declared without drift checks (add cognitive_check or explain_step)")

        risky_tokens = ("delete", "drop", "truncate", "rm ", "remove", "wipe")
        if any(tok in context.lower() for tok in risky_tokens) and not self.decision_log:
            warnings.append("Risky operation detected without decision rationale")

        lines = [line for line in context.splitlines() if line.strip()]
        if len(lines) > 200:
            warnings.append("High line count (200+): consider cognitive_scope or refactor")

        lint_report = {"warnings": warnings, "warning_count": len(warnings)}
        if warnings:
            self.lint_warnings.append(lint_report)
        return lint_report

    def export_trace(self, params: dict[str, Any]) -> dict[str, Any]:
        """Export trace/logs to JSON file or return payload."""
        payload = self._report_payload()
        path = params.get("path") or params.get("file") or params.get("arg0")
        if not path:
            return {"status": "ok", "payload": payload}
        try:
            import json
            with open(str(path), "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            return {"status": "ok", "path": str(path)}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def report(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a snapshot suitable for docs or explainability output."""
        return self._report_payload()

    def evaluate_scope_budget(self, meta: dict[str, Any], body: list[Any]) -> list[str]:
        """Evaluate scope complexity against budget metadata."""
        budget = meta.get("budget") or meta.get("max_complexity") or meta.get("max_statements")
        if budget is None:
            return []
        try:
            budget_val = int(budget)
        except Exception:
            return []

        complexity = self._estimate_complexity(body)
        if complexity <= budget_val:
            return []
        warning = f"Scope complexity {complexity} exceeds budget {budget_val}"
        self.lint_warnings.append({"warnings": [warning], "warning_count": 1})
        return [warning]

    def _estimate_complexity(self, body: list[Any]) -> int:
        """Estimate complexity by walking statement nodes."""
        if not body:
            return 0
        total = 0
        for stmt in body:
            total += 1
            total += self._nested_complexity(stmt)
        return total

    def _nested_complexity(self, stmt: Any) -> int:
        """Recursively count nested statements for complexity."""
        nested = 0
        for attr in ("body", "if_body", "else_body", "try_body", "finally_body"):
            block = getattr(stmt, attr, None)
            if isinstance(block, list):
                nested += len(block)
                for child in block:
                    nested += self._nested_complexity(child)
        for attr in ("elif_clauses", "catch_clauses"):
            block = getattr(stmt, attr, None)
            if isinstance(block, list):
                for child in block:
                    nested += self._nested_complexity(child)
        return nested

    def _attention_alerts(self, load: str) -> list[str]:
        """Compute attention alerts based on active focus sessions."""
        alerts: list[str] = []
        if not self.focus_sessions:
            return alerts
        if load == "high":
            alerts.append("High cognitive load during focus session: consider a short break")
        now = time.time()
        for session in self.focus_sessions:
            started_at = session.get("started_at")
            minutes = session.get("minutes")
            if started_at and minutes and (now - started_at) > (minutes * 60):
                alerts.append("Focus session exceeded planned duration")
        self.last_attention_alerts = alerts
        return alerts

    def _report_payload(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "intents": self.intent_stack[-5:],
            "decisions": self.decision_log[-10:],
            "last_analysis": self.last_analysis,
            "lint_warnings": self.lint_warnings[-5:],
            "scope": self.scope_stack[-1] if self.scope_stack else None,
            "attention_alerts": self.last_attention_alerts,
            "trace_enabled": self.trace_enabled,
            "trace": self.trace_log[-20:] if self.trace_enabled else [],
        }


class SonaFunction:
    """Represents a function in Sona"""

    def __init__(
        self,
        name: str,
        parameters: list[str],
        varargs_param: str | None,
        default_values: dict[str, Any] | None,
        body: Any,
        interpreter,
        cognitive_context: dict[str, Any] | None = None,
        closure: dict[str, Any] | None = None
    ):
        self.name = name
        self.parameters = parameters
        self.varargs_param = varargs_param
        self.default_values = default_values or {}
        self.body = body
        self.interpreter = interpreter
        self.cognitive_context = cognitive_context or {}
        self.closure = closure

    def call(
        self,
        arguments: list[Any],
        keyword_arguments: dict[str, Any] | None = None
    ) -> Any:
        """Call the function with given arguments"""
        keyword_arguments = keyword_arguments or {}

        bound: dict[str, Any] = {}
        extra_positional: list[Any] = []

        # Bind positional arguments
        for i, value in enumerate(arguments):
            if i < len(self.parameters):
                bound[self.parameters[i]] = value
            else:
                extra_positional.append(value)

        if extra_positional and not self.varargs_param:
            raise ValueError(
                f"Function '{self.name}' expects {len(self.parameters)} "
                f"arguments, got {len(arguments)}"
            )

        # Bind keyword arguments
        for key, value in keyword_arguments.items():
            if key in bound:
                raise ValueError(
                    f"Function '{self.name}' got multiple values for argument '{key}'"
                )
            if key in self.parameters:
                bound[key] = value
            else:
                raise ValueError(
                    f"Function '{self.name}' got an unexpected keyword argument '{key}'"
                )

        # Fill missing parameters from defaults
        for param in self.parameters:
            if param in bound:
                continue
            if param not in self.default_values:
                raise ValueError(
                    f"Function '{self.name}' missing required argument: {param}"
                )

            default_expr = self.default_values[param]
            # Defaults are stored as AST Expressions; evaluate in caller context
            if hasattr(default_expr, 'evaluate'):
                bound[param] = default_expr.evaluate(self.interpreter)
            else:
                bound[param] = default_expr

        # Bind varargs
        if self.varargs_param:
            bound[self.varargs_param] = extra_positional

        # Push new scope for function execution
        closure_active = False
        if self.closure:
            self.interpreter.memory.push_scope(f"closure:{self.name}")
            closure_active = True
            global_scope = self.interpreter.memory.global_scope
            for key, value in self.closure.items():
                if key in global_scope:
                    continue
                self.interpreter.memory.set_variable(key, value)

        self.interpreter.memory.push_scope(f"function:{self.name}")

        try:
            # Set parameters as local variables
            for param in self.parameters:
                self.interpreter.memory.set_variable(param, bound[param])

            if self.varargs_param:
                self.interpreter.memory.set_variable(
                    self.varargs_param,
                    bound.get(self.varargs_param, [])
                )

            # Execute function body
            result = self.interpreter.execute_block(self.body)
            return result
        finally:
            # Always pop the function scope
            self.interpreter.memory.pop_scope()
            if closure_active:
                self.interpreter.memory.pop_scope()


class SonaUnifiedInterpreter:
    """
    Unified interpreter for the Sona programming language.
    Supports cognitive programming, AI assistance, and enhanced control flow.
    """

    def __init__(self, *, project_root: str | Path | None = None):
        """Initialize the interpreter with all necessary components"""
        self.memory = SonaMemoryManager()
        self.functions = {}
        self.modules = {}
        self.ai_enabled = False
        self.debug_mode = False
        self.execution_stack = []
        self.focus_block_stack = []
        self.focus_block_active = False
        self.suppress_diagnostics = False
        self.auto_ai_suggestions_enabled = True
        self._pending_focus_restore = None

        # Initialize module system
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.module_system = SimpleModuleSystem(self, project_root=self.project_root)

        # Initialize cognitive assistant
        self.cognitive_assistant = CognitiveAssistant()
        self.cognitive_monitor = CognitiveMonitor(self, self.cognitive_assistant)
        self.session_start_time = time.time()
        self.current_context = ""

        # Initialize built-in functions
        self._setup_builtins()

        # Preload stdlib modules into the core runtime namespace
        self.stdlib_status = self.module_system.load_stdlib_modules()

    def _setup_builtins(self):
        """Setup built-in functions and variables"""
        # Built-in functions
        gv = self.memory.set_variable
        gv('print', self._builtin_print, global_scope=True)
        gv('len', self._builtin_len, global_scope=True)
        gv('type', self._builtin_type, global_scope=True)
        gv('str', self._builtin_str, global_scope=True)
        gv('int', self._builtin_int, global_scope=True)
        gv('float', self._builtin_float, global_scope=True)
        gv('bool', self._builtin_bool, global_scope=True)
        gv('list', self._builtin_list, global_scope=True)
        gv('dict', self._builtin_dict, global_scope=True)
        gv('set', self._builtin_set, global_scope=True)
        gv('range', self._builtin_range, global_scope=True)
        gv('sum', self._builtin_sum, global_scope=True)
        gv('max', self._builtin_max, global_scope=True)
        gv('min', self._builtin_min, global_scope=True)

        # Cognitive AI built-in functions
        self.memory.set_variable('think', self._cognitive_think,
                                 global_scope=True)
        self.memory.set_variable('remember', self._cognitive_remember,
                                 global_scope=True)
        self.memory.set_variable('focus', self._cognitive_focus,
                                 global_scope=True)
        self.memory.set_variable('analyze_load', self._cognitive_analyze_load,
                                 global_scope=True)
        self.memory.set_variable('cognitive_check', self._builtin_cognitive_check,
                                 global_scope=True)
        self.memory.set_variable('focus_mode', self._builtin_focus_mode,
                                 global_scope=True)
        self.memory.set_variable('working_memory', self._builtin_working_memory,
                                 global_scope=True)
        self.memory.set_variable('cognitive_load', self._cognitive_analyze_load,
                                 global_scope=True)
        self.memory.set_variable('check_focus', self._builtin_check_focus,
                                 global_scope=True)
        self.memory.set_variable('intent', self._builtin_intent,
                                 global_scope=True)
        self.memory.set_variable('decision', self._builtin_decision,
                                 global_scope=True)
        self.memory.set_variable('cognitive_trace', self._builtin_cognitive_trace,
                                 global_scope=True)
        self.memory.set_variable('explain_step', self._builtin_explain_step,
                                 global_scope=True)
        self.memory.set_variable('profile', self._builtin_profile,
                                 global_scope=True)
        self.memory.set_variable('cognitive_lint', self._builtin_cognitive_lint,
                                 global_scope=True)
        self.memory.set_variable('cognitive_report', self._builtin_cognitive_report,
                                 global_scope=True)
        self.memory.set_variable('cognitive_export', self._builtin_cognitive_export,
                                 global_scope=True)

        # REAL AI-Native Language Features - NO MOCKS
        self.memory.set_variable('ai_complete', self._real_ai_complete,
                                 global_scope=True)
        self.memory.set_variable('ai_explain', self._real_ai_explain,
                                 global_scope=True)
        self.memory.set_variable('ai_simplify', self._real_ai_simplify,
                                 global_scope=True)
        self.memory.set_variable('ai_debug', self._real_ai_debug,
                                 global_scope=True)
        # Week 2: Advanced AI Programming Constructs
        self.memory.set_variable('ai_reason', self._real_ai_reason,
                                 global_scope=True)
        self.memory.set_variable('ai_refactor', self._real_ai_refactor,
                                 global_scope=True)
        self.memory.set_variable('ai_test', self._real_ai_test,
                                 global_scope=True)
        self.memory.set_variable('ai_analyze', self._real_ai_analyze,
                                 global_scope=True)
        self.memory.set_variable('ai_generate', self._real_ai_generate,
                                 global_scope=True)
        # Week 3: AI-Enhanced Development Environment Integration
        self.memory.set_variable('ai_context', self._real_ai_context,
                                 global_scope=True)
        self.memory.set_variable('ai_suggest', self._real_ai_suggest,
                                 global_scope=True)
        self.memory.set_variable('ai_document', self._real_ai_document,
                                 global_scope=True)
        self.memory.set_variable('ai_optimize', self._real_ai_optimize,
                                 global_scope=True)
        self.memory.set_variable('ai_security', self._real_ai_security,
                                 global_scope=True)
        self.memory.set_variable('ai_mentor', self._real_ai_mentor,
                                 global_scope=True)
        self.memory.set_variable('generate_code', self._real_ai_generate_code,
                                 global_scope=True)
        self.memory.set_variable('complete_function',
                                 self._real_ai_complete_function,
                                 global_scope=True)
        self.memory.set_variable('explain_code', self._real_ai_explain_code,
                                 global_scope=True)
        self.memory.set_variable('suggest_improvements',
                                 self._real_ai_suggest_improvements,
                                 global_scope=True)
        self.memory.set_variable('when_confused',
                                 self._cognitive_when_confused,
                                 global_scope=True)
        self.memory.set_variable('break_if_overwhelmed',
                                 self._cognitive_break_if_overwhelmed,
                                 global_scope=True)
        self.memory.set_variable('simplify_task',
                                 self._cognitive_simplify_task,
                                 global_scope=True)
        self.memory.set_variable('review_progress',
                                 self._cognitive_review_progress,
                                 global_scope=True)

        # Day 3C: Advanced AI Constructs
        self.memory.set_variable('adaptive_learning',
                                 self._ai_adaptive_learning,
                                 global_scope=True)
        self.memory.set_variable('meta_cognition',
                                 self._ai_meta_cognition,
                                 global_scope=True)
        self.memory.set_variable('dynamic_context_switching',
                                 self._ai_dynamic_context_switching,
                                 global_scope=True)
        self.memory.set_variable('multi_step_reasoning',
                                 self._ai_multi_step_reasoning,
                                 global_scope=True)

        # Built-in variables
        self.memory.set_variable('__version__', '0.10.1', global_scope=True)
        self.memory.set_variable('__sona__', True, global_scope=True)
        self.memory.set_variable('True', True, global_scope=True)
        self.memory.set_variable('False', False, global_scope=True)
        self.memory.set_variable('None', None, global_scope=True)
        self.memory.set_variable('nil', None, global_scope=True)

    def _builtin_print(self, *args):
        """Built-in print function"""
        print(*args)
        return None

    def _builtin_len(self, obj):
        """Built-in len function"""
        return len(obj)

    def _builtin_type(self, obj):
        """Built-in type function"""
        return type(obj).__name__

    def _builtin_str(self, obj):
        """Built-in str function"""
        return str(obj)

    def _builtin_int(self, obj):
        """Built-in int function"""
        return int(obj)

    def _builtin_float(self, obj):
        """Built-in float function"""
        return float(obj)

    def _builtin_bool(self, obj):
        """Built-in bool function"""
        return bool(obj)

    def _builtin_list(self, obj=None):
        """Built-in list function"""
        if obj is None:
            return []
        return list(obj)

    def _builtin_dict(self, *args, **kwargs):
        """Built-in dict function"""
        return dict(*args, **kwargs)

    def _builtin_set(self, obj=None):
        """Built-in set function"""
        if obj is None:
            return set()
        if isinstance(obj, set):
            return set(obj)
        if isinstance(obj, dict):
            return set(obj.keys())
        return set(obj)

    def _builtin_range(self, *args):
        """Built-in range function"""
        return list(range(*args))

    def _builtin_sum(self, iterable, start=0):
        """Built-in sum function"""
        return sum(iterable, start)

    def _builtin_max(self, *args):
        """Built-in max function"""
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            return max(args[0])
        return max(args)

    def _builtin_min(self, *args):
        """Built-in min function"""
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            return min(args[0])
        return min(args)

    def _builtin_cognitive_check(self, *args, **kwargs):
        """Built-in cognitive_check(...) function that routes to the monitor."""
        return self._call_cognitive_monitor('check_cognitive_load', args, kwargs)

    def _builtin_focus_mode(self, *args, **kwargs):
        """Built-in focus_mode(...) helper."""
        return self._call_cognitive_monitor('configure_focus_mode', args, kwargs)

    def _builtin_working_memory(self, *args, **kwargs):
        """Built-in working_memory(...) helper for storing/recalling values."""
        kw = dict(kwargs)
        if 'action' not in kw and not args:
            kw['action'] = 'status'
        return self._call_cognitive_monitor('manage_working_memory', args, kw)

    def _builtin_check_focus(self, *args, **kwargs):
        """Check current focus session status."""
        return self._call_cognitive_monitor('configure_focus_mode', (), {'action': 'status'})

    def _builtin_intent(self, *args, **kwargs):
        """Record intent metadata."""
        return self._call_cognitive_monitor('record_intent', args, kwargs)

    def _builtin_decision(self, *args, **kwargs):
        """Record a decision/rationale."""
        return self._call_cognitive_monitor('record_decision', args, kwargs)

    def _builtin_cognitive_trace(self, *args, **kwargs):
        """Toggle reasoning trace on/off."""
        return self._call_cognitive_monitor('toggle_trace', args, kwargs)

    def _builtin_explain_step(self, *args, **kwargs):
        """Return an explainability snapshot."""
        return self._call_cognitive_monitor('explain_step', args, kwargs)

    def _builtin_profile(self, *args, **kwargs):
        """Set or declare a cognitive accessibility profile."""
        return self._call_cognitive_monitor('set_profile', args, kwargs)

    def _builtin_cognitive_lint(self, *args, **kwargs):
        """Run cognitive lint checks on provided context."""
        return self._call_cognitive_monitor('lint_context', args, kwargs)

    def _builtin_cognitive_report(self, *args, **kwargs):
        """Return a structured cognitive report."""
        return self._call_cognitive_monitor('report', args, kwargs)

    def _builtin_cognitive_export(self, *args, **kwargs):
        """Export trace/report to a JSON file."""
        return self._call_cognitive_monitor('export_trace', args, kwargs)

    def _call_cognitive_monitor(self, method_name: str, args, kwargs):
        """Normalize arguments and dispatch to the cognitive monitor."""
        monitor = getattr(self, 'cognitive_monitor', None)
        if not monitor:
            raise RuntimeError("Cognitive monitor is not available")
        payload = self._build_cognitive_payload(args, kwargs)
        method = getattr(monitor, method_name)
        return method(payload)

    def _build_cognitive_payload(self, args, kwargs):
        """Convert positional/keyword args to a payload map for the monitor."""
        payload = {f'arg{i}': arg for i, arg in enumerate(args or [])}
        payload.update(kwargs)
        return payload

    def _format_cognitive_context(self) -> str | None:
        monitor = getattr(self, 'cognitive_monitor', None)
        if not monitor:
            return None
        intent = monitor.intent_stack[-1] if monitor.intent_stack else {}
        goal = intent.get("goal") or intent.get("intent") or intent.get("arg0")
        drift = None
        if monitor.last_analysis:
            drift = monitor.last_analysis.get("intent_drift_score")
        parts = []
        if monitor.profile:
            parts.append(f"profile={monitor.profile}")
        if goal:
            parts.append(f"intent={goal}")
        if drift is not None:
            parts.append(f"drift={drift:.2f}")
        if monitor.decision_log:
            parts.append(f"decisions={len(monitor.decision_log)}")
        return " ".join(parts) if parts else None

    def _explain_exception(
        self,
        exc: Exception,
        code: str | None = None,
        filename: str | None = None,
    ) -> str:
        """Return a cognitive-first explanation for an exception."""
        if isinstance(exc, SonaRuntimeError) and getattr(exc, "_sona_explained", False):
            return str(exc)
        try:
            from .utils.error_explainer import explain_error
        except Exception:
            return str(exc)

        monitor = getattr(self, 'cognitive_monitor', None)
        intent = None
        if monitor and monitor.intent_stack:
            intent = (
                monitor.intent_stack[-1].get("goal")
                or monitor.intent_stack[-1].get("intent")
                or monitor.intent_stack[-1].get("arg0")
            )
        return explain_error(
            exc,
            filename=filename,
            source=code,
            intent=intent,
            suppress_details=self.suppress_diagnostics,
        )

    @property
    def current_scope(self):
        """Return the current active scope (top-most local or global)."""
        if self.memory.local_scopes:
            return self.memory.local_scopes[-1]
        return self.memory.global_scope

    # ========================================================================
    # FUNCTION MANAGEMENT (v0.9.6)
    # ========================================================================

    def define_function(self, name: str, func_def):
        """Define a user function"""
        monitor = getattr(self, 'cognitive_monitor', None)
        cognitive_context = None
        module_context = getattr(self, "_module_context", None)
        if monitor:
            cognitive_context = {
                "profile": monitor.profile,
                "intent": monitor.intent_stack[-1] if monitor.intent_stack else None,
                "decisions": monitor.decision_log[-3:],
            }
        self.functions[name] = SonaFunction(
            name=name,
            parameters=func_def.parameters,
            varargs_param=getattr(func_def, 'varargs_param', None),
            default_values=getattr(func_def, 'default_values', None),
            body=func_def.body,
            interpreter=self,
            cognitive_context=cognitive_context,
            closure=module_context
        )
        # Also register in variable scope for calling
        self.memory.set_variable(name, self.functions[name], global_scope=True)

    def call_function(
        self,
        name: str,
        arguments: list[Any],
        keyword_arguments: dict[str, Any] | None = None
    ) -> Any:
        """Call a user-defined or built-in function"""
        # Check built-in functions first
        if name == "range":
            if len(arguments) == 1:
                return list(range(int(arguments[0])))
            elif len(arguments) == 2:
                return list(range(int(arguments[0]), int(arguments[1])))
            elif len(arguments) == 3:
                return list(
                    range(
                        int(arguments[0]),
                        int(arguments[1]),
                        int(arguments[2])
                    )
                )
            else:
                raise TypeError(
                    f"range() takes 1-3 arguments, got {len(arguments)}"
                )
        elif name == "len":
            if len(arguments) != 1:
                raise TypeError(
                    f"len() takes exactly 1 argument, got {len(arguments)}"
                )
            return len(arguments[0])

        # Check user-defined functions
        if name not in self.functions:
            raise NameError(f"Function '{name}' is not defined")

        func = self.functions[name]
        return func.call(arguments, keyword_arguments)

    def execute_block(self, statements: list) -> Any:
        """Execute a block of Sona AST statements"""
        result = None
        for stmt in statements:
            try:
                if hasattr(stmt, 'execute'):
                    # Custom Sona AST node
                    result = stmt.execute(self)
                elif hasattr(stmt, 'evaluate'):
                    # Custom Sona AST node
                    result = stmt.evaluate(self)
                else:
                    # Python AST node or other
                    result = self.execute_ast_node(stmt)
            except ReturnValue as ret:
                # Return from function
                return ret.value
            except (BreakException, ContinueException):
                # Re-raise break/continue to propagate to enclosing loop
                raise
        return result

    # Alias for compatibility with AST nodes
    def execute_statements(self, statements: list) -> Any:
        """Alias for execute_block for AST node compatibility"""
        return self.execute_block(statements)

    # ========================================================================
    # CODE INTERPRETATION
    # ========================================================================

    def interpret(self, code: str, filename: str = "<string>") -> Any:
        """
        Interpret Sona code from a string

        Args:
            code: The Sona source code
            filename: Optional filename for error reporting

        Returns:
            The result of the interpretation
        """
        try:
            # Use Sona parser if available and code contains Sona syntax
            if SonaParserv090 and self._is_sona_syntax(code):
                return self._execute_sona_code(code, filename)
            else:
                # Fallback to Python-like compatibility mode
                if not SonaParserv090:
                    print("⚠️  Sona parser not available, using Python compatibility mode")
                return self.execute_python_like(code, filename)
        except Exception as e:
            if self.debug_mode:
                traceback.print_exc()
            message = self._explain_exception(e, code=code, filename=filename)
            self._restore_focus_after_error()
            err = SonaRuntimeError(message)
            err._sona_explained = True
            raise err from e

    def _is_sona_syntax(self, code: str) -> bool:
        """Detect if code contains Sona-specific syntax"""

        # AI-native function names that should use Python execution
        ai_functions = [
            'think', 'remember', 'focus', 'analyze_load',
            'generate_code', 'complete_function', 'explain_code',
            'suggest_improvements', 'when_confused', 'break_if_overwhelmed',
            'simplify_task', 'review_progress',
            # Day 3C: Advanced AI Constructs
            'adaptive_learning', 'meta_cognition', 'dynamic_context_switching',
            'multi_step_reasoning'
        ]

        # Check for AI function calls - these should use Python execution
        for func_name in ai_functions:
            if f'{func_name}(' in code:
                return False  # Force Python execution for AI functions

        sona_keywords = [
            'let', 'const', 'func', 'function', '=>',
            'if', 'else', 'while', 'for', 'match', 'case',
            'class', 'extends', 'import', 'export',
            'true', 'false', 'null', 'undefined',
            'intent', 'decision', 'cognitive_scope', 'cognitive_trace',
            'cognitive_check', 'focus_mode', 'working_memory', 'explain_step',
            'profile', 'cognitive_lint', 'cognitive_report', 'cognitive_export',
            'focus'
        ]

        # Check for Sona keywords
        for keyword in sona_keywords:
            if keyword in code:
                return True

        # Check for Sona-style syntax patterns
        sona_patterns = [
            ' = [',  # List assignments
            ' = {',  # Object assignments
            'let ',  # Variable declarations
            'const ', # Constant declarations
        ]

        return any(pattern in code for pattern in sona_patterns)

        return False

    def _convert_sona_to_python(self, code: str) -> str:
        """Convert Sona C-style syntax to Python for compatibility"""
        import re

        # First, convert boolean/null literals throughout the code
        # Use word boundaries to avoid matching inside other words
        code = re.sub(r'\btrue\b', 'True', code)
        code = re.sub(r'\bfalse\b', 'False', code)
        code = re.sub(r'\bnull\b', 'None', code)

        # Handle line-by-line conversion of keywords
        lines = code.split('\n')
        result_lines = []
        i = 0
        indent_level = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                result_lines.append('')
                i += 1
                continue

            # Remove trailing semicolons
            if stripped.endswith(';'):
                stripped = stripped[:-1]

            # Handle "} else {" on same line
            if stripped == '} else {':
                indent_level = max(0, indent_level - 1)
                result_lines.append('    ' * indent_level + 'else:')
                indent_level += 1
                i += 1
                continue

            # Handle "} else if (condition) {" on same line
            match = re.match(r'\}\s*else\s+if\s*\((.+?)\)\s*\{', stripped)
            if match:
                indent_level = max(0, indent_level - 1)
                condition = match.group(1).strip()
                result_lines.append('    ' * indent_level + f'elif {condition}:')
                indent_level += 1
                i += 1
                continue

            # Handle closing braces (including "} else" split across lines)
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
                i += 1
                continue

            # Handle standalone "else {"
            if stripped == 'else {' or re.match(r'^else\s*\{$', stripped):
                result_lines.append('    ' * indent_level + 'else:')
                indent_level += 1
                i += 1
                continue

            # Handle "else if (condition) {" (elif)
            match = re.match(r'^else\s+if\s*\((.+?)\)\s*\{', stripped)
            if match:
                condition = match.group(1).strip()
                result_lines.append('    ' * indent_level + f'elif {condition}:')
                indent_level += 1
                i += 1
                continue

            # Convert while (condition) { to while condition:
            if 'while' in stripped and '{' in stripped:
                # Extract condition
                match = re.search(
                    r'while\s*\(?\s*(.+?)\s*\)?\s*\{',
                    stripped
                )
                if match:
                    condition = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'while {condition}:'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert if (condition) { to if condition:
            if stripped.startswith('if') and '{' in stripped:
                match = re.search(
                    r'if\s*\((.+?)\)\s*\{',
                    stripped
                )
                if match:
                    condition = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'if {condition}:'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert repeat N times { to for _ in range(N):
            if 'repeat' in stripped and 'times' in stripped and '{' in stripped:
                match = re.search(
                    r'repeat\s+(.+?)\s+times\s*\{',
                    stripped
                )
                if match:
                    count = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'for _ in range({count}):'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert repeat N { to for _ in range(N):
            if 'repeat' in stripped and '{' in stripped and 'times' not in stripped:
                match = re.search(
                    r'repeat\s+(.+?)\s*\{',
                    stripped
                )
                if match:
                    count = match.group(1).strip()
                    result_lines.append(
                        '    ' * indent_level + f'for _ in range({count}):'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Convert for x in y { to for x in y:
            if 'for' in stripped and 'in' in stripped and '{' in stripped:
                match = re.search(
                    r'for\s+(\w+)\s+in\s+(.+?)\s*\{',
                    stripped
                )
                if match:
                    var = match.group(1).strip()
                    iter_expr = match.group(2).strip()
                    result_lines.append(
                        '    ' * indent_level + f'for {var} in {iter_expr}:'
                    )
                    indent_level += 1
                    i += 1
                    continue

            # Regular statement (add indentation)
            result_lines.append('    ' * indent_level + stripped)
            i += 1

        return '\n'.join(result_lines)

    def _execute_sona_code(self, code: str, filename: str = "<string>") -> Any:
        """Execute Sona code using the proper Sona parser"""
        # Create parser instance
        parser = SonaParserv090()

        def _fallback(parse_error: Exception):
            print(f"DEBUG: Exception in _execute_sona_code: {parse_error}")
            print(f"DEBUG: Exception type: {type(parse_error)}")

            # If Sona parsing fails, try converting to Python
            has_braces = '{' in code
            has_keywords = any(
                kw in code for kw in ['while', 'for', 'if', 'repeat']
            )

            print(f"DEBUG: has_braces={has_braces}, has_keywords={has_keywords}")

            if has_braces and has_keywords:
                try:
                    print("DEBUG: Converting Sona to Python...")
                    converted_code = self._convert_sona_to_python(code)
                    print(
                        "DEBUG: Conversion successful, executing converted code..."
                    )
                    result = self.execute_python_like(
                        converted_code,
                        filename
                    )
                    print("DEBUG: Converted code executed successfully!")
                    return result
                except Exception as convert_error:
                    print(f"Convert error: {convert_error}")
                    import traceback
                    traceback.print_exc()

            # If Sona parsing fails, try Python compatibility mode
            print(f"⚠️  Sona parsing failed: {parse_error}")
            print("   Falling back to Python compatibility mode")
            return self.execute_python_like(code, filename)

        # Parse Sona code into AST nodes
        try:
            ast_nodes = parser.parse(code, filename)
        except Exception as e:
            return _fallback(e)

        if ast_nodes is None:
            return _fallback(SonaRuntimeError(f"Failed to parse Sona code in {filename}"))

        # Execute AST nodes (runtime errors should NOT trigger Python fallback)
        result = None
        for node in ast_nodes:
            if hasattr(node, 'execute'):
                result = node.execute(self)
            elif hasattr(node, 'evaluate'):
                result = node.evaluate(self)
            else:
                # Handle raw values or simple nodes
                result = self._handle_simple_node(node)

        return result

    def _handle_simple_node(self, node) -> Any:
        """Handle simple AST nodes that don't have execute/evaluate methods"""
        if hasattr(node, 'value'):
            return node.value
        elif isinstance(node, (int, float, str, bool)):
            return node
        else:
            return str(node)

    def execute_python_like(
        self,
        code: str,
        filename: str = "<string>"
    ) -> Any:
        """Execute Python-like code (temporary implementation)"""
        try:
            # Parse as Python AST for now
            tree = ast.parse(code, filename=filename)
            return self.execute_ast_node(tree)
        except SyntaxError as e:
            raise SonaRuntimeError(f"Syntax error in {filename}: {e}") from e

    def execute(
        self,
        tree
    ) -> Any:
        """Execute a parse tree (main entry point for CLI)"""
        try:
            # For now, if it's a Lark tree, convert to string and parse as Python
            if hasattr(tree, 'pretty'):
                # Lark tree - convert to string representation
                tree_str = str(tree.pretty())
                return self.execute_python_like(tree_str)
            elif hasattr(tree, 'data'):
                # Lark tree node - basic handling
                return self.execute_python_like(str(tree))
            elif isinstance(tree, str):
                # String code
                return self.execute_python_like(tree)
            else:
                # Assume it's an AST node
                return self.execute_ast_node(tree)
        except Exception as e:
            if self.debug_mode:
                traceback.print_exc()
            message = self._explain_exception(e)
            self._restore_focus_after_error()
            err = SonaRuntimeError(message)
            err._sona_explained = True
            raise err from e

    def execute_ast_node(
        self,
        node: ast.AST
    ) -> Any:
        """Execute an AST node"""
        if isinstance(node, ast.Module):
            result = None
            for stmt in node.body:
                result = self.execute_ast_node(stmt)
            return result

        elif isinstance(node, ast.Expr):
            return self.execute_ast_node(node.value)

        elif isinstance(node, ast.Assign):
            value = self.execute_ast_node(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.memory.set_variable(target.id, value)
                else:
                    raise SonaRuntimeError(f"Unsupported assignment target: {type(target)}")
            return value

        elif isinstance(node, ast.AugAssign):
            # Augmented assignment (+=, -=, etc.)
            if isinstance(node.target, ast.Name):
                current_value = self.memory.get_variable(node.target.id)
                new_value = self.execute_ast_node(node.value)
                result = self._execute_binary_op(node.op, current_value, new_value)
                self.memory.set_variable(node.target.id, result)
                return result
            else:
                raise SonaRuntimeError(f"Unsupported augmented assignment target: {type(node.target)}")

        elif isinstance(node, ast.Name):
            return self.memory.get_variable(node.id)

        elif isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.BinOp):
            left = self.execute_ast_node(node.left)
            right = self.execute_ast_node(node.right)
            return self._execute_binary_op(node.op, left, right)

        elif isinstance(node, ast.BoolOp):
            # Handle 'and' / 'or' boolean operations
            if isinstance(node.op, ast.And):
                result = True
                for value in node.values:
                    result = self.execute_ast_node(value)
                    if not result:
                        return result  # Short-circuit
                return result
            elif isinstance(node.op, ast.Or):
                result = False
                for value in node.values:
                    result = self.execute_ast_node(value)
                    if result:
                        return result  # Short-circuit
                return result
            else:
                raise SonaRuntimeError(f"Unsupported BoolOp: {type(node.op)}")

        elif isinstance(node, ast.Compare):
            left = self.execute_ast_node(node.left)
            # For chained comparisons like a < b < c, we need to check each pair
            # and track both the boolean result AND the right operand
            current_left = left
            for op, comparator in zip(node.ops, node.comparators, strict=False):
                right = self.execute_ast_node(comparator)
                cmp_result = self._execute_compare_op(op, current_left, right)
                if not cmp_result:
                    return False  # Short-circuit: comparison failed
                current_left = right  # For chained comparisons: a < b < c
            return True  # All comparisons passed

        elif isinstance(node, ast.List):
            return [self.execute_ast_node(elt) for elt in node.elts]

        elif isinstance(node, ast.Subscript):
            value = self.execute_ast_node(node.value)
            index = self.execute_ast_node(node.slice)
            return value[index]

        elif isinstance(node, ast.Dict):
            result = {}
            for key, value in zip(node.keys, node.values, strict=False):
                key_val = self.execute_ast_node(key)
                value_val = self.execute_ast_node(value)
                result[key_val] = value_val
            return result

        elif isinstance(node, ast.Call):
            func = self.execute_ast_node(node.func)
            args = [self.execute_ast_node(arg) for arg in node.args]

            if callable(func):
                return func(*args)
            elif isinstance(func, SonaFunction):
                return func.call(args)
            else:
                raise SonaRuntimeError(f"'{func}' is not callable")

        elif isinstance(node, ast.If):
            condition = self.execute_ast_node(node.test)
            if condition:
                return self.execute_block(node.body)
            elif node.orelse:
                return self.execute_block(node.orelse)
            return None

        elif isinstance(node, ast.For):
            iterable = self.execute_ast_node(node.iter)
            result = None
            try:
                for item in iterable:
                    if isinstance(node.target, ast.Name):
                        self.memory.set_variable(node.target.id, item)
                    try:
                        result = self.execute_block(node.body)
                    except ContinueException:
                        continue
                    except BreakException:
                        break
            except BreakException:
                pass
            return result

        elif isinstance(node, ast.While):
            result = None
            try:
                while self.execute_ast_node(node.test):
                    try:
                        result = self.execute_block(node.body)
                    except ContinueException:
                        continue
                    except BreakException:
                        break
            except BreakException:
                pass
            return result

        elif hasattr(ast, 'Repeat') and isinstance(node, ast.Repeat):
            # Handle repeat N times { ... } construct
            # This is a custom AST node that may come from Lark parser
            count = self.execute_ast_node(node.count)
            result = None
            try:
                for _ in range(int(count)):
                    try:
                        result = self.execute_block(node.body)
                    except ContinueException:
                        continue
                    except BreakException:
                        break
            except BreakException:
                pass
            return result

        elif isinstance(node, ast.FunctionDef):
            params = [arg.arg for arg in node.args.args]
            func = SonaFunction(node.name, params, None, None, node.body, self)
            self.functions[node.name] = func
            self.memory.set_variable(node.name, func)
            return func

        elif isinstance(node, ast.Lambda):
            params = [arg.arg for arg in node.args.args]
            # Create anonymous function with lambda body
            lambda_func = SonaFunction(
                name=f"<lambda_{id(node)}>",
                parameters=params,
                varargs_param=None,
                default_values=None,
                body=[ast.Return(value=node.body)],  # Wrap lambda body in return
                interpreter=self
            )
            return lambda_func

        elif isinstance(node, ast.Return):
            if node.value:
                return self.execute_ast_node(node.value)
            return None

        elif isinstance(node, ast.Break):
            raise BreakException()

        elif isinstance(node, ast.Continue):
            raise ContinueException()

        elif isinstance(node, ast.Attribute):
            obj = self.execute_ast_node(node.value)
            return getattr(obj, node.attr)

        elif isinstance(node, ast.ListComp):
            # List comprehension: [expr for target in iter if condition]
            result = []
            iterable = self.execute_ast_node(node.generators[0].iter)
            for item in iterable:
                # Set the target variable
                if isinstance(node.generators[0].target, ast.Name):
                    old_value = None
                    var_name = node.generators[0].target.id
                    # Save old value if it exists
                    if self.memory.has_variable(var_name):
                        old_value = self.memory.get_variable(var_name)

                    self.memory.set_variable(var_name, item)

                    # Check conditions
                    include = True
                    for condition in node.generators[0].ifs:
                        if not self.execute_ast_node(condition):
                            include = False
                            break

                    # Add to result if conditions met
                    if include:
                        result.append(self.execute_ast_node(node.elt))

                    # Restore old value or remove variable
                    if old_value is not None:
                        self.memory.set_variable(var_name, old_value)
                    elif self.memory.has_variable(var_name):
                        # Note: This is simplified - proper scope handling needed
                        pass
            return result

        elif isinstance(node, ast.JoinedStr):
            # f-string support
            result = ""
            for value in node.values:
                if isinstance(value, ast.Constant):
                    result += str(value.value)
                elif isinstance(value, ast.FormattedValue):
                    formatted_val = self.execute_ast_node(value.value)
                    result += str(formatted_val)
                else:
                    result += str(self.execute_ast_node(value))
            return result

        else:
            raise SonaRuntimeError(f"Unsupported AST node type: {type(node)}")

    def execute_python_block(self, statements: list[ast.AST]) -> Any:
        """Execute a block of Python AST statements"""
        result = None
        for stmt in statements:
            result = self.execute_ast_node(stmt)
        return result

    def _execute_binary_op(
        self,
        op: ast.operator,
        left: Any,
        right: Any
    ) -> Any:
        """Execute a binary operation"""
        if isinstance(op, ast.Add):
            return left + right
        elif isinstance(op, ast.Sub):
            return left - right
        elif isinstance(op, ast.Mult):
            return left * right
        elif isinstance(op, ast.Div):
            return left / right
        elif isinstance(op, ast.Mod):
            return left % right
        elif isinstance(op, ast.Pow):
            return left ** right
        else:
            raise SonaRuntimeError(f"Unsupported binary operator: {type(op)}")

    def _execute_compare_op(
        self,
        op: ast.cmpop,
        left: Any,
        right: Any
    ) -> bool:
        """Execute a comparison operation"""
        if isinstance(op, ast.Eq):
            return left == right
        elif isinstance(op, ast.NotEq):
            return left != right
        elif isinstance(op, ast.Lt):
            return left < right
        elif isinstance(op, ast.LtE):
            return left <= right
        elif isinstance(op, ast.Gt):
            return left > right
        elif isinstance(op, ast.GtE):
            return left >= right
        elif isinstance(op, ast.Is):
            return left is right
        elif isinstance(op, ast.IsNot):
            return left is not right
        elif isinstance(op, ast.In):
            return left in right
        elif isinstance(op, ast.NotIn):
            return left not in right
        else:
            raise SonaRuntimeError(f"Unsupported comparison operator: {type(op)}")

    def evaluate(self, expression: str) -> Any:
        """
        Evaluate a single Sona expression

        Args:
            expression: The expression to evaluate

        Returns:
            The result of the evaluation
        """
        try:
            # Parse as expression
            tree = ast.parse(expression, mode='eval')
            return self.execute_ast_node(tree.body)
        except Exception as e:
            raise SonaRuntimeError(f"Evaluation error: {e}") from e

    def execute_statement(self, statement: str) -> Any:
        """
        Execute a single Sona statement

        Args:
            statement: The statement to execute

        Returns:
            The result of the execution
        """
        return self.interpret(statement)

    def execute_file(self, filepath: str) -> Any:
        """
        Execute a Sona file

        Args:
            filepath: Path to the Sona file

        Returns:
            The result of the file execution
        """
        path = Path(filepath)
        if not path.exists():
            raise SonaRuntimeError(f"File not found: {filepath}")

        try:
            with open(filepath, encoding='utf-8') as f:
                code = f.read()
            return self.interpret(code, filename=filepath)
        except Exception as e:
            raise SonaRuntimeError(f"Error executing file {filepath}: {e}") from e

    def set_variable(self, name: str, value: Any, global_scope: bool = False):
        """Set a variable in the interpreter"""
        self.memory.set_variable(name, value, global_scope)

    def get_variable(self, name: str) -> Any:
        """Get a variable from the interpreter"""
        return self.memory.get_variable(name)

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists"""
        return self.memory.has_variable(name)

    def enable_ai(self):
        """Enable AI assistance features"""
        self.ai_enabled = True

    def disable_ai(self):
        """Disable AI assistance features"""
        self.ai_enabled = False

    def enable_debug(self):
        """Enable debug mode"""
        self.debug_mode = True

    def disable_debug(self):
        """Disable debug mode"""
        self.debug_mode = False

    def _enter_focus_block(self, meta: dict[str, Any]) -> dict[str, Any]:
        """Enter a focus block, tightening diagnostics and enabling trace."""
        monitor = getattr(self, 'cognitive_monitor', None)
        state = {
            "suppress_diagnostics": self.suppress_diagnostics,
            "auto_ai_suggestions_enabled": self.auto_ai_suggestions_enabled,
            "focus_block_active": self.focus_block_active,
            "trace_enabled": monitor.trace_enabled if monitor else None,
            "pushed_scope": False,
        }
        self.focus_block_stack.append(state)
        self.focus_block_active = True
        self.suppress_diagnostics = True
        self.auto_ai_suggestions_enabled = False

        if monitor:
            monitor.trace_enabled = True
            name = (
                meta.get("task")
                or meta.get("name")
                or meta.get("goal")
                or "focus"
            )
            scope_meta = dict(meta)
            scope_meta.setdefault("focus", True)
            monitor.push_scope(name=name, meta=scope_meta)
            state["pushed_scope"] = True

        return state

    def _exit_focus_block(self, state: dict[str, Any], *, error: bool = False) -> None:
        """Exit a focus block and restore prior runtime settings."""
        monitor = getattr(self, 'cognitive_monitor', None)
        if self.focus_block_stack:
            if self.focus_block_stack[-1] is state:
                self.focus_block_stack.pop()
            else:
                try:
                    self.focus_block_stack.remove(state)
                except ValueError:
                    pass
        if monitor and state.get("pushed_scope"):
            monitor.pop_scope()
        if state.get("trace_enabled") is not None and monitor:
            monitor.trace_enabled = state["trace_enabled"]
        if error:
            self._pending_focus_restore = state
            return
        self.suppress_diagnostics = state.get("suppress_diagnostics", False)
        self.auto_ai_suggestions_enabled = state.get("auto_ai_suggestions_enabled", True)
        self.focus_block_active = state.get("focus_block_active", False)

    def _restore_focus_after_error(self) -> None:
        """Restore focus block settings after an error is explained."""
        state = self._pending_focus_restore
        if not state:
            return
        self.suppress_diagnostics = state.get("suppress_diagnostics", False)
        self.auto_ai_suggestions_enabled = state.get("auto_ai_suggestions_enabled", True)
        self.focus_block_active = state.get("focus_block_active", False)
        self._pending_focus_restore = None

    def reset(self):
        """Reset the interpreter state"""
        self.__init__()

    def get_state(self) -> dict[str, Any]:
        """Get the current interpreter state"""
        return {
            'variables': dict(self.memory.global_scope),
            'functions': list(self.functions.keys()),
            'modules': list(self.modules.keys()),
            'ai_enabled': self.ai_enabled,
            'debug_mode': self.debug_mode
        }

    # Cognitive AI Built-in Functions

    def _cognitive_think(self, prompt: str) -> dict[str, Any]:
        """Built-in cognitive thinking function"""
        self.current_context = prompt
        session_time = time.time() - self.session_start_time

        # Provide compatible parameters for both real and placeholder
        try:
            analysis = self.cognitive_assistant.analyze_working_memory(
                current_task=prompt,
                context=self.current_context
            )
        except TypeError:
            # Fallback for placeholder or different interface
            analysis = self.cognitive_assistant.analyze_working_memory()

        return {
            'thought': prompt,
            'cognitive_analysis': analysis,
            'timestamp': time.time(),
            'session_duration': session_time
        }

    def _cognitive_remember(self, key: str, value: Any = None) -> Any:
        """Built-in cognitive memory function"""
        memory_key = f"_cognitive_memory_{key}"

        if value is not None:
            # Store memory
            self.memory.set_variable(memory_key, value, global_scope=True)
            return {
                'action': 'stored',
                'key': key,
                'value': value,
                'timestamp': time.time()
            }
        else:
            # Retrieve memory
            try:
                stored_value = self.memory.get_variable(memory_key)
                return stored_value
            except NameError:
                return {
                    'action': 'not_found',
                    'key': key,
                    'message': f"No memory found for key '{key}'"
                }

    def _cognitive_focus(self, task_description: str) -> dict[str, Any]:
        """Built-in cognitive focus function"""
        session_time = time.time() - self.session_start_time

        # Provide compatible parameters for both real and placeholder
        try:
            # Real CognitiveAssistant expects typing_data
            typing_data = [{'timestamp': time.time(),
                           'chars': len(task_description)}]
            hyperfocus_analysis = self.cognitive_assistant.\
                detect_hyperfocus(typing_data)
        except TypeError:
            hyperfocus_analysis = self.cognitive_assistant.detect_hyperfocus()

        try:
            executive_analysis = self.cognitive_assistant.\
                analyze_executive_function(task_description)
        except TypeError:
            executive_analysis = self.cognitive_assistant.\
                analyze_executive_function()

        return {
            'task': task_description,
            'hyperfocus_state': hyperfocus_analysis,
            'executive_function': executive_analysis,
            'focus_timestamp': time.time(),
            'session_duration': session_time
        }

    def _cognitive_analyze_load(self) -> dict[str, Any]:
        """Built-in cognitive load analysis function"""
        session_time = time.time() - self.session_start_time

        # Provide compatible parameters for both real and placeholder
        try:
            memory_analysis = self.cognitive_assistant.analyze_working_memory(
                current_task=self.current_context or "General analysis",
                context=f"Session: {session_time:.1f}s, "
                        f"Vars: {len(self.memory.global_scope)}, "
                        f"Funcs: {len(self.functions)}"
            )
        except TypeError:
            memory_analysis = self.cognitive_assistant.analyze_working_memory()

        return {
            'cognitive_load': memory_analysis.get('cognitive_load', 'medium'),
            'working_memory_analysis': memory_analysis,
            'session_metrics': {
                'duration': session_time,
                'scope_depth': len(self.memory.local_scopes),
                'variables': len(self.memory.global_scope),
                'functions': len(self.functions),
                'modules': len(self.modules)
            },
            'recommendations': memory_analysis.get('suggestions', []),
            'timestamp': time.time()
        }

    # AI-Native Language Features (Day 3B)

    # REAL AI IMPLEMENTATION METHODS - NO MOCKS
    def _setup_real_ai_provider(self):
        """Initialize REAL AI provider using MultiAIProvider - NO MOCKS"""
        try:
            # Use our MultiAIProvider with external credentials
            import sys
            from pathlib import Path

            # Add current directory to path for imports
            sona_root = Path(__file__).parent.parent
            if str(sona_root) not in sys.path:
                sys.path.append(str(sona_root))

            from multi_ai_provider import MultiAIProvider
            self.real_ai = MultiAIProvider()
            print("✅ REAL AI provider initialized with MultiAIProvider")
        except ImportError as e:
            print(f"❌ Failed to import MultiAIProvider: {e}")
            # Fallback to original real AI provider
            try:
                from .ai.real_ai_provider import REAL_AI_PROVIDER
                self.real_ai = REAL_AI_PROVIDER
                print("✅ REAL AI provider initialized (fallback)")
            except ImportError:
                print("❌ Failed to import fallback AI provider")
                self.real_ai = None

    def _real_ai_complete(self, code_context: str) -> str:
        """REAL AI code completion - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_complete(code_context)
                # MultiAIProvider returns string directly, not object with .content
                if isinstance(response, str):
                    return response
                elif hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
            except Exception as e:
                return f"# AI completion failed: {e}"
        else:
            return "# Real AI not available - check configuration"

    def _real_ai_explain(self, code_snippet: str,
                         level: str = "intermediate") -> str:
        """REAL AI code explanation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_explain(code_snippet, level)
                # MultiAIProvider returns string directly, not object with .content
                if isinstance(response, str):
                    return response
                elif hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
            except Exception as e:
                return f"AI explanation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_debug(self, error_context: str, code: str = "") -> str:
        """REAL AI debugging assistance - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_debug(error_context, code)
                return response.content
            except Exception as e:
                return f"AI debugging failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_generate_code(self, description: str) -> dict[str, Any]:
        """REAL AI code generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                prompt = f"Generate Python code for: {description}"
                response = self.real_ai.ai_complete(prompt)
                return {
                    'description': description,
                    'generated_code': response.content,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time(),
                    'ready_to_execute': True
                }
            except Exception as e:
                return {
                    'description': description,
                    'generated_code': f"# Real AI generation failed: {e}",
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time(),
                    'ready_to_execute': False
                }
        else:
            return {
                'description': description,
                'generated_code': "# Real AI not available - check configuration",
                'source': 'error',
                'timestamp': time.time(),
                'ready_to_execute': False
            }

    def _real_ai_complete_function(self, signature: str, description: str = "") -> dict[str, Any]:
        """REAL AI function completion - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                prompt = f"Complete this Python function:\n{signature}\n# {description}"
                response = self.real_ai.ai_complete(prompt)
                return {
                    'signature': signature,
                    'description': description,
                    'complete_function': response.content,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'signature': signature,
                    'description': description,
                    'complete_function': f"# Real AI completion failed: {e}",
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        else:
            return {
                'signature': signature,
                'description': description,
                'complete_function': "# Real AI not available - check configuration",
                'source': 'error',
                'timestamp': time.time()
            }

    def _real_ai_explain_code(self, code: str, level: str = "intermediate") -> dict[str, Any]:
        """REAL AI code explanation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_explain(code, level)
                return {
                    'code': code,
                    'explanation': response.content,
                    'level': level,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'code': code,
                    'explanation': f"Real AI explanation failed: {e}",
                    'level': level,
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        else:
            return {
                'code': code,
                'explanation': "Real AI not available - check configuration",
                'level': level,
                'source': 'error',
                'timestamp': time.time()
            }

    def _real_ai_suggest_improvements(self, code: str) -> dict[str, Any]:
        """REAL AI code improvement suggestions - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                prompt = f"Suggest improvements for this Python code:\n{code}"
                response = self.real_ai.ai_complete(prompt)
                return {
                    'original_code': code,
                    'suggestions': response.content,
                    'source': 'REAL_AI',
                    'cost_usd': response.cost_usd,
                    'tokens_used': response.tokens_used,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'original_code': code,
                    'suggestions': f"Real AI suggestions failed: {e}",
                    'source': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        else:
            return {
                'original_code': code,
                'suggestions': "Real AI not available - check configuration",
                'source': 'error',
                'timestamp': time.time()
            }

    # Week 2: Advanced AI Programming Constructs
    def _real_ai_reason(self, problem: str, steps: int = 3) -> str:
        """REAL AI multi-step reasoning - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_reason(problem, steps)
                return str(response)
            except Exception as e:
                return f"AI reasoning failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_refactor(self, code: str, goal: str = "optimize") -> str:
        """REAL AI code refactoring - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_refactor(code, goal)
                return str(response)
            except Exception as e:
                return f"AI refactoring failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_test(self, function: str, test_type: str = "unit") -> str:
        """REAL AI test generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_test(function, test_type)
                return str(response)
            except Exception as e:
                return f"AI test generation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_analyze(self, code: str, focus: str = "quality") -> str:
        """REAL AI code analysis - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_analyze(code, focus)
                return str(response)
            except Exception as e:
                return f"AI analysis failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_generate(self, specification: str,
                          language: str = "python") -> str:
        """REAL AI spec-to-code generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_generate(specification, language)
                return str(response)
            except Exception as e:
                return f"AI generation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_simplify(self, text: str) -> str:
        """REAL AI text simplification - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_simplify(text)
                return str(response)
            except Exception as e:
                return f"AI simplification failed: {e}"
        else:
            return "Real AI not available - check configuration"

    # Week 3: AI-Enhanced Development Environment Integration
    def _real_ai_context(self, code: str, file_path: str = "") -> str:
        """REAL AI code context understanding - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_context(code, file_path)
                return str(response)
            except Exception as e:
                return f"AI context analysis failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_suggest(self, code: str, cursor_position: int = 0) -> str:
        """REAL AI code suggestions - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_suggest(code, cursor_position)
                return str(response)
            except Exception as e:
                return f"AI suggestions failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_document(self, code: str, style: str = "google") -> str:
        """REAL AI documentation generation - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_document(code, style)
                return str(response)
            except Exception as e:
                return f"AI documentation failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_optimize(self, code: str, focus: str = "performance") -> str:
        """REAL AI optimization recommendations - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_optimize(code, focus)
                return str(response)
            except Exception as e:
                return f"AI optimization failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_security(self, code: str, framework: str = "general") -> str:
        """REAL AI security analysis - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_security(code, framework)
                return str(response)
            except Exception as e:
                return f"AI security analysis failed: {e}"
        else:
            return "Real AI not available - check configuration"

    def _real_ai_mentor(self, question: str, level: str = "beginner") -> str:
        """REAL AI mentoring assistance - NO MOCKS"""
        if not hasattr(self, 'real_ai'):
            self._setup_real_ai_provider()

        if self.real_ai:
            try:
                response = self.real_ai.ai_mentor(question, level)
                return str(response)
            except Exception as e:
                return f"AI mentoring failed: {e}"
        else:
            return "Real AI not available - check configuration"

    # EXISTING MOCK METHODS (TO BE REPLACED COMPLETELY)
        """AI-powered code generation from natural language description"""
        try:
            # Use GPT-2 through cognitive assistant if available
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Generate Python code for: {description}\n\n# Code:"
                generated_code = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=100,
                                        temperature=0.3)

                # Ensure generated_code is a string
                if isinstance(generated_code, list):
                    generated_code = ' '.join(str(x) for x in generated_code)
                elif not isinstance(generated_code, str):
                    generated_code = str(generated_code)

                # Clean up the generated code
                lines = generated_code.split('\n')
                code_lines = []
                for line in lines:
                    if line.strip() and not line.strip().startswith('#'):
                        code_lines.append(line)
                    if len(code_lines) >= 10:  # Limit output length
                        break

                generated_code = '\n'.join(code_lines)
            else:
                # Fallback for when AI is not available
                generated_code = f"# Generated code for: {description}\n" \
                                 f"# TODO: Implement {description.lower()}\n" \
                                 f"pass"

            return {
                'description': description,
                'generated_code': generated_code,
                'source': 'AI' if hasattr(self.cognitive_assistant, 'gpt2')
                          else 'template',
                'timestamp': time.time(),
                'ready_to_execute': True
            }

        except Exception as e:
            return {
                'description': description,
                'generated_code': f"# Error generating code: {e}\n# TODO: "
                                  f"Implement {description}",
                'source': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'ready_to_execute': False
            }

    def _ai_complete_function(self, signature: str,
                              description: str = "") -> dict[str, Any]:
        """AI-powered function completion"""
        try:
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Complete this Python function:\n{signature}\n" \
                        f"    # {description}\n    "
                completion = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=80,
                                        temperature=0.2)

                # Ensure completion is a string
                if isinstance(completion, list):
                    completion = ' '.join(str(x) for x in completion)
                elif not isinstance(completion, str):
                    completion = str(completion)

                # Clean and format the completion
                lines = completion.split('\n')
                body_lines = []
                for line in lines:
                    if line.strip():
                        body_lines.append(f"    {line.strip()}")
                    if len(body_lines) >= 8:
                        break

                complete_function = f"{signature}\n" + '\n'.join(body_lines)
            else:
                complete_function = f"{signature}\n    # {description}\n" \
                                   f"    # TODO: Implement function body\n" \
                                   f"    pass"

            return {
                'signature': signature,
                'description': description,
                'complete_function': complete_function,
                'source': 'AI' if hasattr(self.cognitive_assistant, 'gpt2')
                          else 'template',
                'timestamp': time.time()
            }

        except Exception as e:
            return {
                'signature': signature,
                'description': description,
                'complete_function': f"{signature}\n    # Error: {e}\n"
                                     f"    pass",
                'source': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    def _ai_explain_code(self, code: str) -> dict[str, Any]:
        """AI-powered code explanation in natural language"""
        try:
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Explain this Python code in simple terms:\n\n" \
                        f"{code}\n\nExplanation:"
                explanation = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=80,
                                        temperature=0.3)

                # Ensure explanation is a string
                if isinstance(explanation, list):
                    explanation = ' '.join(str(x) for x in explanation)
                elif not isinstance(explanation, str):
                    explanation = str(explanation)

                # Clean up explanation
                explanation = explanation.strip()
                if len(explanation) > 200:
                    explanation = explanation[:200] + "..."
            else:
                # Simple pattern-based explanation for fallback
                lines = code.split('\n')
                elements = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('def '):
                        elements.append("defines a function")
                    elif line.startswith('for '):
                        elements.append("loops through items")
                    elif line.startswith('if '):
                        elements.append("checks a condition")
                    elif '=' in line and not line.startswith('#'):
                        elements.append("assigns a value")

                explanation = f"This code {', '.join(elements[:3])}"
                if len(elements) > 3:
                    explanation += " and more"
                explanation += "."

            return {
                'code': code,
                'explanation': explanation,
                'source': 'AI' if hasattr(self.cognitive_assistant, 'gpt2')
                          else 'pattern',
                'timestamp': time.time(),
                'clarity_level': 'beginner'
            }

        except Exception as e:
            return {
                'code': code,
                'explanation': f"Unable to explain code: {e}",
                'source': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'clarity_level': 'unknown'
            }

    def _ai_suggest_improvements(self, code: str) -> dict[str, Any]:
        """AI-powered code improvement suggestions"""
        try:
            suggestions = []

            # Basic pattern-based suggestions (always available)
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if len(line) > 100:
                    suggestions.append(f"Line {i+1}: Consider breaking "
                                     f"long line for readability")
                if 'TODO' in line or 'FIXME' in line:
                    suggestions.append(f"Line {i+1}: Complete the TODO item")
                if line.count('(') != line.count(')'):
                    suggestions.append(f"Line {i+1}: Check parentheses "
                                     f"balance")

            # AI-powered suggestions if available
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Suggest improvements for this Python code:\n\n" \
                        f"{code}\n\nSuggestions:"
                ai_suggestions = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=60,
                                        temperature=0.4)

                # Ensure ai_suggestions is a string
                if isinstance(ai_suggestions, list):
                    ai_suggestions = ' '.join(str(x) for x in ai_suggestions)
                elif not isinstance(ai_suggestions, str):
                    ai_suggestions = str(ai_suggestions)

                # Parse AI suggestions
                ai_lines = ai_suggestions.strip().split('\n')
                for line in ai_lines[:3]:  # Limit to 3 AI suggestions
                    if line.strip() and len(line.strip()) > 10:
                        suggestions.append(f"AI: {line.strip()}")

            return {
                'code': code,
                'suggestions': suggestions[:5],  # Limit total suggestions
                'improvement_areas': ['readability', 'performance', 'style'],
                'source': 'hybrid',
                'timestamp': time.time(),
                'priority': 'medium'
            }

        except Exception as e:
            return {
                'code': code,
                'suggestions': [f"Error analyzing code: {e}"],
                'improvement_areas': ['unknown'],
                'source': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'priority': 'low'
            }

    # Cognitive Programming Constructs (Day 3B)

    def _cognitive_when_confused(self, explanation: str) -> dict[str, Any]:
        """Cognitive clarity assistance when confused"""
        try:
            clarity_response = {
                'confusion_noted': explanation,
                'timestamp': time.time(),
                'assistance_provided': [],
                'next_steps': []
            }

            # Analyze the confusion and provide assistance
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Help clarify this programming confusion: " \
                        f"{explanation}\n\nClarification:"
                clarification = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=60,
                                        temperature=0.3)
                clarity_response['assistance_provided'].append(
                    f"AI: {clarification.strip()}")

            # Provide structured next steps
            clarity_response['next_steps'] = [
                "Break down the problem into smaller parts",
                "Look for examples of similar code patterns",
                "Try explaining the problem out loud",
                "Consider asking for help or reviewing documentation"
            ]

            # Log confusion for learning
            confusion_key = f"_confusion_{int(time.time())}"
            self.memory.set_variable(confusion_key, {
                'explanation': explanation,
                'timestamp': time.time(),
                'context': self.current_context
            }, global_scope=True)

            return clarity_response

        except Exception as e:
            return {
                'confusion_noted': explanation,
                'assistance_provided': [f"Error providing assistance: {e}"],
                'next_steps': ["Try a different approach", "Seek help"],
                'timestamp': time.time(),
                'error': str(e)
            }

    def _cognitive_break_if_overwhelmed(self) -> dict[str, Any]:
        """Automatic cognitive load management and break suggestion"""
        try:
            # Analyze current cognitive load
            load_analysis = self._cognitive_analyze_load()

            current_load = load_analysis['cognitive_load']
            session_duration = load_analysis['session_metrics']['duration']

            # Determine if a break is needed
            break_needed = False
            break_reason = ""

            if current_load in ['high', 'very_high']:
                break_needed = True
                break_reason = "High cognitive load detected"
            elif session_duration > 3600:  # 1 hour
                break_needed = True
                break_reason = "Long session duration"
            elif len(self.memory.global_scope) > 50:
                break_needed = True
                break_reason = "High memory complexity"

            response = {
                'break_recommended': break_needed,
                'reason': break_reason,
                'current_load': current_load,
                'session_duration_minutes': session_duration / 60,
                'timestamp': time.time()
            }

            if break_needed:
                # Get break suggestions from cognitive assistant
                break_suggestions = self.cognitive_assistant.\
                    suggest_break_activity(current_load)
                response['break_suggestions'] = break_suggestions
                response['recommended_break_duration'] = \
                    break_suggestions.get('recommended_duration', 15)

                print(f"🧠 Break recommended: {break_reason}")
                activities = break_suggestions.get('suggested_activities', [])
                print(f"💡 Suggested activities: {', '.join(activities[:2])}")

            return response

        except Exception as e:
            return {
                'break_recommended': True,
                'reason': f"Error analyzing load: {e}",
                'break_suggestions': {
                    'suggested_activities': ['Take a short break']
                },
                'timestamp': time.time(),
                'error': str(e)
            }

    def _cognitive_simplify_task(self,
                                 complex_operation: str) -> dict[str, Any]:
        """AI-powered task decomposition and simplification"""
        try:
            simplified_response = {
                'original_task': complex_operation,
                'simplified_steps': [],
                'estimated_time': 0,
                'complexity_reduction': 'medium',
                'timestamp': time.time()
            }

            # Use cognitive assistant for task breakdown
            try:
                breakdown = self.cognitive_assistant.\
                    analyze_executive_function(complex_operation)
                simplified_response['simplified_steps'] = \
                    breakdown.get('task_breakdown', [])
                simplified_response['estimated_time'] = \
                    breakdown.get('estimated_time', 30)
                simplified_response['support_strategies'] = \
                    breakdown.get('support_strategies', [])
            except Exception:
                # Fallback to pattern-based simplification
                steps = []
                if 'function' in complex_operation.lower():
                    steps.extend([
                        "1. Define function signature",
                        "2. Write basic structure",
                        "3. Implement core logic",
                        "4. Add error handling",
                        "5. Test the function"
                    ])
                elif 'class' in complex_operation.lower():
                    steps.extend([
                        "1. Define class structure",
                        "2. Add __init__ method",
                        "3. Implement core methods",
                        "4. Add properties if needed",
                        "5. Test the class"
                    ])
                else:
                    steps.extend([
                        "1. Understand the requirements",
                        "2. Break into smaller parts",
                        "3. Implement each part",
                        "4. Combine and test",
                        "5. Refactor if needed"
                    ])

                simplified_response['simplified_steps'] = steps
                simplified_response['estimated_time'] = len(steps) * 10

            return simplified_response

        except Exception as e:
            return {
                'original_task': complex_operation,
                'simplified_steps': [
                    "1. Break down the problem",
                    "2. Start with the simplest part",
                    f"3. Handle error: {e}"
                ],
                'estimated_time': 20,
                'timestamp': time.time(),
                'error': str(e)
            }

    def _cognitive_review_progress(self) -> dict[str, Any]:
        """Review session progress and provide insights"""
        try:
            session_duration = time.time() - self.session_start_time

            # Gather session statistics
            stats = {
                'session_duration_minutes': session_duration / 60,
                'variables_created': len(self.memory.global_scope),
                'functions_defined': len(self.functions),
                'current_scope_depth': len(self.memory.local_scopes),
                'cognitive_memories': len([k for k in self.memory.global_scope
                                            if k.startswith('_cognitive_memory_')]),
                'confusion_instances': len([k for k in self.memory.global_scope
                                             if k.startswith('_confusion_')])
            }

            # Generate insights
            insights = []
            if stats['session_duration_minutes'] > 60:
                insights.append("Long productive session - consider a break soon")
            if stats['functions_defined'] > 3:
                insights.append("Good function organization!")
            if stats['cognitive_memories'] > 0:
                insights.append(f"Stored {stats['cognitive_memories']} insights")
            if stats['confusion_instances'] == 0:
                insights.append("Clear coding session - great focus!")
            elif stats['confusion_instances'] > 3:
                insights.append("Several confusion points - consider simpler approach")

            # AI-powered insights if available
            if hasattr(self.cognitive_assistant, 'gpt2') and \
               self.cognitive_assistant.gpt2:
                prompt = f"Generate programming session insight for: " \
                        f"{stats['session_duration_minutes']:.1f} min session, " \
                        f"{stats['functions_defined']} functions, " \
                        f"{stats['variables_created']} variables\n\nInsight:"
                ai_insight = self.cognitive_assistant.gpt2.\
                    generate_completion(prompt, max_new_tokens=40,
                                        temperature=0.4)
                if ai_insight.strip():
                    insights.append(f"AI: {ai_insight.strip()}")

            return {
                'session_stats': stats,
                'insights': insights,
                'productivity_score': min(10, stats['functions_defined'] * 2 +
                                        stats['variables_created'] * 0.1),
                'learning_progress': 'steady' if stats['confusion_instances'] < 3
                                   else 'challenging',
                'timestamp': time.time(),
                'next_session_tips': [
                    "Set clear goals at the start",
                    "Take breaks when cognitive load is high",
                    "Use the think() function for complex problems"
                ]
            }

        except Exception as e:
            return {
                'session_stats': {'error': str(e)},
                'insights': [f"Error reviewing progress: {e}"],
                'productivity_score': 0,
                'timestamp': time.time(),
                'error': str(e)
            }

    # Day 3C: Advanced AI Constructs
    def _ai_adaptive_learning(self, feedback: str) -> dict[str, Any]:
        """AI-powered adaptive learning from user feedback"""
        try:
            from advanced_ai.adaptive_learning import AdaptiveLearning
            adaptive_learning = AdaptiveLearning(self.cognitive_assistant)
            return adaptive_learning.learn_from_feedback(feedback)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Adaptive learning error: {str(e)}',
                'fallback_action': 'feedback_noted'
            }

    def _ai_meta_cognition(self,
                           task_description: str = "current_task") -> dict[str, Any]:
        """AI-powered meta-cognitive self-assessment"""
        try:
            from advanced_ai.meta_cognition import MetaCognition
            meta_cognition = MetaCognition(self.cognitive_assistant)
            return meta_cognition.self_assess(task_description)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Meta-cognition error: {str(e)}',
                'fallback_assessment': 'self_reflection_needed'
            }

    def _ai_dynamic_context_switching(self, new_context: str) -> dict[str, Any]:
        """AI-powered dynamic context switching"""
        try:
            from advanced_ai.dynamic_context_switching import (
                DynamicContextSwitching,
            )
            context_switcher = DynamicContextSwitching(self.cognitive_assistant)
            old_context = self.current_context
            result = context_switcher.switch_context(old_context, new_context)
            if result.get('status') == 'success':
                self.current_context = new_context
            return result
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Context switching error: {str(e)}',
                'current_context': self.current_context
            }

    def _ai_multi_step_reasoning(self, problem_description: str) -> dict[str, Any]:
        """AI-powered multi-step problem reasoning"""
        try:
            from advanced_ai.multi_step_reasoning import MultiStepReasoning
            reasoner = MultiStepReasoning(self.cognitive_assistant)
            return reasoner.solve_problem(problem_description)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Multi-step reasoning error: {str(e)}',
                'fallback_approach': 'break_problem_manually'
            }


# Create a default interpreter instance for convenience
default_interpreter = SonaUnifiedInterpreter()

# Alias for backward compatibility
SonaInterpreter = SonaUnifiedInterpreter

# Export the main classes and functions
__all__ = [
    'SonaInterpreter',
    'SonaUnifiedInterpreter',
    'SonaFunction',
    'SonaMemoryManager',
    'SonaRuntimeError',
    'default_interpreter'
]
