# Sona REPL Tools

This directory contains utility tools that can be loaded and run directly from the Sona REPL. These tools are written in pure Sona syntax and showcase practical, production-grade functionality for real-world developer workflows.

## Available Tools

- **api_formatter**: Pretty-prints and validates JSON data with path extraction capabilities
- **color_picker**: Converts between RGB/HEX/HSL colors and provides color manipulation functions
- **markdown_preview**: Converts Markdown to HTML with support for headings, lists, and other elements
- **password_generator**: Creates secure passwords with custom settings and strength evaluation
- **task_manager**: Manages to-do lists with add/list/complete functionality and task priorities
- **time_tracker**: Tracks time spent on tasks with start/stop/pause functionality
- **unit_converter**: Converts between temperature, length, weight, and volume units

## Using the Tools in REPL

To use these tools in the Sona REPL:

1. Start the Sona REPL:

   ```
   $ sona repl
   ```

2. List available tools with:

   ```
   sona> :apps
   ```

3. Run a specific tool with:

   ```
   sona> :run <tool_name>
   ```

   For example:

   ```
   sona> :run unit_converter
   ```

4. Each tool provides its own help function. After loading a tool, typically you can run:
   ```
   sona> show_help()
   ```

## Creating Your Own Tools

You can create your own REPL tools by adding new `.sona` files to this directory. Follow these guidelines:

1. Include a description comment at the top of your file:

   ```
   // Description: Brief description of what your tool does
   ```

2. Implement a `show_help()` function to display usage information.

3. Use meaningful function and variable names with proper documentation.

4. Test thoroughly before committing.

Your tool will automatically appear in the `:apps` list and be available via the `:run` command.
