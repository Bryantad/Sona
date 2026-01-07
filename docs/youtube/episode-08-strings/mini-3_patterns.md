# Mini-Episode 8.3: String Patterns 🎯

> Common string operations you'll use everywhere

---

## Pattern 1: Input Validation

```sona
func validate_email(email) {
    // Simple check - contains @ and .
    if "@" in email and "." in email {
        return true
    }
    return false
}

// Test it
print(validate_email("user@example.com"))  // true
print(validate_email("not-an-email"))      // false
```

---

## Pattern 2: Building Strings

```sona
// Bad: String concatenation in loop (slow)
let result = ""
for i in range(5) {
    result = result + str(i) + ","  // Creates new string each time!
}

// Good: Use a list and join
let parts = []
for i in range(5) {
    parts.append(str(i))
}
let result = ",".join(parts)  // Much faster!
```

---

## Pattern 3: Parsing Data

```sona
// Parse a CSV line
let line = "John,25,Engineer"
let parts = line.split(",")

let name = parts[0]
let age = int(parts[1])
let job = parts[2]

print(f"{name} is a {age}-year-old {job}")
```

---

## Pattern 4: Text Search

```sona
func find_hashtags(text) {
    let hashtags = []
    let words = text.split(" ")
    
    for word in words {
        if word.startswith("#") {
            hashtags.append(word)
        }
    }
    return hashtags
}

let tweet = "Learning #Sona is fun! #coding #programming"
print(find_hashtags(tweet))
// ["#Sona", "#coding", "#programming"]
```

---

## Pattern 5: Text Cleanup

```sona
func clean_text(text) {
    // Remove extra whitespace
    let cleaned = text.strip()
    
    // Replace multiple spaces with single
    while "  " in cleaned {
        cleaned = cleaned.replace("  ", " ")
    }
    
    return cleaned
}

let messy = "   Hello    World!   "
print(clean_text(messy))  // "Hello World!"
```

---

## Pattern 6: Word Counter

```sona
func count_words(text) {
    let words = text.lower().split()
    let counts = {}
    
    for word in words {
        if word in counts {
            counts[word] = counts[word] + 1
        } else {
            counts[word] = 1
        }
    }
    return counts
}

let story = "the cat sat on the mat"
print(count_words(story))
// {"the": 2, "cat": 1, "sat": 1, "on": 1, "mat": 1}
```

---

## Common String Checks

```sona
let text = "Hello123"

// Check what string contains
print(text.isalpha())    // false (has numbers)
print(text.isdigit())    // false (has letters)
print(text.isalnum())    // true (letters + numbers OK)

print(text.startswith("He"))  // true
print(text.endswith("23"))    // true
```

---

## Challenge: Username Validator

```sona
func is_valid_username(username) {
    // Rules:
    // - 3-20 characters
    // - Only letters, numbers, underscore
    // - Must start with letter
    
    let length_ok = len(username) >= 3 and len(username) <= 20
    let starts_ok = username[0].isalpha()
    
    // Check each character
    for char in username {
        if not (char.isalnum() or char == "_") {
            return false
        }
    }
    
    return length_ok and starts_ok
}
```
