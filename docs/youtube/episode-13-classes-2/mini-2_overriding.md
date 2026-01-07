# Mini-Episode 13.2: Overriding Methods 🔄

> Customize inherited behavior

---

## What is Overriding?

**Overriding** = Replacing a parent method with your own version.

Child keeps the same method name, but different behavior!

---

## Basic Example

```sona
class Animal {
    func speak() {
        print("Some generic sound")
    }
}

class Dog extends Animal {
    func speak() {  // Override!
        print("Woof!")
    }
}

class Cat extends Animal {
    func speak() {  // Override!
        print("Meow!")
    }
}

let animal = Animal()
let dog = Dog()
let cat = Cat()

animal.speak()  // Some generic sound
dog.speak()     // Woof!
cat.speak()     // Meow!
```

---

## Using super

`super` calls the **parent's** version of a method:

```sona
class Animal {
    func init(name) {
        self.name = name
    }
}

class Dog extends Animal {
    func init(name, breed) {
        super.init(name)    // Call parent's init first!
        self.breed = breed   // Then add own property
    }
}

let dog = Dog("Buddy", "Golden Retriever")
print(dog.name)   // Buddy (from parent)
print(dog.breed)  // Golden Retriever (from Dog)
```

---

## Extending Parent Behavior

Sometimes you want parent behavior **plus** more:

```sona
class Employee {
    func work() {
        print("Working on tasks...")
    }
}

class Developer extends Employee {
    func work() {
        super.work()  // Do normal work
        print("...and writing code!")  // Plus extra
    }
}

let dev = Developer()
dev.work()
// Working on tasks...
// ...and writing code!
```

---

## Override with Different Logic

```sona
class Shape {
    func area() {
        return 0  // Default
    }
}

class Rectangle extends Shape {
    func init(width, height) {
        self.width = width
        self.height = height
    }
    
    func area() {
        return self.width * self.height
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

let rect = Rectangle(10, 5)
let circle = Circle(7)

print(rect.area())    // 50
print(circle.area())  // 153.938...
```

---

## Polymorphism

Same method name, different behavior based on type:

```sona
func print_areas(shapes) {
    for shape in shapes {
        print(f"Area: {shape.area()}")
    }
}

let shapes = [
    Rectangle(10, 5),
    Circle(7),
    Rectangle(3, 4)
]

print_areas(shapes)
// Area: 50
// Area: 153.938...
// Area: 12
```

Each shape calculates area its own way!

---

## Common Override Pattern: __str__

```sona
class Product {
    func init(name, price) {
        self.name = name
        self.price = price
    }
    
    func to_string() {
        return f"{self.name}: ${self.price}"
    }
}

class DiscountProduct extends Product {
    func init(name, price, discount) {
        super.init(name, price)
        self.discount = discount
    }
    
    func to_string() {
        let sale_price = self.price * (1 - self.discount)
        return f"{self.name}: ${sale_price} (was ${self.price})"
    }
}
```

---

## When to Override

✅ **Override when:**
- Child needs different behavior
- Child needs to add to parent behavior
- Parent method doesn't apply to child

❌ **Don't override when:**
- Parent behavior is fine
- You'd just call super anyway
- It would break expected behavior
