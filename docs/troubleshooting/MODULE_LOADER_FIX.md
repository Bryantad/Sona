# Sona v0.9.6 - Module Loader Fix

## Problem Discovered

During pre-release audit, 4 stdlib modules were reported as "not implemented":

- collection
- queue
- stack
- yaml

However, these modules existed in v0.9.5 and have full implementations in `sona/stdlib/*.py`.

## Root Cause

The module loader in `interpreter.py` only searched for files with the `native_` prefix:

```python
native_module_path = self.stdlib_path / f"native_{module_path}.py"
if native_module_path.exists():
    # load module
else:
    raise ImportError(f"Module '{module_path}' not found")
```

This meant:

- ✅ `native_json.py` → Found
- ✅ `native_math.py` → Found
- ❌ `collection.py` → Not found (no `native_collection.py`)
- ❌ `queue.py` → Not found (no `native_queue.py`)
- ❌ `stack.py` → Not found (no `native_stack.py`)
- ❌ `yaml.py` → Not found (no `native_yaml.py`)

## Solution Implemented

Updated `import_module()` to check for both `native_` prefixed and regular `.py` files:

```python
def import_module(self, module_path: str, alias: str | None = None):
    """Import a module and make it available in the interpreter"""
    module_name = alias if alias else module_path

    # Check if already loaded
    if module_name in self.loaded_modules:
        return self.loaded_modules[module_name]

    # Try native module first (native_{module}.py)
    native_module_path = self.stdlib_path / f"native_{module_path}.py"
    if native_module_path.exists():
        # Load and return native module
        ...

    # Try regular module (module.py) - NEW!
    regular_module_path = self.stdlib_path / f"{module_path}.py"
    if regular_module_path.exists():
        # Load and return regular module
        ...

    raise ImportError(f"Module '{module_path}' not found")
```

## Test Results

### Before Fix

```
❌ collection - Module 'collection' not found
❌ queue - Module 'queue' not found
❌ stack - Module 'stack' not found
❌ yaml - Module 'yaml' not found
Result: 16/30 modules working (53%)
```

### After Fix

```
✅ 1. json
✅ 2. string
✅ 3. math
✅ 4. regex
✅ 5. fs
✅ 6. path
✅ 7. io
✅ 8. env
✅ 9. csv
✅ 10. date
✅ 11. time
✅ 12. numbers
✅ 13. boolean
✅ 14. type
✅ 15. comparison
✅ 16. operators
✅ 17. random
✅ 18. encoding
✅ 19. timer
✅ 20. validation
✅ 21. statistics
✅ 22. sort
✅ 23. search
✅ 24. uuid
✅ 25. toml
✅ 26. hashing
✅ 27. collection
✅ 28. queue
✅ 29. stack
✅ 30. yaml

Result: 30/30 modules working (100%) 🎉
```

## Individual Module Tests

### collection module ✅

```sona
import collection;
let arr = [1, 2, 3, 4, 5];
print("Length: " + collection.len(arr));        // 5
print("First: " + collection.first(arr));       // 1
print("Last: " + collection.last(arr));         // 5
let first_three = collection.take(arr, 3);
print("First 3: " + first_three);               // [1, 2, 3]
```

### queue module ✅

```sona
import queue;
let q = queue.Queue();
q.enqueue(1);
q.enqueue(2);
q.enqueue(3);
print("Size: " + q.size());          // 3
print("Dequeue: " + q.dequeue());    // 1
print("Size: " + q.size());          // 2
```

### stack module ✅

```sona
import stack;
let s = stack.Stack();
s.push(10);
s.push(20);
s.push(30);
print("Size: " + s.size());    // 3
print("Pop: " + s.pop());      // 30
print("Peek: " + s.peek());    // 20
```

### yaml module ✅

```sona
import yaml;
let obj = {"language": "Sona", "version": "0.9.6"};
let yaml_str = yaml.dumps(obj);
print(yaml_str);
// Output:
// language: Sona
// version: 0.9.6
```

## Files Modified

- `sona/interpreter.py` - Updated `import_module()` method
- `sona/stdlib/MANIFEST.json` - Restored all 30 modules as working

## Impact

- ✅ Regression fixed - all v0.9.5 modules now work in v0.9.6
- ✅ Module count restored to 30/30 (100%)
- ✅ No breaking changes - backward compatible
- ✅ Future-proof - supports both naming conventions

## Compatibility

The loader now supports:

1. **Native modules**: `native_module.py` (priority)
2. **Regular modules**: `module.py` (fallback)

This allows flexibility in module implementation while maintaining backward compatibility.

---

**Status**: ✅ All 30 stdlib modules verified working  
**Test**: `python run_sona.py test_all_30_imports.sona`  
**Result**: 30/30 passed 🎉
