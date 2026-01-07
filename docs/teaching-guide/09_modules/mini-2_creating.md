# Mini-Lesson 9.2: Creating Your Own Modules

## Why Create Modules?

- **Reuse code** across projects
- **Organize** related functions together
- **Share** code with others
- **Keep files small** and focused

---

## Creating a Simple Module

A module is just a `.sona` file:

**helpers.sona:**
```sona
// helpers.sona - Utility functions

func greet(name) {
    return "Hello, " + name + "!"
}

func double(n) {
    return n * 2
}

let VERSION = "1.0"
```

**main.sona:**
```sona
import helpers

print(helpers.greet("Alex"))  // "Hello, Alex!"
print(helpers.double(21))     // 42
print(helpers.VERSION)        // "1.0"
```

That's it! Any `.sona` file is a module.

---

## Module Location

For imports to work, the module must be findable:

```
project/
├── main.sona          # import helpers
├── helpers.sona       # Found! Same folder
└── utils/
    └── math_utils.sona  # import utils.math_utils
```

---

## Import from Subfolders

```sona
// Import from utils folder
import utils.math_utils
import utils.string_utils

// Use them
print(utils.math_utils.calculate())
```

Or with aliases:
```sona
import utils.math_utils as mutils
print(mutils.calculate())
```

---

## What Goes in a Module

### Variables and Constants
```sona
// config.sona
let DEBUG = true
let VERSION = "2.0"
let MAX_USERS = 100
```

### Functions
```sona
// calculator.sona
func add(a, b) {
    return a + b
}

func subtract(a, b) {
    return a - b
}

func multiply(a, b) {
    return a * b
}
```

### Classes
```sona
// models.sona
class User {
    func init(name, email) {
        self.name = name
        self.email = email
    }
    
    func display() {
        print("{self.name} <{self.email}>")
    }
}

class Product {
    func init(name, price) {
        self.name = name
        self.price = price
    }
}
```

---

## Private vs Public

By convention, names starting with `_` are private:

```sona
// database.sona

// Public - meant to be used
func connect(url) {
    return _create_connection(url)
}

func query(sql) {
    return _execute(sql)
}

// Private - internal use only
func _create_connection(url) {
    // ...
}

func _execute(sql) {
    // ...
}
```

Others can still access `_create_connection`, but the underscore signals "don't use this directly."

---

## Module Initialization

Code at module level runs when imported:

```sona
// logger.sona
print("Logger module loaded!")  // Runs on import

let _log_file = null

func _initialize() {
    _log_file = io.open("app.log", "a")
}

func log(message) {
    // ...
}

// Initialize when module loads
_initialize()
```

---

## Exporting Specific Items

Control what's exported:

```sona
// utils.sona

// This will be exported
export func calculate() {
    return _helper()
}

export let PI = 3.14159

// This stays private (no export)
func _helper() {
    return 42
}
```

---

## Circular Imports (Avoid!)

**Problem:** Module A imports Module B, which imports Module A.

```sona
// a.sona
import b
func funcA() { b.funcB() }

// b.sona  
import a  // ERROR: Circular import!
func funcB() { a.funcA() }
```

**Solution:** Restructure so there's no cycle, or use a third module.

---

## Complete Example

**Project structure:**
```
game/
├── main.sona
├── player.sona
├── enemies.sona
└── utils/
    └── math.sona
```

**utils/math.sona:**
```sona
func distance(x1, y1, x2, y2) {
    let dx = x2 - x1
    let dy = y2 - y1
    return math.sqrt(dx*dx + dy*dy)
}

func clamp(value, min, max) {
    if value < min { return min }
    if value > max { return max }
    return value
}
```

**player.sona:**
```sona
import utils.math as umath

class Player {
    func init(name) {
        self.name = name
        self.x = 0
        self.y = 0
        self.health = 100
    }
    
    func move(dx, dy) {
        self.x = self.x + dx
        self.y = self.y + dy
    }
    
    func distanceTo(other) {
        return umath.distance(self.x, self.y, other.x, other.y)
    }
    
    func takeDamage(amount) {
        self.health = umath.clamp(self.health - amount, 0, 100)
    }
}
```

**main.sona:**
```sona
import player
import enemies

let hero = player.Player("Hero")
let goblin = enemies.Goblin(5, 5)

print("Distance to enemy: " + hero.distanceTo(goblin))
```

---

## Practice

### Exercise 1
Create a module `greetings.sona` with functions `hello(name)` and `goodbye(name)`. Import and use them in another file.

### Exercise 2
Create a `math_helpers.sona` module with:
- `square(n)` - returns n²
- `cube(n)` - returns n³
- `is_even(n)` - returns true if n is even

### Exercise 3
Organize a calculator into modules:
- `operations.sona` - add, subtract, multiply, divide
- `advanced.sona` - power, sqrt, factorial
- `main.sona` - uses both modules

---

## Summary

| Task | How |
|------|-----|
| Create module | Save as `.sona` file |
| Import module | `import modulename` |
| Import from folder | `import folder.module` |
| Mark as private | Start name with `_` |
| Control exports | Use `export` keyword |

---

→ Next: [mini-3: Code Organization](mini-3_organizing.md)
