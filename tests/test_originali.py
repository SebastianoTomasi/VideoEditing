import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import UserError  # noqa: E402
from originali import holdings, send_to_recycle_bin  # noqa: E402


def write_cut_list(folder: Path, *recordings: Path) -> None:
    folder.mkdir(exist_ok=True)
    data = {"recordings": [p.as_posix() for p in recordings], "changes": []}
    (folder / "tagli.json").write_text(json.dumps(data), encoding="utf-8")


class OriginalsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.videos = root / "videos"
        self.videos.mkdir()
        self.final = self.videos / "2026-10-25-demo"
        self.final.mkdir()
        self.recording = self.final / "2026-10-25 17-20-17.mp4"
        self.recording.write_bytes(b"x" * 1000)
        (self.final / "montaggio.mp4").write_bytes(b"edit")
        (self.final / "descrizione.txt").write_text("Descrizione", encoding="utf-8")
        write_cut_list(self.final, self.recording)
        self.older = self.videos / "2026-10-24-presentazione"
        write_cut_list(self.older, self.recording)
        self.in_progress = self.videos / "2026-10-26-nuovo"
        outside = root / "OBS" / "2026-10-26 10-00-00.mp4"
        outside.parent.mkdir()
        outside.write_bytes(b"video")
        write_cut_list(self.in_progress, outside)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lists_only_recordings_inside_their_folder(self):
        found = holdings(self.videos)

        self.assertEqual(len(found), 1)
        holding = found[0]
        self.assertEqual(holding.folder, self.final)
        self.assertEqual(holding.recordings, [self.recording])
        self.assertEqual(holding.size, 1000)
        self.assertTrue(holding.final)
        self.assertEqual(holding.shared_with, [self.older.name])

    def test_sends_only_the_recordings_to_the_recycle_bin(self):
        recycled = []

        freed = send_to_recycle_bin(
            [self.final], self.videos, recycle=lambda p: (recycled.append(p), p.unlink()), report=lambda _: None
        )

        self.assertEqual(recycled, [self.recording])
        self.assertEqual(freed, 1000)
        self.assertTrue((self.final / "montaggio.mp4").exists())
        self.assertTrue((self.final / "tagli.json").exists())

    def test_refuses_a_folder_without_recordings(self):
        with self.assertRaises(UserError):
            send_to_recycle_bin([self.in_progress], self.videos, recycle=lambda p: None, report=lambda _: None)


if __name__ == "__main__":
    unittest.main()
