import importlib.util
import importlib
import os
from lark import Lark, Transformer, Tree, Token
from pathlib import Path

# Native module imports
from sona.stdlib import (
    env as env_module,
    time as time_module,
)

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

# Update the import statement at the top of the file
from sona.stdlib.native_stdin import native_stdin

class SonaInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.env = [{}]
        self.functions = {}
        self.modules = {}

        # Register native modules
        self.modules["native_stdin"] = native_stdin
        self.modules["env"] = {
            "get": env_module.get,
            "set": env_module.set,
        }
        self.modules["time"] = {
            "now": time_module.now,
            "sleep": time_module.sleep,
        }

    def push_scope(self):
        self.env.append({})

    def pop_scope(self):
        self.env.pop()

    def set_var(self, name, value):
        self.env[-1][name] = value

    def get_var(self, name):
        # Handle dotted access: module.attr
        if '.' in name:
            module_name, attr_name = name.split('.', 1)
            if module_name not in self.modules:
                raise ImportError(f"Module '{module_name}' not loaded")
            module = self.modules[module_name]
            # Object-style module
            if hasattr(module, attr_name):
                return getattr(module, attr_name)
            # Dict-style module
            if isinstance(module, dict) and attr_name in module:
                return module[attr_name]
            raise AttributeError(f"Module '{module_name}' has no attribute '{attr_name}'")
        # Regular variable lookup
        for scope in reversed(self.env):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' not found")

    def assignment(self, args):
        name_token, value_expr = args
        value = self.eval_arg(value_expr)
        self.set_var(str(name_token), value)
        return value

    def print_stmt(self, args):
        val = self.eval_arg(args[0])
        print(f"[OUTPUT] {val}")
        return val

    def import_stmt(self, args):
        module_name = ".".join(str(part) for part in args)
        module_path = module_name.replace(".smod", "").replace(".", "/")
        py_module = f"sona.stdlib.{module_path.replace('/', '.')}"

        try:
            mod = importlib.import_module(py_module)
            # Only expose the final part (e.g., `math` in `utils.math.smod`)
            final_var = str(args[-2]) if args[-1] == "smod" else str(args[-1])
            self.set_var(final_var, mod)
            self.modules[final_var] = mod
            print(f"[DEBUG] Sona import statement for: '{module_name}', sona_var_name: '{final_var}'")
        except Exception as e:
            raise ImportError(f"Could not import module '{module_name}': {e}")

    def if_stmt(self, args):
        cond, true_block, *false_block = args
        if self.eval_arg(cond):
            self._exec(true_block.children)
        elif false_block:
            self._exec(false_block[0].children)

    def while_stmt(self, args):
        cond_expr, body = args
        while self.eval_arg(cond_expr):
            self._exec(body.children)

    def for_stmt(self, args):
        var_token, start_expr, end_expr, body = args
        varname = str(var_token)
        for i in range(int(self.eval_arg(start_expr)), int(self.eval_arg(end_expr))):
            self.push_scope()
            self.set_var(varname, i)
            self._exec(body.children)
            self.pop_scope()

    def func_def(self, args):
        name = str(args[0])
        params = [str(p) for p in args[1].children] if hasattr(args[1], "children") else [str(args[1])]
        body = args[2] if len(args) == 3 else args[1]
        self.functions[name] = (params, body)
        print(f"[DEBUG] Stored function '{name}' with params {params}")

    def func_call(self, args):
        # Extract function name and arguments
        name_node = args[0]
        passed_args = []
        if len(args) > 1 and isinstance(args[1], Tree) and args[1].data == "args":
            passed_args = [self.eval_arg(a) for a in args[1].children]

        # Handle dotted calls (module.method)
        if isinstance(name_node, Tree) and name_node.data == "dotted_name":
            name_parts = [str(t.value) if isinstance(t, Token) else str(t) for t in name_node.children]
            obj_name, method_name = name_parts[0], name_parts[1]

            # Resolve from self.modules
            if obj_name in self.modules:
                obj = self.modules[obj_name]
                print(f"[DEBUG] Found {obj_name} in self.modules: {type(obj)}")

                # Attribute access (object-style)
                if hasattr(obj, method_name):
                    attr = getattr(obj, method_name)
                    print(f"[DEBUG] {obj_name}.{method_name} resolved via attribute: {attr} (callable={callable(attr)})")
                    if callable(attr):
                        return attr(*passed_args)
                    else:
                        raise TypeError(f"Attribute '{method_name}' of module '{obj_name}' is not callable")
                # Dict-style access
                elif isinstance(obj, dict) and method_name in obj:
                    func = obj[method_name]
                    print(f"[DEBUG] {obj_name}.{method_name} resolved via dict key: {func} (callable={callable(func)})")
                    if callable(func):
                        return func(*passed_args)
                    else:
                        raise TypeError(f"Key '{method_name}' of module '{obj_name}' is not callable")
                else:
                    raise AttributeError(f"Module '{obj_name}' has no method or key '{method_name}'")
            # ... (rest of the method remains the same)
            elif hasattr(self, "native") and obj_name in getattr(self, "native", {}):
                native_obj = self.native[obj_name]
                print(f"[DEBUG] Fallback: Found {obj_name} in self.native: {type(native_obj)}")
                if hasattr(native_obj, method_name):
                    attr = getattr(native_obj, method_name)
                    print(f"[DEBUG] {obj_name}.{method_name} (native) resolved via attribute: {attr} (callable={callable(attr)})")
                    if callable(attr):
                        return attr(*passed_args)
                    else:
                        raise TypeError(f"Attribute '{method_name}' of native module '{obj_name}' is not callable")
                elif isinstance(native_obj, dict) and method_name in native_obj:
                    func = native_obj[method_name]
                    print(f"[DEBUG] {obj_name}.{method_name} (native) resolved via dict key: {func} (callable={callable(func)})")
                    if callable(func):
                        return func(*passed_args)
                    else:
                        raise TypeError(f"Key '{method_name}' of native module '{obj_name}' is not callable")
                else:
                    raise AttributeError(f"Native module '{obj_name}' has no method or key '{method_name}'")
            else:
                raise NameError(f"Module '{obj_name}' not imported")

        # Handle user-defined function calls
        name = str(name_node)
        if name not in self.functions:
            raise NameError(f"Function '{name}' not defined")

        params, body = self.functions[name]
        if len(params) != len(passed_args):
            raise ValueError(f"Function '{name}' expects {len(params)} arguments, got {len(passed_args)}")

        # Push a new scope for the function call
        self.push_scope()
        for pname, pval in zip(params, passed_args):
            self.set_var(pname, pval)

        try:
            self._exec(body.children)
        except ReturnSignal as r:
            self.pop_scope()
            return r.value

        # 🟢 Don't forget to pop scope on normal exit too!
        self.pop_scope()

    def return_stmt(self, args):
        raise ReturnSignal(self.eval_arg(args[0]))

    def add(self, args): 
        return self.eval_arg(args[0]) + self.eval_arg(args[1])
    def sub(self, args): 
        return self.eval_arg(args[0]) - self.eval_arg(args[1])
    def mul(self, args): 
        return self.eval_arg(args[0]) * self.eval_arg(args[1])
    def div(self, args): 
        return self.eval_arg(args[0]) / self.eval_arg(args[1])

    def number(self, args): 
        return float(args[0])
    def string(self, args): 
        return str(args[0])[1:-1]
    def var(self, args): 
        return self.get_var(str(args[0]))

    def eval_arg(self, arg):
        return self._eval(arg) if isinstance(arg, Tree) else arg

    def _eval(self, node):
        return self.transform(node)

    def _exec(self, node):
        if isinstance(node, Tree):
            self.transform(node)
        elif isinstance(node, list):
            for n in node:
                self._exec(n)

def load_smod_module(module_name):
    path = os.path.join("sona", "stdlib", f"{module_name}.py")
    if not os.path.isfile(path):
        raise ImportError(f"No backend found for module '{module_name}'")
    spec = importlib.util.spec_from_file_location(f"sona.stdlib.{module_name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_code(code):
    print("[DEBUG] run_code() received input:")
    print(code[:100])
    with open("sona/grammar.lark") as f:
        grammar = f.read()

    parser = Lark(grammar, parser="lalr", propagate_positions=True)
    try:
        tree = parser.parse(code)
    except Exception as e:
        print(f"[PARSER ERROR] {e}")
        return

    print("[DEBUG] Starting execution...")
    interpreter = SonaInterpreter()
    try:
        print(tree.pretty())
        interpreter.transform(tree)
    except Exception as e:
        print(f"[INTERPRETER ERROR] {e}")

if __name__ == "__main__":
    test_files = [
        "examples/test_all_modules.sona",
    ]

    for file in test_files:
        try:
            code = Path(file).read_text()
            print(f"Running: {file}")
            run_code(code)
            print("✅ Success\n")
        except Exception as e:
            print(f"❌ Error in {file}: {e}\n")
        finally:
            print("-" * 40)
