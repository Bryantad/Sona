# Mini-Lesson 10.2: Methods & Self

## What Are Methods?

**Methods** are functions that belong to a class. They define what objects can DO.

```sona
class Dog {
    func init(name) {
        self.name = name
    }
    
    // This is a method
    func bark() {
        print("{self.name} says Woof!")
    }
}

let buddy = Dog("Buddy")
buddy.bark()  // "Buddy says Woof!"
```

---

## The `self` Keyword

`self` refers to the current object. It lets methods access the object's properties:

```sona
class Counter {
    func init() {
        self.count = 0
    }
    
    func increment() {
        self.count = self.count + 1  // Modify this object's count
    }
    
    func get_count() {
        return self.count  // Return this object's count
    }
}

let c1 = Counter()
let c2 = Counter()

c1.increment()
c1.increment()
c1.increment()

print(c1.get_count())  // 3
print(c2.get_count())  // 0 (different object!)
```

---

## Methods with Parameters

```sona
class BankAccount {
    func init(owner) {
        self.owner = owner
        self.balance = 0
    }
    
    func deposit(amount) {
        if amount > 0 {
            self.balance = self.balance + amount
            print("Deposited ${amount}")
        }
    }
    
    func withdraw(amount) {
        if amount <= self.balance {
            self.balance = self.balance - amount
            print("Withdrew ${amount}")
        } else {
            print("Insufficient funds!")
        }
    }
    
    func get_balance() {
        return self.balance
    }
}

let account = BankAccount("Alice")
account.deposit(100)       // "Deposited $100"
account.withdraw(30)       // "Withdrew $30"
print(account.get_balance())  // 70
account.withdraw(100)      // "Insufficient funds!"
```

---

## Methods Returning Values

```sona
class Rectangle {
    func init(width, height) {
        self.width = width
        self.height = height
    }
    
    func area() {
        return self.width * self.height
    }
    
    func perimeter() {
        return 2 * (self.width + self.height)
    }
    
    func is_square() {
        return self.width == self.height
    }
}

let rect = Rectangle(5, 3)
print(rect.area())        // 15
print(rect.perimeter())   // 16
print(rect.is_square())   // false

let square = Rectangle(4, 4)
print(square.is_square()) // true
```

---

## Methods Calling Other Methods

Methods can call other methods using `self`:

```sona
class Circle {
    func init(radius) {
        self.radius = radius
    }
    
    func area() {
        return 3.14159 * self.radius * self.radius
    }
    
    func diameter() {
        return self.radius * 2
    }
    
    func describe() {
        // Call other methods!
        print("Circle with radius {self.radius}")
        print("Diameter: {self.diameter()}")
        print("Area: {self.area()}")
    }
}

let c = Circle(5)
c.describe()
// Circle with radius 5
// Diameter: 10
// Area: 78.53975
```

---

## Methods That Modify State

```sona
class Player {
    func init(name) {
        self.name = name
        self.health = 100
        self.level = 1
        self.xp = 0
    }
    
    func take_damage(amount) {
        self.health = self.health - amount
        if self.health < 0 {
            self.health = 0
        }
        print("{self.name} took {amount} damage! Health: {self.health}")
    }
    
    func heal(amount) {
        self.health = self.health + amount
        if self.health > 100 {
            self.health = 100
        }
        print("{self.name} healed! Health: {self.health}")
    }
    
    func gain_xp(amount) {
        self.xp = self.xp + amount
        print("{self.name} gained {amount} XP!")
        
        // Check for level up
        if self.xp >= 100 {
            self.level_up()
        }
    }
    
    func level_up() {
        self.level = self.level + 1
        self.xp = self.xp - 100
        self.health = 100  // Full heal on level up
        print("🎉 {self.name} reached level {self.level}!")
    }
    
    func is_alive() {
        return self.health > 0
    }
}

let hero = Player("Hero")
hero.take_damage(30)    // "Hero took 30 damage! Health: 70"
hero.heal(20)           // "Hero healed! Health: 90"
hero.gain_xp(50)        // "Hero gained 50 XP!"
hero.gain_xp(60)        // "Hero gained 60 XP!" + "🎉 Hero reached level 2!"
```

---

## Method Chaining

Some methods return `self` to allow chaining:

```sona
class StringBuilder {
    func init() {
        self.text = ""
    }
    
    func add(s) {
        self.text = self.text + s
        return self  // Return self for chaining
    }
    
    func add_line(s) {
        self.text = self.text + s + "\n"
        return self
    }
    
    func build() {
        return self.text
    }
}

let result = StringBuilder()
    .add("Hello, ")
    .add("World!")
    .add_line("")
    .add_line("How are you?")
    .build()

print(result)
```

---

## toString / Display Methods

Create methods to display objects nicely:

```sona
class Person {
    func init(name, age) {
        self.name = name
        self.age = age
    }
    
    func toString() {
        return "{self.name} (age {self.age})"
    }
    
    func display() {
        print(self.toString())
    }
}

let person = Person("Alice", 25)
print(person.toString())  // "Alice (age 25)"
person.display()          // "Alice (age 25)"
```

---

## Practice

### Exercise 1
Add a `describe()` method to this class:
```sona
class Car {
    func init(make, model, year) {
        self.make = make
        self.model = model
        self.year = year
    }
}
```

### Exercise 2
Create a `Counter` class with methods: `increment()`, `decrement()`, `reset()`, and `get()`.

### Exercise 3
Create a `ShoppingCart` class with methods: `add_item(item, price)`, `remove_item(item)`, `get_total()`, `list_items()`.

<details>
<summary>Exercise 2 Answer</summary>

```sona
class Counter {
    func init(start = 0) {
        self.value = start
    }
    
    func increment() {
        self.value = self.value + 1
    }
    
    func decrement() {
        self.value = self.value - 1
    }
    
    func reset() {
        self.value = 0
    }
    
    func get() {
        return self.value
    }
}
```

</details>

---

## Summary

| Concept | Description |
|---------|-------------|
| Method | Function inside a class |
| `self` | Reference to current object |
| Calling | `object.method()` |
| Chaining | Return `self` to chain calls |
| Modify state | Methods can change properties |

---

→ Next: [mini-3: Inheritance](mini-3_inheritance.md)
