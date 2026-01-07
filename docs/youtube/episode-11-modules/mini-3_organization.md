# Mini-Episode 11.3: Project Organization 📁

> Structure your code like a pro

---

## Why Organization Matters

Small project: One file is fine
```
my_script.sona
```

Bigger project: You need structure!
```
my_project/
├── main.sona
├── helpers.sona
├── models.sona
└── data/
    └── config.json
```

---

## Basic Project Structure

```
my_app/
├── main.sona           # Entry point
├── config.sona         # Configuration
├── models/             # Data structures
│   ├── user.sona
│   └── product.sona
├── utils/              # Helper functions
│   ├── strings.sona
│   └── validation.sona
├── data/               # Data files
│   └── settings.json
└── tests/              # Test files
    └── test_utils.sona
```

---

## Importing from Folders

```sona
// Import from subfolder
from models.user import User
from utils.strings import clean_text

// Use them
let user = User("Alice")
let text = clean_text("  hello  ")
```

---

## The Main Entry Point

```sona
// main.sona - Your application starts here

from models import User
from utils import helpers
import config

func main() {
    print("Starting application...")
    
    // Your app logic here
    let settings = config.load()
    // ...
    
    print("Application finished.")
}

// Run main when script is executed
main()
```

---

## Configuration Module

```sona
// config.sona
import json

let DEFAULT_CONFIG = {
    "debug": false,
    "max_users": 100,
    "theme": "light"
}

func load() {
    try {
        return json.load("data/settings.json")
    } catch error {
        return DEFAULT_CONFIG
    }
}

func save(config) {
    json.save("data/settings.json", config)
}
```

---

## Separating Concerns

**Models** - Data structures (what things ARE)
```sona
// models/user.sona
class User {
    func init(name, email) {
        self.name = name
        self.email = email
    }
}
```

**Services** - Business logic (what things DO)
```sona
// services/user_service.sona
from models.user import User

func create_user(name, email) {
    // Validation, database saving, etc.
    return User(name, email)
}
```

**Utils** - General helpers
```sona
// utils/validation.sona
func is_valid_email(email) {
    return "@" in email and "." in email
}
```

---

## Package Initialization

Create `__init__.sona` to make a folder importable:

```
models/
├── __init__.sona
├── user.sona
└── product.sona
```

```sona
// models/__init__.sona
from .user import User
from .product import Product
```

```sona
// main.sona
from models import User, Product  // Clean import!
```

---

## Real Project Example

```
todo_app/
├── main.sona           # Entry point
├── config.sona         # Settings
├── models/
│   └── task.sona       # Task class
├── services/
│   └── task_service.sona  # Task operations
├── ui/
│   └── menu.sona       # User interface
├── storage/
│   └── file_storage.sona  # Save/load tasks
└── data/
    └── tasks.json      # Task data file
```

---

## Organization Rules of Thumb

1. **One class per file** (for larger classes)
2. **Group related functions** in a module
3. **Keep files under 200 lines** when possible
4. **Name files after their contents**
5. **Use folders** when you have 5+ related files
