# Ghostty config

One-way, copy-based deployment of my Ghostty preferences and ten Hawk themes.
No symlinks, background sync, deployment history, backups, or runtime state in
this repository. Requires Git and Python 3; no Python packages to install.

## First use

```sh
git clone https://github.com/pnettto/ghostty-config.git
cd ghostty-config
./setup.sh apply
```

The repository can live anywhere. Reload Ghostty afterward (Command+Shift+R
with this configuration on macOS); some options require restarting Ghostty.

## Update

```sh
git pull --ff-only
./setup.sh apply
```

Git operations are explicit: the installer never pulls, commits, or pushes.
To change the shared setup, edit the repository's source files, commit and push.
Nothing from the installed configuration is ever copied back into the repo.

## Unapply

```sh
./setup.sh unapply
```

Reload Ghostty. Only our exact optional include line and our dedicated
`repo-managed/` directory are removed. Existing settings and themes remain.
If apply created a previously nonexistent config file, unapply leaves it empty:
without keeping state, we deliberately do not guess whether it predated us.
Keep the config path unchanged between apply and unapply, or supply the original
path explicitly. Unapply before moving your Ghostty config directory.

## Boundaries

- Your existing Ghostty config is changed **only** by adding/removing this line:
  `config-file = ?/absolute/path/to/repo-managed/config.ghostty`.
- Your other config bytes and unrelated files are preserved, including themes.
- `repo-managed/` beside the selected config is reserved entirely for this tool.
  Apply replaces that folder; unapply deletes it. **Do not store local edits or
  preexisting files there.** There is no backup or merge mechanism.
- Configs and themes are ordinary copies. Removing or moving the checkout does
  not affect an applied setup.
- Repeating either command is safe under these ownership rules.
- There is no manifest, tracking database, or saved deployment state anywhere.
- Do not run deployment concurrently or while another program edits the config.

### Precedence (important)

Ghostty loads includes **after** the containing file, regardless of where the
include line appears. While applied, repo settings therefore win over conflicting
settings in that file. Unapply restores the original behavior. Keybindings and
other additive settings follow Ghostty's own merge rules.

Existing additional includes are preserved; their order can affect precedence.
This tool does not rewrite them or implement automatic local overrides.

## Paths and platforms

The script discovers `config` or `config.ghostty` in:

- macOS: `~/Library/Application Support/com.mitchellh.ghostty/` and the XDG location.
- Linux: `$XDG_CONFIG_HOME/ghostty/` (default `~/.config/ghostty/`).

If multiple configs exist, it stops rather than guessing. Specify the actual
entry-point file in that case, using the same option for both commands:

```sh
./setup.sh apply --config "$HOME/.config/ghostty/config.ghostty"
./setup.sh unapply --config "$HOME/.config/ghostty/config.ghostty"
```

Symlinked entry-point files or managed directories are refused. macOS-only
preferences are deployed only on macOS. Compositor support determines whether
Linux supports global shortcuts, blur, and the quick terminal; Linux deployment
is unit-tested, not tested on a live Linux desktop.

## Layout

```text
config/common.ghostty   Shared preferences
config/macos.ghostty    macOS-specific preferences
themes/                Custom Hawk themes
setup.sh               Command entry point
setup.py               Standard-library deployment implementation
tests/test_setup.py    Isolated deployment tests
```

The deployed entry point selects `Hawk Gruvbox Dark` by absolute path inside the
managed folder; existing themes in Ghostty's normal theme directory are untouched.
Change the selected theme in `setup.py` if desired.

## Checks

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use temporary directories, not your live Ghostty config. To validate a
deployed config with Ghostty:

```sh
ghostty +validate-config --config-file="/path/to/repo-managed/config.ghostty"
```
