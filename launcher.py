#!/usr/bin/env python3
"""A phosphor-styled, dependency-free front end for the existing generators."""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parent
THEMES = {'green': (120, 48), 'amber': (223, 172), 'ice': (153, 39),
          'blood': (217, 160), 'bone': (230, 145)}
SCENES = [
    ('auto', 'Automatic mission selection'),
    ('ship', 'Service tug / vehicle inspection'),
    ('archive', 'Reel transport / magnetic archive'),
    ('survey', 'Terrain mesh / surface telemetry'),
    ('tracking', 'Earth orbit / flight dynamics'),
    ('launch', 'Launch vehicle / ascent guidance'),
    ('probe', 'Deep-space probe / spacecraft engineering'),
    ('docking', 'Station approach / rendezvous control'),
    ('comms', 'Tracking antenna / deep-space network'),
    ('descent', 'Lunar lander / descent guidance'),
    ('legacy', 'Original abstract heroes and instruments'),
]


class Back(Exception):
    pass


class ExitLauncher(Exception):
    pass


@dataclass
class Job:
    name: str
    args: list
    folder: Path
    summary: list
    expected: int


def parse_size(value):
    match = re.fullmatch(r'\s*(\d+)\s*[xX]\s*(\d+)\s*', value)
    if not match or min(map(int, match.groups())) < 64:
        raise ValueError('Use WIDTHxHEIGHT, with each dimension at least 64 pixels.')
    return f'{int(match[1])}x{int(match[2])}'


def number(value, low, high, integer=False):
    try:
        result = int(value) if integer else float(value)
    except ValueError:
        raise ValueError('Enter a whole number.' if integer else 'Enter a number.')
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f'Choose a value from {low:g} to {high:g}.')
    return result


class Console:
    def __init__(self, theme='green', plain=False):
        self.theme = theme
        self.styled = (not plain and sys.stdin.isatty() and sys.stdout.isatty()
                       and os.environ.get('TERM', '') not in ('', 'dumb')
                       and 'NO_COLOR' not in os.environ)

    @property
    def width(self):
        return max(24, min(94, shutil.get_terminal_size((80, 24)).columns - 2))

    def ink(self, text, kind='normal'):
        if not self.styled:
            return text
        core, accent = THEMES[self.theme]
        colors = {'normal': core, 'bright': 231, 'dim': accent}
        return f'\033[38;5;{colors[kind]}m{text}\033[38;5;{core}m'

    @contextmanager
    def session(self):
        if self.styled:
            core = THEMES[self.theme][0]
            sys.stdout.write(f'\033[?1049h\033[48;5;233m\033[38;5;{core}m\033[2J\033[H')
            sys.stdout.flush()
        try:
            yield
        finally:
            if self.styled:
                sys.stdout.write('\033[0m\033[?1049l')
                sys.stdout.flush()

    def rule(self):
        print(self.ink('  +' + '-' * (self.width - 4) + '+', 'dim'))

    def row(self, text='', kind='normal'):
        available = self.width - 6
        for line in textwrap.wrap(str(text), available, replace_whitespace=False) or ['']:
            print('  ' + self.ink('| ', 'dim') + self.ink(line.ljust(available), kind)
                  + self.ink(' |', 'dim'))

    def screen(self, title, subtitle='GENERATOR CONTROL', status='READY'):
        if self.styled:
            core = THEMES[self.theme][0]
            print(f'\033[48;5;233m\033[38;5;{core}m\033[2J\033[H', end='')
        print()
        self.rule()
        self.row('C A S S E T T E   /   R E M O T E   S Y S T E M S', 'bright')
        self.row(f'{subtitle}  //  {status}', 'dim')
        self.rule()
        self.row(title.upper(), 'bright')
        self.row()

    def footer(self, help_text='ENTER selects default   /   B returns to main menu'):
        self.row()
        self.rule()
        print(self.ink('  ' + help_text, 'dim'))

    def read(self, prompt, default):
        try:
            raw = input(self.ink(f'  > {prompt} [{default}]: ', 'bright')).strip()
        except EOFError:
            raise ExitLauncher
        if raw.lower() in ('b', 'back'):
            raise Back
        return raw or str(default)

    def choose(self, title, options, default, subtitle='GENERATOR CONTROL'):
        error = ''
        keys = [key for key, _ in options]
        while True:
            self.screen(title, subtitle)
            for index, (key, description) in enumerate(options, 1):
                marker = '*' if key == default else ' '
                # Each option stays one row in normal-width terminals.
                self.row(f'{marker} [{index:02}] {key.upper():12} {description}')
            if error:
                self.row(error, 'bright')
            self.footer()
            value = self.read('SELECT', default).lower()
            if value == 'q' and 'quit' in keys:
                return 'quit'
            if value in keys:
                return value
            if value.isdigit() and 1 <= int(value) <= len(keys):
                return keys[int(value)-1]
            error = 'Unknown selection. Enter a listed number or name.'

    def ask(self, title, prompt, default, validate, hint=''):
        error = ''
        while True:
            self.screen(title, 'RENDER CONFIGURATION')
            if hint:
                self.row(hint)
                self.row()
            self.row(prompt, 'bright')
            self.row(f'DEFAULT / {default}', 'dim')
            if error:
                self.row(error, 'bright')
            self.footer()
            value = self.read('VALUE', default)
            try:
                return validate(value)
            except ValueError as exc:
                error = str(exc)


