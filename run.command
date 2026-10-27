#!/bin/bash
# Double-click on macOS. Bootstrap stays compatible with Apple's bash 3.2.
cd "$(dirname "$0")" || exit 1
VENV=".venv"
PY="$VENV/bin/python3"
# First-run setup is deliberately plain so errors remain readable everywhere.
hr() { printf '%s\n' '------------------------------------------------------------'; }
# ---------------------------------------------------------------- setup
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 isn't installed."
    echo "Install it from https://www.python.org/downloads/macos/ or run:"
    echo "  brew install python"
    read -r -p "Press return to close. "
    exit 1
fi

if [ ! -x "$PY" ]; then
    echo "First run. This will:"
    echo "  - create a virtual environment in ./$VENV  (a self-contained"
    echo "    Python folder inside this directory, ~50 MB)"
    echo "  - install Pillow and numpy into it"
    echo
    echo "Nothing is installed system-wide. Delete the .venv folder to undo."
    hr
    printf '%s' "Continue? [Y/n] "; read -r go || exit 0
    case "$go" in [Nn]*) exit 0 ;; esac

    python3 -m venv "$VENV" || { echo "venv failed"; read -r _; exit 1; }
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r requirements.txt || {
        echo "install failed"; read -r _; exit 1; }
    echo "Ready."
    hr
fi

# The console uses only the Python standard library.
exec "$PY" launcher.py "$@"
