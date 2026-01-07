# Mini-Episode 13.1: Inheritance Basics 🧬

> Building on existing classes

---

## What is Inheritance?

**Inheritance** = Creating a new class based on an existing one.

Think of it like:
- Parent class (base) = General
- Child class (derived) = Specific

---

## Real World Example

**Animal** (parent)
- Has: name, age
- Can: eat, sleep

**Dog** (child of Animal)
- Has: name, age, breed
- Can: eat, sleep, bark

**Cat** (child of Animal)
- Has: name, age, color
- Can: eat, sleep, meow

Dogs and cats are **both** animals, but with extras!

---

## Basic Syntax

```sona
// Parent class
class Animal {
    func init(name) {
        self.name = name
    }
    
    func speak() {
        print(f"{self.name} makes a sound")
    }
}

// Child class - inherits from Animal
class Dog extends Animal {
    func bark() {
        print(f"{self.name} says Woof!")
    }
}
```

---

## Using Inheritance

```sona
let dog = Dog("Buddy")

// From Animal (inherited)
print(dog.name)   // Buddy
dog.speak()       // Buddy makes a sound

// From Dog (own method)
dog.bark()        // Buddy says Woof!
```

The dog has **everything** from Animal, plus its own stuff!

---

## Why Use Inheritance?

**Without inheritance (repeated code):**
```sona
class Dog {
    func init(name) { self.name = name }
    func eat() { print(f"{self.name} eats") }
    func sleep() { print(f"{self.name} sleeps") }
    func bark() { print("Woof!") }
}

class Cat {
    func init(name) { self.name = name }
    func eat() { print(f"{self.name} eats") }    // Duplicate!
    func sleep() { print(f"{self.name} sleeps") } // Duplicate!
    func meow() { print("Meow!") }
}
```

**With inheritance (DRY - Don't Repeat Yourself):**
```sona
class Animal {
    func init(name) { self.name = name }
    func eat() { print(f"{self.name} eats") }
    func sleep() { print(f"{self.name} sleeps") }
}

class Dog extends Animal {
    func bark() { print("Woof!") }
}

class Cat extends Animal {
    func meow() { print("Meow!") }
}
```

---

## The extends Keyword

```sona
class Child extends Parent {
    // Child has everything Parent has
    // Plus anything new you add here
}
```

---

## Inheritance Chain

```sona
class Vehicle {
    func start() { print("Starting...") }
}

class Car extends Vehicle {
    func honk() { print("Beep!") }
}

class SportsCar extends Car {
    func turbo() { print("ZOOM!") }
}

let ferrari = SportsCar()
ferrari.start()  // From Vehicle
ferrari.honk()   // From Car
ferrari.turbo()  // From SportsCar
```

---

## Checking Class Type

```sona
let dog = Dog("Rex")

print(dog is Dog)     // true
print(dog is Animal)  // true - Dog IS an Animal!
print(dog is Cat)     // false
```

---

## Practical Example

```sona
class Shape {
    func init(color) {
        self.color = color
    }
    
    func describe() {
        print(f"A {self.color} shape")
    }
}

class Circle extends Shape {
    func init(color, radius) {
        super.init(color)  // Call parent init
        self.radius = radius
    }
}

class Rectangle extends Shape {
    func init(color, width, height) {
        super.init(color)
        self.width = width
        self.height = height
    }
}
```
