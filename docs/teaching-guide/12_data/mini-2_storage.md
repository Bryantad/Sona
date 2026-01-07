# Mini-Lesson 12.2: Data Storage

## Storage Options

| Type | Best For | Persistence |
|------|----------|-------------|
| Variables | Temporary data | Lost on exit |
| Files | Simple data, configs | Permanent |
| JSON files | Structured data | Permanent |
| SQLite | Complex queries | Permanent |
| Cache | Speed optimization | Temporary |

---

## File-Based Storage

### Simple Key-Value Store

```sona
import io
import json

class Storage {
    func init(filename = "data.json") {
        self.filename = filename
        self._load()
    }
    
    func _load() {
        if io.exists(self.filename) {
            self.data = json.parse(io.read(self.filename))
        } else {
            self.data = {}
        }
    }
    
    func _save() {
        io.write(self.filename, json.stringify(self.data, indent: 2))
    }
    
    func get(key, default = null) {
        if key in self.data {
            return self.data[key]
        }
        return default
    }
    
    func set(key, value) {
        self.data[key] = value
        self._save()
    }
    
    func delete(key) {
        if key in self.data {
            delete self.data[key]
            self._save()
        }
    }
    
    func all() {
        return self.data
    }
}

// Usage
let storage = Storage("settings.json")
storage.set("theme", "dark")
storage.set("volume", 80)

print(storage.get("theme"))    // "dark"
print(storage.get("missing", "default"))  // "default"
```

---

## Collection Storage

Store lists of items:

```sona
import io
import json
import uuid
import time

class Collection {
    func init(name) {
        self.filename = name + ".json"
        self._load()
    }
    
    func _load() {
        if io.exists(self.filename) {
            self.items = json.parse(io.read(self.filename))
        } else {
            self.items = []
        }
    }
    
    func _save() {
        io.write(self.filename, json.stringify(self.items, indent: 2))
    }
    
    func create(data) {
        let item = {
            "id": uuid.generate(),
            "created_at": time.now().format("%Y-%m-%d %H:%M:%S"),
            ...data
        }
        self.items.push(item)
        self._save()
        return item
    }
    
    func find(id) {
        for item in self.items {
            if item.id == id {
                return item
            }
        }
        return null
    }
    
    func findBy(key, value) {
        let results = []
        for item in self.items {
            if item[key] == value {
                results.push(item)
            }
        }
        return results
    }
    
    func update(id, data) {
        for i, item in enumerate(self.items) {
            if item.id == id {
                for key, value in data.items() {
                    self.items[i][key] = value
                }
                self._save()
                return self.items[i]
            }
        }
        return null
    }
    
    func delete(id) {
        for i, item in enumerate(self.items) {
            if item.id == id {
                self.items.remove(i)
                self._save()
                return true
            }
        }
        return false
    }
    
    func all() {
        return self.items
    }
    
    func count() {
        return self.items.length()
    }
}

// Usage
let users = Collection("users")

// Create
let user = users.create({
    "name": "Alice",
    "email": "alice@example.com"
})
print("Created: " + user.id)

// Read
let found = users.find(user.id)
let admins = users.findBy("role", "admin")

// Update
users.update(user.id, {"name": "Alice Smith"})

// Delete
users.delete(user.id)

// List all
for user in users.all() {
    print("{user.name} - {user.email}")
}
```

---

## Caching

Speed up slow operations:

```sona
import time

class Cache {
    func init(ttl = 300) {  // Default 5 minutes
        self.ttl = ttl
        self.data = {}
        self.timestamps = {}
    }
    
    func get(key) {
        if key in self.data {
            let age = time.timestamp() - self.timestamps[key]
            if age < self.ttl {
                return self.data[key]
            }
            // Expired
            self.delete(key)
        }
        return null
    }
    
    func set(key, value) {
        self.data[key] = value
        self.timestamps[key] = time.timestamp()
    }
    
    func delete(key) {
        if key in self.data {
            delete self.data[key]
            delete self.timestamps[key]
        }
    }
    
    func clear() {
        self.data = {}
        self.timestamps = {}
    }
}

// Usage with expensive operations
let cache = Cache(60)  // 1 minute TTL

func fetchUserData(userId) {
    // Check cache first
    let cached = cache.get("user_" + userId)
    if cached != null {
        print("Cache hit!")
        return cached
    }
    
    // Fetch from API (slow)
    print("Fetching from API...")
    let data = http.get_json("https://api.example.com/users/" + userId)
    
    // Store in cache
    cache.set("user_" + userId, data)
    
    return data
}

// First call - fetches from API
let user1 = fetchUserData("123")

// Second call - uses cache
let user2 = fetchUserData("123")
```

---

## Application State

Manage complex application state:

```sona
import io
import json

class AppState {
    func init() {
        self.state = {
            "user": null,
            "settings": {
                "theme": "light",
                "notifications": true
            },
            "data": {}
        }
        self._loadSaved()
    }
    
    func _loadSaved() {
        if io.exists("appstate.json") {
            let saved = json.parse(io.read("appstate.json"))
            // Merge with defaults
            for key, value in saved.items() {
                self.state[key] = value
            }
        }
    }
    
    func save() {
        io.write("appstate.json", json.stringify(self.state, indent: 2))
    }
    
    func get(path) {
        let parts = path.split(".")
        let current = self.state
        
        for part in parts {
            if part in current {
                current = current[part]
            } else {
                return null
            }
        }
        return current
    }
    
    func set(path, value) {
        let parts = path.split(".")
        let current = self.state
        
        // Navigate to parent
        for i in range(parts.length() - 1) {
            if parts[i] not in current {
                current[parts[i]] = {}
            }
            current = current[parts[i]]
        }
        
        // Set value
        current[parts[-1]] = value
        self.save()
    }
    
    func login(user) {
        self.set("user", user)
    }
    
    func logout() {
        self.set("user", null)
    }
    
    func isLoggedIn() {
        return self.get("user") != null
    }
}

// Usage
let app = AppState()

app.set("settings.theme", "dark")
print(app.get("settings.theme"))  // "dark"

app.login({"name": "Alice", "id": "123"})
if app.isLoggedIn() {
    print("Welcome, " + app.get("user.name"))
}
```

---

## Practice

### Exercise 1
Create a simple note-taking storage that can add, list, and delete notes.

### Exercise 2
Build a cache that persists to a file (survives restarts).

### Exercise 3
Create a todo app with persistent storage:
- Add tasks
- Mark as complete
- Delete tasks
- List all/pending/completed

---

→ Next: [mini-3: Data Transformation](mini-3_transform.md)
