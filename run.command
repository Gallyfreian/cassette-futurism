#!/bin/bash
# Double-click on macOS, or run ./run.command
# Targets bash 3.2 (what macOS ships) no associative arrays, no mapfile.

cd "$(dirname "$0")" || exit 1

VENV=".venv"
PY="$VENV/bin/python3"

bold=$'\033[1m'; dim=$'\033[2m'; amber=$'\033[38;5;208m'; off=$'\033[0m'

hr() { printf '%s\n' "$dim------------------------------------------------------------$off"; }

# ask "prompt" "default" -> echoes the answer
ask() {
    local prompt="$1" default="$2" reply
    read -r -p "$prompt ${dim}[$default]${off} " reply || exit 0
    printf '%s' "${reply:-$default}"
}

# pick "prompt" "default" opt1 opt2 ... -> echoes chosen option
pick() {
    local prompt="$1" default="$2"; shift 2
    local opts=("$@") i=1 reply
    # menu goes to stderr: stdout is captured by the caller's $(...)
    for o in "${opts[@]}"; do printf '  %d) %s\n' "$i" "$o" >&2; i=$((i + 1)); done
    read -r -p "$prompt ${dim}[$default]${off} " reply || exit 0
    reply="${reply:-$default}"
    case "$reply" in
        ''|*[!0-9]*) printf '%s' "$reply" ;;                 # typed a name
        *) if [ "$reply" -ge 1 ] && [ "$reply" -le ${#opts[@]} ]; then
               printf '%s' "${opts[$((reply - 1))]}"
           else printf '%s' "$default"; fi ;;
    esac
}

printf '\n%s\n' "${amber}${bold}  cassette-futurism${off}"
printf '%s\n\n' "${dim}  wallpaper and macOS icon generator${off}"

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
    printf '%s' "Continue? [Y/n] "; read -r go
    case "$go" in [Nn]*) exit 0 ;; esac

    python3 -m venv "$VENV" || { echo "venv failed"; read -r _; exit 1; }
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r requirements.txt || {
        echo "install failed"; read -r _; exit 1; }
    echo "Ready."
    hr
fi

PALETTES="amber green ice blood bone"

# ------------------------------------------------------------ wallpapers
do_wallpapers() {
    echo
    echo "${bold}Wallpapers${off}"
    local size count pal crt busy
    size=$(pick "Resolution?" 1 \
        "5120x1440" "3840x2160" "3456x2234" "2560x1600" "custom")
    if [ "$size" = "custom" ]; then
        size=$(ask "  Width x height, e.g. 3440x1440:" "3840x2160")
    fi
    count=$(ask "How many?" 5)
    echo "Palette (blank = random per image):"
    pal=$(pick "  Which?" "random" $PALETTES "random")
    crt=$(ask "CRT bulge, 0 = flat:" 0.14)
    busy=$(ask "Clutter, 0.2 sparse .. 1.0 dense:" 0.55)

    local args="--size $size --count $count --crt $crt --busy $busy"
    [ "$pal" != "random" ] && args="$args --palette $pal"

    hr
    echo "${dim}wallgen.py $args${off}"
    "$PY" wallgen.py $args || return 1
    open wallpapers 2>/dev/null
}

# ----------------------------------------------------------------- icons
do_icons() {
    echo
    echo "${bold}Icons${off}"
    local pal crt icns
    pal=$(pick "Palette?" 1 $PALETTES)
    crt=$(ask "CRT bulge, 0 = flat:" 0.18)
    printf '%s' "Also build .icns files? [Y/n] "; read -r icns

    local args="--palette $pal --crt $crt"
    case "$icns" in [Nn]*) ;; *) args="$args --icns" ;; esac

    hr
    echo "${dim}icongen.py $args${off}"
    "$PY" icongen.py $args || return 1
    echo
    echo "To apply one: open the PNG in Preview, Cmd-A then Cmd-C,"
    echo "select the app or folder, Cmd-I, click its icon top-left, Cmd-V."
    open icons 2>/dev/null
}

# ------------------------------------------------------------------ menu
while true; do
    echo
    choice=$(pick "What would you like to make?" 1 \
        "wallpapers" "icons" "both" "quit")
    [ -z "$choice" ] && { echo; exit 0; } # EOF / ctrl-D
    case "$choice" in
        wallpapers) do_wallpapers ;;
        icons)      do_icons ;;
        both)       do_wallpapers; do_icons ;;
        quit|q)     echo "Bye."; exit 0 ;;
        *)          echo "Didn't catch that." ;;
    esac
    hr
done
