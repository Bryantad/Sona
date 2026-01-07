# Mini-Lesson 15.2: Functional Programming

## What is Functional Programming?

**Functional programming** = Writing code using functions as building blocks

Key ideas:
- Functions are values (can pass them around)
- Avoid changing data (immutability)
- No side effects (pure functions)

---

## Functions as Values

In Sona, functions are "first-class citizens":

```sona
// Assign function to variable
let greet = func(name) {
    return "Hello, {name}!"
}

print(greet("Alice"))  // Hello, Alice!

// Pass function as argument
func applyTwice(f, x) {
    return f(f(x))
}

func double(n) {
    return n * 2
}

print(applyTwice(double, 5))  // 20 (5→10→20)

// Return function from function
func makeMultiplier(factor) {
    return func(n) {
        return n * factor
    }
}

let triple = makeMultiplier(3)
let quadruple = makeMultiplier(4)

print(triple(10))     // 30
print(quadruple(10))  // 40
```

---

## Closures

A **closure** captures variables from its environment:

```sona
func makeCounter() {
    let count = 0  // This is "captured"
    
    return func() {
        count = count + 1
        return count
    }
}

let counter = makeCounter()
print(counter())  // 1
print(counter())  // 2
print(counter())  // 3

// Each call creates a NEW closure
let counter2 = makeCounter()
print(counter2())  // 1 (independent!)
```

### Practical Closure Example

```sona
func makeCache() {
    let cache = {}
    
    return {
        "get": func(key) {
            return cache[key] if key in cache else null
        },
        "set": func(key, value) {
            cache[key] = value
        },
        "has": func(key) {
            return key in cache
        }
    }
}

let cache = makeCache()
cache.set("user_1", {"name": "Alice"})
print(cache.get("user_1").name)  // Alice
```

---

## Pure Functions

