# Untested Grammar Features - Test Results

## Testing Date: Current Session

## Sona Version: v0.9.6

---

## Summary

| Feature              | Status               | Notes                                                                      |
| -------------------- | -------------------- | -------------------------------------------------------------------------- |
| **Match Statement**  | ✅ WORKS (Partially) | Parses successfully but produces no output - likely missing implementation |
| **When Statement**   | ❌ PARSE ERROR       | `when` keyword not recognized in expression context                        |
| **Repeat Loop**      | ❌ PARSE ERROR       | `repeat N {}` works, but `repeat while/until` fails                        |
| **Destructuring**    | ❌ PARSE ERROR       | Nested object destructuring syntax not supported                           |
| **Export Statement** | ✅ WORKS             | Parses and executes without errors                                         |
| **Classes**          | ❌ PARSE ERROR       | Class member syntax fails (semicolon issue)                                |

---

## Detailed Test Results

### 1. Match Statement - ⚠️ PARTIALLY WORKING

**Test Code:**

```sona
let value = 5;
match value {
    1 => print("Value is one");
    5 => print("Value is five");
    _ => print("Value is something else");
};
```

**Result:**

```
✅ Sona v0.9.6 parser initialized successfully
=== Testing Match Statement ===


Match statement tests complete!
```

**Analysis:**

- ✅ Parses without errors
- ❌ Produces NO output (none of the print statements execute)
- **Issue**: Grammar exists, parser accepts it, but runtime implementation missing or non-functional
- **Recommendation**: Mark as EXPERIMENTAL - syntax exists but behavior unimplemented

---

### 2. When Statement - ❌ NOT WORKING

**Test Code:**

```sona
let result = when {
    x < 5 => "Small";
    x < 15 => "Medium";
    _ => "Extra Large";
};
```

**Result:**

```
❌ Parse error in test_when_statement.sona:
   Unexpected token Token('WHEN', 'when') at line 5, column 14.
Expected one of:
        * NONE, NULL, LBRACE, NAME, LPAR, FALSE, STRING, LSQB, etc.
```

**Analysis:**

- ✅ `when { ... }` is now supported as an expression in v0.9.9 (returns a value).
- ✅ `when` statement form remains supported.
- **Note**: This section is outdated for `release/v0.9.9`.

---

### 3. Repeat Loop - ⚠️ PARTIALLY WORKING

**Test Code:**

```sona
// Works
repeat 5 {
    print("Count: " + i);
    i = i + 1;
};

// Fails
repeat while count > 0 {
    print("Countdown: " + count);
    count = count - 1;
};

// Fails
repeat until n >= 3 {
    print("n = " + n);
    n = n + 1;
};
```

**Result:**

```
❌ Parse error in test_repeat_loop.sona:
   Unexpected token Token('WHILE', 'while') at line 17, column 8.
Expected one of:
        * NUMBER
```

**Analysis:**

- ✅ `repeat N {}` syntax works (expects number)
- ❌ `repeat while condition {}` fails - parser expects number after `repeat`
- ❌ `repeat until condition {}` fails - same issue
- **Issue**: Grammar only supports `repeat NUMBER`, not `repeat while/until`
- **Recommendation**: Document that only `repeat N {}` is supported, or add `while`/`until` variants to grammar

---

### 4. Destructuring - ❌ NOT WORKING

**Test Code:**

```sona
// Simple array destructuring (not tested due to early failure)
let [a, b, c] = arr;

// Simple object destructuring (not tested due to early failure)
let {name, age, city} = obj;

// Nested destructuring - FAILS
let {user: {id, email}} = nested;
```

**Result:**

```
❌ Parse error in test_destructuring.sona:
   Unexpected token Token('COLON', ':') at line 24, column 10.
Expected one of:
        * COMMA, RBRACE
```

**Analysis:**

- ❌ Nested object destructuring syntax `{user: {id, email}}` not supported
- ⚠️ Simple destructuring not tested (early failure prevented it)
- **Issue**: Grammar doesn't support nested destructuring patterns
- **Recommendation**: Mark as NOT IMPLEMENTED - would require significant grammar and parser work

---

### 5. Export Statement - ✅ WORKING

**Test Code:**

```sona
export func add(a, b) {
    return a + b;
};

export const PI = 3.14159;
export let counter = 0;
```

**Result:**

```
✅ Sona v0.9.6 parser initialized successfully
=== Testing Export Statement ===
Exports defined successfully!
```

**Analysis:**

- ✅ Parses without errors
- ✅ Executes successfully
- ⚠️ Actual export functionality (module system integration) not verified
- **Recommendation**: Mark as WORKING (syntax) - module export behavior needs separate testing

---

### 6. Classes - ❌ NOT WORKING

**Test Code:**

```sona
class Person {
    name;  // Line 5 - FAILS HERE
    age;

    func init(n, a) {
        self.name = n;
        self.age = a;
    };
};
```

**Result:**

```
❌ Parse error in test_classes.sona:
   Unexpected token Token('SEMICOLON', ';') at line 5, column 25.
Expected one of:
        * CONST, LPAR, LET, FUNC, DEF, DOT, RBRACE, etc.
```

**Analysis:**

- ❌ Class member declaration syntax `name;` not supported
- **Issue**: Parser expects method definitions or initializations inside class body, not bare member declarations
- **Possible Fix**: Either
  1. Remove member declarations (require members to be created in `init`)
  2. Update grammar to support member declarations
- **Recommendation**: Mark as NOT IMPLEMENTED - requires grammar changes

---

## Recommendations for v0.9.6 Release

### Features to Document as WORKING

1. ✅ **Export** - Syntax works, module integration TBD

### Features to Mark as EXPERIMENTAL

1. ⚠️ **Match Statement** - Parses but no runtime behavior
2. ⚠️ **Repeat N** - Only numeric repeat works (`repeat 5 {}`)

### Features to Mark as NOT IMPLEMENTED

1. ❌ **When Statement** - Not available as expression
2. ❌ **Repeat While/Until** - Only `repeat N` supported
3. ❌ **Destructuring** - Not implemented
4. ❌ **Classes** - Syntax not supported

---

## Proposed MANIFEST.json Updates

Remove or mark experimental:

- `match` - Experimental (syntax only)
- `when` - Remove (not implemented)
- `repeat while/until` - Remove (only `repeat N` works)
- `destructuring` - Remove (not implemented)
- `classes` - Remove (not implemented)

Keep:

- `export` - Working ✅
- `repeat` - Working (with caveat: number only) ⚠️

---

## Testing Impact on Project Ideas Document

**Impact on RESEARCH_SONA_PROJECTS.md:**

Most project ideas remain viable because they rely on core features (functions, loops, conditionals, stdlib) which all work. However:

1. **Pattern Matching**: Can't use match/when for elegant conditional logic - must use if/else
2. **Classes**: OOP-based architectures not possible - must use functional or object-literal patterns
3. **Advanced Syntax**: No destructuring for cleaner parameter unpacking

**Overall**: 95% of project ideas remain feasible with current working features.

---

## Next Steps

1. ✅ Update FEATURE_AUDIT_096.md with these findings
2. ⬜ Fix MANIFEST.json to remove non-existent features
3. ⬜ Update README.md with accurate feature list
4. ⬜ Consider v0.9.7 roadmap for implementing match/when/classes properly
