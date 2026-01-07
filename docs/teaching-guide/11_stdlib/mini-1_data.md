# Mini-Lesson 11.1: Data Processing Modules

## JSON Module

JSON (JavaScript Object Notation) is the most common data format. Use it for:
- Configuration files
- API responses
- Data storage

```sona
import json

// Parse JSON string to object
let text = '{"name": "Alex", "age": 25, "active": true}'
let data = json.parse(text)

print(data.name)    // "Alex"
print(data.age)     // 25
print(data.active)  // true

// Convert object to JSON string
let person = {
    "name": "Jordan",
    "scores": [100, 95, 87]
}
let jsonText = json.stringify(person)
print(jsonText)  // '{"name": "Jordan", "scores": [100, 95, 87]}'

// Pretty print (formatted)
let pretty = json.stringify(person, indent: 2)
print(pretty)
// {
//   "name": "Jordan",
//   "scores": [100, 95, 87]
// }
```

### JSON File Operations

```sona
import json
import io

// Save data to JSON file
let settings = {
    "theme": "dark",
    "volume": 80,
    "notifications": true
}
io.write("settings.json", json.stringify(settings, indent: 2))

// Load data from JSON file
let loaded = json.parse(io.read("settings.json"))
print(loaded.theme)  // "dark"
```

---

## CSV Module

CSV (Comma-Separated Values) is perfect for spreadsheet-like data.

```sona
import csv

// Parse CSV string
let text = "name,age,city\nAlice,25,NYC\nBob,30,LA"
let data = csv.parse(text)

for row in data {
    print("{row.name} is {row.age} from {row.city}")
}

// Create CSV
let people = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30}
]
let csvText = csv.stringify(people)
print(csvText)
// name,age
// Alice,25
// Bob,30
```

### CSV File Operations

```sona
import csv
import io

// Read CSV file
let content = io.read("students.csv")
let students = csv.parse(content)

// Process and calculate
let total = 0
for student in students {
    total = total + int(student.grade)
}
print("Average: " + (total / students.length()))

// Write CSV file
let results = [
    {"test": "Math", "score": 95},
    {"test": "English", "score": 88}
]
io.write("results.csv", csv.stringify(results))
```

---

## TOML Module

TOML is great for configuration files (cleaner than JSON).

```toml
# config.toml
title = "My App"

[database]
host = "localhost"
port = 5432

[features]
dark_mode = true
notifications = false
```

```sona
import toml
import io

// Read TOML config
let config = toml.parse(io.read("config.toml"))

print(config.title)             // "My App"
print(config.database.host)     // "localhost"
print(config.features.dark_mode) // true

// Create TOML
let settings = {
    "app": "MyApp",
    "version": "1.0",
    "debug": false
}
let tomlText = toml.stringify(settings)
```

---

## Encoding Module

Convert data to/from different formats.

```sona
import encoding

// Base64
let encoded = encoding.base64_encode("Hello, World!")
print(encoded)  // "SGVsbG8sIFdvcmxkIQ=="

let decoded = encoding.base64_decode(encoded)
print(decoded)  // "Hello, World!"

// Hex encoding
let hex = encoding.hex_encode("ABC")
print(hex)  // "414243"

let text = encoding.hex_decode("414243")
print(text)  // "ABC"

// URL encoding
let url = encoding.url_encode("hello world")
print(url)  // "hello%20world"

let original = encoding.url_decode("hello%20world")
print(original)  // "hello world"
```

---

## Practical Example: Data Pipeline

```sona
import json
import csv
import io

// 1. Read CSV data
let csvData = csv.parse(io.read("sales.csv"))

// 2. Process and transform
let processed = []
for row in csvData {
    processed.push({
        "product": row.product,
        "revenue": int(row.quantity) * float(row.price),
        "date": row.date
    })
}

// 3. Calculate totals
let totalRevenue = 0
for item in processed {
    totalRevenue = totalRevenue + item.revenue
}

// 4. Create summary
let summary = {
    "total_transactions": processed.length(),
    "total_revenue": totalRevenue,
    "transactions": processed
}

// 5. Save as JSON
io.write("sales_report.json", json.stringify(summary, indent: 2))
print("Report generated!")
```

---

## Practice

### Exercise 1
Parse this JSON and print each person's name:
```json
{"people": [{"name": "Alice"}, {"name": "Bob"}]}
```

### Exercise 2
Create a CSV string from this data:
```sona
let items = [
    {"product": "Apple", "price": 1.50},
    {"product": "Banana", "price": 0.75}
]
```

### Exercise 3
Create a config file system that loads from TOML if available, otherwise uses defaults.

---

→ Next: [mini-2: Utilities](mini-2_utilities.md)
