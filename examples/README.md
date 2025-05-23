# Sona Language Demo Programs

This directory contains demo programs for Sona v0.5.0+ that showcase different features and capabilities of the language. These demos are designed to be accessible through the Sona REPL in both debug and regular modes.

## Available Demos

### 1. Data Analyzer (`data_analyzer.sona`)

A data processing and statistical analysis tool that demonstrates:

- Data collection and manipulation
- Statistical calculations (average, min/max, standard deviation)
- Text-based data visualization with histograms
- File import capabilities
- Menu-driven user interface

**Usage:**

```
sona run examples/data_analyzer.sona
```

**Features:**

- Add single or multiple data points
- Import data from files
- Display statistical analysis
- Generate histograms
- Sample data option for quick demos

### 2. ASCII Visualization (`ascii_visualization.sona`)

A comprehensive text-based visualization toolkit showing:

- Multiple chart types (bar, line, scatter, box, pie)
- Data scaling and normalization
- Custom text rendering algorithms
- Mathematical operations for visualization

**Usage:**

```
sona run examples/ascii_visualization.sona
```

**Features:**

- Bar charts with labels and values
- Line charts with point connections
- Scatter plots with coordinate mapping
- Box plots showing statistical distribution
- Pie charts with percentage calculations

### 3. Snake Game (`snake_game_fixed.sona`)

A console-based implementation of the classic Snake game that demonstrates:

- Game loop and state management
- User input handling
- Array manipulation
- Custom comparison functions
- Terminal-based drawing

**Usage:**

```
sona run examples/snake_game_fixed.sona
```

**Controls:**

- Use `up`, `down`, `left`, `right` to move the snake
- Type `exit` to quit

### 2. Timer Demo (`timer.sona`)

Demonstrates time-related functionality with:

- Countdown timer
- Stopwatch
- Sleep/delay function usage

**Usage:**

```
sona run examples/timer.sona
```

**Features:**

- Option 1: Create a countdown timer with specified seconds
- Option 2: Start a stopwatch (press Enter to stop)

### 3. Todo List (`todo.sona`)

An in-memory todo list application showcasing:

- Array operations
- Basic CRUD operations
- User interface design
- Input validation

**Usage:**

```
sona run examples/todo.sona
```

**Features:**

- Add new todo items
- List all pending todo items
- Mark todos as completed
- View completed items

### 4. File Writer (`file_writer.sona`)

File I/O operations demo showing:

- Writing to files
- Appending to files
- Reading file contents
- Creating timestamped log entries

**Usage:**

```
sona run examples/file_writer.sona
```

**Features:**

- Create new files with content
- Append to existing files
- Read and display file contents
- Create timestamped log entries

### 5. HTTP Client (`http_get.sona`)

Simulated HTTP requests demo showcasing:

- HTTP GET requests (with simulation fallback)
- JSON parsing and manipulation
- API endpoint interaction

**Usage:**

```
sona run examples/http_get.sona
```

**Features:**

- Predefined API endpoint examples
- JSON response handling
- Custom URL input option

### 8. Pattern Matcher (`pattern_matcher.sona`)

A text processing utility that demonstrates:

- String pattern matching with wildcards
- Text extraction between markers
- String transformations and manipulations
- Text statistics and analysis

**Usage:**

```
sona run examples/pattern_matcher.sona
```

**Features:**

- Pattern matching with \* and ? wildcards
- Extract text between delimiters
- Text transformations (upper/lower/title case)
- Text analysis with statistics
- Search and replace functionality

### 9. Memory Game (`memory_game.sona`)

An interactive card matching game showcasing:

- Array manipulation and randomization
- Game state management
- Interactive user interface
- Card shuffling algorithm implementation

**Usage:**

```
sona run examples/memory_game.sona
```

**Features:**

- 4x4 board with matching card pairs
- Visual game board representation
- Score and move tracking
- Card selection and matching logic

### 10. Functions Demo (`functions.sona`)

A comprehensive showcase of function capabilities in Sona:

- Basic function definitions and calls
- Function composition and nesting
- Recursive functions
- Functions with default parameters
- Functions that return collections

**Usage:**

```
sona run examples/functions.sona
```

**Features:**

- Various function examples with explanations
- Demonstration of return values and parameter passing
- Helper functions for comparisons
- Practical usage examples

### 11. Quiz Application (`quiz.sona`)

An interactive multi-category quiz application:

- Multiple choice questions across diverse topics
- Score tracking and analytics
- Category filtering
- Difficulty levels

**Usage:**

```
sona run examples/quiz.sona
```

**Features:**

- Select question categories
- Track performance statistics
- Explanations for answers
- Multiple difficulty levels

## Running in REPL

You can load any of these demos directly in the Sona REPL:

```
$ sona
Welcome to Sona v0.5.0
> import examples.data_analyzer
> import examples.ascii_visualization
> import examples.pattern_matcher
> import examples.memory_game
> import examples.snake_game_fixed
> import examples.timer
> import examples.todo
> import examples.file_writer
> import examples.http_get
> import examples.functions
> import examples.quiz
```

## Debug Mode

To run these demos in debug mode, use the `--debug` flag:

```
sona run --debug examples/snake_game_fixed.sona
```

In REPL debug mode:

```
$ sona --debug
Welcome to Sona v0.5.0 (Debug Mode)
> import examples.snake_game_fixed
```

## Common Issues and Solutions

- **Comparison operators**: Sona doesn't support operators like `<`, `>`, `<=`, `>=` directly. Use helper functions like `is_less_than()`, `is_greater_than()`, etc.
- **Boolean values**: Use integers (0 for false, 1 for true) instead of boolean literals
- **Return statements**: All return statements must include an expression (use `return 0` instead of just `return`)
- **Variable reassignment**: Use `let` keyword each time you reassign a variable
