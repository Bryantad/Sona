# Sona Studio 1.0 Beta (GUI Launcher)

A modern graphical interface for the Sona programming language that makes it easy to explore examples, write code, and learn the language.

# Quick Start

```bash
# Clone the repository
git clone https://github.com/Bryantad/Sona.git
cd Sona

# Launch the GUI (basic interface)
python launcher.py

# Or for the enhanced modern interface, first install PySide6:
pip install PySide6
python launcher.py
```

## Features

Note: The GUI is branded as "Sona Studio 1.0 Beta" for this release. The
Sona language runtime and tooling remain at version 0.9.1 — this change is a
UI/packaging upgrade only and does not modify the language or runtime.

### 🎯 **Dual Interface Support**

- **Modern Interface** (PySide6) - Professional, responsive UI with advanced features
- **Classic Interface** (Tkinter) - Reliable fallback that works everywhere

### 📁 **Example Browser**

- Browse all Sona language examples
- Search and filter examples
- Quick preview of code content
- One-click execution

### 💻 **Interactive Development**

- Built-in REPL for testing code snippets
- Real-time output console
- Syntax highlighting for Sona code
- Error highlighting and reporting

### 🎮 **Embedded Applications**

- Run games and interactive demos directly in the GUI
- Calculator, Snake, Tetris, and more
- Seamless switching between code view and application view

## Interface Comparison

| Feature        | Classic (Tkinter) | Modern (PySide6)    |
| -------------- | ----------------- | ------------------- |
| Availability   | ✅ Always works   | ⚡ Requires PySide6 |
| Performance    | Good              | Excellent           |
| Visual Design  | Standard          | Professional        |
| Responsiveness | Standard          | Smooth              |
| Features       | Full              | Enhanced            |

## Installation Options

### Option 1: Basic Setup (Tkinter only)

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
python launcher.py
```

### Option 2: Enhanced Setup (with modern UI)

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
pip install PySide6
python launcher.py
```

### Option 3: Full Development Setup

```bash
git clone https://github.com/Bryantad/Sona.git
cd Sona
pip install -r requirements.txt
python launcher.py
```

## Troubleshooting

### GUI won't start

- **Check Python version**: Requires Python 3.8+
- **Check tkinter**: `python -m tkinter` should show a test window
- **Try fallback**: If modern UI fails, classic UI will start automatically

### PySide6 not working

```bash
# Reinstall PySide6
pip uninstall PySide6
pip install PySide6

# Test installation
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 works!')"
```

### Examples not loading

- Ensure you're in the Sona directory when running `python launcher.py`
- Check that the `examples/` folder exists and contains `.sona` files

## Development

The GUI launcher consists of:

- `launcher.py` - Main entry point with auto-detection
- `gui/gui_launcher.py` - Classic Tkinter interface
- `gui/modern/launcher.py` - Modern PySide6 interface
- `run_gui.py` - Development launcher script

## Contributing

1. Fork the repository
2. Make your changes
3. Test with both interfaces: `python launcher.py`
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
