# Sona Demo Applications

This directory contains example applications showcasing Sona's capabilities in version 0.5.1. Run any demo using:

```sh
sona run <filename>
# or from REPL:
:run <appname>
```

## Demo Applications by Category

### Core Applications

| App Name              | Description                 | Modules                      | Run Command                                                                          |
| --------------------- | --------------------------- | ---------------------------- | ------------------------------------------------------------------------------------ |
| Calculator            | Basic arithmetic operations | `math`, `io`                 | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:calculator)            |
| Password Generator    | Generate secure passwords   | `random`, `string`           | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:password_generator)    |
| Quiz App              | Interactive quiz system     | `io`, `random`               | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:quiz_app)              |
| Note Writer           | Simple note-taking app      | `io`, `file`, `fmt`          | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:note_writer)           |
| Time Tracker          | Track time spent on tasks   | `io`, `time`, `fmt`, `file`  | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:time_tracker)          |
| Task List             | Todo list manager           | `io`, `file`, `time`, `fmt`  | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:task_list)             |
| Static Site Generator | Generate HTML from MD       | `io`, `file`, `fmt`, `path`  | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:static_site_generator) |
| Markdown Preview      | Live markdown previewer     | `io`, `file`, `path`, `time` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:markdown_preview)      |

### Games

| App Name        | Description               | Modules                    | Run Command                                                                    |
| --------------- | ------------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| Snake Game      | Classic snake game        | `console`, `stdin`, `time` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:snake_game)      |
| Memory Game     | Card matching memory game | `io`, `random`             | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:memory_game)     |
| Pattern Matcher | Pattern recognition game  | `io`, `random`             | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:pattern_matcher) |

### Utilities

| App Name        | Description                | Modules             | Run Command                                                                    |
| --------------- | -------------------------- | ------------------- | ------------------------------------------------------------------------------ |
| Loan Calculator | Calculate loan payments    | `math`, `io`, `fmt` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:loan_calculator) |
| Unit Converter  | Convert between units      | `math`, `io`        | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:unit_converter)  |
| File Writer     | Create and edit text files | `io`, `file`        | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:file_writer)     |

### Data Processing

| App Name        | Description          | Modules             | Run Command                                                                    |
| --------------- | -------------------- | ------------------- | ------------------------------------------------------------------------------ |
| Expense Tracker | Track daily expenses | `io`, `file`, `fmt` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:expense_tracker) |
| Data Formatter  | Format JSON/CSV data | `io`, `file`, `fmt` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:data_formatter)  |

### Web Tools

| App Name | Description        | Modules             | Run Command                                                             |
| -------- | ------------------ | ------------------- | ----------------------------------------------------------------------- |
| HTTP Get | Simple HTTP client | `http`, `io`, `fmt` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:http_get) |

### GUI Applications

| App Name              | Description               | Modules          | Run Command                                                                          |
| --------------------- | ------------------------- | ---------------- | ------------------------------------------------------------------------------------ |
| Color Picker          | RGB color selector        | `ui`, `color`    | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:color_picker)          |
| Time Tracker          | Track time spent on tasks | `time`, `io`     | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:time_tracker)          |
| Task List             | Todo list manager         | `io`, `fmt`      | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:task_list)             |
| Static Site Generator | Generate HTML from MD     | `markdown`, `io` | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:static_site_generator) |
| Data Formatter        | Format JSON/CSV data      | `fmt`, `io`      | [![Run](https://img.shields.io/badge/Sona-Run-blue)](sona:run:data_formatter)        |
