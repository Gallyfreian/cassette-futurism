"""Console navigation, validation, subprocess cleanup and terminal restoration."""
from contextlib import redirect_stdout
import io
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import launcher


class LauncherTests(unittest.TestCase):
    def test_back_from_both_aborts_whole_manifest(self):
        out = io.StringIO()
        with patch('builtins.input', side_effect=['both','b','quit']), redirect_stdout(out), \
                patch('launcher.subprocess.Popen') as spawn:
            self.assertEqual(launcher.main(['--plain']), 0)
        spawn.assert_not_called()
        self.assertNotIn('ICON PHOSPHOR', out.getvalue())

    def test_eof_exits_cleanly(self):
        with patch('builtins.input', side_effect=EOFError), redirect_stdout(io.StringIO()):
            self.assertEqual(launcher.main(['--plain']), 0)

    def test_invalid_input_reprompts_and_manifest_preserves_values(self):
        ui = launcher.Console(plain=True)
        answers = ['custom','bad-size','960x600','tracking','0','2','green',
                   'nan','123','.14','.55']
        with patch('builtins.input', side_effect=answers), redirect_stdout(io.StringIO()):
            job = launcher.wallpaper_job(ui)
        self.assertEqual(job.expected, 2)
        self.assertEqual(job.args, ['wallgen.py','--size','960x600','--scene','tracking',
                                    '--count','2','--crt','0.14','--busy','0.55',
                                    '--palette','green','--seed','123'])

    def test_terminal_is_restored_on_error(self):
        ui = launcher.Console()
        ui.styled = True
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(RuntimeError):
                with ui.session():
                    raise RuntimeError('failure')
        self.assertTrue(out.getvalue().endswith('\033[0m\033[?1049l'))

    def test_cancelled_render_reaps_child(self):
        ui = launcher.Console(plain=True)
        # The second progress screen follows the child's READY line.
        ui.screen = unittest.mock.Mock(side_effect=[None, KeyboardInterrupt])
        children = []
        actual_popen = subprocess.Popen
        def spawn(*args, **kwargs):
            child = actual_popen(*args, **kwargs)
            children.append(child)
            return child
        job = launcher.Job('test', ['-c', 'import time; print("READY",flush=True); time.sleep(30)'],
                           launcher.ROOT, [], 1)
        with patch('launcher.subprocess.Popen', side_effect=spawn), redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                launcher.run_job(ui, job)
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())

    def test_real_render_reports_completed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = launcher.Job('Wallpapers', ['wallgen.py','--scene','tracking',
                               '--size','320x200','--seed','42','--out',tmp],
                               launcher.ROOT, [], 1)
            out = io.StringIO()
            with redirect_stdout(out), patch('builtins.input', return_value=''), \
                    patch('launcher.subprocess.run'):
                self.assertTrue(launcher.run_job(launcher.Console(plain=True), job))
            self.assertIn('001 / 001 FILES WRITTEN', out.getvalue())
            self.assertTrue((launcher.Path(tmp)/'wall_320x200_42.png').is_file())

    def test_failed_child_reports_error_and_does_not_open_finder(self):
        job = launcher.Job('test', ['-c', 'print("render failed"); raise SystemExit(3)'],
                           launcher.ROOT, [], 1)
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', return_value=''), \
                patch('launcher.subprocess.run') as open_folder:
            self.assertFalse(launcher.run_job(launcher.Console(plain=True), job))
        self.assertIn('Generator exited with code 3', out.getvalue())
        open_folder.assert_not_called()

    def test_bootstrap_quit_and_plain_fallback(self):
        result = subprocess.run(['/bin/bash',str(launcher.ROOT/'run.command'),'--plain'],
                                input='4\n',text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('\033', result.stdout)
        self.assertIn('R E M O T E', result.stdout)

    def test_numbers_reject_nonfinite_and_size_rejects_shell_text(self):
        for value in ('nan','inf','-inf'):
            with self.assertRaises(ValueError):
                launcher.number(value,0,1)
        with self.assertRaises(ValueError):
            launcher.parse_size('1920x1080; touch file')
        self.assertEqual(launcher.parse_size(' 1920 X 1080 '),'1920x1080')


if __name__ == '__main__':
    unittest.main()
