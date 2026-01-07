# Mini-Lesson 12.3: Data Transformation

## The Three Core Operations

Most data processing uses three patterns:

| Operation | Purpose | Example |
|-----------|---------|---------|
| **Filter** | Keep matching items | Active users only |
| **Map** | Transform each item | Get just names |
| **Reduce** | Combine into one | Sum all prices |

---

## Filter: Keep What You Need

```sona
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Keep only even numbers
let evens = numbers.filter(func(n) {
    return n % 2 == 0
})
print(evens)  // [2, 4, 6, 8, 10]

// Keep numbers greater than 5
let big = numbers.filter(func(n) { return n > 5 })
print(big)  // [6, 7, 8, 9, 10]
```

### Real Example: Filter Users

```sona
let users = [
    {"name": "Alice", "active": true, "age": 25},
    {"name": "Bob", "active": false, "age": 30},
    {"name": "Carol", "active": true, "age": 17},
    {"name": "Dave", "active": true, "age": 45}
]

// Active users only
let active = users.filter(func(u) { return u.active })

// Adults only
let adults = users.filter(func(u) { return u.age >= 18 })

// Active adults
let activeAdults = users.filter(func(u) {
    return u.active and u.age >= 18
})
```

---

## Map: Transform Data

```sona
let numbers = [1, 2, 3, 4, 5]

// Double each number
let doubled = numbers.map(func(n) {
    return n * 2
})
print(doubled)  // [2, 4, 6, 8, 10]

// Square each number
let squared = numbers.map(func(n) { return n * n })
print(squared)  // [1, 4, 9, 16, 25]
```

### Real Example: Extract Fields

```sona
let users = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
]

// Get just names
let names = users.map(func(u) { return u.name })
print(names)  // ["Alice", "Bob"]

// Format for display
let display = users.map(func(u) {
    return "{u.name} <{u.email}>"
})
print(display)  // ["Alice <alice@example.com>", "Bob <bob@example.com>"]
```

---

## Reduce: Combine Into One

```sona
let numbers = [1, 2, 3, 4, 5]

// Sum all numbers
let sum = numbers.reduce(0, func(total, n) {
    return total + n
})
print(sum)  // 15

// Multiply all numbers
let product = numbers.reduce(1, func(total, n) {
    return total * n
})
print(product)  // 120

// Find maximum
let max = numbers.reduce(numbers[0], func(biggest, n) {
    if n > biggest { return n }
    return biggest
})
print(max)  // 5
```

### Real Example: Calculate Total

```sona
let cart = [
    {"item": "Apple", "price": 1.50, "qty": 3},
    {"item": "Bread", "price": 2.50, "qty": 1},
    {"item": "Milk", "price": 3.00, "qty": 2}
]

let total = cart.reduce(0, func(sum, item) {
    return sum + (item.price * item.qty)
})
print("Total: $" + total)  // "Total: $12.50"
```

---

## Chaining Operations

Combine filter, map, and reduce:

```sona
let orders = [
    {"product": "A", "price": 100, "status": "completed"},
    {"product": "B", "price": 50, "status": "pending"},
    {"product": "C", "price": 200, "status": "completed"},
    {"product": "D", "price": 75, "status": "completed"}
]

// Total revenue from completed orders
let revenue = orders
    .filter(func(o) { return o.status == "completed" })
    .map(func(o) { return o.price })
    .reduce(0, func(sum, p) { return sum + p })

print("Revenue: $" + revenue)  // "Revenue: $375"
```

---

## Sorting

```sona
let numbers = [3, 1, 4, 1, 5, 9, 2, 6]

// Sort ascending
let sorted = numbers.sort()
print(sorted)  // [1, 1, 2, 3, 4, 5, 6, 9]

// Sort descending
let descending = numbers.sort(reverse: true)
print(descending)  // [9, 6, 5, 4, 3, 2, 1, 1]

// Sort by custom key
let users = [
    {"name": "Charlie", "age": 30},
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 35}
]

// Sort by age
let byAge = users.sort(key: func(u) { return u.age })

// Sort by name
let byName = users.sort(key: func(u) { return u.name })
```

---

## Grouping Data

```sona
func groupBy(items, key) {
    let groups = {}
    for item in items {
        let groupKey = item[key]
        if groupKey not in groups {
            groups[groupKey] = []
        }
        groups[groupKey].push(item)
    }
    return groups
}

let sales = [
    {"product": "Apple", "region": "North", "amount": 100},
    {"product": "Banana", "region": "South", "amount": 150},
    {"product": "Apple", "region": "South", "amount": 200},
    {"product": "Banana", "region": "North", "amount": 75}
]

let byRegion = groupBy(sales, "region")
print(byRegion["North"])  // [{Apple, North}, {Banana, North}]

let byProduct = groupBy(sales, "product")
print(byProduct["Apple"])  // [{Apple, North}, {Apple, South}]
```

---

## Complete Example: Sales Report

```sona
let sales = [
    {"date": "2024-01-01", "product": "Widget", "qty": 10, "price": 25.00, "region": "North"},
    {"date": "2024-01-01", "product": "Gadget", "qty": 5, "price": 50.00, "region": "South"},
    {"date": "2024-01-02", "product": "Widget", "qty": 15, "price": 25.00, "region": "South"},
    {"date": "2024-01-02", "product": "Gizmo", "qty": 3, "price": 100.00, "region": "North"},
    {"date": "2024-01-03", "product": "Widget", "qty": 20, "price": 25.00, "region": "North"}
]

// Calculate revenue per sale
let withRevenue = sales.map(func(s) {
    return {
        ...s,
        "revenue": s.qty * s.price
    }
})

// Total revenue
let totalRevenue = withRevenue
    .map(func(s) { return s.revenue })
    .reduce(0, func(sum, r) { return sum + r })

print("Total Revenue: ${totalRevenue}")

// Revenue by region
let byRegion = groupBy(withRevenue, "region")
for region, items in byRegion.items() {
    let regionTotal = items
        .map(func(s) { return s.revenue })
        .reduce(0, func(sum, r) { return sum + r })
    print("{region}: ${regionTotal}")
}

// Top selling product
let byProduct = groupBy(withRevenue, "product")
let productTotals = []
for product, items in byProduct.items() {
    let total = items.reduce(0, func(sum, s) { return sum + s.qty })
    productTotals.push({"product": product, "total": total})
}
let topProduct = productTotals.sort(key: func(p) { return -p.total })[0]
print("Top Product: {topProduct.product} ({topProduct.total} units)")
```

---

## Practice

### Exercise 1
Given a list of numbers, find the sum of all even numbers.

### Exercise 2
Given a list of products, get the names of all products under $20.

### Exercise 3
Create a report from order data:
- Total orders
- Total revenue
- Average order value
- Orders by status (pending, completed, cancelled)

---

## Module 12 Complete! 🎉

You've learned:
- ✅ Fetching data from APIs
- ✅ Storing data persistently
- ✅ Transforming data with filter, map, reduce

→ Next: [Module 13: Building Projects](../13_projects/README.md)
