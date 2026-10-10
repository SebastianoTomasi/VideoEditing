import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import MediaInfo, Piece, Timeline  # noqa: E402
from monta import filter_graph, parse_loudnorm  # noqa: E402

INFO = MediaInfo(duration=100.0, width=1280, height=800, fps="20/1")


def timeline(*pieces: Piece) -> Timeline:
    return Timeline(list(pieces), [], [], [])


class FilterGraphTests(unittest.TestCase):
    normal = Piece(0, 0.0, 10.2, 1.0, False, 0.0, 10.2)
    wait = Piece(0, 21.0, 39.0, 9.0, True, 10.2, 12.2)

    def test_normal_and_sped_up_pieces(self):
        graph = filter_graph(timeline(self.normal, self.wait), [INFO])
        self.assertIn("[0:v:0]trim=start=0.000:end=10.200,setpts=PTS-STARTPTS,setsar=1,fps=20/1", graph)
        self.assertIn("[0:a:0]atrim=start=0.000:end=10.200", graph)
        self.assertIn("afade=t=in:d=0.030", graph)
        self.assertIn("afade=t=out:st=10.170:d=0.030", graph)
        self.assertIn("setpts=(PTS-STARTPTS)/9.000000", graph)
        self.assertIn("anullsrc=r=48000:cl=stereo,atrim=duration=2.000", graph)
        self.assertIn("[v0][a0][v1][a1]concat=n=2:v=1:a=1[vout][acat]", graph)
        self.assertTrue(graph.endswith("[acat]anull,aresample=48000[aout]"))

    def test_audio_only_graph_for_measuring_loudness(self):
        graph = filter_graph(timeline(self.normal, self.wait), [INFO], audio_only=True, loudnorm="loudnorm=I=-14")
        self.assertNotIn(":v:0]", graph)
        self.assertIn("[a0][a1]concat=n=2:v=0:a=1[acat]", graph)
        self.assertIn("[acat]loudnorm=I=-14,aresample=48000[aout]", graph)

    def test_a_recording_of_another_size_is_scaled_to_the_first(self):
        other = MediaInfo(duration=50.0, width=1920, height=1080, fps="30/1")
        second = Piece(1, 0.0, 5.0, 1.0, False, 12.2, 17.2)
        graph = filter_graph(timeline(self.normal, second), [INFO, other])
        self.assertIn("[1:v:0]trim=start=0.000:end=5.000,setpts=PTS-STARTPTS,scale=1280:800", graph)
        self.assertIn("pad=1280:800", graph)
        self.assertNotIn("[0:v:0]trim=start=0.000:end=10.200,setpts=PTS-STARTPTS,scale", graph)


class LoudnormTests(unittest.TestCase):
    def test_parse_the_measuring_pass(self):
        stderr = """[Parsed_loudnorm_0 @ 0000]
{
	"input_i" : "-23.54",
	"input_tp" : "-4.11",
	"input_lra" : "6.20",
	"input_thresh" : "-34.10",
	"output_i" : "-14.20",
	"target_offset" : "0.20"
}
"""
        measured = parse_loudnorm(stderr)
        self.assertEqual(measured["input_i"], "-23.54")
        self.assertEqual(measured["target_offset"], "0.20")


if __name__ == "__main__":
    unittest.main()
