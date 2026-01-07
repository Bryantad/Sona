# Mini-Lesson 13.3: Example Projects

## Project 1: Todo List Application

A complete, working todo app with persistent storage.

```sona
// todo.sona - Complete Todo Application
import io
import json
import uuid
import time

// ========== Data Layer ==========

class TodoStorage {
    func init(filename = "todos.json") {
        self.filename = filename
        self.todos = []
        self.load()
    }
    
    func load() {
        if io.exists(self.filename) {
            self.todos = json.parse(io.read(self.filename))
        }
    }
    
    func save() {
        io.write(self.filename, json.stringify(self.todos, indent: 2))
    }
}

// ========== Business Logic ==========

class TodoService {
    func init() {
        self.storage = TodoStorage()
    }
    
    func add(title, due_date = null) {
        let todo = {
            "id": uuid.generate()[:8],
            "title": title,
            "due_date": due_date,
            "completed": false,
            "created": time.now().format("%Y-%m-%d %H:%M")
        }
        self.storage.todos.push(todo)
        self.storage.save()
        return todo
    }
    
    func complete(id) {
        for todo in self.storage.todos {
            if todo.id == id {
                todo.completed = true
                self.storage.save()
                return true
            }
        }
        return false
    }
    
    func delete(id) {
        for i, todo in enumerate(self.storage.todos) {
            if todo.id == id {
                self.storage.todos.remove(i)
                self.storage.save()
                return true
            }
        }
        return false
    }
    
    func list(show_completed = true) {
        if show_completed {
            return self.storage.todos
        }
        return self.storage.todos.filter(func(t) { return !t.completed })
    }
}

// ========== User Interface ==========

class TodoApp {
    func init() {
        self.service = TodoService()
    }
    
    func showMenu() {
        print("\n" + "=" * 40)
        print("       📋 TODO LIST")
        print("=" * 40)
        print("1. Add task")
        print("2. List all tasks")
        print("3. List pending tasks")
        print("4. Complete task")
        print("5. Delete task")
        print("6. Exit")
        print("-" * 40)
    }
    
    func displayTasks(todos) {
        if todos.length() == 0 {
            print("\n  No tasks found!")
            return
        }
        
        print("\n  ID       Status  Title")
        print("  " + "-" * 35)
        
        for todo in todos {
            let status = "✓" if todo.completed else "○"
            let due = ""
            if todo.due_date {
                due = " (due: {todo.due_date})"
            }
            print("  {todo.id}  [{status}]    {todo.title}{due}")
        }
    }
    
    func addTask() {
        print("\n--- Add New Task ---")
        let title = input("Title: ")
        if title.strip() == "" {
            print("❌ Title cannot be empty!")
            return
        }
        
        let due = input("Due date (YYYY-MM-DD or blank): ")
        due = due if due.strip() != "" else null
        
        let todo = self.service.add(title, due)
        print("✅ Added task: {todo.title} (ID: {todo.id})")
    }
    
    func completeTask() {
        print("\n--- Complete Task ---")
        let id = input("Enter task ID: ")
        
        if self.service.complete(id) {
            print("✅ Task marked complete!")
        } else {
            print("❌ Task not found!")
        }
    }
    
    func deleteTask() {
        print("\n--- Delete Task ---")
        let id = input("Enter task ID: ")
        
        if self.service.delete(id) {
            print("✅ Task deleted!")
        } else {
            print("❌ Task not found!")
        }
    }
    
    func run() {
        print("\n🎯 Welcome to Todo List!")
        
        loop {
            self.showMenu()
            let choice = input("Choice: ")
            
            match choice {
                "1" => self.addTask()
                "2" => self.displayTasks(self.service.list())
                "3" => self.displayTasks(self.service.list(false))
                "4" => self.completeTask()
                "5" => self.deleteTask()
                "6" => {
                    print("\n👋 Goodbye!")
                    break
                }
                _ => print("Invalid choice!")
            }
        }
    }
}

// ========== Run App ==========
let app = TodoApp()
app.run()
```

---

## Project 2: Quiz Game

An interactive quiz with scoring:

