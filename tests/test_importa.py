import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import UserError  # noqa: E402
from importa import import_recordings  # noqa: E402

NAME = "2026-10-25 21-14-56"


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.obs = root / "OBS"
        self.videos = root / "videos"
        self.obs.mkdir()
        self.videos.mkdir()
        self.folder = self.videos / "2026-10-25-video"
        self.recording = self.obs / f"{NAME}.mp4"
        self.recording.write_bytes(b"video")
        transcript = {"file": f"{NAME}.mp4", "recording": str(self.recording), "turns": []}
        (self.obs / f"{NAME} - trascrizione.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        (self.obs / f"{NAME} - trascrizione.txt").write_text("Trascrizione", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_import(self, *recordings: Path) -> list[Path]:
        return import_recordings(self.folder, list(recordings), self.videos, report=lambda _: None)

    def test_moves_the_recording_and_its_transcripts_into_a_new_folder(self):
        paths = self.run_import(self.recording)

        moved = self.folder / f"{NAME}.mp4"
        self.assertEqual(paths, [moved])
        self.assertTrue(moved.exists())
        self.assertFalse(self.recording.exists())
        self.assertTrue((self.folder / f"{NAME} - trascrizione.txt").exists())
        self.assertEqual(list(self.obs.iterdir()), [])
        cut_list = json.loads((self.folder / "tagli.json").read_text(encoding="utf-8"))
        self.assertEqual(cut_list, {"recordings": [moved.as_posix()], "changes": []})
        transcript = json.loads((self.folder / f"{NAME} - trascrizione.json").read_text(encoding="utf-8"))
        self.assertEqual(transcript["recording"], str(moved))

    def test_points_the_files_of_an_existing_folder_at_the_moved_recording(self):
        self.folder.mkdir()
        cut_list = (
            "{\n"
            f'  "recordings": ["{self.recording.as_posix()}"],\n'
            '  "changes": [\n'
            '    {"recording": 0, "start": 0.0, "end": 1.6, "action": "cut", "reason": "inizio", "text": "è"}\n'
            "  ]\n"
            "}\n"
        )
        (self.folder / "tagli.json").write_text(cut_list, encoding="utf-8")
        edit_map = {"recordings": [str(self.recording)], "pieces": []}
        (self.folder / "montaggio.json").write_text(json.dumps(edit_map, indent=1), encoding="utf-8")
        silences = {str(self.recording): {"stamp": [5, 0, "-35dB:0.3"], "silences": []}}
        (self.folder / "silenzi.json").write_text(json.dumps(silences, indent=1), encoding="utf-8")

        self.run_import(self.recording)

        moved = self.folder / f"{NAME}.mp4"
        self.assertEqual(
            (self.folder / "tagli.json").read_text(encoding="utf-8"),
            cut_list.replace(self.recording.as_posix(), moved.as_posix()),
        )
        self.assertEqual(json.loads((self.folder / "montaggio.json").read_text(encoding="utf-8"))["recordings"], [str(moved)])
        self.assertEqual(list(json.loads((self.folder / "silenzi.json").read_text(encoding="utf-8"))), [str(moved)])

    def test_refuses_to_overwrite_and_moves_nothing(self):
        self.folder.mkdir()
        (self.folder / f"{NAME} - trascrizione.txt").write_text("altro", encoding="utf-8")

        with self.assertRaises(UserError):
            self.run_import(self.recording)

        self.assertTrue(self.recording.exists())
        self.assertEqual((self.folder / f"{NAME} - trascrizione.txt").read_text(encoding="utf-8"), "altro")
        self.assertFalse((self.folder / "tagli.json").exists())

    def test_leaves_a_recording_already_in_another_video_folder_where_it_is(self):
        other = self.videos / "2026-10-24-video"
        other.mkdir()
        kept = other / "2026-10-24 17-15-51.mp4"
        kept.write_bytes(b"video")

        paths = self.run_import(kept, self.recording)

        self.assertTrue(kept.exists())
        self.assertEqual(paths, [kept, self.folder / f"{NAME}.mp4"])

    def test_stops_on_a_missing_recording(self):
        with self.assertRaises(UserError):
            self.run_import(self.obs / "manca.mp4")


if __name__ == "__main__":
    unittest.main()
