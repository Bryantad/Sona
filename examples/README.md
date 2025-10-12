# Sona Examples

This directory contains practical examples demonstrating Sona's capabilities.

## 📚 Available Examples

### 1. [hello_world.sona](./hello_world.sona)

**Difficulty**: ⭐☆☆☆☆ (Beginner)

The simplest Sona program - print "Hello, World!".

```bash
python run_sona.py examples/hello_world.sona
```

**What you'll learn:**

- Basic print statements
- Running Sona scripts

---

### 2. [file_processor.sona](./file_processor.sona)

**Difficulty**: ⭐⭐☆☆☆ (Beginner)

Process files in a directory - list and filter .sona files.

```bash
python run_sona.py examples/file_processor.sona
```

**What you'll learn:**

- File system operations (`fs`)
- Path manipulation (`path`)
- String operations (`string`)
- Array filtering
- For loops

**Modules used:** `fs`, `path`, `io`, `string`

---

### 3. [json_processor.sona](./json_processor.sona)

**Difficulty**: ⭐⭐☆☆☆ (Beginner)

Work with JSON data - create, save, load, and parse JSON.

```bash
python run_sona.py examples/json_processor.sona
```

**What you'll learn:**

- JSON parsing and serialization
- File I/O operations
- Working with objects and arrays
- Data transformation

**Modules used:** `json`, `io`, `string`

**Output:** Creates `users.json` file

---

### 4. [csv_analysis.sona](./csv_analysis.sona)

**Difficulty**: ⭐⭐⭐☆☆ (Intermediate)

CSV data processing and statistical analysis.

```bash
python run_sona.py examples/csv_analysis.sona
```

**What you'll learn:**

- CSV reading and parsing
- Data analysis
- Statistical functions
- Number parsing
- Data aggregation

**Modules used:** `csv`, `io`, `statistics`

**Output:** Creates `students.csv` file

---

### 5. [data_structures.sona](./data_structures.sona)

**Difficulty**: ⭐⭐⭐☆☆ (Intermediate)

Using advanced data structures - collections, queues, and stacks.

```bash
python run_sona.py examples/data_structures.sona
```

**What you'll learn:**

- Collection utilities (first, last, range, len)
- Queue operations (FIFO - First In, First Out)
- Stack operations (LIFO - Last In, First Out)
- When to use each data structure

**Modules used:** `collection`, `queue`, `stack`

**Use cases:**

- **Queue**: Task scheduling, message processing, breadth-first search
- **Stack**: Undo/redo, navigation history, depth-first search

---

### 6. [control_flow.sona](./control_flow.sona)

**Difficulty**: ⭐⭐☆☆☆ (Beginner)

Control flow patterns - loops, conditionals, break, continue.

```bash
python run_sona.py examples/control_flow.sona
```

**What you'll learn:**

- If/elif/else conditionals
- For loops
- While loops
- Break statements (exit loop early)
- Continue statements (skip iteration)
- Nested loops

**Modules used:** `math`

---

## 🚀 Running Examples

### Run Single Example

```bash
python run_sona.py examples/hello_world.sona
```

### Run All Examples

```bash
# PowerShell
Get-ChildItem examples/*.sona | ForEach-Object { python run_sona.py $_.FullName }

# Bash
for file in examples/*.sona; do python run_sona.py "$file"; done
```

---

## 📖 Learning Path

### Beginner Path:

1. `hello_world.sona` - Basic syntax
2. `file_processor.sona` - File operations
3. `json_processor.sona` - Data handling
4. `control_flow.sona` - Logic and loops

### Intermediate Path:

5. `csv_analysis.sona` - Data analysis
6. `data_structures.sona` - Advanced structures

---

## 🎯 Next Steps

After completing these examples, check out:

- **[docs/projects/RESEARCH_SONA_PROJECTS.md](../docs/projects/RESEARCH_SONA_PROJECTS.md)** - 8 detailed project ideas
- **[docs/guides/README.md](../docs/guides/README.md)** - Comprehensive tutorials
- **[docs/features/STDLIB_30_MODULES.md](../docs/features/STDLIB_30_MODULES.md)** - All 30 stdlib modules

---

## 💡 Tips

- **Start small**: Begin with hello_world.sona
- **Experiment**: Modify examples to see what happens
- **Read comments**: Examples include explanatory comments
- **Check output**: Run examples to see results
- **Build on them**: Use examples as templates for your projects

---

## 🤝 Contributing Examples

Have a great example? We'd love to include it!

1. Create your example in `examples/`
2. Add clear comments
3. Update this README
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## 📚 Example Categories

### Data Processing

- `json_processor.sona` - JSON handling
- `csv_analysis.sona` - CSV processing

### File Operations

- `file_processor.sona` - File system tasks

### Language Features

- `hello_world.sona` - Basic syntax
- `control_flow.sona` - Loops and conditionals
- `data_structures.sona` - Advanced data types

---

**Happy coding with Sona!** 🎉
