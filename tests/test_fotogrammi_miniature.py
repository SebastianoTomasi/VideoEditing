import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fotogrammi import sheet_filter  # noqa: E402
from miniature import copy_images, preview_graph  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
