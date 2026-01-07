# Mini-Lesson 15.1: Design Patterns

## What Are Design Patterns?

**Design patterns** = Proven solutions to common problems

Like recipes for programmers - you don't reinvent the wheel!

---

## Pattern 1: Singleton

**Problem:** Need exactly ONE instance of something (database, config, logger)

**Solution:** The Singleton pattern

```sona
class Database {
    // Class-level variable
    static instance = null
    
    func init() {
        self.connected = false
        self.data = {}
    }
    
    static func getInstance() {
        if Database.instance == null {
            Database.instance = Database()
        }
        return Database.instance
    }
    
    func connect() {
        self.connected = true
        print("Database connected!")
    }
    
    func query(sql) {
        if !self.connected {
            self.connect()
        }
        return "Result for: " + sql
    }
}

// Usage - always get the SAME instance
let db1 = Database.getInstance()
let db2 = Database.getInstance()

// db1 and db2 are the SAME object!
db1.connect()
print(db2.connected)  // true - same instance!
```

### Simple Singleton Alternative

```sona
// Just use a module as singleton
// database.sona

let _connected = false
let _data = {}

func connect() {
    _connected = true
}

func query(sql) {
    if !_connected { connect() }
    return "Result for: " + sql
}

// Usage
import "database" as db
db.connect()
```

---

## Pattern 2: Factory

**Problem:** Create different objects based on input

**Solution:** The Factory pattern

```sona
// Base class
class Animal {
    func speak() {
        return "..."
    }
}

class Dog extends Animal {
    func speak() {
        return "Woof!"
    }
}

class Cat extends Animal {
    func speak() {
        return "Meow!"
    }
}

class Bird extends Animal {
    func speak() {
        return "Tweet!"
    }
}

// The Factory
class AnimalFactory {
    static func create(type) {
        match type.lower() {
            "dog" => return Dog()
            "cat" => return Cat()
            "bird" => return Bird()
            _ => {
                print("Unknown animal: " + type)
                return Animal()
            }
        }
    }
}

// Usage
let pet1 = AnimalFactory.create("dog")
let pet2 = AnimalFactory.create("cat")

print(pet1.speak())  // Woof!
print(pet2.speak())  // Meow!

// Works with user input
let choice = input("What pet? ")
let pet = AnimalFactory.create(choice)
print(pet.speak())
```

### Factory with Configuration

```sona
class ButtonFactory {
    static func create(style) {
        let button = {}
        
        match style {
            "primary" => {
                button.color = "blue"
                button.textColor = "white"
                button.size = "large"
            }
            "secondary" => {
                button.color = "gray"
                button.textColor = "black"
                button.size = "medium"
            }
            "danger" => {
                button.color = "red"
                button.textColor = "white"
                button.size = "medium"
            }
            _ => {
                button.color = "white"
                button.textColor = "black"
                button.size = "small"
            }
        }
        
        return button
    }
}

let submitBtn = ButtonFactory.create("primary")
let cancelBtn = ButtonFactory.create("secondary")
let deleteBtn = ButtonFactory.create("danger")
```

---

## Pattern 3: Observer

**Problem:** Multiple things need to react when something changes

**Solution:** The Observer pattern (pub/sub)

```sona
class EventEmitter {
    func init() {
        self.listeners = {}
    }
    
    func on(event, callback) {
        if event not in self.listeners {
            self.listeners[event] = []
        }
        self.listeners[event].push(callback)
    }
    
    func off(event, callback) {
        if event in self.listeners {
            self.listeners[event] = self.listeners[event].filter(
                func(cb) { return cb != callback }
            )
        }
    }
    
    func emit(event, data = null) {
        if event in self.listeners {
            for callback in self.listeners[event] {
                callback(data)
            }
        }
    }
}

// Usage
let events = EventEmitter()

// Subscribe to events
events.on("userLogin", func(user) {
    print("Welcome, {user.name}!")
})

events.on("userLogin", func(user) {
    log("User logged in: {user.id}")
})

events.on("userLogout", func(user) {
    print("Goodbye, {user.name}!")
})

// Trigger events
events.emit("userLogin", {"id": 123, "name": "Alice"})
// Output:
// Welcome, Alice!
// User logged in: 123

events.emit("userLogout", {"id": 123, "name": "Alice"})
// Output:
// Goodbye, Alice!
```

