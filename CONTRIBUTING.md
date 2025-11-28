# Contributing to GRID Protocol Specification

Thank you for your interest in contributing to GRID! This document provides guidelines for contributing to the GRID Protocol Specification.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Contribution Guidelines](#contribution-guidelines)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## How Can I Contribute?

### 1. Reporting Issues

**Before creating an issue:**
- Check if the issue already exists
- Collect relevant information (version, environment, etc.)
- Provide clear reproduction steps

**Issue Types:**
- 🐛 **Bug Report** - Errors in the specification
- ✨ **Feature Request** - New features or enhancements
- 📖 **Documentation** - Improvements to documentation
- 🔌 **Adapter Proposal** - New protocol adapter ideas
- ❓ **Question** - Clarification on specification

### 2. Contributing Code/Documentation

We welcome contributions in these areas:

#### Policy Examples
- New policy patterns (RBAC, ABAC, temporal, etc.)
- Real-world use case policies
- Policy testing examples

#### Protocol Adapters
- HTTP/REST adapter improvements
- gRPC adapter implementation
- Custom protocol adapters
- Adapter testing frameworks

#### Documentation
- Tutorial improvements
- Architecture diagrams
- Use case walkthroughs
- Translation to other languages

#### Integration Examples
- Kubernetes deployment manifests
- Docker Compose configurations
- Terraform modules
- CI/CD pipeline examples

#### Specification Improvements
- Clarifications to existing sections
- New sections for emerging patterns
- Gap analysis updates

---

## Getting Started

### Prerequisites

- Git
- Text editor (VS Code recommended)
- OPA (for testing policies)
- Python 3.8+ (for adapter development)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/grid-protocol.git
cd grid-protocol

# Add upstream remote
git remote add upstream https://github.com/anthropics/grid-protocol.git
```

### Set Up Development Environment

```bash
# Install OPA for policy testing
brew install opa  # macOS
# or download from https://www.openpolicyagent.org/

# Install Python dependencies (for adapters)
pip install -r requirements-dev.txt  # if exists

# Verify setup
opa version
python --version
```

---

## Contribution Guidelines

### Policy Examples

**Location:** `examples/policies/`

**Requirements:**
1. **File naming:** Use descriptive names (e.g., `rbac-basic.rego`, `time-based-access.rego`)
2. **Package:** Must use `package grid.authorization`
3. **Default deny:** Always include `default allow := false`
4. **Comments:** Explain complex logic
5. **Testing:** Include test cases

**Template:**
```rego
# GRID Policy Example: [Name]
#
# Description of what this policy does
# Use cases: ...

package grid.authorization

default allow := false

# Rule 1: Description
allow if {
    # Conditions
}

# Helper functions
helper_function if {
    # Logic
}
```

**Testing:**
```bash
# Test your policy
opa test examples/policies/your-policy.rego

# Evaluate with sample input
opa eval -d examples/policies/your-policy.rego \
  -i test-input.json \
  "data.grid.authorization.allow"
```

### Protocol Adapters

**Location:** `examples/adapters/`

**Requirements:**
1. **Inherit from ProtocolAdapter:** Implement all required methods
2. **Type hints:** Use Python type hints
3. **Documentation:** Docstrings for all public methods
4. **Error handling:** Graceful error handling
5. **Testing:** Unit tests required

**Template:**
```python
"""
GRID Protocol Adapter: [Protocol Name]

Description of the protocol and use cases.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

class YourProtocolAdapter(ProtocolAdapter):
    """Adapter for [Protocol Name]"""
    
    def translate_request(self, protocol_request: Any) -> GridRequest:
        """Translate protocol request to GRID format"""
        # Implementation
        pass
    
    # Implement other required methods...
```

### Documentation

**Requirements:**
1. **Markdown format:** Use standard Markdown
2. **Clear structure:** Use headings, lists, code blocks
3. **Examples:** Include practical examples
4. **Links:** Use relative links for cross-references
5. **Spell check:** Run spell checker before submitting

**Style:**
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Be concise but clear
- Include code examples where helpful

### Integration Examples

**Location:** `examples/integrations/`

**Requirements:**
1. **Working examples:** Must be deployable
2. **Documentation:** README.md explaining setup
3. **Comments:** Explain configuration choices
4. **Security:** Follow security best practices
5. **Testing:** Include testing instructions

---

## Development Process

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Write clear, concise code/documentation
- Follow style guidelines
- Add tests where applicable
- Update documentation

### 3. Test Your Changes

```bash
# Test policies
opa test examples/policies/

# Test Python code
python -m pytest tests/

# Spell check
# Use your editor's spell checker or:
aspell check your-file.md
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "Add: Brief description of changes

Detailed explanation if needed.

Fixes #123"
```

**Commit Message Format:**
```
Type: Brief description (50 chars or less)

Detailed explanation (wrap at 72 chars)
- Bullet points for multiple changes
- Reference issues: Fixes #123, Relates to #456

Type can be:
- Add: New feature or content
- Fix: Bug fix
- Update: Improvements to existing content
- Remove: Deletion of content
- Docs: Documentation only changes
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill out the PR template
```

---

## Style Guidelines

### Markdown

- Use ATX-style headers (`#` not underlines)
- Use fenced code blocks with language identifiers
- Use relative links for internal references
- Keep lines under 100 characters where possible
- Use tables for structured data

### Rego (Policy Language)

```rego
# Good
allow if {
    input.principal.role == "admin"
    input.resource.sensitivity in ["low", "medium"]
}

# Bad (unclear, no spacing)
allow{input.principal.role=="admin"&&input.resource.sensitivity in["low","medium"]}
```

**Style:**
- Use 4 spaces for indentation
- Add blank lines between rules
- Use descriptive variable names
- Comment complex logic
- Group related rules together

### Python

Follow [PEP 8](https://pep8.org/):
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter)
- Use type hints
- Write docstrings for public methods
- Use descriptive variable names

```python
# Good
def translate_request(self, http_request: HTTPRequest) -> GridRequest:
    """
    Translate HTTP request to GRID format.
    
    Args:
        http_request: HTTP request object
        
    Returns:
        GridRequest with GRID abstractions
    """
    principal = self.get_principal(http_request)
    return GridRequest(principal=principal, ...)

# Bad (no types, no docstring)
def translate_request(self, req):
    p = self.get_principal(req)
    return GridRequest(principal=p, ...)
```

---

## Pull Request Process

### Before Submitting

- [ ] Code/documentation follows style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Policy example
- [ ] Protocol adapter
- [ ] Integration example

## Testing
How was this tested?

## Checklist
- [ ] Follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Added tests (if applicable)
```

### Review Process

1. **Automated checks:** CI/CD runs automatically
2. **Maintainer review:** At least one maintainer approval required
3. **Community feedback:** Open for community comments
4. **Revisions:** Address feedback and update PR
5. **Merge:** Maintainer merges when approved

---

## Community

### Communication Channels

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, ideas, general discussion
- **Pull Requests:** Code/documentation contributions

### Getting Help

- Check [QUICKSTART.md](QUICKSTART.md) for basics
- Read [TUTORIAL.md](TUTORIAL.md) for hands-on guide
- Browse [examples/](examples/) for patterns
- Ask in GitHub Discussions
- Reference [GRID Specification](GRID_PROTOCOL_SPECIFICATION_v0.1.md)

### Recognition

Contributors are recognized in:
- Git commit history
- Release notes
- CONTRIBUTORS.md file (if significant contribution)

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## Questions?

- **General questions:** GitHub Discussions
- **Bug reports:** GitHub Issues
- **Security issues:** See SECURITY.md
- **Specification questions:** Reference the spec or ask in Discussions

---

**Thank you for contributing to GRID! 🚀**

Your contributions help make machine-to-machine governance universal, interoperable, and trustworthy.