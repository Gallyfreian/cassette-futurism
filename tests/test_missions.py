"""Mission-state relationships and drawing bounds, independent of CRT effects."""
import math
import random
import unittest

from mission_scenes import (MISSION_SCENES, View, instruments, make_mission,
                            orbit_point, terrain_height, compose_mission)
from wallgen import Canvas, load_font


class BoundsCanvas:
    """Catch geometry and text that escape a supplied panel at native size."""
    def __init__(self, width, height):
        self.width, self.height = width, height

    def point(self, x, y):
        assert -.01 <= x <= self.width+.01, (x, self.width)
        assert -.01 <= y <= self.height+.01, (y, self.height)

    def line(self, points, *args):
        for point in points:
            self.point(*point)

    def rect(self, x0, y0, x1, y1, *args):
        self.point(x0, y0)
        self.point(x1, y1)

    def circle(self, x, y, r, *args):
        self.point(x-r, y-r)
        self.point(x+r, y+r)

    def ellipse(self, x, y, rx, ry, *args):
        self.point(x-rx, y-ry)
        self.point(x+rx, y+ry)

    def text(self, x, y, text, size, v=255, anchor='la', bold=True):
        font = load_font(int(size), bold)
        left, top, right, bottom = font.getbbox(text, anchor=anchor)
        self.point(x+left, y+top)
        self.point(x+right, y+bottom)


class MissionTests(unittest.TestCase):
    def test_shared_state_relationships(self):
        for seed in range(100):
            tracking = make_mission('tracking', random.Random(seed))
            d = tracking.data
            self.assertAlmostEqual(d['radius_ratio'], 1+d['altitude']/6371)
            pos = orbit_point(d, d['phase'])
            self.assertAlmostEqual(math.sqrt(sum(p*p for p in pos)), d['radius_ratio'])
            self.assertEqual(tracking.value, f'{d["altitude"]:04.0f} KM')
            docking = make_mission('docking', random.Random(seed))
            d = docking.data
            self.assertEqual(d['aligned'], math.hypot(d['dx'], d['dy']) <= .28)
            self.assertEqual('ALIGNED' in docking.status, d['aligned'])
            descent = make_mission('descent', random.Random(seed))
            d = descent.data
            self.assertAlmostEqual(d['lander_height']-terrain_height(d,d['lander_x']), d['altitude'])
            self.assertEqual(descent.value, f'{d["altitude"]:04.0f} M')
            launch = make_mission('launch', random.Random(seed))
            d = launch.data
            self.assertEqual(launch.rows[0][1], f'{d["altitude"][-1]:.1f} KM')
            self.assertEqual(launch.rows[1][1], f'{d["velocity"][-1]:.0f} M/S')
            comms = make_mission('comms', random.Random(seed))
            self.assertEqual('LOCKED' in comms.status, comms.data['snr'] >= 10)

    def test_full_layout_bounds_at_target_resolutions(self):
        for scene in MISSION_SCENES:
            for width, height in ((5120, 1440), (3456, 2234)):
                for seed in (0, 91, 7048):
                    with self.subTest(scene=scene, size=(width, height), seed=seed):
                        compose_mission(BoundsCanvas(width,height),width,height,
                                        random.Random(seed),scene)

    def test_different_seeds_change_drawn_geometry(self):
        for scene, draw in MISSION_SCENES.items():
            with self.subTest(scene=scene):
                images=[]
                for seed in (91,7048):
                    canvas=Canvas(660,400,ss=1)
                    draw(View(canvas,(0,0,660,400),1),make_mission(scene,random.Random(seed)),.55)
                    images.append(canvas.img.tobytes())
                self.assertNotEqual(*images)

    def test_main_diagrams_and_instruments_stay_in_panels(self):
        for scene, draw in MISSION_SCENES.items():
            for seed in range(100):
                mission=make_mission(scene,random.Random(seed))
                with self.subTest(scene=scene,seed=seed):
                    canvas=BoundsCanvas(1650,1000)
                    draw(View(canvas,(0,0,1650,1000),1),mission,1)
                    for width in (1800,3000):
                        instruments(BoundsCanvas(width,280),(0,0,width,280),mission,1,1)


if __name__ == '__main__':
    unittest.main()