```sona
// quiz.sona - Quiz Game
import random

class Question {
    func init(text, options, correct) {
        self.text = text
        self.options = options
        self.correct = correct
    }
    
    func display() {
        print("\n" + self.text)
        for i, option in enumerate(self.options) {
            print("  {i + 1}. {option}")
        }
    }
    
    func check(answer) {
        return answer == self.correct
    }
}

class Quiz {
    func init(title) {
        self.title = title
        self.questions = []
        self.score = 0
    }
    
    func addQuestion(text, options, correct) {
        self.questions.push(Question(text, options, correct))
    }
    
    func shuffle() {
        self.questions = random.shuffle(self.questions)
    }
    
    func run() {
        print("\n" + "=" * 50)
        print("  🧠 {self.title}")
        print("=" * 50)
        print("Answer each question by entering the number.")
        print("You'll see your score at the end!\n")
        
        self.score = 0
        let total = self.questions.length()
        
        for i, q in enumerate(self.questions) {
            print("\nQuestion {i + 1} of {total}")
            q.display()
            
            let answer = input("\nYour answer (1-{q.options.length()}): ")
            
            try {
                let answerNum = int(answer)
                if q.check(answerNum) {
                    print("✅ Correct!")
                    self.score = self.score + 1
                } else {
                    print("❌ Wrong! The answer was {q.correct}")
                }
            } catch {
                print("❌ Invalid input! Counted as wrong.")
            }
        }
        
        self.showResults(total)
    }
    
    func showResults(total) {
        let percentage = (self.score / total) * 100
        
        print("\n" + "=" * 50)
        print("  📊 RESULTS")
        print("=" * 50)
        print("Score: {self.score} / {total} ({percentage}%)")
        
        if percentage >= 90 {
            print("🏆 Excellent! You're a master!")
        } else if percentage >= 70 {
            print("⭐ Great job!")
        } else if percentage >= 50 {
            print("👍 Good effort! Keep learning!")
        } else {
            print("📚 Keep studying! You'll get better!")
        }
    }
}

// Create and run a quiz
let quiz = Quiz("Sona Programming Quiz")

quiz.addQuestion(
    "What keyword declares a variable in Sona?",
    ["var", "let", "define", "set"],
    2  // let
)

quiz.addQuestion(
    "Which symbol is used for comments?",
    ["#", "//", "/*", "--"],
    2  // //
)

quiz.addQuestion(
    "How do you define a function?",
    ["function name()", "def name():", "func name() {}", "fn name() =>"],
    3  // func
)

quiz.addQuestion(
    "What method adds to the end of a list?",
    ["add()", "append()", "push()", "insert()"],
    3  // push
)

quiz.addQuestion(
    "How do you create a class?",
    ["class Name {}", "Class Name:", "define class Name", "new class Name()"],
    1  // class Name {}
)

quiz.shuffle()
quiz.run()
```

---

## Project 3: Simple Calculator

A calculator with history:

```sona
// calculator.sona - Calculator with History

class Calculator {
    func init() {
        self.history = []
        self.lastResult = 0
    }
    
    func add(a, b) {
        let result = a + b
        self._record("{a} + {b} = {result}")
        return result
    }
    
    func subtract(a, b) {
        let result = a - b
        self._record("{a} - {b} = {result}")
        return result
    }
    
    func multiply(a, b) {
        let result = a * b
        self._record("{a} × {b} = {result}")
        return result
    }
    
    func divide(a, b) {
        if b == 0 {
            self._record("{a} ÷ {b} = ERROR (division by zero)")
            return null
        }
        let result = a / b
        self._record("{a} ÷ {b} = {result}")
        return result
    }
    
    func power(a, b) {
        let result = a ** b
        self._record("{a} ^ {b} = {result}")
        return result
    }
    
    func sqrt(a) {
        if a < 0 {
            self._record("√{a} = ERROR (negative number)")
            return null
        }
        let result = a ** 0.5
        self._record("√{a} = {result}")
        return result
    }
    
    func _record(entry) {
        self.history.push(entry)
        if self.history.length() > 10 {
            self.history.remove(0)
        }
    }
    
    func showHistory() {
        if self.history.length() == 0 {
            print("No history yet!")
            return
        }
        print("\n📜 History:")
        for i, entry in enumerate(self.history) {
            print("  {i + 1}. {entry}")
        }
    }
    
    func clearHistory() {
        self.history = []
        print("History cleared!")
    }
}

class CalculatorApp {
    func init() {
        self.calc = Calculator()
    }
    
    func showMenu() {
        print("\n🔢 CALCULATOR")
        print("-" * 30)
        print("1. Add (+)")
        print("2. Subtract (-)")
        print("3. Multiply (×)")
        print("4. Divide (÷)")
        print("5. Power (^)")
        print("6. Square Root (√)")
        print("7. History")
        print("8. Clear History")
        print("9. Exit")
        print("-" * 30)
    }
    
    func getNumber(prompt) {
        loop {
            let value = input(prompt)
            try {
                return float(value)
            } catch {
                print("Please enter a valid number!")
            }
        }
    }
    
    func doOperation(op) {
        let a = self.getNumber("First number: ")
        
        let result = null
        if op == "sqrt" {
            result = self.calc.sqrt(a)
        } else {
            let b = self.getNumber("Second number: ")
            match op {
                "add" => result = self.calc.add(a, b)
                "sub" => result = self.calc.subtract(a, b)
                "mul" => result = self.calc.multiply(a, b)
                "div" => result = self.calc.divide(a, b)
                "pow" => result = self.calc.power(a, b)
            }
        }
        
        if result != null {
            print("\n✨ Result: {result}")
        }
    }
    
    func run() {
        print("\n👋 Welcome to Calculator!")
        
        loop {
            self.showMenu()
            let choice = input("Choice: ")
            
            match choice {
                "1" => self.doOperation("add")
                "2" => self.doOperation("sub")
                "3" => self.doOperation("mul")
                "4" => self.doOperation("div")
                "5" => self.doOperation("pow")
                "6" => self.doOperation("sqrt")
                "7" => self.calc.showHistory()
                "8" => self.calc.clearHistory()
                "9" => {
                    print("\n👋 Goodbye!")
                    break
                }
                _ => print("Invalid choice!")
            }
        }
    }
}

let app = CalculatorApp()
app.run()
```

