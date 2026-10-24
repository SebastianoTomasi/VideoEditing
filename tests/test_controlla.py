import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import Piece, Segment, Timeline  # noqa: E402
from controlla import (  # noqa: E402
    EXCERPT_GAP_SEC,
    changed_joins,
    compare,
    compare_excerpts,
    excerpts,
    expected_words,
    heard_in_excerpts,
    heard_words,
    spread,
    straddling_words,
    subtitles,
)


def words_at(text: str, start: float, step: float = 0.5):
    return [(w, start + k * step) for k, w in enumerate(text.split())]


def edit_of(*stretches):
    """A timeline playing (recording, from, to) stretches one after the other, with a join between each."""
    pieces, out = [], 0.0
    for recording, start, end in stretches:
        pieces.append(Piece(recording, start, end, 1.0, False, out, out + end - start))
        out += end - start
    return Timeline(pieces, [p.out_start for p in pieces[1:]], [], [])


class ChangedJoinsTests(unittest.TestCase):
    one = [Path("a.mp4")]

    def test_an_unchanged_edit_has_no_changed_joins(self):
        edit = edit_of((0, 0.0, 100.0), (0, 120.0, 200.0), (0, 230.0, 300.0))
        self.assertEqual(changed_joins(edit, self.one, edit, self.one), [])

    def test_a_new_cut_changes_only_its_own_join(self):
        before = edit_of((0, 0.0, 100.0), (0, 120.0, 300.0))
        after = edit_of((0, 0.0, 100.0), (0, 120.0, 200.0), (0, 230.0, 300.0))
        self.assertEqual(changed_joins(before, self.one, after, self.one), [180.0])

    def test_a_join_that_only_moved_in_the_edit_is_not_changed(self):
        before = edit_of((0, 0.0, 100.0), (0, 120.0, 300.0))
        after = edit_of((0, 0.0, 40.0), (0, 60.0, 100.0), (0, 120.0, 300.0))
        self.assertEqual(changed_joins(before, self.one, after, self.one), [40.0])

    def test_a_join_with_a_change_close_by_is_changed(self):
        before = edit_of((0, 0.0, 100.0), (0, 120.0, 300.0))
        after = edit_of((0, 0.0, 100.0), (0, 120.0, 125.0), (0, 130.0, 300.0))
        self.assertEqual(changed_joins(before, self.one, after, self.one), [100.0, 105.0])

    def test_recordings_are_matched_by_path_not_by_index(self):
        before = edit_of((0, 0.0, 100.0), (0, 120.0, 300.0))
        after = edit_of((0, 0.0, 50.0), (1, 0.0, 100.0), (1, 120.0, 300.0))
        self.assertEqual(changed_joins(before, self.one, after, [Path("intro.mp4"), Path("a.mp4")]), [50.0])


class ExcerptsTests(unittest.TestCase):
    def test_each_join_gets_its_own_stretch_inside_the_edit(self):
        self.assertEqual(excerpts([10.0, 30.0, 100.0], duration=110.0), [(0.0, 25.0), (15.0, 45.0), (85.0, 110.0)])


class HeardInExcerptsTests(unittest.TestCase):
    # The stretches 0-25 and 85-110 of the edit sit at 0-25 and 25+gap onwards in the excerpts file.
    stretches = [(0.0, 25.0), (85.0, 110.0)]
    second = 25.0 + EXCERPT_GAP_SEC

    def test_words_get_back_their_time_in_the_edit(self):
        segments = [Segment(10.0, 12.0, "uno due"), Segment(self.second + 3.0, self.second + 5.0, "tre quattro")]
        self.assertEqual(heard_in_excerpts(segments, self.stretches),
                         [[("uno", 10.5), ("due", 11.5)], [("tre", 88.5), ("quattro", 89.5)]])

    def test_a_word_heard_in_the_silence_between_goes_to_the_nearer_stretch(self):
        middle = 25.0 + EXCERPT_GAP_SEC / 2
        segments = [Segment(middle - 1.0, middle - 0.5, "eh"), Segment(middle + 0.5, middle + 1.0, "ah")]
        self.assertEqual(heard_in_excerpts(segments, self.stretches), [[("eh", 25.0)], [("ah", 85.0)]])


class CompareExcerptsTests(unittest.TestCase):
    def test_a_problem_between_two_close_joins_is_reported_once(self):
        expected = words_at("ecco il primo passo apriamo il file e vediamo il risultato finale", 98.0)
        heard_text = "ecco il primo passo apriamo il e vediamo il risultato finale"
        joins = [100.0, 102.0]
        heard = [words_at(heard_text, 98.0), words_at(heard_text, 98.0)]
        problems = compare_excerpts(expected, heard, joins, [], duration=200.0)
        self.assertEqual([(p.join, p.kind, p.expected) for p in problems], [(100.0, "manca", "file")])

    def test_a_stretch_is_not_compared_at_a_join_near_its_cut_edge(self):
        # The stretch of the join at 100 ends at 115, cutting the speech around the join at 114.
        expected = words_at("ecco il primo passo apriamo il file", 111.0)
        heard = [words_at("ecco il primo passo", 111.0), words_at("ecco il primo passo apriamo il file", 111.0)]
        self.assertEqual(compare_excerpts(expected, heard, [100.0, 114.0], [], duration=200.0), [])


class StraddlingWordsTests(unittest.TestCase):
    def test_a_sentence_crossed_by_a_cut_edge_is_listed_at_that_edge(self):
        timeline = Timeline([Piece(0, 0.0, 11.0, 1.0, False, 0.0, 11.0)], [], [], [])
        segments = [[Segment(2.0, 5.0, "tutta dentro"), Segment(9.0, 14.0, "skill di matt pocock")]]
        self.assertEqual(straddling_words(timeline, segments), [(11.0, {"skill", "di", "matt", "pocock"})])


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

    def test_an_extra_word_of_a_sentence_cut_through_is_not_reported(self):
        heard = words_at("ecco il primo passo apriamo il file pocock e vediamo il risultato finale", 0.0)
        straddling = [(3.0, {"skill", "di", "matt", "pocock"})]
        self.assertEqual(compare(self.expected, heard, joins=[3.0], straddling=straddling), [])

    def test_a_missing_word_of_a_sentence_cut_through_is_still_reported(self):
        heard = words_at("ecco il primo passo apriamo il e vediamo il risultato finale", 0.0)
        straddling = [(3.0, {"apriamo", "il", "file"})]
        self.assertEqual([p.kind for p in compare(self.expected, heard, [3.0], straddling)], ["manca"])

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


class SpreadTests(unittest.TestCase):
    def test_words_skip_a_silence_hidden_in_the_segment(self):
        # A stretched last word: speech 0-4 s, then 4 s of measured silence.
        spread_words = spread(Segment(0.0, 8.0, "uno due tre quattro"), [(4.0, 8.0)])
        self.assertEqual([round(t, 2) for _, t in spread_words], [0.5, 1.5, 2.5, 3.5])

    def test_a_hidden_silence_cuts_through_the_middle(self):
        spread_words = spread(Segment(0.0, 6.0, "uno due"), [(1.0, 5.0)])
        self.assertEqual([round(t, 2) for _, t in spread_words], [0.5, 5.5])


if __name__ == "__main__":
    unittest.main()
