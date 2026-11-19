#!/usr/bin/env python3
"""One-way deployment. Only our include line and dedicated directory are managed."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
CONFIG_NAMES = ("config", "config.ghostty")
MANAGED_DIR = "repo-managed"
MANAGED_ENTRY = "config.ghostty"
DEFAULT_THEME = "Hawk Gruvbox Dark"


def config_search_dirs():
    xdg_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    xdg_config = xdg_home / "ghostty"
    if sys.platform == "darwin":
        macos_config = Path.home() / "Library/Application Support/com.mitchellh.ghostty"
        return [macos_config, xdg_config]
    return [xdg_config]


def default_config():
    """Use the sole existing config, or the preferred path for a new one."""
    folders = config_search_dirs()
    candidates = [folder / name for folder in folders for name in CONFIG_NAMES]
    existing = [path for path in candidates if path.exists()]
    if len(existing) > 1:
        raise ValueError("Multiple Ghostty configs found; choose one with --config PATH.")
    return existing[0] if existing else folders[0] / MANAGED_ENTRY


def install_managed_files(managed, platform):
    """Replace the reserved directory with copies and a generated entry point."""
    if managed.exists():
        shutil.rmtree(managed)
    managed.mkdir(parents=True)

    themes = managed / "themes"
    shutil.copytree(ROOT / "themes", themes)
    config_files = ["common.ghostty"]
    if platform == "darwin":
        config_files.append("macos.ghostty")

    # Ghostty resolves the includes relative to the generated entry point.
    lines = [f"theme = {themes / DEFAULT_THEME}"]
    for name in config_files:
        shutil.copyfile(ROOT / "config" / name, managed / name)
        lines.append(f"config-file = {name}")
    (managed / MANAGED_ENTRY).write_text("\n".join(lines) + "\n")


def update_include(config, original, include, *, apply):
    """Add or remove the exact include line without reformatting local settings."""
    lines = original.splitlines(keepends=True)
    if apply:
        if include not in lines:
            # Prepending also preserves an existing file without a final newline.
            config.write_bytes(include + original)
        return

    remaining = b"".join(line for line in lines if line != include)
    if remaining != original:
        config.write_bytes(remaining)


def deploy(action, config, platform=None):
    # Make the include absolute without following symlinks before the safety check.
    config = Path(os.path.abspath(config.expanduser()))
    managed = config.parent / MANAGED_DIR
    if config.is_symlink() or managed.is_symlink():
        raise ValueError("Refusing symlinked config or managed directory.")
    if any(char in str(managed) for char in ('\n', '\r', '"')):
        raise ValueError("Unsupported characters in config path.")

    # Read the local config before replacing the managed files.
    original = config.read_bytes() if config.exists() else b""
    include = f"config-file = ?{managed / MANAGED_ENTRY}\n".encode()
    if action == "apply":
        install_managed_files(managed, platform or sys.platform)
        update_include(config, original, include, apply=True)
    else:
        update_include(config, original, include, apply=False)
        if managed.exists():
            shutil.rmtree(managed)
    return managed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "unapply"))
    parser.add_argument("--config", type=Path, help="Ghostty config file (otherwise auto-detected)")
    args = parser.parse_args()
    try:
        config = args.config if args.config is not None else default_config()
        managed = deploy(args.action, config)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"{args.action}: {config}\nManaged directory: {managed}\nReload Ghostty to apply the change.")


if __name__ == "__main__":
    main()
