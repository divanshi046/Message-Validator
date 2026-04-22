#!/usr/bin/env python3
"""Install the Git hooks used by this project."""

from __future__ import annotations

from pathlib import Path
import shutil
import stat
import subprocess
import sys

HOOKS = ("commit-msg", "pre-commit")


def run_git_command(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def get_repo_root() -> Path:
    return Path(run_git_command("rev-parse", "--show-toplevel"))


def get_hooks_directory() -> Path:
    return Path(run_git_command("rev-parse", "--git-path", "hooks"))


def get_source_directory() -> Path:
    return Path(__file__).resolve().parent / "hooks"


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_hook(hook_name: str, source_dir: Path, target_dir: Path) -> None:
    source = source_dir / hook_name
    target = target_dir / hook_name

    if not source.is_file():
        raise FileNotFoundError(f"Missing source hook: {source}")

    if target.exists():
        backup_path = target.with_name(f"{target.name}.backup")
        shutil.copy2(target, backup_path)
        print(f"Backed up existing {hook_name} hook to {backup_path}")

    shutil.copy2(source, target)
    make_executable(target)
    print(f"Installed {hook_name} hook to {target}")


def main() -> int:
    try:
        repo_root = get_repo_root()
        hooks_dir = get_hooks_directory()
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "Not inside a Git repository."
        print(stderr, file=sys.stderr)
        return 1

    source_dir = get_source_directory()
    if not source_dir.is_dir():
        print(f"Missing hooks directory: {source_dir}", file=sys.stderr)
        return 1

    hooks_dir.mkdir(parents=True, exist_ok=True)

    print(f"Repository root: {repo_root}")
    print(f"Hooks directory: {hooks_dir}")

    try:
        for hook_name in HOOKS:
            install_hook(hook_name, source_dir, hooks_dir)
    except OSError as exc:
        print(f"Failed to install hooks: {exc}", file=sys.stderr)
        return 1

    print("")
    print("Hook installation complete.")
    print("Example valid commit: feat(auth): add jwt login support")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