A **pure function**:
- Same input → same output (always!)
- No side effects (doesn't change anything outside)

```sona
// ❌ IMPURE - uses external variable
let total = 0
func addToTotal(n) {
    total = total + n  // Side effect!
    return total
}

// ❌ IMPURE - depends on current time
func isExpired(date) {
    return date < time.now()  // Different result each time!
}

// ✅ PURE - same input = same output
func add(a, b) {
    return a + b
}

// ✅ PURE - no side effects
func calculateTax(price, rate) {
    return price * rate
}
```

### Why Pure Functions?

| Pure | Impure |
|------|--------|
| Easy to test | Hard to test |
| Predictable | Unpredictable |
| Safe to parallelize | May have race conditions |
| Easy to reason about | Hard to debug |

---

## Higher-Order Functions

Functions that take OR return other functions:

### Map, Filter, Reduce

```sona
let numbers = [1, 2, 3, 4, 5]

// MAP: Transform each element
let doubled = numbers.map(func(n) { return n * 2 })
print(doubled)  // [2, 4, 6, 8, 10]

// FILTER: Keep matching elements
let evens = numbers.filter(func(n) { return n % 2 == 0 })
print(evens)  // [2, 4]

// REDUCE: Combine into single value
let sum = numbers.reduce(0, func(total, n) { return total + n })
print(sum)  // 15
```

### Building Your Own

```sona
// Custom map
func myMap(list, transform) {
    let result = []
    for item in list {
        result.push(transform(item))
    }
    return result
}

// Custom filter
func myFilter(list, predicate) {
    let result = []
    for item in list {
        if predicate(item) {
            result.push(item)
        }
    }
    return result
}

// Custom reduce
func myReduce(list, initial, combine) {
    let result = initial
    for item in list {
        result = combine(result, item)
    }
    return result
}
```

---

## Function Composition

Combine small functions into bigger ones:

```sona
// Small, focused functions
func addOne(n) { return n + 1 }
func double(n) { return n * 2 }
func square(n) { return n * n }

// Compose them
func compose(f, g) {
    return func(x) {
        return f(g(x))
    }
}

// Create combined functions
let addOneThenDouble = compose(double, addOne)
print(addOneThenDouble(5))  // (5+1)*2 = 12

let doubleThenSquare = compose(square, double)
print(doubleThenSquare(3))  // (3*2)² = 36
```

### Pipe: Left-to-Right Composition

```sona
func pipe(...functions) {
    return func(x) {
        let result = x
        for f in functions {
            result = f(result)
        }
        return result
    }
}

let process = pipe(addOne, double, square)
print(process(2))  // ((2+1)*2)² = 36

// More readable pipeline
let processUser = pipe(
    func(user) { return user.name },
    func(name) { return name.upper() },
    func(name) { return "Hello, {name}!" }
)

print(processUser({"name": "alice"}))
// "Hello, ALICE!"
```

---

## Partial Application

Fix some arguments now, provide rest later:

```sona
func partial(fn, ...fixedArgs) {
    return func(...remainingArgs) {
        return fn(...fixedArgs, ...remainingArgs)
    }
}

func greet(greeting, name) {
    return "{greeting}, {name}!"
}

let sayHello = partial(greet, "Hello")
let sayGoodbye = partial(greet, "Goodbye")

print(sayHello("Alice"))    // Hello, Alice!
print(sayGoodbye("Bob"))    // Goodbye, Bob!
```

### Practical Example

```sona
func formatMoney(currency, amount) {
    return "{currency}{amount}"
}

let formatUSD = partial(formatMoney, "$")
let formatEUR = partial(formatMoney, "€")
let formatGBP = partial(formatMoney, "£")

print(formatUSD(99.99))  // $99.99
print(formatEUR(99.99))  // €99.99
print(formatGBP(99.99))  // £99.99
```

---

## Currying

Turn a function with multiple args into a chain of single-arg functions:

```sona
// Regular function
func add(a, b, c) {
    return a + b + c
}
print(add(1, 2, 3))  // 6

// Curried version
func curriedAdd(a) {
    return func(b) {
        return func(c) {
            return a + b + c
        }
    }
}

print(curriedAdd(1)(2)(3))  // 6

// Partial application becomes easy
let addOne = curriedAdd(1)
let addOneAndTwo = addOne(2)
print(addOneAndTwo(3))  // 6
```

---

## Immutability

Don't change data, create new data:

```sona
// ❌ Mutating
func addItem(cart, item) {
    cart.items.push(item)  // Changes original!
    return cart
}

// ✅ Immutable
func addItem(cart, item) {
    return {
        ...cart,
        "items": [...cart.items, item]
    }
}

let cart1 = {"items": ["Apple"]}
let cart2 = addItem(cart1, "Banana")

print(cart1.items)  // ["Apple"] - unchanged!
print(cart2.items)  // ["Apple", "Banana"] - new cart
```

### Immutable Updates

```sona
// Update nested object
func updateUser(user, updates) {
    return {
        ...user,
        ...updates
    }
}

// Update item in list
func updateAt(list, index, newValue) {
    return list.map(func(item, i) {
        return newValue if i == index else item
    })
}

// Remove from list
func removeAt(list, index) {
    return list.filter(func(item, i) {
        return i != index
    })
}
```

---

## Complete Example: Data Pipeline

```sona
let orders = [
    {"id": 1, "product": "Widget", "price": 25, "qty": 2, "status": "completed"},
    {"id": 2, "product": "Gadget", "price": 50, "qty": 1, "status": "pending"},
    {"id": 3, "product": "Gizmo", "price": 30, "qty": 3, "status": "completed"},
    {"id": 4, "product": "Widget", "price": 25, "qty": 1, "status": "cancelled"},
    {"id": 5, "product": "Gadget", "price": 50, "qty": 2, "status": "completed"}
]

// Build a data processing pipeline
let processOrders = pipe(
    // Filter completed orders
    func(orders) {
        return orders.filter(func(o) { return o.status == "completed" })
    },
    
    // Add total to each order
    func(orders) {
        return orders.map(func(o) {
            return {...o, "total": o.price * o.qty}
        })
    },
    
    // Calculate summary
    func(orders) {
        return {
            "orderCount": orders.length(),
            "totalRevenue": orders.reduce(0, func(sum, o) { 
                return sum + o.total 
            }),
            "orders": orders
        }
    }
)

let report = processOrders(orders)
print("Completed Orders: {report.orderCount}")
print("Total Revenue: ${report.totalRevenue}")
```

---

## Practice

### Exercise 1
Create a `memoize` function that caches results of expensive functions.

### Exercise 2
Build a validation pipeline using composition:
- Validate email format
- Validate password strength
- Check username availability

### Exercise 3
Create an immutable state manager with `getState`, `setState`, and `subscribe` methods.

---

→ Next: [mini-3: Mastery Path](mini-3_mastery.md)
