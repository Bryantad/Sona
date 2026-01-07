# Mini-Lesson 11.3: System & Network Modules

## Environment Variables (env)

Environment variables store configuration outside your code.

```sona
import env

// Get environment variable
let home = env.get("HOME")           // "/home/user" (Linux/Mac)
let path = env.get("PATH")           // System PATH
let user = env.get("USERNAME")       // Current user

// Get with default
let debug = env.get("DEBUG", "false")
let port = env.get("PORT", "3000")

// Set environment variable (for this session)
env.set("MY_VAR", "hello")
print(env.get("MY_VAR"))  // "hello"

// Check if exists
if env.has("API_KEY") {
    let key = env.get("API_KEY")
    // Use the API key
}

// Get all environment variables
let allVars = env.all()
for name, value in allVars.items() {
    print("{name}={value}")
}
```

### Practical: Config from Environment

```sona
import env

class Config {
    func init() {
        self.debug = env.get("DEBUG", "false") == "true"
        self.port = int(env.get("PORT", "3000"))
        self.database_url = env.get("DATABASE_URL", "localhost")
        self.api_key = env.get("API_KEY")
    }
    
    func validate() {
        if self.api_key == null {
            print("WARNING: API_KEY not set!")
            return false
        }
        return true
    }
}

let config = Config()
config.validate()
print("Running on port {config.port}")
```

---

## Path Module

Work with file paths safely.

```sona
import path

// Join paths (handles separators)
let full = path.join("data", "users", "file.txt")
print(full)  // "data/users/file.txt"

// Get parts of a path
let p = "data/users/profile.json"
print(path.basename(p))    // "profile.json"
print(path.dirname(p))     // "data/users"
print(path.extension(p))   // ".json"

// Split extension
let [name, ext] = path.splitext("photo.jpg")
print(name)  // "photo"
print(ext)   // ".jpg"

// Make absolute path
let abs = path.absolute("myfile.txt")
print(abs)  // "/home/user/project/myfile.txt"

// Normalize path
let messy = "data/../data/./users//file.txt"
let clean = path.normalize(messy)
print(clean)  // "data/users/file.txt"
```

---

## IO Module (Extended)

File system operations beyond read/write.

```sona
import io

// List directory contents
let files = io.list_directory("data")
for file in files {
    print(file)
}

// Check existence
print(io.exists("config.txt"))       // true/false
print(io.is_file("config.txt"))      // true
print(io.is_directory("data"))       // true

// Get file info
let info = io.stat("document.txt")
print(info.size)          // Size in bytes
print(info.modified)      // Last modified time
print(info.created)       // Creation time

// Create directory
io.create_directory("output")
io.create_directory("deep/nested/folder")  // Creates all levels

// Delete
io.delete("temp.txt")              // Delete file
io.delete_directory("old_folder")  // Delete empty directory

// Copy and move
io.copy("original.txt", "backup.txt")
io.move("old.txt", "new.txt")

// Walk directory tree
func listAllFiles(folder) {
    let items = io.list_directory(folder)
    for item in items {
        let full = path.join(folder, item)
        if io.is_directory(full) {
            listAllFiles(full)  // Recurse
        } else {
            print(full)
        }
    }
}
```

---

## HTTP Module

Make web requests.

```sona
import http

// Simple GET request
let response = http.get("https://api.example.com/data")
print(response.status)    // 200
print(response.body)      // Response content

// GET with parameters
let response = http.get("https://api.example.com/search", {
    "query": "sona",
    "limit": 10
})

// POST request
let response = http.post("https://api.example.com/users", {
    "name": "Alice",
    "email": "alice@example.com"
})

// With headers
let response = http.get("https://api.example.com/protected", {
    "headers": {
        "Authorization": "Bearer my-token"
    }
})

// JSON API helper
let data = http.get_json("https://api.example.com/data")
print(data.items)  // Already parsed!
```

### Practical: API Client

```sona
import http
import json

class WeatherAPI {
    func init(api_key) {
        self.api_key = api_key
        self.base_url = "https://api.weather.com"
    }
    
    func get_current(city) {
        let url = "{self.base_url}/current"
        let response = http.get(url, {
            "city": city,
            "key": self.api_key
        })
        
        if response.status == 200 {
            return json.parse(response.body)
        }
        return null
    }
    
    func get_forecast(city, days) {
        let url = "{self.base_url}/forecast"
        let response = http.get(url, {
            "city": city,
            "days": days,
            "key": self.api_key
        })
        
        if response.status == 200 {
            return json.parse(response.body)
        }
        return null
    }
}

let weather = WeatherAPI("my-api-key")
let current = weather.get_current("Seattle")
print("Temperature: {current.temp}°F")
```

---

## Putting It All Together

### Example: Backup Script

```sona
import io
import path
import time
import hashing

func createBackup(sourceDir, backupDir) {
    // Create timestamped backup folder
    let timestamp = time.now().format("%Y%m%d_%H%M%S")
    let backupPath = path.join(backupDir, "backup_" + timestamp)
    io.create_directory(backupPath)
    
    // Copy all files
    let files = io.list_directory(sourceDir)
    let count = 0
    
    for file in files {
        let src = path.join(sourceDir, file)
        let dest = path.join(backupPath, file)
        
        if io.is_file(src) {
            io.copy(src, dest)
            count = count + 1
            print("Backed up: {file}")
        }
    }
    
    // Create manifest
    let manifest = {
        "timestamp": timestamp,
        "source": sourceDir,
        "files_count": count,
        "checksum": createChecksum(backupPath)
    }
    
    io.write(
        path.join(backupPath, "manifest.json"),
        json.stringify(manifest, indent: 2)
    )
    
    print("Backup complete: {count} files")
    return backupPath
}

func createChecksum(folder) {
    let combined = ""
    for file in io.list_directory(folder) {
        let content = io.read(path.join(folder, file))
        combined = combined + hashing.sha256(content)
    }
    return hashing.sha256(combined)
}

// Usage
createBackup("data", "backups")
```

---

## Practice

### Exercise 1
Create a script that lists all `.txt` files in a directory.

### Exercise 2
Make a simple download function using the http module.

### Exercise 3
Create an environment-based configuration system for a web app (PORT, DATABASE_URL, DEBUG).

---

## Module 11 Complete! 🎉

You've explored:
- ✅ Data processing (JSON, CSV, TOML)
- ✅ Utilities (time, random, math, uuid, hashing)
- ✅ System modules (env, path, io, http)

→ Next: [Module 12: Working with Data](../12_data/README.md)
