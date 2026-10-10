"""Write the compact transcript of a video's recordings.

    python scripts/prepara.py <video folder>

Reads the recordings listed in tagli.json, their transcripts (written by the
transcriber beside each recording), the measured silences and any OBS
markers, and writes trascrizione-compatta.md: one line per sentence, with the
pause before it, plus waits, possible retakes, audio without text, silences
hidden inside a sentence, and markers.
"""

from __future__ import annotations

import argparse
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import (  # noqa: E402
    COMPACT_TRANSCRIPT,
    Interval,
    Segment,
    chapter_markers,
    fmt,
    load_cut_list,
    load_segments,
    load_silences,
    main_wrapper,
    probe,
    silence_covering,
    transcript_path,
    words,
)

WAIT_MIN_SEC = 5.0
RETAKE_WINDOW_SEC = 30.0  # a retake starts within this long of the attempt it repeats
RETAKE_LOOKAHEAD = 3  # sentences after an attempt that can be its retake
RETAKE_RATIO = 0.8
HIDDEN_SILENCE_MIN_SEC = 1.0
UNTEXTED_GAP_MIN_SEC = 1.0
UNTEXTED_SOUND_MIN_SEC = 1.5  # shorter sounds are mostly fillers and breaths
PAUSE_SHOWN_MIN_SEC = 0.5

LEGEND = (
    "Tempi della registrazione (mm:ss.s). (+N s) = pausa prima della frase · "
    "⏸ attesa · ⟲ possibile ripartenza · ♪ audio senza testo · "
    "⧗ silenzio nascosto dentro la frase · ⚑ marcatore OBS"
)


def is_retake(earlier: list[str], later: list[str]) -> bool:
    """Whether the later sentence looks like a new attempt at the earlier one."""
    if len(earlier) < 3 or not later:
        return False
    if later[: len(earlier)] == earlier:
        return True
    head_a, head_b = earlier[:10], later[:10]
    block = SequenceMatcher(None, head_a, head_b, autojunk=False).find_longest_match(
        0, len(head_a), 0, len(head_b)
    )
    if block.size >= 4:
        return True
    return SequenceMatcher(None, earlier, later, autojunk=False).ratio() >= RETAKE_RATIO


def find_retakes(segments: list[Segment]) -> dict[int, int]:
    """Index of a sentence -> index of the later sentence that seems to retake it.

    The window counts from the start of the attempt, because the transcriber
    sometimes stretches the attempt's last word over the pause that follows.
    """
    retakes: dict[int, int] = {}
    for i, first in enumerate(segments):
        first_words = words(first.text)
        for j in range(i + 1, min(i + 1 + RETAKE_LOOKAHEAD, len(segments))):
            if segments[j].start - first.start > RETAKE_WINDOW_SEC:
                break
            if is_retake(first_words, words(segments[j].text)):
                retakes[i] = j
                break
    return retakes


def compact_lines(
    segments: list[Segment],
    silences: list[Interval],
    markers: list[float],
    duration: float,
) -> list[str]:
    """The lines of one recording in the compact transcript, in time order."""
    events: list[tuple[float, int, str]] = []
    retakes = find_retakes(segments)

    for s0, s1 in silences:
        if s1 - s0 > WAIT_MIN_SEC:
            events.append((s0, 0, f"⏸ attesa {fmt(s0)}–{fmt(s1)} ({s1 - s0:.0f} s)"))
    for t in markers:
        events.append((t, 1, f"⚑ marcatore {fmt(t)}"))

    previous_end = 0.0
    edges = [(0.0, 0.0)] + [(s.start, s.end) for s in segments] + [(duration, duration)]
    for (_, gap_start), (gap_end, _) in zip(edges, edges[1:]):
        length = gap_end - gap_start
        if length >= UNTEXTED_GAP_MIN_SEC:
            sound = length - silence_covering(silences, gap_start, gap_end)
            if sound >= UNTEXTED_SOUND_MIN_SEC:
                events.append(
                    (gap_start, 2, f"♪ audio senza testo {fmt(gap_start)}–{fmt(gap_end)} ({sound:.1f} s di suono)")
                )

    for i, segment in enumerate(segments):
        pause = segment.start - previous_end
        line = f"[{fmt(segment.start)}–{fmt(segment.end)}]"
        if pause >= PAUSE_SHOWN_MIN_SEC:
            line += f" (+{pause:.1f} s)"
        line += f" {segment.text}"
        for s0, s1 in silences:
            if s1 - s0 >= HIDDEN_SILENCE_MIN_SEC and segment.start + 0.1 < s0 and s1 < segment.end - 0.1:
                line += f"  ⧗ silenzio {fmt(s0)}–{fmt(s1)}"
        if i in retakes:
            line += f"  ⟲ forse ripresa a {fmt(segments[retakes[i]].start)}"
        events.append((segment.start, 3, line))
        previous_end = max(previous_end, segment.end)

    return [text for _, _, text in sorted(events, key=lambda e: (e[0], e[1]))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrive la trascrizione compatta del video.")
    parser.add_argument("cartella", type=Path, help="cartella del video, con tagli.json")
    folder = parser.parse_args().cartella.resolve()

    cut_list = load_cut_list(folder)
    infos = [probe(path) for path in cut_list.recordings]
    durations = [info.duration for info in infos]
    segments = [load_segments(transcript_path(path)) for path in cut_list.recordings]
    silences = load_silences(folder, cut_list.recordings, durations)

    out = ["# Trascrizione compatta", "", LEGEND]
    summary = []
    for index, path in enumerate(cut_list.recordings):
        markers = chapter_markers(path)
        lines = compact_lines(segments[index], silences[index], markers, durations[index])
        out += ["", f"## Registrazione {index + 1}: {path.name} ({fmt(durations[index])})", ""]
        out += lines
        waits = sum(1 for line in lines if line.startswith("⏸"))
        retakes = sum(1 for line in lines if "⟲" in line)
        untexted = sum(1 for line in lines if line.startswith("♪"))
        summary.append(
            f"{path.name}: {len(segments[index])} frasi, {waits} attese, "
            f"{retakes} possibili ripartenze, {untexted} tratti di audio senza testo, "
            f"{len(markers)} marcatori"
        )
    target = folder / COMPACT_TRANSCRIPT
    target.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Scritta {target}")
    for line in summary:
        print(f"- {line}")


if __name__ == "__main__":
    main_wrapper(main)
