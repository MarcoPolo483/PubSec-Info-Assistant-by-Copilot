# Contributing to PubSec Information Assistant

First off, thank you for considering contributing to PubSec Information Assistant! It's people like you that make this project a great tool for public sector organizations.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots and animated GIFs if relevant**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and explain which behavior you expected to see instead**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required PR template
* Follow the coding conventions (see below)
* Include appropriate test coverage (minimum 80%)
* Update documentation as needed
* Ensure all tests pass
* Ensure security scans pass (no HIGH/CRITICAL vulnerabilities)

## Development Process

### Setting Up Your Development Environment

```bash
# Clone the repository
git clone https://github.com/MarcoPolo483/PubSec-Info-Assistant-by-Copilot.git
cd PubSec-Info-Assistant-by-Copilot

# Install dependencies
./scripts/setup-dev.sh

# Start local development environment (Docker Compose)
docker-compose up -d

# Run tests
./scripts/run-tests.sh
```

### Coding Conventions

#### Python (Backend)
* Follow PEP 8 style guide
* Use type hints for all functions
* Run black, isort, flake8, mypy before committing
* Minimum 80% test coverage required

#### TypeScript (Frontend)
* Follow ESLint configuration
* Use strict TypeScript mode
* Run prettier before committing
* Minimum 80% test coverage required

#### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
* `feat`: New feature
* `fix`: Bug fix
* `docs`: Documentation only
* `style`: Code style changes (formatting, etc.)
* `refactor`: Code refactoring
* `test`: Adding or updating tests
* `chore`: Maintenance tasks
* `ci`: CI/CD changes
* `perf`: Performance improvements
* `security`: Security improvements

**Example:**
```
feat(retriever): add reranking with cross-encoder

Implemented cross-encoder reranking to improve citation accuracy.
Precision@3 increased from 85% to 95%.

Closes #123
```

### Testing Requirements

* **Unit Tests**: Minimum 80% line coverage
* **Integration Tests**: Minimum 70% API endpoint coverage
* **E2E Tests**: All critical user flows must pass
* **Performance Tests**: Must meet SLA (p99 < 2s)
* **Security Tests**: No HIGH/CRITICAL vulnerabilities

### Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. Make your changes with atomic commits

3. Ensure all tests pass:
   ```bash
   ./scripts/run-tests.sh
   ```

4. Push to your fork and create a PR:
   ```bash
   git push origin feat/my-feature
   ```

5. Fill out the PR template completely

6. Request review from at least 2 maintainers

7. Address review feedback

8. Once approved and CI passes, a maintainer will merge

### PR Checklist

- [ ] Tests added/updated (80%+ coverage maintained)
- [ ] Documentation updated (README, API docs, runbooks)
- [ ] Security considerations documented
- [ ] Migration notes added (if applicable)
- [ ] Performance impact assessed
- [ ] Accessibility tested (WCAG 2.1 AA)
- [ ] Multi-tenancy isolation validated (if applicable)
- [ ] Cost impact analyzed (if applicable)

## Branch Protection Rules

The `main` branch is protected:
* Require PR reviews (minimum 2 approvals)
* Require status checks to pass (CI, tests, security scans)
* No force pushes allowed
* No direct commits to `main`

## Security

If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md) and report it privately to marco.polo483@protonmail.com.

**DO NOT** create a public GitHub issue for security vulnerabilities.

## Style Guides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Style Guide

* Follow PEP 8
* Use docstrings for all public modules, functions, classes, and methods
* Use type hints consistently
* Prefer list comprehensions over map/filter
* Use f-strings for string formatting

### TypeScript Style Guide

* Use 2 spaces for indentation
* Use semicolons
* Use single quotes for strings
* Prefer const over let
* Use async/await over promises

### Documentation Style Guide

* Use Markdown for all documentation
* Include code examples where applicable
* Keep line length under 120 characters
* Use relative links for internal references

## Questions?

Feel free to create an issue with the "question" label or reach out to the maintainers.

## Recognition

Contributors are recognized in our [README](README.md) and release notes.

Thank you for contributing! 🎉
