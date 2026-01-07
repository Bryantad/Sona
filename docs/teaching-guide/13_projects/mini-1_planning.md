# Mini-Lesson 13.1: Project Planning

## Why Plan?

Jumping straight into code often leads to:
- 🔄 Rewriting the same thing
- 😵 Getting lost in complexity
- 🐛 More bugs
- 😤 Frustration

A little planning saves a lot of time!

---

## Step 1: Define What You're Building

Write down clearly:

### Bad Example ❌
"I want to make a todo app"

### Good Example ✅
"A todo app that can:
- Add tasks with a title and due date
- Mark tasks as complete
- Delete tasks
- Show all tasks, sorted by due date
- Save tasks between sessions"

---

## Step 2: List Your Features

Break it into specific features:

```
Todo App Features:
1. Add task (title, due date)
2. List all tasks
3. List pending tasks only
4. Mark task complete
5. Delete task
6. Save to file
7. Load from file
```

---

## Step 3: Design Your Data

What information do you need to store?

```sona
// A single task
let task = {
    "id": "abc123",          // Unique identifier
    "title": "Buy groceries", // What to do
    "due_date": "2024-01-15", // When it's due
    "completed": false,       // Is it done?
    "created_at": "2024-01-10 09:30:00"
}

// Collection of tasks
let tasks = [task1, task2, task3]
```

---

## Step 4: Plan Your Functions

List functions you'll need:

```
Functions needed:
- addTask(title, due_date) -> task
- getTasks() -> list
- getPendingTasks() -> list
- completeTask(id) -> success?
- deleteTask(id) -> success?
- saveTasks() -> none
- loadTasks() -> none
```

---

## Step 5: Organize Your Files

For small projects (one file):
```
todo.sona        # Everything in one file
```

For medium projects:
```
todo/
├── main.sona    # Entry point, user interface
├── task.sona    # Task class/functions
└── storage.sona # Save/load functions
```

For larger projects:
```
todo/
├── main.sona
├── models/
│   └── task.sona
├── services/
│   ├── task_service.sona
│   └── storage_service.sona
└── utils/
    └── date_utils.sona
```

---

## Step 6: Build in Stages

Don't try to build everything at once!

### Stage 1: Core (Get it Working)
```sona
// Just make it work - no saving yet
let tasks = []

func addTask(title) {
    tasks.push({"title": title, "done": false})
}

func listTasks() {
    for task in tasks {
        print(task.title)
    }
}

// Test it!
addTask("Test task")
listTasks()
```

### Stage 2: Improve (Add Features)
```sona
// Add proper IDs and dates
import uuid
import time

func addTask(title, due_date = null) {
    let task = {
        "id": uuid.generate(),
        "title": title,
        "due_date": due_date,
        "completed": false,
        "created_at": time.now().format("%Y-%m-%d %H:%M")
    }
    tasks.push(task)
    return task
}
```

### Stage 3: Polish (User Experience)
```sona
// Nice formatted output
func listTasks() {
    if tasks.length() == 0 {
        print("📋 No tasks yet!")
        return
    }
    
    print("📋 Your Tasks:")
    print("-" * 40)
    for i, task in enumerate(tasks) {
        let status = "✓" if task.completed else "○"
        let due = task.due_date or "No due date"
        print("{i+1}. [{status}] {task.title}")
        print("      Due: {due}")
    }
}
```

### Stage 4: Save (Persistence)
```sona
// Add storage
import io
import json

func saveTasks() {
    io.write("tasks.json", json.stringify(tasks, indent: 2))
    print("✅ Tasks saved!")
}

func loadTasks() {
    if io.exists("tasks.json") {
        tasks = json.parse(io.read("tasks.json"))
        print("📥 Loaded {tasks.length()} tasks")
    }
}
```

---

## Creating a Project Checklist

```markdown
## My Project Checklist

### Planning
- [ ] Clear description written
- [ ] Features listed
- [ ] Data structures designed
- [ ] Functions planned
- [ ] File structure decided

### Building
- [ ] Stage 1: Core working
- [ ] Stage 2: All features added
- [ ] Stage 3: User experience polished
- [ ] Stage 4: Data persistence added

### Testing
- [ ] All features tested manually
- [ ] Edge cases handled
- [ ] Error messages helpful

### Polish
- [ ] Code is readable
- [ ] Comments added where needed
- [ ] README written
```

---

## Common Beginner Mistakes

### 1. Starting Too Big
❌ "I'll build a full social network!"  
✅ Start with: "I'll build a profile page"

### 2. No Testing as You Go
❌ Write 200 lines, then test  
✅ Write 10 lines, test, write 10 more

### 3. Ignoring Errors
❌ "It works if I enter the right thing"  
✅ Handle what happens with wrong input

### 4. No Saves
❌ Building for hours without saving  
✅ Save after each working feature

---

## Practice

### Exercise 1
Plan a simple contact manager. Write:
- Feature list
- Data structure for a contact
- List of functions needed

### Exercise 2
Create a checklist for a number guessing game project.

### Exercise 3
Take an existing idea and break it into 4 stages (core → improve → polish → save).

---

→ Next: [mini-2: Debugging & Testing](mini-2_debugging.md)
