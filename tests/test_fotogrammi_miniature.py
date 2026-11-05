import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import UserError  # noqa: E402
from fotogrammi import sheet_filter  # noqa: E402
from miniature import copy_images, preview_graph, render  # noqa: E402


class SheetFilterTests(unittest.TestCase):
    def test_crop_scale_label_and_tile(self):
        graph = sheet_filter(20, 120, "1040,544,240,256", 4, 3, 480)
        self.assertTrue(graph.startswith("[0:v]fps=1/20,crop=240:256:1040:544,scale=480:-2,drawtext="))
        self.assertIn("gmtime\\:120", graph)
        self.assertTrue(graph.endswith("tile=4x3:padding=4:color=gray[out]"))

    def test_without_crop(self):
        self.assertNotIn("crop=", sheet_filter(10, 0, None, 4, 3, 480))


class PreviewGraphTests(unittest.TestCase):
    def test_three_thumbnails_make_three_rows(self):
        graph = preview_graph(3)
        self.assertEqual(graph.count("split=4"), 3)
        self.assertIn("scale=168:94:flags=area", graph)
        self.assertIn("format=gray", graph)
        self.assertIn("drawbox=", graph)
        self.assertIn("hstack=inputs=4[row2]", graph)
        self.assertTrue(graph.endswith("[row0][row1][row2]vstack=inputs=3[out]"))

    def test_one_thumbnail_needs_no_vstack(self):
        self.assertTrue(preview_graph(1).endswith("[row0]null[out]"))


class CopyImagesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.generated = root / "generated_images"
        self.generated.mkdir()
        self.target = root / "video" / "immagini"

    def tearDown(self):
        self.tmp.cleanup()

    def picture(self, name: str, content: bytes) -> Path:
        path = self.generated / name
        path.write_bytes(content)
        return path

    def test_numbers_copies_from_one(self):
        copies = copy_images([self.picture("a.png", b"a"), self.picture("b.PNG", b"b")], self.target, "B")

        self.assertEqual([p.name for p in copies], ["B-1.png", "B-2.png"])
        self.assertEqual(copies[1].read_bytes(), b"b")

    def test_second_run_continues_after_the_first(self):
        copy_images([self.picture("first.png", b"first")], self.target, "B")
        copies = copy_images([self.picture("second.png", b"second")], self.target, "B")

        self.assertEqual([p.name for p in copies], ["B-2.png"])
        self.assertEqual((self.target / "B-1.png").read_bytes(), b"first")

    def test_continues_after_the_highest_number_of_that_name(self):
        self.target.mkdir(parents=True)
        for name in ("B-1.png", "B-3.jpg", "C-7.png", "B-fondo-9.png", "B-4.txt"):
            (self.target / name).write_bytes(b"old")

        copies = copy_images([self.picture("new.webp", b"new")], self.target, "B")

        self.assertEqual([p.name for p in copies], ["B-4.webp"])


class FakeTime:
    """Stands in for miniature's time module: sleeping moves the clock on and
    writes what a late Edge has written by then."""

    def __init__(self):
        self.now = 0.0
        self.writes = []  # (seconds, path, the whole file at that moment)

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        while self.writes and self.writes[0][0] <= self.now:
            _, path, content = self.writes.pop(0)
            path.write_bytes(content)


class RenderTests(unittest.TestCase):
    """Edge and ffmpeg are faked; the fake Edge, like the real one, writes a
    relative --screenshot against a working directory of its own."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.edge_dir = self.root / "edge"
        self.edge_dir.mkdir()
        self.folder = self.root / "videos" / "prova"
        self.folder.mkdir(parents=True)
        (self.folder / "miniatura-A.html").write_text("<html></html>", encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def fake_run(self, args, **kwargs):
        if args[0] == "msedge.exe":
            screenshot = next(a for a in args if a.startswith("--screenshot=")).split("=", 1)[1]
            target = self.edge_dir / screenshot
            if not target.parent.is_dir():
                return subprocess.CompletedProcess(args, 0, "", f"Failed to write file {screenshot}")
            target.write_bytes(b"png")
        else:
            shutil.copy(args[args.index("-i") + 1], args[-1])
        return subprocess.CompletedProcess(args, 0, "", "")

    def test_relative_layout_renders_next_to_it(self):
        with mock.patch("miniature.find_edge", return_value=Path("msedge.exe")), \
                mock.patch("miniature.run", side_effect=self.fake_run):
            jpg = render(Path("videos/prova/miniatura-A.html"))

        self.assertEqual(jpg, self.folder / "miniatura-A.jpg")
        self.assertEqual(jpg.read_bytes(), b"png")
        self.assertFalse((self.folder / "miniatura-A.png").exists())

    def render_with_late_edge(self, *writes):
        """Render with an Edge that exits at once and writes its screenshot
        afterwards: writes are (seconds after the start, whole file so far)."""
        clock = FakeTime()

        def fake_run(args, **kwargs):
            if args[0] != "msedge.exe":
                return self.fake_run(args, **kwargs)
            screenshot = Path(next(a for a in args if a.startswith("--screenshot=")).split("=", 1)[1])
            clock.writes = [(at, screenshot, content) for at, content in writes]
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch("miniature.find_edge", return_value=Path("msedge.exe")), \
                mock.patch("miniature.run", side_effect=fake_run), \
                mock.patch("miniature.time", clock):
            try:
                return render(self.folder / "miniatura-A.html")
            finally:
                self.elapsed = clock.now

    def test_waits_until_the_screenshot_stops_growing(self):
        jpg = self.render_with_late_edge((1.0, b"pn"), (1.1, b"png, all of it"))

        self.assertEqual(jpg.read_bytes(), b"png, all of it")
        self.assertFalse((self.folder / "miniatura-A.png").exists())

    def test_a_leftover_screenshot_is_not_taken_for_the_new_one(self):
        (self.folder / "miniatura-A.png").write_bytes(b"old")

        jpg = self.render_with_late_edge((1.0, b"new"))

        self.assertEqual(jpg.read_bytes(), b"new")

    def test_gives_up_when_edge_writes_nothing_in_time(self):
        with self.assertRaisesRegex(UserError, "non ha scritto nessun file entro 20 s$"):
            self.render_with_late_edge()

        self.assertGreaterEqual(self.elapsed, 20)
        self.assertLess(self.elapsed, 21)
        self.assertFalse((self.folder / "miniatura-A.jpg").exists())


if __name__ == "__main__":
    unittest.main()
