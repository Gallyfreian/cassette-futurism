"""Run with: python -m unittest discover -s tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from wallgen import render
from terminal_scenes import SCENES
from icongen import GLYPHS, make_icon, build_icns


class RenderingTests(unittest.TestCase):
    def test_scene_seed_reproduces_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            for scene in (*SCENES, 'auto', 'legacy'):
                with self.subTest(scene=scene):
                    a, b = Path(tmp) / 'a.png', Path(tmp) / 'b.png'
                    for path in (a, b):
                        render(480, 300, seed=42, palette='green',
                               scene=scene, out=str(path))
                    self.assertEqual(a.read_bytes(), b.read_bytes())
                    with Image.open(a) as image:
                        self.assertEqual(image.size, (480, 300))
                        self.assertGreater(max(image.getextrema()[1]), 200)

    def test_mono_has_transparent_background_and_white_foreground(self):
        for glyph in GLYPHS:
            for size in (16, 64):
                with self.subTest(glyph=glyph, size=size):
                    image = make_icon(glyph, size, style='mono')
                    self.assertEqual(image.getpixel((0, 0))[3], 0)
                    self.assertEqual(image.getextrema()[:3], ((255, 255),) * 3)
                    self.assertEqual(image.getextrema()[3][1], 255)

    def test_icns_fallback_contains_decodable_renditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Terminal.icns'
            with patch('icongen.shutil.which', return_value=None):
                self.assertTrue(build_icns('terminal', str(path), style='mono'))
            with Image.open(path) as image:
                sizes = image.info['sizes']
                self.assertEqual({w * scale for w, h, scale in sizes},
                                 {32, 64, 128, 256, 512, 1024})
                for size in sizes:
                    rendition = image.icns.getimage(size)
                    rendition.load()
                    self.assertEqual(rendition.getextrema()[3][1], 255)
            self.assertFalse(path.with_suffix('.iconset').exists())


if __name__ == '__main__':
    unittest.main()
