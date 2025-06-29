# Sona Modern GUI Launcher v0.7.0

## Overview

The modernized Sona GUI Launcher provides a sophisticated, configuration-driven desktop application hub for the Sona programming language platform. It features a collapsible sidebar navigation, theme switching, modular application loading, and a responsive modern UI.

## Features

### 🎨 Modern UI Design

- **Dark Theme**: Professional dark theme with blue accents
- **Light Theme**: Clean light theme option
- **Responsive Layout**: Adaptive UI that works on various screen sizes
- **Collapsible Sidebar**: Space-efficient navigation with icon mode

### 🔧 Configuration-Driven Architecture

- **Theme Configuration**: JSON-based theme system (`gui/config/themes.json`)
- **Application Registry**: Modular app loading via `gui/config/applications.json`
- **Plugin-Ready**: Extensible architecture for future plugins

### 📱 Core Interface Components

#### Top Bar

- **Platform Info**: Shows Sona version
- **Context Display**: Current application/activity indicator
- **Theme Switcher**: Live theme changing
- **Console Toggle**: Show/hide embedded console
- **Sidebar Toggle**: Collapse/expand navigation

#### Sidebar Navigation

- **Categorized Applications**: Organized by type (Dev Tools, Games, Examples, etc.)
- **Collapsible Categories**: Expand/collapse category sections
- **Quick Launch**: One-click application launching
- **Icon Mode**: Compact collapsed view

#### Main Content Area

- **Dynamic Content**: Context-aware content rendering
- **Application Embedding**: Support for embedded GUI applications
- **Code Display**: Syntax-aware code viewing for examples
- **Welcome Dashboard**: Getting started information

#### Embedded Console

- **Real-time Output**: Live streaming of application output
- **Clear Function**: Easy console cleanup
- **Scrollback**: Full output history
- **Resizable**: Adjustable console height

### 🚀 Application Support

#### Built-in Applications

- **Sona REPL**: Interactive language console
- **Code Editor**: Edit and run Sona code
- **Example Browser**: Browse and run example programs

#### Game Applications

- Calculator, Snake Game, Ping Pong, Space Shooter, Invaders
- Flappy Bird, Visual Novel, Endless Runner, Platformer
- Doom 2D, Bejeweled, Painter, Solitaire, Tetris, Mahjong
- Bubble Shooter, Sudoku

#### Utility Applications

- Todo Manager, Notes Manager, Calendar
- File Organizer, Media Player, Text Editor

### ⚙️ Configuration Files

#### `gui/config/themes.json`

Defines available themes with color schemes, fonts, and styling:

```json
{
  "themes": [
    {
      "id": "dark",
      "name": "Dark Theme",
      "isDefault": true,
      "colors": {
        "background": "#1e1e1e",
        "sidebar": "#252526",
        "content": "#282828",
        "text": "#e0e0e0",
        "accent": "#2979ff"
      },
      "fonts": {
        "main": { "family": "Segoe UI" },
        "code": { "family": "Consolas" }
      }
    }
  ]
}
```

#### `gui/config/applications.json`

Defines application categories and registry:

```json
{
  "categories": [
    {
      "id": "dev_tools",
      "name": "Developer Tools",
      "icon": "code",
      "defaultExpanded": true
    }
  ],
  "applications": [
    {
      "id": "sona_repl",
      "name": "Sona REPL",
      "category": "dev_tools",
      "module": "repl_app",
      "class": "SonaREPLApp"
    }
  ]
}
```

## Usage

### Running the Launcher

#### Modern Interface (Default)

```bash
python gui/gui_launcher.py
# or
python gui/gui_launcher.py --modern
```

#### Legacy Interface

```bash
python gui/gui_launcher.py --legacy
```

### Keyboard Shortcuts

- **F11**: Toggle fullscreen
- **Ctrl+Shift+C**: Toggle console
- **Ctrl+B**: Toggle sidebar
- **Ctrl+,**: Open settings (future)

### Navigation

1. **Browse Applications**: Use the sidebar to explore available apps
2. **Launch Applications**: Click any app in the sidebar to launch
3. **Switch Themes**: Use the theme dropdown in the top bar
4. **View Output**: Monitor the embedded console for real-time feedback
5. **Manage Layout**: Toggle sidebar and console visibility as needed

## Development

### Adding New Applications

1. **Create Application Class**: Inherit from `EmbeddedApplication`
2. **Register in Config**: Add entry to `applications.json`
3. **Implement Interface**: Provide `create_gui()`, `start()`, `stop()`, `update()` methods

Example:

```python
class MyApp(EmbeddedApplication):
    def create_gui(self, container):
        frame = ttk.Frame(container)
        ttk.Label(frame, text="My Application").pack()
        return frame
```

### Creating New Themes

Add theme entries to `themes.json` with required color definitions and font specifications.

### Extending Categories

Add new categories to `applications.json` with appropriate icons and organization.

## Technical Architecture

### Core Classes

- **`ModernGUILauncher`**: Main application controller
- **`ConfigManager`**: Configuration file management
- **`EmbeddedApplication`**: Base class for applications

### Design Patterns

- **Configuration-Driven**: JSON-based system configuration
- **Plugin Architecture**: Modular application loading
- **Observer Pattern**: UI updates and theme changes
- **Factory Pattern**: Application instantiation

### Dependencies

- **tkinter**: Core GUI framework
- **ttk**: Modern widget theming
- **json**: Configuration management
- **pathlib**: File system operations
- **threading**: Asynchronous operations

## Compatibility

### Legacy Support

The original `SonaExampleLauncher` class is preserved for backward compatibility. Use `--legacy` flag to access the original interface.

### Cross-Platform

- **Windows**: Full support with native theming
- **macOS**: Compatible with system themes
- **Linux**: Standard tkinter support

## Future Enhancements

- **Plugin System**: Dynamic plugin loading
- **Settings Dialog**: User preferences management
- **Multi-Language**: Internationalization support
- **Advanced Themes**: Custom theme creation tools
- **Workspace Management**: Project organization
- **Integrated Debugger**: Step-through debugging
- **Extension Marketplace**: Community plugins

## Contributing

When adding new features or applications:

1. Follow the existing code style and patterns
2. Update configuration files appropriately
3. Test with both modern and legacy interfaces
4. Document new features in this README
5. Ensure cross-platform compatibility

## License

Part of the Sona Programming Language project. See main project LICENSE for details.
