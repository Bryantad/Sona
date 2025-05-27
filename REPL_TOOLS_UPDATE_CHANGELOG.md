# Sona REPL Tools Update - Changelog

## Added

- Added `:apps` command to REPL to list available tools
- Added `:run <tool_name>` command to REPL to load and run specific tools
- Created README.md in repl_tools directory with usage documentation

## Changed

- Updated REPL help message to include new commands

## Implementation Details

- The `:apps` command scans the examples/repl_tools directory and lists all .sona files
- The `:run <tool_name>` command loads and executes a specified tool from the repl_tools directory
- Tools are automatically discovered, and their descriptions are extracted from file comments
- The implementation includes helpful error messages and suggestions for similar tool names if exact match not found
