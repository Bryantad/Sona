# Mini-Episode 11.2: Creating Modules 📦

> Make your own reusable code files

---

## Why Create Modules?

- **Organize** code into logical files
- **Reuse** code across projects
- **Share** code with others
- Keep files **manageable** size

---

## Creating a Simple Module

Create a file called `helpers.sona`:

```sona
// helpers.sona

func greet(name) {
    return f"Hello, {name}!"
}

func add(a, b) {
    return a + b
}

let VERSION = "1.0"
```

---

## Using Your Module

```sona
// main.sona
import helpers

print(helpers.greet("Alice"))  // Hello, Alice!
print(helpers.add(5, 3))       // 8
print(helpers.VERSION)          // 1.0
```

Both files should be in the same folder!

---

## Module as a Toolkit

```sona
// string_tools.sona - A collection of string utilities

func is_palindrome(text) {
    let clean = text.lower().replace(" ", "")
    return clean == clean.reverse()
}

func word_count(text) {
    return len(text.split())
}

func capitalize_words(text) {
    return text.title()
}
```

```sona
// main.sona
import string_tools

print(string_tools.is_palindrome("race car"))  // true
print(string_tools.word_count("hello world"))  // 2
```

---

## Module with Classes

```sona
// models.sona

class User {
    func init(name, email) {
        self.name = name
        self.email = email
    }
    
    func display() {
        return f"{self.name} <{self.email}>"
    }
}

class Product {
    func init(name, price) {
        self.name = name
        self.price = price
    }
}
```

```sona
// main.sona
from models import User, Product

let user = User("Alice", "alice@email.com")
print(user.display())
```

---

## Module Initialization

Code at the top level runs when imported:

```sona
// database.sona

print("Connecting to database...")  // Runs on import

let connection = create_connection()

func query(sql) {
    return connection.execute(sql)
}
```

---

## Prevent Code Running on Import

```sona
// my_module.sona

func main() {
    print("This only runs when executed directly")
}

// Only runs if this file is run directly, not imported
if __name__ == "__main__" {
    main()
}
```

---

## Module Best Practices

1. **One purpose per module** - Keep focused
2. **Clear names** - `user_auth.sona` not `ua.sona`
3. **Document functions** - Add comments
4. **No side effects** - Avoid code that runs on import

---

## Module Template

```sona
// my_module.sona
// Description: What this module does

// Constants
let DEFAULT_VALUE = 100

// Helper functions (internal)
func _internal_helper() {
    // Used only inside this module
    pass
}

// Public functions
func public_function() {
    // For others to use
    pass
}

// Classes
class MyClass {
    // ...
}
```
