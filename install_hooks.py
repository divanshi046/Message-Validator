#!/usr/bin/env python3
"""
install_hooks.py — One-time setup script to install Git hooks into .git/hooks/
Run this once after cloning the repo: python install_hooks.py
"""

import os
import sys
import shutil
import stat

# ──────────────────────────────────────────────
# COLORS
# ──────────────────────────────────────────────

RED    = "\033[0;31m"
YELLOW = "\033[0;33m"
GREEN  = "\033[0;32m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ──────────────────────────────────────────────
# HOOKS TO INSTALL
# ──────────────────────────────────────────────

HOOKS = [
    "commit-msg",
    "pre-commit",
]

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def print_banner():
    print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════╗")
    print(f"║     Git Commit Validator — Hook Setup     ║")
    print(f"╚═══════════════════════════════════════════╝{RESET}\n")

def print_success(msg):
    print(f"  {GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"  {RED}✗ {msg}{RESET}")

def print_info(msg):
    print(f"  {CYAN}→ {msg}{RESET}")

def find_git_root() -> str | None:
    """Walk up directories to find the .git folder."""
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent

def find_hooks_source_dir() -> str | None:
    """Find the hooks/ source directory relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hooks_dir = os.path.join(script_dir, "hooks")
    if os.path.isdir(hooks_dir):
        return hooks_dir
    return None

def make_executable(filepath: str):
    """Add executable permission to a file."""
    current = stat.S_IMODE(os.lstat(filepath).st_mode)
    os.chmod(filepath, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def install_hook(hook_name: str, source_dir: str, target_dir: str) -> bool:
    """Copy a hook from source to .git/hooks/. Returns True on success."""
    src = os.path.join(source_dir, hook_name)
    dst = os.path.join(target_dir, hook_name)

    if not os.path.isfile(src):
        print_error(f"Source hook not found: {src}")
        return False

    # Backup existing hook
    if os.path.isfile(dst):
        backup = dst + ".backup"
        shutil.copy2(dst, backup)
        print_info(f"Backed up existing '{hook_name}' → '{hook_name}.backup'")

    shutil.copy2(src, dst)
    make_executable(dst)
    print_success(f"Installed '{hook_name}' → {dst}")
    return True

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    print_banner()

    # ── Find .git root ──
    git_root = find_git_root()
    if not git_root:
        print_error("Not inside a Git repository. Please run from within your project.")
        sys.exit(1)

    git_hooks_dir = os.path.join(git_root, ".git", "hooks")
    print_info(f"Git root:   {git_root}")
    print_info(f"Hooks dir:  {git_hooks_dir}\n")

    # ── Find source hooks ──
    source_dir = find_hooks_source_dir()
    if not source_dir:
        print_error("Could not find 'hooks/' directory next to this script.")
        sys.exit(1)

    # ── Install each hook ──
    success_count = 0
    for hook in HOOKS:
        if install_hook(hook, source_dir, git_hooks_dir):
            success_count += 1

    # ── Summary ──
    print(f"\n{'─' * 45}")
    if success_count == len(HOOKS):
        print(f"\n{GREEN}{BOLD}  ✓ All {success_count} hook(s) installed successfully!{RESET}")
        print(f"\n{BOLD}  What happens now:{RESET}")
        print(f"  • {CYAN}pre-commit{RESET}  — runs on every {BOLD}git commit{RESET} (file checks)")
        print(f"  • {CYAN}commit-msg{RESET}  — validates your message format\n")
        print(f"  {BOLD}Example valid commit:{RESET}")
        print(f"  {GREEN}git commit -m \"feat(auth): add JWT login support\"{RESET}\n")
    else:
        print(f"\n{YELLOW}{BOLD}  ⚠ {success_count}/{len(HOOKS)} hook(s) installed. Check errors above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
