import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comune import Segment, words  # noqa: E402
from prepara import compact_lines, find_retakes, is_retake  # noqa: E402


class RetakeTests(unittest.TestCase):
    def test_a_reworded_restart_is_a_retake(self):
        first = words("Buon salve a tutti, io mi chiamo Sebastiano, quasi PhD in fisica teorica.")
        second = words("Salve a tutti, io sono Sebastiano, sono un quasi PhD in fisica teorica.")
        self.assertTrue(is_retake(first, second))

    def test_a_cut_off_sentence_said_again_is_a_retake(self):
        self.assertTrue(is_retake(words("Quindi adesso apriamo"), words("Quindi adesso apriamo il file di configurazione.")))

    def test_the_same_sentence_twice_is_a_retake(self):
        self.assertTrue(is_retake(words("Qui vedete il risultato."), words("Qui vedete il risultato finale.")))

    def test_two_different_sentences_are_not(self):
        self.assertFalse(is_retake(words("Apriamo il terminale e lanciamo il comando."),
                                   words("Il risultato è una lista di file.")))

    def test_the_same_words_inside_both_openings_are_a_retake(self):
        self.assertTrue(is_retake(
            words("nient'altro da fare, ok, senza perdere altro tempo, passiamo ad una demo."),
            words("Ok, quindi senza perdere altro tempo cominciamo con una demo."),
        ))

    def test_only_sentences_close_in_time_count(self):
        near = [Segment(0.0, 3.0, "Apriamo il file di configurazione"),
                Segment(5.0, 8.0, "Apriamo il file di configurazione adesso")]
        far = [Segment(0.0, 3.0, "Apriamo il file di configurazione"),
               Segment(40.0, 43.0, "Apriamo il file di configurazione adesso")]
        self.assertEqual(find_retakes(near), {0: 1})
        self.assertEqual(find_retakes(far), {})

    def test_a_retake_after_a_stretched_word_is_found(self):
        # From the recording of 2026-10-10: the transcriber stretched "erba."
        # over the 12 s pause before the retake.
        segments = [
            Segment(2.6, 7.3, "Buon salve a tutti, io mi chiamo Sebastiano, quasi PhD in fisica teorica"),
            Segment(8.6, 21.6, "e programmatore in erba."),
            Segment(21.6, 23.5, "Salve a tutti, io sono Sebastiano,"),
        ]
        self.assertEqual(find_retakes(segments), {0: 2})


class CompactLinesTests(unittest.TestCase):
    def test_sentences_waits_markers_and_audio_without_text(self):
        segments = [
            Segment(1.0, 4.0, "Salve a tutti."),
            Segment(5.0, 20.0, "Oggi vediamo come funziona."),
            Segment(40.0, 42.0, "Ecco il risultato."),
        ]
        silences = [(0.0, 1.0), (4.0, 5.0), (8.0, 10.0), (20.0, 30.0)]  # 30-40 s: sound without text
        lines = compact_lines(segments, silences, markers=[41.0], duration=42.0)
        self.assertEqual(lines[0], "[00:01.0–00:04.0] (+1.0 s) Salve a tutti.")
        self.assertIn("(+1.0 s) Oggi vediamo come funziona.  ⧗ silenzio 00:08.0–00:10.0", lines[1])
        self.assertEqual(lines[2], "⏸ attesa 00:20.0–00:30.0 (10 s)")
        self.assertEqual(lines[3], "♪ audio senza testo 00:20.0–00:40.0 (10.0 s di suono)")
        self.assertEqual(lines[4], "[00:40.0–00:42.0] (+20.0 s) Ecco il risultato.")
        self.assertEqual(lines[5], "⚑ marcatore 00:41.0")

    def test_a_retake_points_to_the_later_attempt(self):
        segments = [Segment(0.0, 3.0, "Apriamo il file di configurazione"),
                    Segment(5.0, 8.0, "Apriamo il file di configurazione adesso")]
        lines = compact_lines(segments, [(3.0, 5.0)], markers=[], duration=8.0)
        self.assertIn("⟲ forse ripresa a 00:05.0", lines[0])


if __name__ == "__main__":
    unittest.main()
