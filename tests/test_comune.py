import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import (  # noqa: E402
    Change,
    CutList,
    UserError,
    build_timeline,
    edit_to_source,
    fmt,
    parse_silencedetect,
    parse_time,
    snap_cut_end,
    snap_cut_start,
)

REC = [Path("rec.mp4")]


def cut_list(*changes: Change) -> CutList:
    return CutList(REC, list(changes))


class TimeTests(unittest.TestCase):
    def test_fmt(self):
        self.assertEqual(fmt(12.34), "00:12.3")
        self.assertEqual(fmt(200.0), "03:20.0")
        self.assertEqual(fmt(3723.4), "1:02:03.4")

    def test_parse_time(self):
        self.assertEqual(parse_time("3:20"), 200.0)
        self.assertEqual(parse_time("1:02:03.5"), 3723.5)
        self.assertEqual(parse_time("200.5"), 200.5)


class SilenceTests(unittest.TestCase):
    def test_parse_silencedetect(self):
        log = "\n".join([
            "[silencedetect @ 0000] silence_start: -0.0213",
            "[silencedetect @ 0000] silence_end: 2.5 | silence_duration: 2.52",
            "size=N/A time=00:00:05.00",
            "[silencedetect @ 0000] silence_start: 10.25",
            "[silencedetect @ 0000] silence_end: 12 | silence_duration: 1.75",
            "[silencedetect @ 0000] silence_start: 98",
        ])
        self.assertEqual(parse_silencedetect(log, 100.0), [(0.0, 2.5), (10.25, 12.0), (98.0, 100.0)])

    def test_snap_keeps_up_to_200_ms_of_silence_beside_speech(self):
        silences = [(10.0, 11.0)]
        self.assertAlmostEqual(snap_cut_start(10.4, silences), 10.2)
        self.assertAlmostEqual(snap_cut_end(10.6, silences), 10.8)

    def test_snap_reaches_a_silence_within_tolerance(self):
        self.assertAlmostEqual(snap_cut_start(9.5, [(10.0, 11.0)]), 10.2)
        self.assertAlmostEqual(snap_cut_end(11.5, [(10.0, 11.0)]), 10.8)

    def test_snap_refuses_when_no_silence_is_near(self):
        self.assertIsNone(snap_cut_start(8.0, [(10.0, 11.0)]))
        self.assertIsNone(snap_cut_end(13.0, [(10.0, 11.0)]))

    def test_short_silence_is_split_in_the_middle(self):
        self.assertAlmostEqual(snap_cut_start(10.1, [(10.0, 10.3)]), 10.15)
        self.assertAlmostEqual(snap_cut_end(10.2, [(10.0, 10.3)]), 10.15)