---

## Project 4: Contact Manager

```sona
// contacts.sona - Contact Manager
import io
import json
import uuid

class Contact {
    func init(name, phone = null, email = null) {
        self.id = uuid.generate()[:8]
        self.name = name
        self.phone = phone
        self.email = email
    }
    
    func toDict() {
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email
        }
    }
    
    func display() {
        print("\n  📇 {self.name}")
        print("     ID: {self.id}")
        if self.phone {
            print("     📞 {self.phone}")
        }
        if self.email {
            print("     ✉️  {self.email}")
        }
    }
}

class ContactManager {
    func init(filename = "contacts.json") {
        self.filename = filename
        self.contacts = []
        self.load()
    }
    
    func load() {
        if io.exists(self.filename) {
            let data = json.parse(io.read(self.filename))
            for item in data {
                let c = Contact(item.name, item.phone, item.email)
                c.id = item.id
                self.contacts.push(c)
            }
        }
    }
    
    func save() {
        let data = self.contacts.map(func(c) { return c.toDict() })
        io.write(self.filename, json.stringify(data, indent: 2))
    }
    
    func add(name, phone = null, email = null) {
        let contact = Contact(name, phone, email)
        self.contacts.push(contact)
        self.save()
        return contact
    }
    
    func find(id) {
        for c in self.contacts {
            if c.id == id {
                return c
            }
        }
        return null
    }
    
    func search(query) {
        query = query.lower()
        return self.contacts.filter(func(c) {
            return query in c.name.lower() or
                   (c.phone and query in c.phone) or
                   (c.email and query in c.email.lower())
        })
    }
    
    func delete(id) {
        for i, c in enumerate(self.contacts) {
            if c.id == id {
                self.contacts.remove(i)
                self.save()
                return true
            }
        }
        return false
    }
    
    func all() {
        return self.contacts
    }
}

class ContactApp {
    func init() {
        self.manager = ContactManager()
    }
    
    func showMenu() {
        print("\n" + "=" * 40)
        print("       📒 CONTACT MANAGER")
        print("=" * 40)
        print("1. Add contact")
        print("2. List all contacts")
        print("3. Search contacts")
        print("4. Delete contact")
        print("5. Exit")
        print("-" * 40)
    }
    
    func addContact() {
        print("\n--- Add New Contact ---")
        let name = input("Name: ")
        if name.strip() == "" {
            print("❌ Name is required!")
            return
        }
        
        let phone = input("Phone (or blank): ")
        phone = phone if phone.strip() != "" else null
        
        let email = input("Email (or blank): ")
        email = email if email.strip() != "" else null
        
        let contact = self.manager.add(name, phone, email)
        print("✅ Contact added!")
        contact.display()
    }
    
    func listContacts() {
        let contacts = self.manager.all()
        if contacts.length() == 0 {
            print("\n📒 No contacts yet!")
            return
        }
        
        print("\n📒 All Contacts ({contacts.length()}):")
        for c in contacts {
            c.display()
        }
    }
    
    func searchContacts() {
        let query = input("Search: ")
        let results = self.manager.search(query)
        
        if results.length() == 0 {
            print("No contacts found matching '{query}'")
            return
        }
        
        print("\n🔍 Found {results.length()} contact(s):")
        for c in results {
            c.display()
        }
    }
    
    func deleteContact() {
        let id = input("Contact ID to delete: ")
        if self.manager.delete(id) {
            print("✅ Contact deleted!")
        } else {
            print("❌ Contact not found!")
        }
    }
    
    func run() {
        print("\n👋 Welcome to Contact Manager!")
        
        loop {
            self.showMenu()
            let choice = input("Choice: ")
            
            match choice {
                "1" => self.addContact()
                "2" => self.listContacts()
                "3" => self.searchContacts()
                "4" => self.deleteContact()
                "5" => {
                    print("\n👋 Goodbye!")
                    break
                }
                _ => print("Invalid choice!")
            }
        }
    }
}

let app = ContactApp()
app.run()
```

---

## Module 13 Complete! 🎉

You've learned:
- ✅ Planning projects effectively
- ✅ Debugging and testing code
- ✅ Building complete applications

→ Next: [Module 14: Testing & Quality](../14_testing/README.md)
