# Contributing to Blog Post Automation

Welcome to the Blog Post Automation project! We're excited that you're interested in contributing. This document outlines the standards and guidelines for contributing to this project.

## Code of Conduct

By participating in this project, you agree to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/blog-posts-automation.git
   cd blog-posts-automation
   ```

3. Set up your development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/macOS
   .\venv\Scripts\activate   # Windows
   pip install -r requirements-dev.txt
   ```

4. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## Development Guidelines

### Code Style

We follow strict Python coding standards:

1. **Style Guide**: Follow PEP 8
2. **Type Hints**: Required for all functions
3. **Line Length**: Maximum 88 characters
4. **Formatting**: Use Black formatter
5. **Static Type Checking**: Use mypy

Run quality checks:
```bash
black scripts/ tests/
flake8 scripts/ tests/
mypy scripts/ tests/
```

### Project Structure
```
blog-automation/
├── scripts/
│   ├── convert_markdown.py
│   ├── publish_medium.py
│   ├── publish_devto.py
│   └── utils/
├── tests/
├── posts/
└── dist/
```

### Testing Requirements

1. **Test Coverage**:
   - Minimum overall coverage: 80%
   - New features: 90%
   - Core components: 95%

2. **Running Tests**:
   ```bash
   # Full test suite
   pytest
   
   # With coverage
   pytest --cov=scripts tests/
   
   # Single file
   pytest tests/test_specific.py
   ```

3. **Test Structure**:
   ```python
   def test_feature_name():
       # Arrange
       input_data = ...
       expected = ...
       
       # Act
       result = function_under_test(input_data)
       
       # Assert
       assert result == expected
   ```

## Pull Request Process

1. **Before Submitting**:
   - Update documentation
   - Add tests
   - Run full test suite
   - Update README if needed
   - Format code with Black

2. **PR Template**:
   ```markdown
   ## Description
   [Describe your changes]

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement

   ## Test Coverage
   - [ ] Added tests
   - [ ] Updated existing tests
   - [ ] Manual testing performed

   ## Documentation
   - [ ] Updated README
   - [ ] Updated docstrings
   - [ ] Updated comments
   ```

3. **Review Process**:
   - At least one maintainer review required
   - All tests must pass
   - Code coverage requirements met
   - Documentation updated

## Documentation Standards

### Code Documentation

1. **Docstrings**: Required for all public functions/methods:
   ```python
   def function_name(param1: type, param2: type) -> return_type:
       """
       Brief description of function.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Description of return value

       Raises:
           ExceptionType: Description of when this exception occurs
       """
   ```

2. **Comments**: Required for complex logic:
   ```python
   # Calculate weighted average based on user engagement
   # Formula: (views * 0.3) + (likes * 0.5) + (comments * 0.2)
   engagement_score = calculate_weighted_score(metrics)
   ```

### API Documentation

Document all APIs using this format:
```markdown
## Endpoint Name

Description of what this endpoint does.

### Request
`METHOD /path/to/endpoint`

Headers:
- `Authorization`: Bearer token
- `Content-Type`: application/json

Body:
```json
{
    "field": "value"
}
```

### Response
```json
{
    "status": "success",
    "data": {}
}
```
```

## Issue Reporting Guidelines

### Bug Reports

Include:
1. **Environment**:
   - Python version
   - OS details
   - Package versions

2. **Description**:
   - Expected behavior
   - Actual behavior
   - Steps to reproduce

3. **Additional Context**:
   - Error messages
   - Log outputs
   - Screenshots

### Feature Requests

Include:
1. **Problem Statement**:
   - What problem does this solve?
   - Who benefits from this feature?

2. **Proposed Solution**:
   - Detailed description
   - Example usage
   - Alternative approaches considered

## Community and Communication

- **Questions**: Use GitHub Discussions
- **Bug Reports**: Use GitHub Issues
- **Feature Requests**: Use GitHub Issues
- **Security Issues**: Email directly to security@example.com

## Contact

For additional questions or concerns, contact the maintainers:
- Email: toriqul.int@gmail.com
- GitHub: [@TheToriqul](https://github.com/TheToriqul)
- LinkedIn: [@TheToriqul](https://www.linkedin.com/in/thetoriqul/)

Thank you for contributing to the Blog Post Automation project!
