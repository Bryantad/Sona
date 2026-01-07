# Mini-Episode 1.2: Running Your First Code

**Duration**: ~15 minutes  
**Difficulty**: ⭐ Beginner  
**Prerequisites**: [Mini-Episode 1.1: What is Sona?](mini-1_what_is_sona.md)

---

## 📦 What You'll Learn

- [ ] How to set up Sona on your computer
- [ ] How to create a Sona file
- [ ] How to run your first program
- [ ] What to do when something goes wrong

---

## 🎯 Why This Matters

Reading about code is like reading about swimming — you can understand the concept, but you won't really *get it* until you jump in the water. This lesson gets you actually running code.

---

## 🧩 Setting Up (3 Ways)

### Option 1: VS Code (Recommended)

1. **Install VS Code** — Download from [code.visualstudio.com](https://code.visualstudio.com)
2. **Install Sona Extension** — Search "Sona" in Extensions (Ctrl+Shift+X)
3. **Install Python** — Sona runs on Python ([python.org](https://python.org))

### Option 2: Command Line

If you already have Python installed:
```
pip install sona-lang
```

### Option 3: Online (Coming Soon)

Try Sona in your browser at [try.sonalang.com](https://try.sonalang.com) *(placeholder)*

---

## 💻 Your First Program

### Step 1: Create a File

1. Open VS Code
2. Create a new file: `File → New File`
3. Save it as `hello.sona`

### Step 2: Write the Code

Type this exactly:

```sona
print("Hello, world!")
```

### Step 3: Run It

**In VS Code:**
- Press `F5` to run

**In Terminal:**
```
python run_sona.py hello.sona
```

### Step 4: See the Result

You should see:
```
Hello, world!
```

🎉 **Congratulations!** You just ran your first program!

---

## 🔬 Try It Yourself

### Exercise 1: Change the Message

**Goal**: Make the program say something different

**Steps**:
1. Open your `hello.sona` file
2. Change `"Hello, world!"` to your own message
3. Run it again

**Example**:
```sona
print("My name is Sona and I am awesome!")
```

### Exercise 2: Multiple Lines

**Goal**: Print multiple messages

**Steps**:
1. Add more `print()` lines
2. Run and see what happens

**Example**:
```sona
print("Line 1")
print("Line 2")
print("Line 3")
```

**Expected output**:
```
Line 1
Line 2
Line 3
```

---

## 🧠 Common Mistakes

### ❌ Mistake 1: Missing Quotes

```sona
print(Hello, world!)  // ❌ Wrong
```

**Why it's wrong**: Text needs to be in quotes so Sona knows it's text.

**Correct version**:
```sona
print("Hello, world!")  // ✅ Correct
```

### ❌ Mistake 2: Wrong Parentheses

```sona
print["Hello, world!"]  // ❌ Wrong — square brackets
print{"Hello, world!"}  // ❌ Wrong — curly brackets
```

**Correct version**:
```sona
print("Hello, world!")  // ✅ Correct — round parentheses
```

### ❌ Mistake 3: Typo in `print`

```sona
Print("Hello!")  // ❌ Wrong — capital P
pirnt("Hello!")  // ❌ Wrong — typo
```

**Correct version**:
```sona
print("Hello!")  // ✅ Correct — lowercase
```

---

## 🆘 Troubleshooting

### "Command not found" or "sona not recognized"

**Problem**: Sona isn't installed properly

**Solution**:
1. Make sure Python is installed: `python --version`
2. Install Sona: `pip install sona-lang`

### "File not found"

**Problem**: You're in the wrong folder

**Solution**:
1. Open the folder containing your `.sona` file
2. Or use the full path: `python run_sona.py C:\path\to\hello.sona`

### "Syntax error"

**Problem**: There's a typo in your code

**Solution**:
1. Check for missing quotes, parentheses, or typos
2. Compare your code letter-by-letter with the example

---

## ✅ Checkpoint

1. **What file extension do Sona files use?**
   <details><summary>Answer</summary>.sona</details>

2. **What key runs code in VS Code?**
   <details><summary>Answer</summary>F5</details>

3. **What must text always be wrapped in?**
   <details><summary>Answer</summary>Quotes (either "double" or 'single')</details>

---

## 🎉 Module Complete!

You've finished Module 01! You now know:
- What Sona is
- How to run Sona programs
- How to fix common mistakes

---

## ➡️ Next Module

[Module 02: Basics](../02_basics/) — Learn about variables and expressions
