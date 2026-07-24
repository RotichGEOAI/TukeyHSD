# Contributing to Turnkey Statistical Analysis Pipeline

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/turnkey-analysis.git
cd turnkey-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install pytest black flake8
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Document all public functions with docstrings
- Keep functions focused and under 50 lines when possible

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## Pull Request Process

1. Update README.md with details of changes if applicable
2. Update version numbers following Semantic Versioning
3. Ensure all tests pass
4. Request review from maintainers

## Reporting Issues

When reporting bugs, please include:
- Python version
- Streamlit version
- Steps to reproduce
- Expected vs actual behavior
- Sample data (if applicable)
