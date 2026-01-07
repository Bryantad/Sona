# Mini-Episode 6.3: List Patterns

## Script

### Intro (0:00 - 0:15)
"Let's see common patterns for working with lists!"

### Sum All Items (0:15 - 1:00)
```sona
let numbers = [10, 20, 30, 40, 50]
let total = 0

for num in numbers {
    total = total + num
}
print(total)  // 150
```

### Find Maximum (1:00 - 1:45)
```sona
let scores = [85, 92, 78, 95, 88]
let highest = scores[0]

for score in scores {
    if score > highest {
        highest = score
    }
}
print(highest)  // 95
```

### Filter Items (1:45 - 2:30)
```sona
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
let evens = []

for n in numbers {
    if n % 2 == 0 {
        evens.push(n)
    }
}
print(evens)  // [2, 4, 6, 8, 10]
```

### Transform Items (2:30 - 3:15)
```sona
let prices = [10, 20, 30]
let withTax = []

for price in prices {
    withTax.push(price * 1.1)
}
print(withTax)  // [11, 22, 33]
```

### Using Built-in Methods (3:15 - 4:30)
```sona
let numbers = [1, 2, 3, 4, 5]

// Even cleaner with methods!
let doubled = numbers.map(func(n) { return n * 2 })
let evens = numbers.filter(func(n) { return n % 2 == 0 })
let sum = numbers.reduce(0, func(a, b) { return a + b })

print(doubled)  // [2, 4, 6, 8, 10]
print(evens)    // [2, 4]
print(sum)      // 15
```

### Outro (4:30 - 5:00)
"These patterns solve most list problems. Practice them!"
