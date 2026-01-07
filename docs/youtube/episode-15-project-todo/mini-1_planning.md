# Mini-Episode 15.1: Project Planning 📋

> Build a complete Todo App - Part 1

---

## The Project

We're building a **Todo App** that:
- ✅ Adds tasks
- ✅ Shows all tasks
- ✅ Marks tasks complete
- ✅ Deletes tasks
- ✅ Saves to file
- ✅ Loads on startup

---

## Step 1: Plan the Structure

```
todo_app/
├── main.sona          # Entry point
├── todo.sona          # Todo class
├── storage.sona       # Save/load
└── data/
    └── todos.json     # Data file
```

---

## Step 2: Define the Todo Class

```sona
// todo.sona

class Todo {
    func init(text, completed = false) {
        self.text = text
        self.completed = completed
    }
    
    func toggle() {
        self.completed = not self.completed
    }
    
    func to_dict() {
        return {
            "text": self.text,
            "completed": self.completed
        }
    }
    
    func display() {
        let mark = "[x]" if self.completed else "[ ]"
        return f"{mark} {self.text}"
    }
}

func from_dict(data) {
    return Todo(data["text"], data["completed"])
}
```

---

## Step 3: Plan the Menu

```
==== TODO APP ====
1. Show all todos
2. Add todo
3. Complete todo
4. Delete todo
5. Save & Exit
==================
Choose option:
```

---

## Step 4: Core Data Structure

```sona
// Keep todos in a list
let todos = []

// Add a todo
func add_todo(text) {
    let todo = Todo(text)
    todos.append(todo)
    print(f"Added: {text}")
}

// Show all todos
func show_todos() {
    if len(todos) == 0 {
        print("No todos yet!")
        return
    }
    
    for i, todo in enumerate(todos) {
        print(f"{i + 1}. {todo.display()}")
    }
}
```

---

## Step 5: Think About Edge Cases

Before coding more, consider:

1. What if user enters invalid option?
2. What if todo file doesn't exist?
3. What if user tries to complete non-existent todo?
4. What if list is empty when completing?

**Good planning prevents bugs!**

---

## Project Planning Checklist

- [ ] Define what app does (features)
- [ ] Plan file structure
- [ ] Design data structures (classes)
- [ ] Plan user interface (menu)
- [ ] List edge cases to handle
- [ ] Decide on storage format (JSON)

---

## Coming Next

- **Mini 15.2**: Building core features
- **Mini 15.3**: Adding storage and polish
