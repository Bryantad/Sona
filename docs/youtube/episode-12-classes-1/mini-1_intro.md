# Mini-Episode 12.1: What Are Classes? 🏗️

> Blueprints for creating objects

---

## Understanding Classes

A **class** is like a blueprint or template.

Think of it like:
- Class = Cookie cutter 🍪
- Object = Actual cookie

One class → Many objects!

---

## Real World Analogy

**Class: Dog**
- Has: name, breed, age
- Can: bark, eat, sleep

**Objects:**
- Buddy (Golden Retriever, 3 years)
- Max (Poodle, 5 years)
- Luna (Husky, 2 years)

Same blueprint, different dogs!

---

## Basic Class Syntax

```sona
class Dog {
    func init(name, breed) {
        self.name = name
        self.breed = breed
    }
    
    func bark() {
        print(f"{self.name} says Woof!")
    }
}
```

---

## Creating Objects

```sona
// Create objects from the class
let buddy = Dog("Buddy", "Golden Retriever")
let max = Dog("Max", "Poodle")

// Use them
print(buddy.name)   // Buddy
print(max.breed)    // Poodle

buddy.bark()        // Buddy says Woof!
max.bark()          // Max says Woof!
```

---

## What is `self`?

`self` refers to **this specific object**.

```sona
class Cat {
    func init(name) {
        self.name = name  // THIS cat's name
    }
    
    func meow() {
        print(f"{self.name} says Meow!")  // THIS cat's name
    }
}

let kitty = Cat("Whiskers")
kitty.meow()  // Whiskers says Meow!
```

---

## Properties vs Methods

**Properties** = Data (nouns)
- `self.name`
- `self.age`
- `self.color`

**Methods** = Actions (verbs)
- `bark()`
- `eat()`
- `sleep()`

---

## Class vs Dictionary

You could use a dictionary:
```sona
let dog = {
    "name": "Buddy",
    "breed": "Golden Retriever"
}
```

But classes are better because:
1. **Methods** - Functions built in
2. **Structure** - Clear what properties exist
3. **Reusable** - Easy to make many objects
4. **Organized** - Related code stays together

---

## Simple Complete Example

```sona
class Player {
    func init(name) {
        self.name = name
        self.health = 100
        self.score = 0
    }
    
    func take_damage(amount) {
        self.health = self.health - amount
        if self.health <= 0 {
            print(f"{self.name} has been defeated!")
        }
    }
    
    func earn_points(points) {
        self.score = self.score + points
        print(f"{self.name} earned {points} points!")
    }
    
    func status() {
        print(f"{self.name}: {self.health} HP, {self.score} pts")
    }
}

// Use it
let hero = Player("Hero")
hero.earn_points(50)    // Hero earned 50 points!
hero.take_damage(30)
hero.status()           // Hero: 70 HP, 50 pts
```

---

## Key Takeaways

1. **Class** = Blueprint/template
2. **Object** = Instance created from class
3. **self** = "This particular object"
4. **init()** = Setup when object is created
5. **Methods** = Functions inside a class
