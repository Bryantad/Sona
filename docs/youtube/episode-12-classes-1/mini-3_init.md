# Mini-Episode 12.3: The init Method 🎬

> Setting up objects when they're created

---

## What is init?

`init` is a special method that runs automatically when you create an object.

```sona
class Example {
    func init() {
        print("I run automatically!")
    }
}

let obj = Example()  // Prints: "I run automatically!"
```

---

## init Sets Up the Object

```sona
class Car {
    func init(make, model, year) {
        self.make = make
        self.model = model
        self.year = year
        self.mileage = 0      // Start at 0
        self.is_running = false
    }
}

let my_car = Car("Toyota", "Camry", 2020)
print(my_car.make)     // Toyota
print(my_car.mileage)  // 0
```

---

## Required vs Optional Parameters

```sona
class User {
    func init(username, email, role = "user") {
        self.username = username  // Required
        self.email = email        // Required
        self.role = role          // Optional (default: "user")
    }
}

// Both work:
let admin = User("admin", "admin@site.com", "admin")
let guest = User("guest", "guest@site.com")  // role = "user"
```

---

## Validation in init

```sona
class Product {
    func init(name, price) {
        if price < 0 {
            raise Error("Price cannot be negative!")
        }
        
        self.name = name
        self.price = price
    }
}

let item = Product("Book", 15.99)   // OK
let bad = Product("Book", -5)       // Error!
```

---

## init with Default Values

```sona
class GameCharacter {
    func init(name) {
        self.name = name
        
        // Default starting stats
        self.level = 1
        self.health = 100
        self.max_health = 100
        self.experience = 0
        self.inventory = []
        self.skills = []
    }
}

let hero = GameCharacter("Warrior")
// All defaults are set up!
```

---

## init with Calculated Values

```sona
class Rectangle {
    func init(width, height) {
        self.width = width
        self.height = height
        
        // Calculate on creation
        self.area = width * height
        self.perimeter = 2 * (width + height)
    }
}

let rect = Rectangle(10, 5)
print(rect.area)      // 50
print(rect.perimeter) // 30
```

---

## init with Lists and Dicts

```sona
class Playlist {
    func init(name) {
        self.name = name
        self.songs = []      // Empty list
        self.created = time.now()
    }
    
    func add_song(song) {
        self.songs.append(song)
    }
}

let rock = Playlist("Rock Classics")
rock.add_song("Bohemian Rhapsody")
```

⚠️ **Important:** Create new list `[]` in init, not as class variable!

---

## Factory Pattern

Sometimes you want different ways to create objects:

```sona
class User {
    func init(username, email, verified = false) {
        self.username = username
        self.email = email
        self.verified = verified
    }
}

// Factory functions
func create_guest() {
    return User("guest", "guest@temp.com")
}

func create_admin(email) {
    let admin = User("admin", email, true)
    admin.role = "admin"
    return admin
}
```

---

## Common init Patterns

```sona
class DataManager {
    func init(filename) {
        self.filename = filename
        
        // Load data on creation
        self.data = self._load_data()
    }
    
    func _load_data() {
        try {
            return json.load(self.filename)
        } catch error {
            return {}  // Default empty
        }
    }
}
```

---

## Key Points

1. `init` runs **automatically** when creating object
2. Use it to **set up** initial property values
3. Can have **required** and **optional** parameters
4. Can include **validation** logic
5. Can **calculate** derived values
6. Always create **new** lists/dicts (not shared)
