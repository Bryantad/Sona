# Mini-Lesson 6.2: Search & Replace

## Finding Text in Strings

Often you need to find something inside text—like searching for a word in a document.

---

## Checking If Text Exists

### `contains()` - Yes or No

```sona
let sentence = "The quick brown fox jumps over the lazy dog"

print(sentence.contains("fox"))     // true
print(sentence.contains("cat"))     // false
print(sentence.contains("FOX"))     // false (case-sensitive!)
```

**For case-insensitive search:**
```sona
print(sentence.lower().contains("fox"))  // true
```

---

## Finding Position

### `index_of()` - Where Is It?

```sona
let text = "Hello, World!"

print(text.index_of("World"))   // 7 (starts at position 7)
print(text.index_of("o"))       // 4 (first 'o' found)
print(text.index_of("xyz"))     // -1 (not found)
```

### Finding All Occurrences

```sona
let text = "banana"
let positions = []
let pos = 0

while true {
    pos = text.index_of("a", pos)
    if pos == -1 {
        break
    }
    positions.push(pos)
    pos = pos + 1
}

print(positions)  // [1, 3, 5]
```

---

## Counting Occurrences

```sona
let text = "she sells sea shells"

print(text.count("s"))      // 5
print(text.count("she"))    // 2
print(text.count("z"))      // 0
```

---

## Replacing Text

### `replace()` - Swap Text

```sona
let greeting = "Hello, World!"

let newGreeting = greeting.replace("World", "Sona")
print(newGreeting)  // "Hello, Sona!"
```

**Note:** `replace()` creates a NEW string. The original stays the same.

```sona
let text = "I like cats"
text.replace("cats", "dogs")
print(text)  // Still "I like cats"!

// Do this instead:
text = text.replace("cats", "dogs")
print(text)  // "I like dogs"
```

### Replace All Occurrences

```sona
let text = "one fish, two fish, red fish, blue fish"
let newText = text.replace_all("fish", "bird")
print(newText)  // "one bird, two bird, red bird, blue bird"
```

---

## Starts With / Ends With

Perfect for checking file types, URLs, etc.

```sona
let filename = "document.pdf"

if filename.ends_with(".pdf") {
    print("This is a PDF file")
}

let url = "https://example.com"

if url.starts_with("https://") {
    print("Secure connection")
}
```

---

## Splitting Strings

Turn a string into a list by splitting on a separator:

```sona
let sentence = "apple,banana,cherry"
let fruits = sentence.split(",")
print(fruits)  // ["apple", "banana", "cherry"]

let words = "Hello World".split(" ")
print(words)  // ["Hello", "World"]
```

### Split by Lines

```sona
let multiline = "Line 1\nLine 2\nLine 3"
let lines = multiline.split("\n")
print(lines)  // ["Line 1", "Line 2", "Line 3"]
```

---

## Joining Lists into Strings

The opposite of split:

```sona
let words = ["Hello", "World"]
let sentence = words.join(" ")
print(sentence)  // "Hello World"

let path = ["users", "john", "documents"]
let filepath = path.join("/")
print(filepath)  // "users/john/documents"
```

---

## Practical Examples

### Example 1: Censor a Word
```sona
let comment = "This is a bad example of bad code"
let censored = comment.replace_all("bad", "***")
print(censored)  // "This is a *** example of *** code"
```

### Example 2: Extract Username from Email
```sona
let email = "john.doe@example.com"
let parts = email.split("@")
let username = parts[0]
print(username)  // "john.doe"
```

### Example 3: Check File Extension
```sona
func isImage(filename) {
    let lower = filename.lower()
    return lower.ends_with(".jpg") or 
           lower.ends_with(".png") or 
           lower.ends_with(".gif")
}

print(isImage("photo.JPG"))   // true
print(isImage("document.pdf")) // false
```

---

## Practice

### Exercise 1
Replace all spaces in `"hello world program"` with underscores.

### Exercise 2
Split the string `"red;green;blue"` by semicolons and print each color.

### Exercise 3
Check if the URL `"http://example.com"` starts with "https://". If not, print a warning.

<details>
<summary>Exercise 3 Answer</summary>

```sona
let url = "http://example.com"

if not url.starts_with("https://") {
    print("Warning: Not a secure connection!")
}
```

</details>

---

## Summary

| Operation | Code | Result |
|-----------|------|--------|
| Contains | `s.contains("x")` | true/false |
| Find | `s.index_of("x")` | Position or -1 |
| Count | `s.count("x")` | Number found |
| Replace | `s.replace("a", "b")` | New string |
| Replace all | `s.replace_all("a", "b")` | All replaced |
| Starts with | `s.starts_with("x")` | true/false |
| Ends with | `s.ends_with("x")` | true/false |
| Split | `s.split(",")` | List |
| Join | `list.join(",")` | String |

---

→ Next: [mini-3: Formatting](mini-3_formatting.md)