def wallpaper_job(ui):
    size = ui.choose('01 / Display format', [(s, name) for s, name in (
        ('5120x1440', 'Ultrawide / 32:9'), ('3840x2160', 'Desktop / 4K'),
        ('3456x2234', 'Laptop / Retina'), ('2560x1600', 'Desktop / 16:10'),
        ('custom', 'Enter a display resolution'))], '5120x1440')
    if size == 'custom':
        size = ui.ask('01 / Custom display', 'Width x height in pixels', '3840x2160', parse_size)
    scene = ui.choose('02 / Mission selection', SCENES, 'auto', 'WALLPAPER SYSTEMS')
    count = ui.ask('03 / Render queue', 'Number of wallpapers', 5,
                   lambda s: number(s, 1, 1000, True))
    palette = ui.choose('04 / Phosphor output', [('random', 'Seeded palette selection')]
                        + [(p, 'Phosphor palette') for p in THEMES], 'random')
    seed = ui.ask('05 / Mission seed', 'Seed number, or random', 'random', parse_seed,
                  'A fixed seed reproduces the same mission and geometry.')
    crt = ui.ask('06 / Tube geometry', 'CRT curvature', .14,
                 lambda s: number(s, 0, .4), '0 = flat    /    0.14 = standard    /    0.24 = heavy')
    busy = ui.ask('07 / Instrument density', 'Optional instrument detail', .55,
                  lambda s: number(s, 0, 1), '0.2 = sparse    /    0.55 = standard    /    1 = dense')
    args = ['wallgen.py', '--size', size, '--scene', scene, '--count', str(count),
            '--crt', str(crt), '--busy', str(busy)]
    if palette != 'random':
        args += ['--palette', palette]
    if seed is not None:
        args += ['--seed', str(seed)]
    summary = [('DISPLAY', size), ('MISSION', scene), ('QUEUE', str(count)),
               ('PALETTE', palette), ('SEED', 'random' if seed is None else str(seed)),
               ('CRT / DETAIL', f'{crt:g} / {busy:g}')]
    return Job('Wallpapers', args, ROOT / 'wallpapers', summary, count)


def parse_seed(value):
    if value.lower() == 'random':
        return None
    return number(value, 0, 2**31-1, True)


def icon_job(ui):
    from icongen import DEFAULT_MAP
    palette = ui.choose('01 / Icon phosphor', [(p, 'Phosphor palette') for p in THEMES], 'amber')
    style = ui.choose('02 / Icon appearance', [
        ('phosphor', 'Dark tile / bloom / CRT treatment'),
        ('mono', 'Bold transparent foreground / experimental for Clear')], 'phosphor')
    crt = .18
    if style == 'phosphor':
        crt = ui.ask('03 / Tube geometry', 'Icon CRT curvature', .18,
                     lambda s: number(s, 0, .3), '0 = flat    /    0.18 = standard')
    icns = ui.choose('04 / Export formats', [('yes', 'PNG + multi-resolution ICNS'),
                                            ('no', 'PNG only')], 'yes') == 'yes'
    args = ['icongen.py', '--palette', palette, '--style', style, '--crt', str(crt)]
    if icns:
        args.append('--icns')
    summary = [('STYLE', style), ('PALETTE', palette if style=='phosphor' else 'white foreground'),
               ('EXPORT', 'PNG + ICNS' if icns else 'PNG'),
               ('CRT', f'{crt:g}' if style=='phosphor' else 'off')]
    return Job('Icons', args, ROOT / 'icons', summary, len(DEFAULT_MAP)*(2 if icns else 1))