### Real-World Example: Shopping Cart

```sona
class ShoppingCart extends EventEmitter {
    func init() {
        super.init()
        self.items = []
    }
    
    func add(item) {
        self.items.push(item)
        self.emit("itemAdded", item)
        self.emit("cartChanged", self)
    }
    
    func remove(index) {
        let item = self.items[index]
        self.items.remove(index)
        self.emit("itemRemoved", item)
        self.emit("cartChanged", self)
    }
    
    func total() {
        return self.items.reduce(0, func(sum, item) {
            return sum + item.price
        })
    }
}

// Usage
let cart = ShoppingCart()

// React to changes
cart.on("itemAdded", func(item) {
    print("Added: {item.name}")
})

cart.on("cartChanged", func(cart) {
    print("Cart total: ${cart.total()}")
})

cart.add({"name": "Apple", "price": 1.50})
// Output:
// Added: Apple
// Cart total: $1.50

cart.add({"name": "Bread", "price": 2.50})
// Output:
// Added: Bread
// Cart total: $4.00
```

---

## Pattern 4: Strategy

**Problem:** Need to swap algorithms at runtime

**Solution:** The Strategy pattern

```sona
// Different sorting strategies
class BubbleSort {
    func sort(items) {
        print("Using bubble sort...")
        // Slow but simple
        let arr = items.copy()
        for i in range(arr.length()) {
            for j in range(arr.length() - 1) {
                if arr[j] > arr[j + 1] {
                    let temp = arr[j]
                    arr[j] = arr[j + 1]
                    arr[j + 1] = temp
                }
            }
        }
        return arr
    }
}

class QuickSort {
    func sort(items) {
        print("Using quick sort...")
        // Fast and efficient
        return items.sort()  // Built-in is quick sort
    }
}

// Context that uses a strategy
class Sorter {
    func init(strategy = null) {
        self.strategy = strategy or QuickSort()
    }
    
    func setStrategy(strategy) {
        self.strategy = strategy
    }
    
    func sort(items) {
        return self.strategy.sort(items)
    }
}

// Usage
let sorter = Sorter()
let data = [5, 2, 8, 1, 9, 3]

// Use default (quick sort)
print(sorter.sort(data))

// Switch to bubble sort
sorter.setStrategy(BubbleSort())
print(sorter.sort(data))
```

### Strategy with Payment Methods

```sona
class CreditCardPayment {
    func pay(amount) {
        print("Charging ${amount} to credit card...")
        return {"success": true, "method": "credit_card"}
    }
}

class PayPalPayment {
    func pay(amount) {
        print("Processing ${amount} via PayPal...")
        return {"success": true, "method": "paypal"}
    }
}

class CryptoPayment {
    func pay(amount) {
        print("Sending ${amount} worth of crypto...")
        return {"success": true, "method": "crypto"}
    }
}

class Checkout {
    func init() {
        self.paymentMethod = CreditCardPayment()  // Default
    }
    
    func setPaymentMethod(method) {
        self.paymentMethod = method
    }
    
    func processPayment(amount) {
        return self.paymentMethod.pay(amount)
    }
}

// Usage
let checkout = Checkout()

// User selects payment method
let choice = input("Payment (1=Card, 2=PayPal, 3=Crypto): ")
match choice {
    "1" => checkout.setPaymentMethod(CreditCardPayment())
    "2" => checkout.setPaymentMethod(PayPalPayment())
    "3" => checkout.setPaymentMethod(CryptoPayment())
}

checkout.processPayment(99.99)
```

---

## When to Use Each Pattern

| Pattern | Use When |
|---------|----------|
| **Singleton** | Need exactly one instance (config, database) |
| **Factory** | Creating objects based on conditions |
| **Observer** | Multiple parts react to changes |
| **Strategy** | Swapping algorithms/behaviors |

---

## Practice

### Exercise 1
Create a `Logger` singleton that can log to console with different levels (info, warn, error).

### Exercise 2
Build a `DocumentFactory` that creates different document types (PDF, Word, Text).

### Exercise 3
Create a `TemperatureMonitor` using Observer pattern that alerts when temperature is too high or too low.

---

→ Next: [mini-2: Functional Programming](mini-2_functional.md)
