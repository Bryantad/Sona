# Mini-Lesson 9.3: Code Organization

## Why Organization Matters

As projects grow, good organization:
- Makes code easier to find
- Reduces bugs
- Helps others understand your code
- Makes updates safer

---

## Project Structure Templates

### Small Project (1-5 files)
```
my_project/
├── main.sona          # Entry point
├── helpers.sona       # Utility functions
└── config.sona        # Settings
```

### Medium Project (5-15 files)
```
my_project/
├── main.sona
├── config.sona
├── models/
│   ├── user.sona
│   └── product.sona
├── services/
│   ├── auth.sona
│   └── database.sona
└── utils/
    ├── helpers.sona
    └── validators.sona
```

### Large Project (15+ files)
```
my_project/
├── main.sona
├── config/
│   ├── settings.sona
│   └── constants.sona
├── models/
│   └── ...
├── services/
│   └── ...
├── controllers/
│   └── ...
├── utils/
│   └── ...
├── tests/
│   └── ...
└── docs/
    └── ...
```

---

## Naming Conventions

### Files
- Use lowercase with underscores: `user_service.sona`
- Be descriptive: `email_validator.sona` not `ev.sona`
- Group related files in folders

### Functions
- Use verbs: `calculate_total()`, `validate_email()`
- Be specific: `get_user_by_id()` not `getUser()`

### Variables
- Use descriptive names: `user_count` not `uc`
- Constants in CAPS: `MAX_RETRIES`, `API_URL`

### Classes
- Use PascalCase: `UserAccount`, `ShoppingCart`

---

## Single Responsibility Principle

Each module should do ONE thing well:

**❌ Bad - Too many responsibilities:**
```sona
// everything.sona
func readFile() { ... }
func writeFile() { ... }
func parseJSON() { ... }
func validateEmail() { ... }
func connectDatabase() { ... }
func sendEmail() { ... }
```

**✅ Good - Focused modules:**
```
utils/
├── io_utils.sona       # File operations
├── json_utils.sona     # JSON parsing
├── validators.sona     # Validation
├── database.sona       # DB operations
└── email.sona          # Email functions
```

---

## Layered Architecture

Organize by responsibility:

```
┌─────────────────────────────────────┐
│           main.sona                 │  Entry point
├─────────────────────────────────────┤
│          controllers/               │  Handle requests
├─────────────────────────────────────┤
│           services/                 │  Business logic
├─────────────────────────────────────┤
│            models/                  │  Data structures
├─────────────────────────────────────┤
│            utils/                   │  Helper functions
└─────────────────────────────────────┘
```

**Rule:** Upper layers can import lower layers, but not vice versa.

---

## Configuration Management

Keep settings separate:

**config.sona:**
```sona
// Environment-specific settings
let DEBUG = true
let LOG_LEVEL = "info"

// API settings
let API_URL = "https://api.example.com"
let API_TIMEOUT = 30

// Database settings  
let DB_HOST = "localhost"
let DB_PORT = 5432

// Feature flags
let ENABLE_CACHE = true
let ENABLE_ANALYTICS = false
```

**main.sona:**
```sona
import config

if config.DEBUG {
    print("Debug mode enabled")
}
```

---

## Managing Dependencies

Track what each module needs:

**Good Practice:**
```sona
// user_service.sona
// Dependencies: database, validators, logger

import database
import validators
import logger

func create_user(data) {
    if not validators.validate_user(data) {
        logger.error("Invalid user data")
        return null
    }
    
    return database.insert("users", data)
}
```

---

## Avoiding Circular Dependencies

```
     ┌──────────────────────┐
     │    common/utils      │  Shared utilities
     └──────────────────────┘
              ↑
     ┌────────┴────────┐
     │                 │
┌────┴─────┐    ┌──────┴────┐
│ module_a │    │ module_b  │  Both use utils
└──────────┘    └───────────┘
```

**Shared code goes in a common module that others import.**

---

## Index Files

Create an index to simplify imports:

**models/index.sona:**
```sona
// Re-export all models from one place
export { User } from "./user.sona"
export { Product } from "./product.sona"
export { Order } from "./order.sona"
```

**main.sona:**
```sona
// Import all models from one place
from models import User, Product, Order
```

---

## Documentation in Modules

Add module-level documentation:

```sona
// email_service.sona
// 
// Email Service Module
// ====================
// Handles all email-related operations including:
// - Sending emails
// - Email templates
// - Email validation
//
// Dependencies: smtp, templates, config
// Author: Your Name
// Version: 1.0

import smtp
import templates
import config

func send_email(to, subject, body) {
    // ...
}
```

---

## Project Example: Todo App

```
todo_app/
├── main.sona              # Entry point, UI
├── config.sona            # Settings
├── models/
│   └── task.sona         # Task class
├── services/
│   └── task_service.sona # Task operations
├── storage/
│   └── file_storage.sona # Save/load tasks
└── utils/
    └── validators.sona   # Input validation
```

**models/task.sona:**
```sona
class Task {
    func init(title, done = false) {
        self.title = title
        self.done = done
        self.created = time.now()
    }
    
    func complete() {
        self.done = true
    }
    
    func display() {
        let status = self.done ? "✓" : "○"
        print("{status} {self.title}")
    }
}
```

**services/task_service.sona:**
```sona
import models.task as t
import storage.file_storage as storage

let _tasks = []

func add_task(title) {
    let task = t.Task(title)
    _tasks.push(task)
    storage.save(_tasks)
    return task
}

func get_all_tasks() {
    return _tasks
}

func complete_task(index) {
    if index >= 0 and index < _tasks.length() {
        _tasks[index].complete()
        storage.save(_tasks)
    }
}

func load_tasks() {
    _tasks = storage.load()
}
```

---

## Practice

### Exercise 1
Take this flat structure:
```
project/
├── main.sona (500 lines with everything)
```

Reorganize into modules. What would your structure look like?

### Exercise 2
Create a small project structure for a "grade tracker" app with:
- Student data
- Grade calculations
- File storage
- Main program

### Exercise 3
Review your existing code. What could be moved into a separate module?

---

## Summary

**Key Principles:**
1. **Single Responsibility** - One module, one purpose
2. **Clear Naming** - Descriptive file and function names
3. **Layered Structure** - Organize by responsibility
4. **Avoid Cycles** - No circular imports
5. **Document** - Explain what each module does

---

## Module 09 Complete! 🎉

You've learned:
- ✅ Importing standard library modules
- ✅ Creating your own modules
- ✅ Organizing code effectively

→ Next: [Module 10: Object-Oriented Programming](../10_oop/README.md)
