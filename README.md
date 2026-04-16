# Git Commit Message Validator

Automates commit message validation using Git hooks. Rejects commits that don't follow the **Conventional Commits** standard — keeping your project history clean, readable, and consistent.

---

## Project Structure

```
git-commit-validator/
│
├── hooks/
│   ├── commit-msg        ← Validates commit message format
│   └── pre-commit        ← Checks staged files for issues
│
├── tests/
│   └── test_validator.py ← Unit tests for the validator
│
├── install_hooks.py      ← One-time setup script
└── README.md
```

---

## Commit Message Format

All commits must follow the **Conventional Commits** specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Allowed Types

| Type       | When to use                                      |
|------------|--------------------------------------------------|
| `feat`     | Adding a new feature                             |
| `fix`      | Fixing a bug                                     |
| `docs`     | Documentation changes only                       |
| `style`    | Formatting, whitespace (no logic change)         |
| `refactor` | Restructuring code without changing behaviour    |
| `test`     | Adding or updating tests                         |
| `chore`    | Maintenance — deps, build tools, config          |
| `perf`     | Performance improvement                          |
| `ci`       | CI/CD configuration changes                      |
| `revert`   | Reverting a previous commit                      |

### Examples

```bash
# ✅ Valid
git commit -m "feat(auth): add JWT login support"
git commit -m "fix: resolve null pointer in user service"
git commit -m "docs(readme): update installation steps"
git commit -m "chore: bump dependencies to latest versions"
git commit -m "feat(api)!: remove deprecated v1 endpoints"   # breaking change

# ❌ Invalid
git commit -m "added login"                  # no type
git commit -m "Fix: resolve crash."          # uppercase type, ends with period
git commit -m "feat(Auth): add page"         # uppercase scope
git commit -m "feat: bug"                    # description too short
```

---

## Installation

### 1. Clone / set up your repo

```bash
git clone <your-repo-url>
cd <your-repo>
```

### 2. Add this validator to your project

Copy the `hooks/` folder and `install_hooks.py` into your project root.

### 3. Run the setup script (once per developer)

```bash
python install_hooks.py
```

This copies the hooks into `.git/hooks/` and makes them executable. Every teammate must run this once after cloning.

---

## How It Works

### `commit-msg` Hook

Runs automatically after you type your commit message. Validates:

| Rule | Detail |
|------|--------|
| Format | Must match `type(scope): description` |
| Valid type | Must be one of the 10 allowed types |
| Scope | Optional, but must be lowercase with no spaces |
| Description | Must be lowercase start, ≥10 chars, no trailing period |
| Subject length | Max 72 characters |
| Body separator | Body must be separated by a blank line |

### `pre-commit` Hook

Runs before the commit message prompt. Checks staged files for:

- **Merge conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`) — blocks commit
- **Trailing whitespace** — blocks commit
- **Debug statements** — warns (`print()`, `console.log`, `debugger`, `pdb.set_trace`)
- **Large files** (>500KB) — warns

---

## Running Tests

```bash
# Simple run
python tests/test_validator.py

# With pytest (more detailed output)
pip install pytest
python -m pytest tests/ -v
```

---

## Bypassing Hooks (Emergency Only)

```bash
git commit --no-verify -m "your message"
```

> ⚠️ Use this only in emergencies. Bypassing hooks defeats the purpose of having them.

---

## Importing Validator Logic in Tests

The `commit-msg` file has no `.py` extension (Git hook requirement). The test file uses `importlib` to load it dynamically — no renaming needed.

---

## Requirements

- Python 3.10+
- Git 2.x+
- No external dependencies — uses only the Python standard library
