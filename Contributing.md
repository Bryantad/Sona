# Contributing to Sona

Thank you for your interest in contributing to the Sona programming language! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine
   ```bash
   git clone https://github.com/YOUR_USERNAME/Sona.git
   cd Sona
   ```
3. **Add the upstream repository** as a remote
   ```bash
   git remote add upstream https://github.com/Bryantad/Sona.git
   ```
4. **Create a branch** for your work
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
2. **Run the installation script**
   ```bash
   python tools/install.py
   ```

3. **Verify your setup**
   ```bash
   python -m sona.repl
   ```

## Development Workflow

1. **Make your changes** in your feature branch
2. **Write or update tests** to cover your changes
3. **Run the tests** to ensure they pass
   ```bash
   python tools/run_tests.py
   ```
4. **Commit your changes** with clear, descriptive messages
   ```bash
   git commit -m "Add feature: description of your changes"
   ```
5. **Push your branch** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Create a Pull Request** from your fork to the main Sona repository

## Pull Request Guidelines

- Keep pull requests focused on single issues or features
- Follow the provided PR template
- Include tests for new features or bug fixes
- Update documentation as needed
- Ensure all tests pass before submitting
- Describe your changes clearly in the PR description

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Use descriptive variable and function names
- Include docstrings for classes and functions
- Keep functions small and focused
- Write clean, readable, and maintainable code

## Testing

- Write tests for all new features or bug fixes
- Ensure all tests pass locally before submitting
- Test examples in the `examples/` directory
- Consider edge cases in your tests
- Run the comprehensive test suite with `python tools/run_tests.py`

## Documentation

- Update documentation for new features or changes
- Document public APIs with docstrings
- Update README.md or other docs as needed
- Include example code where appropriate
- Check documentation by running examples

## Release Process

Release management is handled by the core team. If you want to contribute to a release:

1. Help with testing and bug fixing
2. Assist with documentation updates
3. Contribute to the release notes

## Community

- Join our discussions on GitHub Issues
- Participate in code reviews
- Help answer questions from other contributors
- Share your experience using Sona

Thank you for contributing to Sona! Your efforts help make this project better for everyone.
