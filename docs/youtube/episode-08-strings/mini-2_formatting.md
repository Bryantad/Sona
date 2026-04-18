# Mini-Episode 8.2: String Formatting 📝

> Put variables inside strings beautifully

---

## Why Format Strings?

Instead of this mess:
```sona
let name = "Alex"
let age = 25
print("Hello " + name + "! You are " + str(age) + " years old.")
```

Do this:
```sona
print(f"Hello {name}! You are {age} years old.")
```

**Much cleaner!**

---

## F-Strings (Formatted Strings)

Put `f` before your string, then use `{curly braces}` for variables:

```sona
let item = "coffee"
let price = 4.50

print(f"Your {item} costs ${price}")
// Output: Your coffee costs $4.50
```

---

## Expressions in F-Strings

You can do math inside the braces!

```sona
let width = 5
let height = 3

print(f"Area: {width * height} square units")
// Output: Area: 15 square units
```

---

## Formatting Numbers

```sona
let pi = 3.14159265359

// 2 decimal places
print(f"Pi is approximately {pi:.2f}")
// Output: Pi is approximately 3.14

// With commas for big numbers
let population = 1000000
print(f"Population: {population:,}")
// Output: Population: 1,000,000
```

---

## Alignment and Padding

```sona
let product = "Apple"
let price = 1.50

// Right align in 10 characters
print(f"{product:>10} = ${price}")
//      Apple = $1.5

// Left align
print(f"{product:<10} = ${price}")
// Apple      = $1.5

// Center
print(f"{product:^10} = ${price}")
//   Apple    = $1.5
```

---

## Practical Example: Receipt

```sona
func print_receipt(items) {
    print("=" * 30)
    print(f"{'RECEIPT':^30}")
    print("=" * 30)
    
    let total = 0
    for item in items {
        print(f"{item['name']:<20} ${item['price']:.2f}")
        total = total + item['price']
    }
    
    print("-" * 30)
    print(f"{'TOTAL:':<20} ${total:.2f}")
}
```

---

## Quick Formatting Cheatsheet

| Format | Example | Result |
|--------|---------|--------|
| `{x}` | `{name}` | Alex |
| `{x:.2f}` | `{3.14159:.2f}` | 3.14 |
| `{x:,}` | `{1000000:,}` | 1,000,000 |
| `{x:>10}` | `{name:>10}` | "      Alex" |
| `{x:<10}` | `{name:<10}` | "Alex      " |
| `{x:^10}` | `{name:^10}` | "   Alex   " |
