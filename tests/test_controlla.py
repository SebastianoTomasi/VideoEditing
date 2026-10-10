import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import Piece, Segment, Timeline  # noqa: E402
from controlla import compare, expected_words, heard_words, subtitles  # noqa: E402


def words_at(text: str, start: float, step: float = 0.5):
    return [(w, start + k * step) for k, w in enumerate(text.split())]


class ExpectedWordsTests(unittest.TestCase):
    def test_kept_words_get_their_time_in_the_edit(self):
        timeline = Timeline(
            [Piece(0, 10.0, 20.0, 1.0, False, 0.0, 10.0), Piece(0, 50.0, 60.0, 1.0, False, 10.0, 20.0)],
            [10.0], [], [],
        )
        segments = [[Segment(10.0, 12.0, "uno due"), Segment(30.0, 32.0, "tagliato via"),
                     Segment(50.0, 52.0, "tre quattro")]]
        expected = expected_words(timeline, segments)
        self.assertEqual([w for w, _ in expected], ["uno", "due", "tre", "quattro"])
        self.assertAlmostEqual(expected[0][1], 0.5)
        self.assertAlmostEqual(expected[2][1], 10.5)


class CompareTests(unittest.TestCase):
    expected = words_at("ecco il primo passo apriamo il file e vediamo il risultato finale", 0.0)

    def test_a_missing_word_at_a_join_is_reported(self):
        heard = words_at("ecco il primo passo apriamo il e vediamo il risultato finale", 0.0)
        problems = compare(self.expected, heard, joins=[3.0])
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].kind, "manca")
        self.assertEqual(problems[0].expected, "file")
        self.assertEqual(problems[0].join, 3.0)

    def test_a_repeated_phrase_at_a_join_is_reported(self):
        heard = words_at("ecco il primo passo apriamo il file apriamo il file e vediamo il risultato finale", 0.0)
        problems = compare(self.expected, heard, joins=[3.0])
        self.assertEqual([p.kind for p in problems], ["in più"])

    def test_differences_far_from_joins_are_ignored(self):
        heard = words_at("ecco il primo passo apriamo il file e vediamo il risultato", 0.0)
        self.assertEqual(compare(self.expected, heard, joins=[0.0]), [])

    def test_a_word_heard_slightly_differently_is_noise(self):
        heard = words_at("ecco il primo passo apriamo il files e vediamo il risultato finale", 0.0)
        self.assertEqual(compare(self.expected, heard, joins=[3.0]), [])


class SubtitleTests(unittest.TestCase):
    def test_short_segment_is_one_cue(self):
        srt = subtitles([Segment(1.5, 3.25, "Ciao a tutti.")])
        self.assertEqual(srt, "1\n00:00:01,500 --> 00:00:03,250\nCiao a tutti.\n")

    def test_long_segment_is_split_into_two_line_cues(self):
        text = " ".join(["parola"] * 30)
        srt = subtitles([Segment(0.0, 12.0, text)])
        cues = [c for c in srt.split("\n\n") if c.strip()]
        self.assertGreater(len(cues), 1)
        for cue in cues:
            lines = cue.strip().split("\n")[2:]
            self.assertLessEqual(len(lines), 2)
            self.assertTrue(all(len(line) <= 42 for line in lines))
        self.assertTrue(srt.rstrip().split("\n")[-2].endswith("00:00:12,000"))


class HeardWordsTests(unittest.TestCase):
    def test_words_are_spread_over_the_segment(self):
        heard = heard_words([Segment(0.0, 2.0, "uno due")])
        self.assertEqual(heard, [("uno", 0.5), ("due", 1.5)])


if __name__ == "__main__":
    unittest.main()
