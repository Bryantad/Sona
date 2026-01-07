# Mini-Lesson 11.2: Utility Modules

## Time Module

Work with dates, times, and durations.

```sona
import time

// Current time
let now = time.now()
print(now)  // 2024-01-15 14:30:45

// Timestamps
let timestamp = time.timestamp()  // Unix timestamp (seconds)
print(timestamp)  // 1705329045

// Format dates
print(now.format("%Y-%m-%d"))       // "2024-01-15"
print(now.format("%H:%M:%S"))       // "14:30:45"
print(now.format("%B %d, %Y"))      // "January 15, 2024"

// Parse date strings
let date = time.parse("2024-12-25", "%Y-%m-%d")

// Sleep (pause execution)
print("Starting...")
time.sleep(2)  // Wait 2 seconds
print("Done!")

// Date components
print(now.year)    // 2024
print(now.month)   // 1
print(now.day)     // 15
print(now.hour)    // 14
print(now.minute)  // 30
print(now.weekday) // "Monday"
```

### Timer for Performance

```sona
import timer

// Measure execution time
let t = timer.start()

// ... do some work ...
repeat 1000000 {
    let x = 1 + 1
}

let elapsed = timer.stop(t)
print("Took {elapsed} seconds")
```

---

## Random Module

Generate random values.

```sona
import random

// Random float (0.0 to 1.0)
let r = random.random()
print(r)  // 0.7234...

// Random integer in range
let num = random.randint(1, 100)
print(num)  // 42 (any number 1-100)

// Random choice from list
let colors = ["red", "green", "blue"]
let pick = random.choice(colors)
print(pick)  // "green"

// Shuffle list (in place)
let deck = [1, 2, 3, 4, 5]
random.shuffle(deck)
print(deck)  // [3, 1, 5, 2, 4]

// Random sample (pick N items)
let winners = random.sample(["A", "B", "C", "D", "E"], 2)
print(winners)  // ["C", "A"]

// Random with seed (reproducible)
random.seed(42)
print(random.randint(1, 100))  // Always 51 with seed 42
```

### Practical: Password Generator

```sona
import random
import string

func generatePassword(length = 12) {
    let chars = "abcdefghijklmnopqrstuvwxyz"
    chars = chars + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chars = chars + "0123456789"
    chars = chars + "!@#$%^&*"
    
    let password = ""
    repeat length {
        let index = random.randint(0, chars.length() - 1)
        password = password + chars[index]
    }
    return password
}

print(generatePassword())     // "kJ8#mPx2Qw$n"
print(generatePassword(20))   // "Hj9@kL2$mNpQrS5&tUvW"
```

---

## Math Module

Mathematical operations.

```sona
import math

// Constants
print(math.pi)   // 3.14159265359
print(math.e)    // 2.71828182846

// Basic functions
print(math.abs(-5))      // 5
print(math.round(3.7))   // 4
print(math.floor(3.9))   // 3
print(math.ceil(3.1))    // 4

// Powers and roots
print(math.pow(2, 8))    // 256
print(math.sqrt(16))     // 4

// Min/Max
print(math.min(5, 3, 8)) // 3
print(math.max(5, 3, 8)) // 8

// Trigonometry
print(math.sin(math.pi / 2))  // 1.0
print(math.cos(0))            // 1.0

// Logarithms
print(math.log(100))     // 4.605... (natural log)
print(math.log10(100))   // 2.0

// Clamp value to range
func clamp(value, min, max) {
    return math.max(min, math.min(value, max))
}
print(clamp(150, 0, 100))  // 100
```

---

## UUID Module

Generate unique identifiers.

```sona
import uuid

// Generate random UUID
let id = uuid.generate()
print(id)  // "550e8400-e29b-41d4-a716-446655440000"

// Another one (always different)
let id2 = uuid.generate()
print(id2)  // "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

// Check if valid UUID
print(uuid.is_valid("550e8400-e29b-41d4-a716-446655440000"))  // true
print(uuid.is_valid("not-a-uuid"))  // false
```

### Practical: Creating Records

```sona
import uuid
import time

func createUser(name, email) {
    return {
        "id": uuid.generate(),
        "name": name,
        "email": email,
        "created_at": time.now().format("%Y-%m-%d %H:%M:%S")
    }
}

let user = createUser("Alice", "alice@email.com")
print(user)
// {
//   "id": "a1b2c3d4-...",
//   "name": "Alice",
//   "email": "alice@email.com",
//   "created_at": "2024-01-15 14:30:45"
// }
```

---

## Hashing Module

Create secure hashes (one-way).

```sona
import hashing

// SHA-256 (most common, secure)
let hash = hashing.sha256("my secret password")
print(hash)  // "5e884898da28047d..."

// MD5 (fast, less secure)
let md5 = hashing.md5("hello")
print(md5)  // "5d41402abc4b2a76..."

// SHA-512 (more secure)
let sha512 = hashing.sha512("data")
print(sha512)

// Hash a file
let fileHash = hashing.sha256_file("document.pdf")
```

### Practical: Password Verification

```sona
import hashing

func hashPassword(password) {
    // Add salt for security
    let salt = "random_salt_here"
    return hashing.sha256(salt + password)
}

func verifyPassword(password, storedHash) {
    return hashPassword(password) == storedHash
}

// Registration
let hash = hashPassword("myPassword123")
// Store hash in database

// Login
if verifyPassword("myPassword123", hash) {
    print("Login successful!")
} else {
    print("Invalid password")
}
```

---

## Validation Module

Validate common data formats.

```sona
import validation

// Email
print(validation.is_email("user@example.com"))  // true
print(validation.is_email("invalid"))            // false

// URL
print(validation.is_url("https://example.com")) // true

// Phone (basic)
print(validation.is_phone("555-123-4567"))      // true

// Number formats
print(validation.is_numeric("12345"))           // true
print(validation.is_numeric("12.34"))           // true
print(validation.is_numeric("abc"))             // false

// Custom pattern
print(validation.matches("ABC123", "^[A-Z]+[0-9]+$"))  // true
```

---

## Practice

### Exercise 1
Create a function that generates a random 6-digit verification code.

### Exercise 2
Create a function that measures how long it takes to run another function.

### Exercise 3
Build a simple user registration that:
- Generates a UUID for user ID
- Hashes the password
- Records the signup timestamp

---

→ Next: [mini-3: System & Network](mini-3_system.md)
