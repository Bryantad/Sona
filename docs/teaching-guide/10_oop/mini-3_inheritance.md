# Mini-Lesson 10.3: Inheritance

## What is Inheritance?

**Inheritance** lets you create a new class based on an existing one. The new class gets all the properties and methods of the parent, plus can add its own.

Think of it like:
- Vehicle → Car, Truck, Motorcycle
- Animal → Dog, Cat, Bird
- Shape → Circle, Rectangle, Triangle

---

## Basic Inheritance

```sona
// Parent class (base class)
class Animal {
    func init(name) {
        self.name = name
    }
    
    func speak() {
        print("{self.name} makes a sound")
    }
}

// Child class (extends Animal)
class Dog extends Animal {
    func speak() {
        print("{self.name} says Woof!")
    }
    
    func fetch() {
        print("{self.name} fetches the ball!")
    }
}

// Another child class
class Cat extends Animal {
    func speak() {
        print("{self.name} says Meow!")
    }
    
    func scratch() {
        print("{self.name} scratches the furniture!")
    }
}
```

**Using them:**
```sona
let dog = Dog("Buddy")
let cat = Cat("Whiskers")

dog.speak()   // "Buddy says Woof!"
cat.speak()   // "Whiskers says Meow!"

dog.fetch()   // "Buddy fetches the ball!"
cat.scratch() // "Whiskers scratches the furniture!"
```

---

## What Inheritance Provides

```
        Animal
       ┌───┴───┐
      Dog     Cat
       │       │
    Inherits: Inherits:
    - name    - name
    - speak() - speak()
       │       │
    + fetch() + scratch()
```

- Child classes GET everything from parent
- Child classes can ADD new features
- Child classes can OVERRIDE parent methods

---

## Calling Parent Methods

Use `super` to call the parent's version:

```sona
class Animal {
    func init(name) {
        self.name = name
    }
    
    func describe() {
        print("This is {self.name}")
    }
}

class Dog extends Animal {
    func init(name, breed) {
        super.init(name)      // Call parent's init
        self.breed = breed    // Add new property
    }
    
    func describe() {
        super.describe()      // Call parent's describe
        print("Breed: {self.breed}")
    }
}

let buddy = Dog("Buddy", "Golden Retriever")
buddy.describe()
// "This is Buddy"
// "Breed: Golden Retriever"
```

---

## Multi-Level Inheritance

```sona
class Vehicle {
    func init(brand) {
        self.brand = brand
    }
    
    func start() {
        print("{self.brand} starting...")
    }
}

class Car extends Vehicle {
    func init(brand, doors) {
        super.init(brand)
        self.doors = doors
    }
    
    func honk() {
        print("Beep beep!")
    }
}

class SportsCar extends Car {
    func init(brand, top_speed) {
        super.init(brand, 2)  // Sports cars have 2 doors
        self.top_speed = top_speed
    }
    
    func race() {
        print("{self.brand} racing at {self.top_speed} mph!")
    }
}

let ferrari = SportsCar("Ferrari", 200)
ferrari.start()  // From Vehicle
ferrari.honk()   // From Car
ferrari.race()   // From SportsCar
```

---

## Checking Inheritance

```sona
let buddy = Dog("Buddy", "Lab")

print(buddy instanceof Dog)     // true
print(buddy instanceof Animal)  // true (Dog extends Animal)
print(buddy instanceof Cat)     // false
```

---

## Real Example: Game Characters

```sona
class Character {
    func init(name, health) {
        self.name = name
        self.health = health
        self.max_health = health
    }
    
    func take_damage(amount) {
        self.health = self.health - amount
        if self.health < 0 { self.health = 0 }
        print("{self.name} takes {amount} damage! HP: {self.health}/{self.max_health}")
    }
    
    func is_alive() {
        return self.health > 0
    }
}

class Warrior extends Character {
    func init(name) {
        super.init(name, 150)  // Warriors have more HP
        self.armor = 10
    }
    
    func take_damage(amount) {
        let reduced = amount - self.armor
        if reduced < 0 { reduced = 0 }
        super.take_damage(reduced)
    }
    
    func shield_bash() {
        print("{self.name} bashes with shield!")
        return 15
    }
}

class Mage extends Character {
    func init(name) {
        super.init(name, 80)  // Mages have less HP
        self.mana = 100
    }
    
    func fireball() {
        if self.mana >= 20 {
            self.mana = self.mana - 20
            print("{self.name} casts Fireball! Mana: {self.mana}")
            return 40
        }
        print("Not enough mana!")
        return 0
    }
}

class Rogue extends Character {
    func init(name) {
        super.init(name, 100)
        self.stealth = false
    }
    
    func hide() {
        self.stealth = true
        print("{self.name} hides in shadows!")
    }
    
    func backstab() {
        let damage = self.stealth ? 50 : 20
        self.stealth = false
        print("{self.name} attacks from behind!")
        return damage
    }
}

// Create characters
let warrior = Warrior("Thorin")
let mage = Mage("Gandalf")
let rogue = Rogue("Shadow")

// Battle!
warrior.take_damage(30)  // Reduced by armor
mage.fireball()
rogue.hide()
rogue.backstab()  // Extra damage from stealth
```

---

## When to Use Inheritance

**Good uses:**
- Clear "is-a" relationship (Dog IS AN Animal)
- Shared behavior across related types
- Extending library classes

**Avoid when:**
- Just to share a little code (use composition)
- No clear hierarchy
- Changes to parent break children

---

## Composition vs Inheritance

Sometimes "has-a" is better than "is-a":

```sona
// Inheritance: Car IS A Vehicle
class Car extends Vehicle { }

// Composition: Car HAS AN Engine
class Car {
    func init() {
        self.engine = Engine()
    }
}
```

Use composition when objects contain other objects rather than being types of them.

---

## Practice

### Exercise 1
Create a `Shape` base class with an `area()` method. Create `Circle` and `Square` that extend it and implement `area()`.

### Exercise 2
Create an `Employee` base class. Create `Manager` and `Developer` that extend it with different `work()` methods.

### Exercise 3
Create a simple game class hierarchy:
- `Entity` (base with name, position)
- `Player` (can move, attack)
- `Enemy` (can patrol, attack)
- `NPC` (can talk)

<details>
<summary>Exercise 1 Answer</summary>

```sona
class Shape {
    func area() {
        return 0  // Override in children
    }
}

class Circle extends Shape {
    func init(radius) {
        self.radius = radius
    }
    
    func area() {
        return 3.14159 * self.radius * self.radius
    }
}

class Square extends Shape {
    func init(side) {
        self.side = side
    }
    
    func area() {
        return self.side * self.side
    }
}

let c = Circle(5)
let s = Square(4)
print(c.area())  // 78.53975
print(s.area())  // 16
```

</details>

---

## Summary

| Concept | Syntax | Purpose |
|---------|--------|---------|
| Extend | `class Child extends Parent` | Inherit from parent |
| Override | Define same method name | Replace parent behavior |
| super | `super.method()` | Call parent's method |
| instanceof | `obj instanceof Class` | Check type |

---

## Module 10 Complete! 🎉

You've learned:
- ✅ Classes and objects
- ✅ Methods and self
- ✅ Inheritance

→ Next: [Module 11: Standard Library Deep Dive](../11_stdlib/README.md)
