# Sona v0.7.0 Examples

This directory contains working examples that demonstrate the actual capabilities of Sona v0.7.0. All examples have been tested and verified to work with the current interpreter.

## Available Examples

### Core Language Features

**basic_syntax.sona** - Fundamental language constructs

- Variable declarations and assignments
- String operations and concatenation
- Basic arithmetic operations
- Print statements and output

**dict_simple.sona** - Dictionary operations

- Dictionary creation with literal syntax
- Property access using dot notation
- Dynamic property addition
- Nested dictionary structures

**dictionary_operations.sona** - Advanced dictionary usage

- Complex dictionary manipulation
- Working with configuration objects
- User profile and data structures
- Property assignment patterns

### Module System

**modules_working.sona** - Module import and usage

- Importing standard library modules (math, string, time)
- Using module functions with proper syntax
- Available module functions and capabilities

**module_demo.sona** - Extended module examples

- Mathematical operations using math module
- String manipulation with string module
- Time and date operations with time module

### Data Processing

**data_processing.sona** - Real-world data manipulation

- Processing user data with dictionaries
- Sales data analysis and calculations
- Student grade processing and statistics
- Product inventory management
- Data aggregation and reporting

### Error Prevention

**error_handling.sona** - Best practices for error prevention

- Safe dictionary access patterns
- Proper data initialization
- Safe mathematical operations
- Input validation strategies
- Working with modules safely

## Language Features in v0.7.0

### Supported Features ✅

- Variables and assignments (`let variable = value`)
- Strings with concatenation (`"text" + variable`)
- Numbers (integers and floats)
- Dictionary literals (`{"key": "value"}`)
- Property access (`dict.property`)
- Dynamic property assignment (`dict.new_prop = value`)
- Module imports (`import module_name`)
- Module function calls (`module.function(args)`)
- Print statements (`print("text")`)
- Basic arithmetic (`+`, `-`, `*`, `/`)
- Comments (`// comment`)

### Not Available in v0.7.0 ❌

- Function definitions with parameters
- Object-oriented programming (classes, methods)
- Control flow (if/else, for/while loops)
- Boolean literals (`true`/`false` - use strings instead)
- Exception handling (try/catch)
- Advanced operators
- List/array operations

## Running Examples

To run any example file:

```bash
python -m sona examples/filename.sona
```

For example:

```bash
python -m sona examples/basic_syntax.sona
python -m sona examples/dict_simple.sona
python -m sona examples/data_processing.sona
```

## Available Standard Library Modules

### math module

- `sqrt(number)` - Square root
- `pow(base, exponent)` - Power operation
- `abs(number)` - Absolute value
- `floor(number)` - Floor function
- `ceil(number)` - Ceiling function

### string module

- `capitalize(text)` - Capitalize first letter
- `upper(text)` - Convert to uppercase
- `lower(text)` - Convert to lowercase
- `title(text)` - Title case conversion

### time module

- `now()` - Current timestamp
- Basic time operations

## Best Practices

1. **Always use quoted dictionary keys**: `{"key": "value"}` not `{key: "value"}`
2. **Initialize all dictionary properties**: Don't rely on dynamic property checking
3. **Use strings for boolean-like values**: `"yes"/"no"` instead of `true/false`
4. **Import modules before using their functions**
5. **Test examples with `python -m sona filename.sona`**
6. **Keep operations simple**: Complex logic may not be supported

## Notes

These examples represent the actual working capabilities of Sona v0.7.0. More advanced features like functions with parameters, object-oriented programming, and control flow statements are planned for future releases but are not functional in the current version.

For the latest updates and documentation, see the main project README.md.