def review(ui, jobs):
    ui.screen('Render manifest', 'PREFLIGHT / REVIEW')
    for job in jobs:
        ui.row(job.name.upper(), 'bright')
        for key, value in job.summary:
            ui.row(f'  {key:14} {value}')
        ui.row('  OUTPUT         ' + str(job.folder.relative_to(ROOT)) + '/', 'dim')
        ui.row()
    ui.row('[1] RENDER    /    [B] RETURN TO MAIN MENU', 'bright')
    ui.footer()
    while ui.read('ACTION', 'render').lower() not in ('1','render','r','yes','y'):
        print(ui.ink('  Enter 1 to render, or B to return.', 'dim'))


def stop_child(child):
    if child.poll() is not None:
        return
    try:
        child.send_signal(signal.SIGINT)
    except ProcessLookupError:
        return
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def run_job(ui, job):
    logs = []
    completed = 0
    def progress(status='RENDERING'):
        ui.screen(job.name, 'OUTPUT TELEMETRY', status)
        fraction = min(1, completed / max(1, job.expected))
        bar_size = min(34, ui.width - 12)
        filled = int(fraction*bar_size)
        ui.row('[' + '#' * filled + '.' * (bar_size-filled) + ']', 'bright')
        ui.row(f'{completed:03} / {job.expected:03} FILES WRITTEN')
        ui.row()
        for line in logs[-5:]:
            ui.row(line, 'dim')
        ui.footer('CTRL-C cancels this render and returns to the main menu')
        sys.stdout.flush()
    progress()
    child = subprocess.Popen([sys.executable, '-u', *job.args], cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for line in child.stdout:
            line = line.rstrip()
            logs.append(line)
            # Generator output reports a path only after that file is saved.
            candidate = line.split('  [', 1)[0]
            path = Path(candidate)
            if path.suffix.lower() in ('.png', '.icns') and (ROOT/path).is_file():
                completed += 1
            progress()
        code = child.wait()
    except BaseException:
        stop_child(child)
        raise
    finally:
        child.stdout.close()
    if code:
        progress('RENDER FAILED')
        ui.row(f'Generator exited with code {code}.', 'bright')
        ui.read('ENTER to return', '')
        return False
    progress('COMPLETE')
    ui.row('OUTPUT / ' + str(job.folder), 'bright')
    if sys.platform == 'darwin':
        subprocess.run(['open', str(job.folder)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ui.read('ENTER to continue', '')
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', choices=THEMES, default='green')
    parser.add_argument('--plain', action='store_true', help='disable terminal escape sequences')
    parser.add_argument('--preview', action='store_true', help='show the main menu without reading input')
    args = parser.parse_args(argv)
    ui = Console(args.theme, args.plain)
    menu = [('wallpapers', 'Mission displays / nine composed scenes'),
            ('icons', 'Matching phosphor or monochrome glyphs'),
            ('both', 'Queue wallpapers and icons'),
            ('quit', 'End this session'),
            ('theme', 'Change this console phosphor color')]
    if args.preview:
        ui.screen('Select an output system')
        for i,(key,description) in enumerate(menu,1):
            ui.row(f'[{i:02}] {key.upper():12} {description}')
        ui.footer('LOCAL RENDERING  /  NO TERMINAL PROFILE CHANGES')
        return 0
    with ui.session():
        while True:
            try:
                choice = ui.choose('Select an output system', menu, 'wallpapers')
                if choice == 'quit':
                    break
                if choice == 'theme':
                    ui.theme = ui.choose('Console phosphor', [(p, 'Interface color only') for p in THEMES], ui.theme)
                    continue
                jobs = []
                if choice in ('wallpapers','both'):
                    jobs.append(wallpaper_job(ui))
                if choice in ('icons','both'):
                    jobs.append(icon_job(ui))
                review(ui,jobs)
                for job in jobs:
                    if not run_job(ui,job):
                        break
            except Back:
                continue
            except KeyboardInterrupt:
                ui.screen('Operation cancelled', status='INTERRUPTED')
                ui.row('Returning to the main menu. Completed files are retained.')
            except ExitLauncher:
                break
            except OSError as exc:
                ui.screen('Operation failed', status='ERROR')
                ui.row(str(exc))
                try:
                    ui.read('ENTER to return', '')
                except (ExitLauncher,Back,KeyboardInterrupt):
                    break
    return 0


if __name__ == '__main__':
    sys.exit(main())
