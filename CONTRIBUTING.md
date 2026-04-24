# Contributing to MarkItDown GUI

Thank you for your interest in contributing to MarkItDown GUI! We welcome contributions from everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](../../issues/new) and include:

- A clear description of the problem
- Steps to reproduce the behavior
- Expected behavior vs. actual behavior
- Your operating system and Python version
- Any relevant log output or screenshots

### Suggesting Features

We'd love to hear your ideas! Please [open an issue](../../issues/new) with:

- A clear description of the proposed feature
- The use case or problem it solves
- Any alternative solutions you've considered

### Submitting Changes

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our code standards
4. **Test your changes** thoroughly
5. **Commit with a clear message**:
   ```bash
   git commit -m "Add: description of your change"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** against the `main` branch

## Code Standards

### Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
- Use meaningful variable and function names
- Keep functions focused and concise
- Maintain consistent indentation (4 spaces)

### Internationalization

All user-facing text must support both Chinese and English:

1. Add translation keys to `i18n.py` in both `LANG_ZH` and `LANG_EN` dictionaries
2. Use the `t()` function for all display text: `t("your_key", param=value)`
3. Ensure both language dictionaries have identical keys
4. Test both languages before submitting

### Commit Messages

Use clear, descriptive commit messages with a prefix:

| Prefix | Usage |
|--------|-------|
| `Add:` | New features |
| `Fix:` | Bug fixes |
| `Update:` | Modifications to existing features |
| `Refactor:` | Code restructuring without behavior changes |
| `Docs:` | Documentation updates |
| `i18n:` | Internationalization changes |
| `Chore:` | Build, dependencies, or tooling changes |

Examples:
```
Add: support for ODT file format
Fix: crash when converting empty PDF files
Update: improve prediction accuracy for large files
i18n: add Japanese language support
```

### Testing

Before submitting a Pull Request:

- Verify the application starts without errors
- Test the feature in both Chinese and English
- Test with various file types and sizes
- Ensure no regressions in existing functionality

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/qttwzy/markitdown_gui.git
   cd markitdown_gui
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install markitdown tkinterdnd2 PyMuPDF
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

```
markitdown_gui/
├── main.py              # Application entry point
├── gui.py               # GUI implementation (Tkinter)
├── converter.py         # File conversion engine
├── predictor.py         # Smart time prediction module
├── i18n.py              # Internationalization module
├── logger_config.py     # Logging configuration
├── MarkItDown.spec      # PyInstaller packaging config
├── setup.iss            # Inno Setup installer script
├── ChineseSimplified.isl # Inno Setup Chinese language file
├── LICENSE              # MIT License
├── README.md            # Project documentation
├── CONTRIBUTING.md      # This file
└── .gitignore           # Git ignore rules
```

## License

By contributing to this project, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions?

Feel free to [open an issue](../../issues/new) for any questions about contributing.
