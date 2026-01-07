# Module 03: Functions

**Learn to create reusable blocks of code.**

---

## 🎯 Module Goals

By the end of this module, you will:
- Understand what functions are and why they're useful
- Create your own functions
- Pass information into functions (parameters)
- Get information back from functions (return values)

---

## 📚 Lessons in This Module

| # | Lesson | Duration | Description |
|---|--------|----------|-------------|
| 1 | [Parameters](mini-1_params.md) | 15 min | Passing data into functions |
| 2 | [Return Values](mini-2_return.md) | 15 min | Getting data back from functions |

---

## 🧠 Key Concepts Preview

- **Function** = A named, reusable block of code
- **Parameter** = A variable that receives input when the function is called
- **Argument** = The actual value passed to a parameter
- **Return value** = The result a function sends back

---

## 💡 Analogy: Functions are like Recipes

A recipe:
- Has a **name** ("Chocolate Cake")
- Takes **ingredients** (eggs, flour, sugar)
- Follows **steps** (mix, bake, cool)
- Produces a **result** (a cake!)

A function:
- Has a **name** (`calculate_total`)
- Takes **parameters** (`price`, `quantity`)
- Follows **code** (multiply, add tax)
- Produces a **return value** (`final_price`)

---

## 💻 Quick Preview

```sona
// Define a function
func greet(name) {
    print("Hello, " + name + "!")
}

// Call (use) the function
greet("Alex")    // Output: Hello, Alex!
greet("Jordan")  // Output: Hello, Jordan!
```

---

## 💡 Tips for This Module

### For Beginners
- Functions might feel abstract at first — that's normal
- Focus on the **pattern**: define once, use many times
- Every function you write saves you from repeating code

### For Neurodivergent Learners
- Think of functions as "teaching the computer a new word"
- Once you define `greet()`, you can use it forever
- Start simple — one line functions, then build up

---

## 🔗 Prerequisites

- [Module 02: Basics](../02_basics/) — Variables and expressions

---

## ✅ Module Checkpoint

After completing this module, you should be able to:
- [ ] Define a function with `func`
- [ ] Call functions with different arguments
- [ ] Use parameters inside functions
- [ ] Return values from functions
- [ ] Understand why functions help avoid repetition

---

## ➡️ Next Module

[Module 04: Control Flow](../04_control_flow/) — Making decisions and loops
