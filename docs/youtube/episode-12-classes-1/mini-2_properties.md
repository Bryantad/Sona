# Mini-Episode 12.2: Properties & Methods 🔧

> Data and behavior in classes

---

## Properties = Data

Properties store information about an object:

```sona
class Book {
    func init(title, author, pages) {
        // These are properties
        self.title = title
        self.author = author
        self.pages = pages
        self.current_page = 1    // Default value
        self.is_finished = false
    }
}

let book = Book("Sona Guide", "You", 200)
print(book.title)        // Sona Guide
print(book.current_page) // 1
```

---

## Accessing Properties

```sona
// Read
print(book.title)

// Write  
book.current_page = 50

// Check
if book.is_finished {
    print("Done reading!")
}
```

---

## Methods = Actions

Methods are functions that belong to a class:

```sona
class Book {
    func init(title, pages) {
        self.title = title
        self.pages = pages
        self.current_page = 1
    }
    
    func read(num_pages) {
        self.current_page = self.current_page + num_pages
        print(f"Now on page {self.current_page}")
    }
    
    func is_finished() {
        return self.current_page >= self.pages
    }
}
```

---

## Methods Using Properties

Methods can read and change properties:

```sona
class BankAccount {
    func init(owner, balance = 0) {
        self.owner = owner
        self.balance = balance
    }
    
    func deposit(amount) {
        self.balance = self.balance + amount
        print(f"Deposited ${amount}. New balance: ${self.balance}")
    }
    
    func withdraw(amount) {
        if amount > self.balance {
            print("Insufficient funds!")
            return false
        }
        self.balance = self.balance - amount
        print(f"Withdrew ${amount}. New balance: ${self.balance}")
        return true
    }
    
    func get_balance() {
        return self.balance
    }
}
```

---

## Methods Calling Methods

```sona
class ShoppingCart {
    func init() {
        self.items = []
    }
    
    func add_item(item, price) {
        self.items.append({"item": item, "price": price})
    }
    
    func get_total() {
        let total = 0
        for item in self.items {
            total = total + item["price"]
        }
        return total
    }
    
    func checkout() {
        let total = self.get_total()  // Method calls method!
        print(f"Total: ${total}")
        self.items = []  // Clear cart
    }
}
```

---

## Getter Methods

Methods that return property values (often with formatting):

```sona
class Person {
    func init(first, last, birth_year) {
        self.first_name = first
        self.last_name = last
        self.birth_year = birth_year
    }
    
    func get_full_name() {
        return f"{self.first_name} {self.last_name}"
    }
    
    func get_age() {
        return 2024 - self.birth_year
    }
}

let person = Person("John", "Doe", 1990)
print(person.get_full_name())  // John Doe
print(person.get_age())        // 34
```

---

## Method Return Types

```sona
class Calculator {
    func init() {
        self.result = 0
    }
    
    // Returns nothing (just does something)
    func reset() {
        self.result = 0
    }
    
    // Returns a value
    func add(x) {
        self.result = self.result + x
        return self.result  // Returns for chaining
    }
    
    // Returns true/false
    func is_positive() {
        return self.result > 0
    }
}
```

---

## Complete Example: Todo Item

```sona
class TodoItem {
    func init(description) {
        self.description = description
        self.completed = false
        self.created_at = time.now()
    }
    
    func complete() {
        self.completed = true
    }
    
    func uncomplete() {
        self.completed = false
    }
    
    func toggle() {
        self.completed = not self.completed
    }
    
    func display() {
        let status = "[x]" if self.completed else "[ ]"
        return f"{status} {self.description}"
    }
}

let task = TodoItem("Learn Sona")
print(task.display())  // [ ] Learn Sona
task.complete()
print(task.display())  // [x] Learn Sona
```
