# Git Commit Message Validator

Validate Git commit messages with local hooks so every commit follows a consistent Conventional Commits format.

## Project Structure

```text
Message-Validator/
|-- hooks/
|   |-- commit-msg
|   |-- commit_msg_hook.py
|   |-- pre-commit
|   `-- pre_commit_hook.py
|-- tests/
|   |-- test_validator.py
|   `-- test_web_interface.py
|-- web/
|   |-- app.css
|   |-- app.js
|   `-- index.html
|-- install_hooks.py
|-- PROJECT_OVERVIEW.md
|-- README.md
|-- validator.py
`-- web_interface.py
```

## What It Enforces

The `commit-msg` hook checks the first line of the commit message:

```text
<type>(<scope>): <description>
```

Supported commit types:

- `feat`
- `fix`
- `docs`
- `style`
- `refactor`
- `test`
- `chore`
- `perf`
- `ci`
- `build`
- `revert`

Validation rules:

- Type must be one of the allowed values.
- Scope is optional and must stay lowercase.
- Description must be at least 10 characters.
- Description must start with a lowercase letter.
- Description must not end with a period.
- Subject length must stay within 72 characters.
- A commit body must be separated from the subject by a blank line.

The `pre-commit` hook scans staged files and:

- Blocks commits with merge conflict markers.
- Blocks commits with trailing whitespace.
- Warns about debug statements such as `print()` or `console.log()`.
- Warns when staged files are larger than 500 KB.

## Examples

Valid:

```bash
git commit -m "feat(auth): add jwt login support"
git commit -m "fix: resolve token refresh race condition"
git commit -m "docs(readme): update installation steps"
git commit -m "feat(api)!: remove deprecated v1 endpoints"
```

Invalid:

```bash
git commit -m "added login"
git commit -m "Fix: resolve crash"
git commit -m "feat(Auth): add page"
git commit -m "feat: bug"
```

## Installation

From the repository root:

```bash
py -3 install_hooks.py
```

The installer copies both hook files into `.git/hooks/`, backs up any existing hooks with a `.backup` suffix, and marks the new hooks as executable where supported.

If `py` is not available on your machine, you can still use:

```bash
python install_hooks.py
```

## Running Tests

```bash
py -3 -m unittest discover -s tests -v
```

## GitHub Pages Demo

The `web/` folder is now a fully static browser app, so it can be deployed on GitHub Pages without a Python backend.

What works on GitHub Pages:

- live commit-message validation in the browser
- file-content scanning for conflict markers, trailing whitespace, debug statements, and large files

What does not work on GitHub Pages:

- reading your local staged files or Git index

The repository includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml` that uploads the `web/` directory to GitHub Pages.

If Pages is not already configured in the repository, open your repository on GitHub and set:

```text
Settings -> Pages -> Source -> GitHub Actions
```

Once enabled, pushes to `main` or `demo-validator` will deploy the static site.

The site URL will be:

```text
https://divanshi046.github.io/Message-Validator/
```

## Local Preview

If you want to preview the static site locally:

```bash
py -3 web_interface.py
```

Then open:

```text
http://127.0.0.1:8000
```

If you want to use another port:

```bash
py -3 web_interface.py --port 8080
```

## How the Hooks Work

- `hooks/commit-msg` loads the commit message file passed by Git and validates it with `validator.py`.
- `hooks/pre-commit` scans staged file contents from Git's index, not just the working tree.
- `web/` contains the static GitHub Pages app.
- `web_interface.py` serves the same static files locally for preview.
- `validator.py` contains the shared validation and scanning logic used by both hooks and the tests.

## Emergency Bypass

```bash
git commit --no-verify -m "chore: emergency release note update"
```

Use this only when you intentionally need to skip local hook validation.
