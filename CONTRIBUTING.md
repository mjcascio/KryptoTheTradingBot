# Contributing to KryptoTheTradingBot

Thank you for your interest in contributing to KryptoTheTradingBot! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the [Issues](https://github.com/mjcascio/KryptoTheTradingBot/issues)
2. If not, create a new issue using the bug report template
3. Include detailed steps to reproduce the bug
4. Add relevant logs and screenshots if possible

### Suggesting Features

1. Check if the feature has already been suggested in the [Issues](https://github.com/mjcascio/KryptoTheTradingBot/issues)
2. If not, create a new issue using the feature request template
3. Clearly describe the problem the feature would solve
4. Outline your proposed solution

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Submit a pull request to the `main` branch
6. Fill out the pull request template completely

## Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Coding Standards

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single responsibility
- Write unit tests for new functionality

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest --cov=src tests/
```

## Git Workflow

1. Create a branch for your work:
   - For features: `feature/your-feature-name`
   - For bugfixes: `fix/issue-description`
   - For documentation: `docs/what-you-documented`

2. Make small, focused commits with clear messages:
   ```
   feat: Add new trading strategy
   
   - Implement momentum strategy
   - Add configuration options
   - Write unit tests
   ```

3. Keep your branch updated with the main branch:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

## Code Review Process

1. All pull requests require at least one review before merging
2. Address all review comments before requesting re-review
3. Ensure all CI checks pass

## Documentation

- Update documentation for any changes to APIs or functionality
- Document new features thoroughly
- Keep the README.md up to date

Thank you for contributing to KryptoTheTradingBot! 