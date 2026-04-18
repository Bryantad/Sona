# Mini-Episode 13.3: Class Design 📐

> When and how to use inheritance

---

## The "Is-A" Test

Use inheritance when child **is a type of** parent:

✅ **Good inheritance:**
- Dog **is a** Animal
- Car **is a** Vehicle
- Button **is a** UIElement

❌ **Bad inheritance:**
- Car **is a** Engine (Car HAS an Engine)
- Player **is a** Inventory (Player HAS an Inventory)

---

## Composition vs Inheritance

**Inheritance** = "Is a" relationship
```sona
class Dog extends Animal { }
// Dog IS an Animal
```

**Composition** = "Has a" relationship
```sona
class Car {
    func init() {
        self.engine = Engine()  // Car HAS an Engine
        self.wheels = [Wheel(), Wheel(), Wheel(), Wheel()]
    }
}
```

---

## Favor Composition

Often composition is better than inheritance:

```sona
// Instead of this (inheritance)
class FlyingCar extends Car {
    func fly() { ... }
}

// Consider this (composition)
class Car {
    func init() {
        self.flying_ability = FlyingModule()
    }
    
    func fly() {
        self.flying_ability.activate()
    }
}
```

**Why?** More flexible! Can add/remove abilities easily.

---

## Keep Inheritance Shallow

```sona
// Too deep - confusing!
class A { }
class B extends A { }
class C extends B { }
class D extends C { }
class E extends D { }  // 5 levels deep!

// Better - flat and clear
class Animal { }
class Dog extends Animal { }
class Cat extends Animal { }
class Bird extends Animal { }
```

Rule of thumb: **2-3 levels max**

---

## Abstract Base Classes

Classes meant to be inherited, not used directly:

```sona
class Shape {
    func area() {
        raise Error("Subclass must implement area()")
    }
    
    func perimeter() {
        raise Error("Subclass must implement perimeter()")
    }
}

// Force children to implement
class Rectangle extends Shape {
    func init(w, h) {
        self.width = w
        self.height = h
    }
    
    func area() {
        return self.width * self.height
    }
    
    func perimeter() {
        return 2 * (self.width + self.height)
    }
}
```

---

## Design Example: Game Entities

```sona
// Base class for all game objects
class Entity {
    func init(x, y) {
        self.x = x
        self.y = y
    }
    
    func move(dx, dy) {
        self.x = self.x + dx
        self.y = self.y + dy
    }
}

// Characters have health
class Character extends Entity {
    func init(x, y, health) {
        super.init(x, y)
        self.health = health
    }
    
    func take_damage(amount) {
        self.health = self.health - amount
    }
}

// Player is a character with inventory
class Player extends Character {
    func init(x, y) {
        super.init(x, y, 100)
        self.inventory = []
    }
    
    func pickup(item) {
        self.inventory.append(item)
    }
}

// Enemy is a character with AI
class Enemy extends Character {
    func init(x, y, health) {
        super.init(x, y, health)
    }
    
    func decide_action() {
        // AI logic
    }
}
```

---

## Class Design Checklist

Before creating a class hierarchy:

- [ ] Does child "is-a" parent? (not "has-a")
- [ ] Is shared code significant enough?
- [ ] Is hierarchy 3 levels or less?
- [ ] Does each class have clear purpose?
- [ ] Would composition be simpler?

---

## Quick Tips

1. **Start simple** - Add inheritance when needed
2. **Test first** - Make sure parent class works
3. **Document** - Explain what children should override
4. **Be consistent** - Similar classes should behave similarly
