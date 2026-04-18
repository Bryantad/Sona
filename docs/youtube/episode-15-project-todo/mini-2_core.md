# Mini-Episode 15.2: Core Features 🔧

> Build a complete Todo App - Part 2

---

## The Todo Manager Class

```sona
// todo_manager.sona
from todo import Todo, from_dict

class TodoManager {
    func init() {
        self.todos = []
    }
    
    func add(text) {
        let todo = Todo(text)
        self.todos.append(todo)
        return todo
    }
    
    func get_all() {
        return self.todos
    }
    
    func complete(index) {
        if index >= 0 and index < len(self.todos) {
            self.todos[index].toggle()
            return true
        }
        return false
    }
    
    func delete(index) {
        if index >= 0 and index < len(self.todos) {
            let removed = self.todos[index]
            self.todos.remove(index)
            return removed
        }
        return null
    }
    
    func count() {
        return len(self.todos)
    }
    
    func count_completed() {
        let count = 0
        for todo in self.todos {
            if todo.completed {
                count = count + 1
            }
        }
        return count
    }
}
```

---

## The Menu System

```sona
// menu.sona

func show_menu() {
    print("\n========== TODO APP ==========")
    print("  1. 📋 Show all todos")
    print("  2. ➕ Add new todo")
    print("  3. ✅ Mark complete")
    print("  4. 🗑️  Delete todo")
    print("  5. 💾 Save and Exit")
    print("================================")
}

func get_choice() {
    let input = prompt("Choose option (1-5): ")
    try {
        return int(input)
    } catch {
        return -1
    }
}
```

---

## Show All Todos

```sona
func show_todos(manager) {
    let todos = manager.get_all()
    
    if len(todos) == 0 {
        print("\n📭 No todos yet! Add some tasks.")
        return
    }
    
    print(f"\n📋 Your Todos ({manager.count_completed()}/{manager.count()} done):")
    print("-" * 35)
    
    for i, todo in enumerate(todos) {
        print(f"  {i + 1}. {todo.display()}")
    }
}
```

---

## Add Todo

```sona
func add_todo(manager) {
    let text = prompt("\nWhat do you need to do? ")
    
    if text.strip() == "" {
        print("❌ Cannot add empty todo!")
        return
    }
    
    manager.add(text)
    print(f"✅ Added: {text}")
}
```

---

## Complete Todo

```sona
func complete_todo(manager) {
    if manager.count() == 0 {
        print("\n📭 No todos to complete!")
        return
    }
    
    show_todos(manager)
    let input = prompt("\nWhich todo to toggle? (number): ")
    
    try {
        let index = int(input) - 1  // Convert to 0-based
        
        if manager.complete(index) {
            let todo = manager.get_all()[index]
            let status = "completed" if todo.completed else "uncompleted"
            print(f"✅ Marked as {status}!")
        } else {
            print("❌ Invalid number!")
        }
    } catch {
        print("❌ Please enter a valid number!")
    }
}
```

---

## Delete Todo

```sona
func delete_todo(manager) {
    if manager.count() == 0 {
        print("\n📭 No todos to delete!")
        return
    }
    
    show_todos(manager)
    let input = prompt("\nWhich todo to delete? (number): ")
    
    try {
        let index = int(input) - 1
        let removed = manager.delete(index)
        
        if removed {
            print(f"🗑️  Deleted: {removed.text}")
        } else {
            print("❌ Invalid number!")
        }
    } catch {
        print("❌ Please enter a valid number!")
    }
}
```

---

## Main Loop (Preview)

```sona
func main() {
    let manager = TodoManager()
    
    print("🎯 Welcome to Todo App!")
    
    while true {
        show_menu()
        let choice = get_choice()
        
        match choice {
            1 => show_todos(manager),
            2 => add_todo(manager),
            3 => complete_todo(manager),
            4 => delete_todo(manager),
            5 => {
                print("👋 Goodbye!")
                break
            },
            _ => print("❌ Invalid option!")
        }
    }
}
```

---

## Next: Adding Storage!

In the next mini-episode, we'll:
- Save todos to JSON file
- Load todos on startup
- Add final polish