class TimelineTests(unittest.TestCase):
    silences = [[(0.0, 2.5), (10.0, 11.0), (20.0, 40.0), (60.0, 61.0)]]

    def test_cuts_at_the_ends_and_a_wait(self):
        timeline = build_timeline(
            cut_list(
                Change(0, 0.0, 2.4, "cut"),
                Change(0, 20.0, 40.0, "speed"),
                Change(0, 60.3, 100.0, "cut"),
            ),
            [100.0],
            self.silences,
        )
        spans = [(round(p.src_start, 3), round(p.src_end, 3), round(p.speed, 3), p.silent)
                 for p in timeline.pieces]
        self.assertEqual(spans, [(2.3, 21.0, 1.0, False), (21.0, 39.0, 9.0, True), (39.0, 60.2, 1.0, False)])
        self.assertAlmostEqual(timeline.duration, 18.7 + 2.0 + 21.2)
        self.assertEqual(timeline.joins, [])
        self.assertEqual(timeline.refusals, [])

    def test_a_wait_lasts_four_seconds_with_one_normal_second_at_each_end(self):
        timeline = build_timeline(cut_list(Change(0, 20.0, 40.0, "speed")), [100.0], self.silences)
        wait = [p for p in timeline.pieces if p.silent][0]
        self.assertAlmostEqual((wait.src_start, wait.src_end), (21.0, 39.0))
        self.assertAlmostEqual(wait.out_end - wait.out_start, 2.0)

    def test_an_inner_cut_makes_a_join(self):
        timeline = build_timeline(cut_list(Change(0, 10.4, 60.6, "cut")), [100.0], self.silences)
        self.assertEqual([(p.src_start, p.src_end) for p in timeline.pieces], [(0.0, 10.2), (60.8, 100.0)])
        self.assertEqual([round(j, 3) for j in timeline.joins], [10.2])

    def test_a_cut_right_after_a_wait_keeps_the_wait_last_second(self):
        silences = [[(100.0, 152.0), (158.0, 159.0)]]
        timeline = build_timeline(
            cut_list(Change(0, 100.5, 150.0, "speed"), Change(0, 150.0, 158.5, "cut")), [200.0], silences
        )
        spans = [(round(p.src_start, 3), round(p.src_end, 3)) for p in timeline.pieces]
        self.assertEqual(spans, [(0.0, 101.5), (101.5, 149.0), (149.0, 150.0), (158.8, 200.0)])
        self.assertEqual(len(timeline.joins), 1)

    def test_a_short_piece_kept_between_two_cuts_survives(self):
        silences = [[(549.9, 550.3), (560.288, 562.711), (563.142, 568.611)]]
        timeline = build_timeline(
            cut_list(Change(0, 550.0, 562.95, "cut"), Change(0, 563.75, 568.35, "cut")), [600.0], silences
        )
        spans = [(round(p.src_start, 3), round(p.src_end, 3)) for p in timeline.pieces]
        self.assertEqual(spans, [(0.0, 550.1), (562.511, 563.342), (568.411, 600.0)])
        self.assertEqual(len(timeline.joins), 2)

    def test_edges_snapping_past_each_other_never_repeat_content(self):
        timeline = build_timeline(
            cut_list(Change(0, 10.0, 10.5, "cut")), [100.0], [[(9.0, 9.9), (10.6, 11.0)]]
        )
        for before, after in zip(timeline.pieces, timeline.pieces[1:]):
            self.assertGreaterEqual(after.src_start, before.src_end)

    def test_a_dropped_tiny_piece_makes_no_false_join(self):
        timeline = build_timeline(
            cut_list(Change(0, 20.0, 40.0, "speed"), Change(0, 40.02, 60.0, "speed")),
            [100.0], [[(20.0, 60.0)]],
        )
        self.assertEqual(timeline.joins, [])

    def test_a_cut_outside_silence_is_refused_and_not_made(self):
        timeline = build_timeline(cut_list(Change(0, 30.0, 50.0, "cut")), [100.0], [[(0.0, 2.5)]])
        self.assertEqual(len(timeline.refusals), 1)
        self.assertEqual([(p.src_start, p.src_end) for p in timeline.pieces], [(0.0, 100.0)])

    def test_a_short_wait_is_left_alone_with_a_warning(self):
        timeline = build_timeline(cut_list(Change(0, 20.0, 23.0, "speed")), [100.0], self.silences)
        self.assertEqual(len(timeline.pieces), 1)
        self.assertEqual(len(timeline.warnings), 1)

    def test_a_wait_with_sound_inside_is_flagged(self):
        timeline = build_timeline(cut_list(Change(0, 45.0, 59.0, "speed")), [100.0], self.silences)
        self.assertTrue(any("silenzio" in w for w in timeline.warnings))

    def test_two_recordings_are_joined_in_order(self):
        timeline = build_timeline(
            CutList([Path("a.mp4"), Path("b.mp4")], []), [10.0, 5.0], [[], []]
        )
        self.assertEqual([p.recording for p in timeline.pieces], [0, 1])
        self.assertEqual(timeline.joins, [10.0])

    def test_invalid_cut_lists_are_rejected(self):
        for changes in (
            [Change(0, 5.0, 4.0, "cut")],
            [Change(0, 5.0, 150.0, "cut")],
            [Change(0, 1.0, 5.0, "zoom")],
            [Change(1, 1.0, 5.0, "cut")],
            [Change(0, 1.0, 5.0, "cut"), Change(0, 4.0, 8.0, "cut")],
        ):
            with self.subTest(changes=changes), self.assertRaises(UserError):
                build_timeline(cut_list(*changes), [100.0], self.silences)

    def test_edit_time_maps_back_to_the_recording(self):
        timeline = build_timeline(
            cut_list(Change(0, 0.0, 2.4, "cut"), Change(0, 20.0, 40.0, "speed")), [100.0], self.silences
        )
        self.assertEqual(edit_to_source(timeline, 0.0), (0, 2.3))
        recording, t = edit_to_source(timeline, 19.7)  # one second into the sped-up wait
        self.assertEqual(recording, 0)
        self.assertAlmostEqual(t, 30.0)


if __name__ == "__main__":
    unittest.main()
