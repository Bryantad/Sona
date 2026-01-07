# Mini-Episode 7.3: Nested Data

## Script

### Intro (0:00 - 0:15)
"Real-world data is often nested - dictionaries inside dictionaries, lists inside dictionaries!"

### Nested Dictionaries (0:15 - 1:30)
```sona
let user = {
    "name": "Alice",
    "address": {
        "street": "123 Main St",
        "city": "Boston",
        "zip": "02101"
    },
    "contact": {
        "email": "alice@example.com",
        "phone": "555-1234"
    }
}

print(user.name)              // Alice
print(user.address.city)      // Boston
print(user.contact.email)     // alice@example.com
```

### Lists in Dictionaries (1:30 - 2:30)
```sona
let student = {
    "name": "Bob",
    "grades": [85, 92, 78, 95],
    "subjects": ["Math", "Science", "English"]
}

print(student.grades[0])     // 85
print(student.subjects[1])   // Science

// Add a grade
student.grades.push(88)
```

### List of Dictionaries (2:30 - 3:30)
```sona
let users = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Carol", "age": 28}
]

for user in users {
    print(user.name + " is " + str(user.age))
}

// Find specific user
for user in users {
    if user.name == "Bob" {
        print("Found Bob! Age: " + str(user.age))
    }
}
```

### Complex Real-World Example (3:30 - 4:30)
```sona
let order = {
    "id": "ORD-001",
    "customer": {
        "name": "Alice",
        "email": "alice@example.com"
    },
    "items": [
        {"product": "Widget", "qty": 2, "price": 25.00},
        {"product": "Gadget", "qty": 1, "price": 50.00}
    ],
    "total": 100.00
}

print("Order for: " + order.customer.name)
for item in order.items {
    print("- {item.product} x{item.qty}: ${item.price * item.qty}")
}
```

### Outro (4:30 - 5:00)
"Nested data models real-world information. Access with chained dots: user.address.city"
