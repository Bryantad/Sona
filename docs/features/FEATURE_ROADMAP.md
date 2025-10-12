# 🚀 Sona 0.9.6 Pre-Release Feature Roadmap

Based on your current implementation and the stdlib you already have, here are high-impact features organized by effort vs. value:

---

## 🎯 **TIER 1: Quick Wins (1-3 hours each)**

_Ship these before release - they're expected for 0.9.6_

### 1. **Import System** ⭐ **HIGHEST PRIORITY**

**Why**: You have 30 stdlib modules but no way to use them in `.sona` files yet.

```sona
import math
import string

x = math.sqrt(16)
print(string.upper("hello"))
```

**Implementation**:

- Parse `import <module>` statements
- Load corresponding `.smod` files
- Register functions in current scope
- **Blocks**: All 7 advanced test files waiting for this

**Files to modify**:

- `sona/parser_v090.py` - Add import grammar rule
- `sona/interpreter.py` - Add module loading logic
- Reference existing `.smod` files in `smod/` directory

---

### 2. **Boolean Type & Literals**

**Why**: Currently missing `true`/`false` keywords.

```sona
is_ready = true
is_done = false

if is_ready and not is_done:
    print("Starting...")
```

**Implementation**:

- Add `true`/`false` to lexer
- Add `and`, `or`, `not` operators
- Boolean evaluation in if/while conditions

---

### 3. **Function Definitions**

**Why**: Can't write reusable code yet.

```sona
func add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8
```

**Implementation**:

- `func` keyword
- Parameter parsing
- `return` statement
- Function call evaluation

---

### 4. **Lists/Arrays**

**Why**: Basic data structure, expected in modern languages.

```sona
numbers = [1, 2, 3, 4, 5]
print(numbers[0])  # 1
numbers.append(6)
print(len(numbers))  # 6
```

**Implementation**:

- List literal syntax `[...]`
- Index access `list[i]`
- Built-in methods: `append`, `pop`, `len`

---

## 🔥 **TIER 2: Medium Impact (3-6 hours each)**

_Add 2-3 of these for a strong release_

### 5. **Dictionary/Map Type**

```sona
person = {"name": "Alice", "age": 30}
print(person["name"])
person["city"] = "NYC"
```

### 6. **For Loops**

```sona
for i in range(5):
    print(i)

for item in [1, 2, 3]:
    print(item)
```

### 7. **String Interpolation**

```sona
name = "World"
print(f"Hello, {name}!")  # or use ${name} syntax
```

### 8. **Try/Catch Error Handling**

```sona
try:
    x = 10 / 0
catch error:
    print("Division by zero!")
```

### 9. **File I/O Built-ins**

```sona
# Using your existing io.smod
import io

content = io.read_file("data.txt")
io.write_file("output.txt", content)
```

### 10. **Comments**

```sona
# This is a comment
x = 5  # Inline comment
```

---

## 💎 **TIER 3: Nice-to-Have (6-12 hours each)**

_Save for 0.9.7+_

### 11. **Class/Object System**

```sona
class Person:
    func init(name, age):
        self.name = name
        self.age = age

    func greet():
        print(f"Hi, I'm {self.name}")

alice = Person("Alice", 30)
alice.greet()
```

### 12. **Module System (Custom Modules)**

```sona
# mylib.sona
export func helper():
    return 42

# main.sona
import mylib
print(mylib.helper())
```

### 13. **Lambda/Anonymous Functions**

```sona
add = lambda a, b: a + b
print(add(3, 4))

# Or with collections
numbers = [1, 2, 3, 4, 5]
doubled = numbers.map(lambda x: x * 2)
```

### 14. **Destructuring Assignment**

```sona
[a, b, c] = [1, 2, 3]
{"name": n, "age": a} = person
```

### 15. **Spread/Rest Operators**

```sona
func sum(...numbers):
    total = 0
    for n in numbers:
        total += n
    return total

print(sum(1, 2, 3, 4, 5))  # 15
```

---

## 🎨 **TIER 4: Quality of Life**

### 16. **Better Error Messages**

```
Error at line 5, column 12:
    x = undefined_var + 5
        ^^^^^^^^^^^^^
NameError: Variable 'undefined_var' not defined
```

### 17. **REPL Improvements**

- Multi-line input support
- History navigation (↑/↓ arrows)
- Auto-completion
- Syntax highlighting

### 18. **Debugger**

```sona
breakpoint()  # Pause execution
print(x)      # Inspect variables
step()        # Step through code
```

### 19. **Package Manager**

```bash
sona install requests
sona list
sona uninstall requests
```

### 20. **Standard Library Expansion**

- `http` - Web requests
- `csv` - CSV parsing
- `xml` - XML processing
- `threading` - Concurrency
- `async` - Async/await

---

## 📋 **Recommended Pre-Release Checklist**

### Must-Have (Ship Blockers):

- [x] Version banner shows 0.9.6
- [ ] **Import system working** (stdlib usable)
- [ ] **Boolean type** (true/false)
- [ ] **Function definitions** (func/return)
- [ ] **Lists** (arrays with indexing)
- [ ] **Comments** (# syntax)
- [ ] Basic error messages show line numbers

### Should-Have (Strong Release):

- [ ] Dictionaries/maps
- [ ] For loops
- [ ] String interpolation
- [ ] File I/O examples working
- [ ] Try/catch error handling

### Nice-to-Have (Wow Factor):

- [ ] Class system (basic OOP)
- [ ] Lambda functions
- [ ] Better REPL experience

---

## 🎯 **My Recommendation: Ship 0.9.6 With These 5**

If you add just these **5 features**, you'll have a solid, usable language:

1. **Import System** ← Unlocks all 30 stdlib modules
2. **Boolean Type** ← Basic logic
3. **Function Definitions** ← Code reuse
4. **Lists** ← Essential data structure
5. **Comments** ← Code documentation

**Estimated total time**: 8-12 hours  
**Result**: A language people can actually write programs in

Then save classes, lambdas, async, etc. for **0.9.7**.

---

## 🚀 **Implementation Order**

```
Day 1 (4 hours):
├── Comments (30 min)
├── Boolean type (1 hour)
└── Lists basics (2.5 hours)

Day 2 (4 hours):
├── Function definitions (3 hours)
└── Return statements (1 hour)

Day 3 (4 hours):
├── Import system (3 hours)
└── Testing & fixes (1 hour)
```

---

## 📦 **Quick Start: Add Comments First**

Want to start small? Here's how to add comments in 30 minutes:

```python
# In sona/parser_v090.py

# Add to grammar:
%ignore /\#[^\n]*/  # Ignore # comments

# That's it! Lark handles the rest.
```

Test:

```sona
# This is a comment
x = 5  # Inline comment
print(x)
```

---

**Which tier interests you most?** I can provide detailed implementation guides for any of these features.
