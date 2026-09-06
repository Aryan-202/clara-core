# Contributing to Clara

Thank you for your interest in contributing to Clara. This project is maintained by Aryan Vishwakarma, and contributions are welcomed from developers, researchers, writers, and users who want to improve the project.

This document outlines how to contribute in a way that is consistent with the project’s goals, quality standards, and community expectations.

## Project ownership

The project is owned by Aryan Vishwakarma.

- GitHub: Aryan-202
- Email: aryanvishwakarma275@gmail.com

For repository decisions, review requests, and ownership-related questions, the project owner is the primary point of contact.

## Ways to contribute

There are several ways to help improve Clara:

- report bugs and issues
- suggest improvements and new features
- improve documentation
- submit code changes and fixes
- add tests for existing functionality
- help review pull requests

## Before you start

1. Fork the repository and create a feature branch.
2. Ensure you are working from the latest version of the default branch.
3. Read the project documentation, especially the README and any relevant module-level guidance.
4. Prefer small, focused changes that are easy to review and maintain.

## Local development workflow

1. Clone the repository.
2. Create a virtual environment for Python development.
3. Install project dependencies.
4. Run the relevant tests for the change you are making.
5. Validate formatting and linting where applicable.

A typical validation flow for this project is:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install flake8 pytest
flake8 .
pytest
```

## Code standards

Contributions should be:

- clear, readable, and maintainable
- consistent with the existing codebase
- covered by tests when behavior changes
- minimal in scope and focused on a single concern
- documented when new functionality or behavior is introduced

Please avoid introducing unrelated refactors or broad formatting-only changes in the same pull request.

## Pull request expectations

When opening a pull request:

- explain the problem clearly and state the proposed solution
- include a summary of changes
- reference related issues when applicable
- keep the scope narrow and easy to review
- ensure the change passes validation checks

Pull requests should be written with enough context for maintainers to understand the rationale behind the work.

## Issues and feature requests

If you identify a bug, missing capability, or potential improvement:

- search whether the issue already exists
- provide a clear reproduction or context
- include relevant environment details
- describe the expected behavior and the actual outcome

Feature requests should explain the use case, expected benefit, and any constraints or trade-offs.

## Documentation contributions

Improvements to documentation are valuable and welcome. Documentation should be:

- accurate
- concise
- easy to understand
- current with the state of the project

## Community expectations

All contributors are expected to behave respectfully and professionally. Disagreements should be handled constructively, and feedback should focus on the work rather than on individuals.

The project’s Code of Conduct applies to all participation, including issues, pull requests, discussions, and other collaboration channels.

## Security and sensitive issues

Do not report security vulnerabilities through public issues or pull requests. Please follow the process described in SECURITY.md.

## Questions and support

If you have questions about contributing, repository workflows, or project direction, please contact the project owner through the official project channels.

Thank you for helping make Clara better.
