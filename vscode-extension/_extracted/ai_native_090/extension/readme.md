# Sona Language Support for VS Code

AI-powered Sona programming language support with cognitive accessibility features.

## 🚀 Features

### AI-Powered Development

- **Code Generation**: Generate Sona code from natural language descriptions
- **Smart Refactoring**: AI-powered code improvements and optimizations
- **Code Explanation**: Get detailed explanations of complex code
- **Intelligent Debugging**: AI-assisted bug detection and fixes
- **Performance Optimization**: Automatic code optimization suggestions

### Cognitive Accessibility

- **Neurotypical Mode (Default)**: Standard UI/UX for familiar development experience
- **ADHD Mode**: High-contrast colors, minimal distractions, bold fonts for enhanced focus
- **Dyslexia Mode**: Dyslexia-friendly fonts (OpenDyslexic) and enhanced readability

### Azure-Powered Infrastructure

- Enterprise-grade AI routing with fallback providers
- Persistent cognitive memory across sessions
- Real-time performance monitoring
- Serverless cognitive functions

## 🎯 Getting Started

### First-Time Setup

When you first install the Sona extension, you'll see a welcome message that guides you through:

1. **Profile Selection**: Choose your preferred UI mode for optimal accessibility
2. **AI Connection**: Verify connection to Sona's AI infrastructure
3. **Feature Overview**: Learn about available commands and capabilities

### Onboarding Experience

The extension provides a seamless onboarding experience:

- **Welcome Dialog**: Introduces Sona v0.9.0 features and benefits
- **Profile Configuration**: Easy setup for cognitive accessibility needs
- **Interactive Tutorial**: Hands-on guidance for key features
- **Help System**: Always-available assistance and documentation

### Manual Setup

You can always reconfigure your experience using:

- **Command Palette** → `Sona: Select User Profile`
- **Status Bar** → Click the Sona icon → Change UI Profile
- **Settings** → Search for "Sona" → Configure preferences

## 🧠 User Profiles

### Neurotypical (Default)

- Standard VS Code-style interface
- Familiar colors and fonts
- Conventional layout and spacing
- Best for users comfortable with typical development environments

### ADHD Mode

- **High Contrast**: Enhanced visual separation and focus
- **Bold Fonts**: Improved readability and attention
- **Minimal Distractions**: Reduced visual clutter
- **Fast Interactions**: Optimized for quick context switching

### Dyslexia Mode

- **OpenDyslexic Font**: Specially designed for dyslexic readers
- **Enhanced Spacing**: Improved line and character spacing
- **Consistent Colors**: Reduced visual stress
- **Clear Hierarchy**: Better information organization

## 📋 Commands

| Command                     | Description                    | Keyboard Shortcut |
| --------------------------- | ------------------------------ | ----------------- |
| `Sona: Select User Profile` | Change accessibility profile   | -                 |
| `Sona: Generate Code`       | Generate code from description | `Ctrl+Shift+G`    |
| `Sona: Refactor Code`       | Improve selected code          | `Ctrl+Shift+R`    |
| `Sona: Explain Code`        | Get code explanation           | `Ctrl+Shift+E`    |
| `Sona: Debug Code`          | AI-assisted debugging          | `Ctrl+Shift+D`    |
| `Sona: Optimize Code`       | Performance optimization       | `Ctrl+Shift+O`    |
| `Sona: Toggle Focus Mode`   | Enable/disable cognitive focus | `Ctrl+Shift+F`    |
| `Sona: Welcome & Setup`     | Show onboarding                | -                 |
| `Sona: Help & Commands`     | View help and commands         | `F1`              |

## ⚙️ Configuration

### Settings

```json
{
  "sona.userProfile": "neurotypical",
  "sona.aiRouter.endpoint": "https://sona-ai-router-prod.azurewebsites.net",
  "sona.aiRouter.timeout": 30000,
  "sona.onboarding.showWelcome": true
}
```

### Profile Switching

Switch profiles anytime through:

1. **Command Palette**: `Sona: Select User Profile`
2. **Status Bar**: Click Sona icon → Change Profile
3. **Settings**: Modify `sona.userProfile` directly

Changes take effect immediately with no restart required.

## 🔧 Status Bar

The Sona status bar indicator shows:

- Current profile mode (Neurotypical/ADHD/Dyslexia)
- AI connection status
- Quick access to profile switching
- Connection health monitoring

**Icons**:

- ⚡ Neurotypical mode
- 🚀 ADHD mode
- 📖 Dyslexia mode

## 🆘 Troubleshooting

### Profile Not Switching

1. Check VS Code settings for `sona.userProfile`
2. Reload VS Code window
3. Run `Sona: Select User Profile` again

### AI Connection Issues

1. Verify internet connection
2. Check AI Router endpoint in settings
3. Run `Sona: Check AI Connection`

### Font Issues (Dyslexia Mode)

1. Install OpenDyslexic font on your system
2. Restart VS Code
3. Font will fallback to Arial if OpenDyslexic unavailable

## 📚 Learn More

- [Sona Documentation](https://github.com/Bryantad/Sona)
- [Azure Infrastructure Guide](https://github.com/Bryantad/Sona/blob/main/azure/README.md)
- [Cognitive Accessibility Features](https://github.com/Bryantad/Sona/wiki/accessibility)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/Bryantad/Sona/blob/main/Contributing.md).

## 📄 License

This extension is licensed under the same terms as the Sona language project.

---

**Sona v0.9.0** - AI-Native Programming with Cognitive Accessibility
🧠 Inclusive | 🤖 AI-Powered | ☁️ Cloud-Native
