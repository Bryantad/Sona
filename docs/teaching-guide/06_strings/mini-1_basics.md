# Mini-Lesson 6.1: String Basics

## What is a String?

A **string** is text—any combination of letters, numbers, symbols, or spaces wrapped in quotes.

```sona
let greeting = "Hello!"
let number_text = "42"      // This is text, not a number!
let mixed = "Room 101"
let empty = ""              // Empty string (valid!)
```

---

## Creating Strings

### Single or Double Quotes

```sona
let single = 'Hello'
let double = "Hello"
// Both work the same way
```

### Multi-line Strings

```sona
let poem = """
Roses are red,
Violets are blue,
Sona is fun,
And so are you!
"""
```

---

## Accessing Characters

Strings are like lists of characters:

```sona
let word = "Hello"
//          01234  (index positions)

print(word[0])    // "H"
print(word[1])    // "e"
print(word[-1])   // "o" (last character)
```

### Getting Substrings (Slices)

```sona
let text = "Hello, World!"

print(text[0:5])    // "Hello" (index 0 to 4)
print(text[7:12])   // "World"
print(text[7:])     // "World!" (from 7 to end)
print(text[:5])     // "Hello" (from start to 4)
```

---

## String Length

```sona
let message = "Hello"
print(message.length())  // 5
```

**Note:** Spaces count!
```sona
let spaced = "Hi there"
print(spaced.length())   // 8 (including the space)
```

---

## Concatenation (Joining)

### Using `+`

```sona
let first = "Hello"
let second = "World"
let combined = first + ", " + second + "!"
print(combined)  // "Hello, World!"
```

### Building Up Strings

```sona
let result = ""
result = result + "Line 1\n"
result = result + "Line 2\n"
result = result + "Line 3"
print(result)
```

---

## Case Conversion

```sona
let text = "Hello World"

print(text.upper())        // "HELLO WORLD"
print(text.lower())        // "hello world"
print(text.capitalize())   // "Hello world"
print(text.title())        // "Hello World"
```

---

## Trimming Whitespace

Remove extra spaces from ends:

```sona
let messy = "   Hello   "

print(messy.trim())    // "Hello" (both sides)
print(messy.ltrim())   // "Hello   " (left only)
print(messy.rtrim())   // "   Hello" (right only)
```

---

## Checking String Content

```sona
let email = "user@example.com"

// Starts/Ends with
print(email.starts_with("user"))    // true
print(email.ends_with(".com"))      // true

// Contains
print(email.contains("@"))          // true

// Is empty?
print(email.is_empty())             // false
print("".is_empty())                // true
```

---

## Special Characters

Use backslash `\` for special characters:

| Code | Meaning |
|------|---------|
| `\n` | New line |
| `\t` | Tab |
| `\\` | Backslash |
| `\"` | Quote inside quotes |

```sona
print("Line 1\nLine 2")
// Output:
// Line 1
// Line 2

print("She said \"Hello\"")
// Output: She said "Hello"
```

---

## Practice

### Exercise 1
Create a string with your full name. Print just your first name using slicing.

### Exercise 2
What will this print?
```sona
let s = "Programming"
print(s[0])
print(s[-1])
print(s.length())
```

<details>
<summary>Answer</summary>

```
P
g
11
```

</details>

### Exercise 3
Take the string `"  hello world  "` and print it trimmed and in title case.

---

## Summary

| Operation | Code | Result |
|-----------|------|--------|
| Create | `"Hello"` | String |
| Access char | `s[0]` | First character |
| Slice | `s[0:5]` | Substring |
| Length | `s.length()` | Number of chars |
| Join | `a + b` | Combined string |
| Upper | `s.upper()` | Uppercase |
| Lower | `s.lower()` | Lowercase |
| Trim | `s.trim()` | Remove whitespace |

---

→ Next: [mini-2: Search & Replace](mini-2_search_replace.md)
