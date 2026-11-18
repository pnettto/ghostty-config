#!/usr/bin/env python3
"""One-way deployment. Only our include line and dedicated directory are managed."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent


def default_config():
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ghostty"
    folders = [xdg]
    if sys.platform == "darwin":
        folders.insert(0, Path.home() / "Library/Application Support/com.mitchellh.ghostty")
    existing = [folder / name for folder in folders
                for name in ("config", "config.ghostty") if (folder / name).exists()]
    if len(existing) > 1:
        raise ValueError("Multiple Ghostty configs found; choose one with --config PATH.")
    return existing[0] if existing else folders[0] / "config.ghostty"


def deploy(action, config, platform=None):
    platform = platform or sys.platform
    config = Path(os.path.abspath(config.expanduser()))
    managed = config.parent / "repo-managed"
    if config.is_symlink() or managed.is_symlink():
        raise ValueError("Refusing symlinked config or managed directory.")
    if any(c in str(managed) for c in ('\n', '\r', '"')):
        raise ValueError("Unsupported characters in config path.")
    include = f'config-file = ?{managed / "config.ghostty"}\n'.encode()
    original = config.read_bytes() if config.exists() else b""

    if action == "apply":
        # Only this reserved directory is ours. No links to the checkout.
        if managed.exists():
            shutil.rmtree(managed)
        managed.mkdir(parents=True)
        shutil.copytree(ROOT / "themes", managed / "themes")
        shutil.copyfile(ROOT / "config/common.ghostty", managed / "common.ghostty")
        lines = [f'theme = {managed / "themes/Hawk Gruvbox Dark"}',
                 'config-file = common.ghostty']
        if platform == "darwin":
            shutil.copyfile(ROOT / "config/macos.ghostty", managed / "macos.ghostty")
            lines.append('config-file = macos.ghostty')
        (managed / "config.ghostty").write_text("\n".join(lines) + "\n")
        if include not in original.splitlines(keepends=True):
            # Prepending preserves every original byte, even without a final newline.
            config.write_bytes(include + original)
    else:
        updated = b"".join(line for line in original.splitlines(keepends=True)
                           if line != include)
        if updated != original:
            config.write_bytes(updated)
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
