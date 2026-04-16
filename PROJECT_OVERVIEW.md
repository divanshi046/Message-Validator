# Git Commit Message Validator Project Overview

## Title

Git Commit Message Validator Using Git Hooks

## Problem Statement

Commit messages in many repositories are inconsistent. Developers often use unclear
messages such as `updated code`, `bug fix`, or `changes`, which makes version history
difficult to understand. This causes problems when teams review changes, trace bugs,
or generate release notes.

## Objective

Build an automated validation system that checks commit messages before Git accepts
them. The system should use Git hooks so that validation runs automatically during
the commit process.

## Proposed Solution

This project uses Python-based Git hooks:

- `commit-msg` validates the commit message format
- `pre-commit` checks staged files for common issues
- `install_hooks.py` installs both hooks into `.git/hooks`

The project follows the Conventional Commits style to ensure every commit message is
structured and meaningful.

## Main Features

- Enforces a standard commit format
- Allows only approved commit types such as `feat`, `fix`, `docs`, and `chore`
- Supports optional scopes such as `feat(auth): add login API`
- Rejects short or poorly formatted descriptions
- Warns about debug statements in staged files
- Blocks commits with merge conflict markers or trailing whitespace
- Warns when very large files are being committed

## Workflow

1. A developer runs `git commit`.
2. The `pre-commit` hook scans staged files.
3. If file errors are found, Git blocks the commit.
4. If the file checks pass, Git opens or reads the commit message.
5. The `commit-msg` hook validates the commit message format.
6. If the message is invalid, Git rejects the commit and shows an error.
7. If all checks pass, the commit is created successfully.

## Example

### Valid

```text
feat(auth): add password reset endpoint
```

### Invalid

```text
updated login code
```

Reason: the message does not include a valid commit type and description structure.

## Technologies Used

- Python 3
- Git hooks
- Regular expressions
- Python `unittest`

## Benefits

- Improves readability of commit history
- Encourages disciplined development practices
- Prevents low-quality commit messages
- Helps teams maintain a professional workflow
- Makes project tracking easier

## Future Enhancements

- Add branch name validation
- Add Jira or issue ID enforcement
- Support team-specific commit templates
- Generate commit analytics reports
