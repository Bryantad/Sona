# Mini-Episode 15.3: Storage & Polish 💾

> Build a complete Todo App - Part 3

---

## The Storage Module

```sona
// storage.sona
import json
import fs
from todo import Todo, from_dict

let DATA_FILE = "data/todos.json"

func save_todos(todos) {
    // Convert todos to dictionaries
    let data = []
    for todo in todos {
        data.append(todo.to_dict())
    }
    
    // Ensure data directory exists
    if not fs.exists("data") {
        fs.mkdir("data")
    }
    
    // Save to file
    json.save(DATA_FILE, data)
    return true
}

func load_todos() {
    // Check if file exists
    if not fs.exists(DATA_FILE) {
        return []
    }
    
    try {
        let data = json.load(DATA_FILE)
        let todos = []
        
        for item in data {
            todos.append(from_dict(item))
        }
        
        return todos
    } catch error {
        print(f"⚠️  Could not load todos: {error}")
        return []
    }
}
```

---

## Integrate Storage with Manager

```sona
// Updated todo_manager.sona
from storage import save_todos, load_todos

class TodoManager {
    func init() {
        self.todos = load_todos()  // Load on startup!
        
        if len(self.todos) > 0 {
            print(f"📂 Loaded {len(self.todos)} todos")
        }
    }
    
    func save() {
        save_todos(self.todos)
        print("💾 Todos saved!")
    }
    
    // ... rest of methods stay the same
}
```

---

## Complete Main Program

```sona
// main.sona
from todo_manager import TodoManager
from menu import show_menu, get_choice

func show_todos(manager) {
    let todos = manager.get_all()
    
    if len(todos) == 0 {
        print("\n📭 No todos yet! Add some tasks.")
        return
    }
    
    print(f"\n📋 Your Todos ({manager.count_completed()}/{manager.count()} done):")
    print("-" * 40)
    
    for i, todo in enumerate(todos) {
        print(f"  {i + 1}. {todo.display()}")
    }
    print("-" * 40)
}

func add_todo(manager) {
    let text = prompt("\n✏️  What do you need to do? ")
    
    if text.strip() == "" {
        print("❌ Cannot add empty todo!")
        return
    }
    
    manager.add(text)
    print(f"✅ Added: {text}")
}

func complete_todo(manager) {
    if manager.count() == 0 {
        print("\n📭 No todos to complete!")
        return
    }
    
    show_todos(manager)
    let input = prompt("\n🔢 Which todo? (number): ")
    
    try {
        let index = int(input) - 1
        if manager.complete(index) {
            let todo = manager.get_all()[index]
            let icon = "✅" if todo.completed else "⬜"
            print(f"{icon} Toggled: {todo.text}")
        } else {
            print("❌ Invalid number!")
        }
    } catch {
        print("❌ Please enter a number!")
    }
}

func delete_todo(manager) {
    if manager.count() == 0 {
        print("\n📭 No todos to delete!")
        return
    }
    
    show_todos(manager)
    let input = prompt("\n🔢 Which todo to delete? (number): ")
    
    try {
        let index = int(input) - 1
        let removed = manager.delete(index)
        if removed {
            print(f"🗑️  Deleted: {removed.text}")
        } else {
            print("❌ Invalid number!")
        }
    } catch {
        print("❌ Please enter a number!")
    }
}

func main() {
    let manager = TodoManager()
    
    print("\n🎯 ═══════════════════════════")
    print("   WELCOME TO TODO APP")
    print("═══════════════════════════════")
    
    while true {
        show_menu()
        let choice = get_choice()
        
        match choice {
            1 => show_todos(manager),
            2 => add_todo(manager),
            3 => complete_todo(manager),
            4 => delete_todo(manager),
            5 => {
                manager.save()
                print("\n👋 Goodbye! Your todos are saved.")
                break
            },
            _ => print("❌ Please choose 1-5")
        }
    }
}

// Run the app!
main()
```

---

## Sample Session

```
🎯 ═══════════════════════════
   WELCOME TO TODO APP
═══════════════════════════════
📂 Loaded 2 todos

========== TODO APP ==========
  1. 📋 Show all todos
  2. ➕ Add new todo
  3. ✅ Mark complete
  4. 🗑️  Delete todo
  5. 💾 Save and Exit
================================
Choose option (1-5): 1

📋 Your Todos (1/2 done):
----------------------------------------
  1. [x] Learn Sona basics
  2. [ ] Build todo app
----------------------------------------

Choose option (1-5): 2

✏️  What do you need to do? Watch episode 16
✅ Added: Watch episode 16

Choose option (1-5): 5
💾 Todos saved!

👋 Goodbye! Your todos are saved.
```

---

## Congratulations! 🎉

You've built a complete app with:
- ✅ Classes and objects
- ✅ File I/O with JSON
- ✅ User input handling
- ✅ Error handling
- ✅ Modular code structure
- ✅ Persistence (data saves!)

**You're ready for more advanced projects!**
