"""Check an edit at its joins and write its subtitles.

    python scripts/controlla.py <video folder>

Has the transcriber transcribe montaggio.mp4, compares the words heard near
each join with the words the cut list keeps there, reports the potential
problems with their time in the edit, checks the duration, and writes
montaggio.srt. It fixes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import (  # noqa: E402
    EDIT,
    EDIT_MAP,
    SUBTITLES,
    Interval,
    Segment,
    Timeline,
    UserError,
    fmt,
    load_segments,
    load_silences,
    main_wrapper,
    probe,
    timeline_from_json,
    transcribe,
    transcript_path,
    words,
)

JOIN_WINDOW_SEC = 3.0
CONTEXT_WORDS = 4
DURATION_TOLERANCE_SEC = 0.5
SUBTITLE_LINE_CHARS = 42

Word = tuple[str, float]  # a word and its approximate time in the edit


@dataclass(frozen=True)
class Problem:
    join: float
    kind: str  # "manca", "in più", "diverso"
    expected: str
    heard: str
    context: str


def spread(segment: Segment, silences: list[Interval] = ()) -> list[tuple[str, float]]:
    """The words of a segment, each at an even share of its spoken time.

    Measured silences inside the segment are skipped, because the transcriber
    sometimes stretches a word over the pause that follows it.
    """
    tokens = words(segment.text)
    if not tokens:
        return []
    spoken: list[Interval] = []
    cursor = segment.start
    for s0, s1 in sorted(silences):
        if s1 <= cursor or s0 >= segment.end:
            continue
        if s0 > cursor:
            spoken.append((cursor, s0))
        cursor = max(cursor, s1)
    if cursor < segment.end:
        spoken.append((cursor, segment.end))
    total = sum(b - a for a, b in spoken)
    if total <= 0:
        spoken, total = [(segment.start, segment.end)], max(segment.end - segment.start, 1e-6)
    result = []
    for k, word in enumerate(tokens):
        offset = total * (k + 0.5) / len(tokens)
        for a, b in spoken:
            if offset <= b - a:
                result.append((word, a + offset))
                break
            offset -= b - a
        else:
            result.append((word, spoken[-1][1]))
    return result


def expected_words(
    timeline: Timeline,
    segments_by_recording: list[list[Segment]],
    silences_by_recording: list[list[Interval]] | None = None,
) -> list[Word]:
    """The words the edit should contain, in order, with their time in the edit."""
    result: list[Word] = []
    for piece in timeline.pieces:
        if piece.silent:
            continue
        silences = silences_by_recording[piece.recording] if silences_by_recording else []
        for segment in segments_by_recording[piece.recording]:
            if segment.end < piece.src_start or segment.start > piece.src_end:
                continue
            for word, t in spread(segment, silences):
                if piece.src_start <= t < piece.src_end:
                    result.append((word, piece.out_start + (t - piece.src_start) / piece.speed))
    return result


def heard_words(segments: list[Segment]) -> list[Word]:
    return [pair for segment in segments for pair in spread(segment)]


def straddling_words(timeline: Timeline, segments_by_recording: list[list[Segment]]) -> list[tuple[float, set[str]]]:
    """Words of sentences that a cut edge goes through, with the edge's time in the edit.

    Which of their words stay in the edit cannot be told from the transcript.
    """
    result = []
    for piece in timeline.pieces:
        if piece.silent:
            continue
        for segment in segments_by_recording[piece.recording]:
            for edge, out in ((piece.src_start, piece.out_start), (piece.src_end, piece.out_end)):
                if segment.start < edge < segment.end:
                    result.append((out, set(words(segment.text))))
    return result


def _minor(expected: list[str], heard: list[str]) -> bool:
    """One word heard slightly differently: transcription noise, not a cut."""
    if len(expected) != 1 or len(heard) != 1:
        return False
    return SequenceMatcher(None, expected[0], heard[0]).ratio() >= 0.6


def compare(
    expected: list[Word],
    heard: list[Word],
    joins: list[float],
    straddling: list[tuple[float, set[str]]] = (),
) -> list[Problem]:
    """Differences between expected and heard words that fall near a join.

    Extra words that belong to a sentence a cut edge goes through, near that
    edge, are not reported: they may simply be kept.
    """
    matcher = SequenceMatcher(None, [w for w, _ in expected], [w for w, _ in heard], autojunk=False)
    problems: list[Problem] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        missing = [w for w, _ in expected[i1:i2]]
        extra = [w for w, _ in heard[j1:j2]]
        if tag == "replace" and _minor(missing, extra):
            continue
        times = [t for _, t in expected[i1:i2]] + [t for _, t in heard[j1:j2]]
        if not times:
            continue
        low, high = min(times) - JOIN_WINDOW_SEC, max(times) + JOIN_WINDOW_SEC
        near = [j for j in joins if low <= j <= high]
        if not near:
            continue
        if tag == "insert":
            uncertain = set().union(*(ws for t, ws in straddling if low <= t <= high))
            if set(extra) <= uncertain:
                continue
        before = " ".join(w for w, _ in heard[max(0, j1 - CONTEXT_WORDS):j1])
        after = " ".join(w for w, _ in heard[j2:j2 + CONTEXT_WORDS])
        kind = {"delete": "manca", "insert": "in più", "replace": "diverso"}[tag]
        problems.append(
            Problem(min(near, key=lambda j: abs(j - min(times))), kind,
                    " ".join(missing), " ".join(extra), f"…{before} ⟨⟩ {after}…")
        )
    return problems


def _timestamp(seconds: float) -> str:
    millis = int(round(max(seconds, 0.0) * 1000))
    hours, rest = divmod(millis, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _wrap(text: str) -> list[str]:
    """Split a cue's text into lines of at most SUBTITLE_LINE_CHARS characters."""
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > SUBTITLE_LINE_CHARS and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def subtitles(segments: list[Segment]) -> str:
    """An SRT file with at most two lines per cue; long segments are split."""
    cues = []
    for segment in segments:
        lines = _wrap(segment.text)
        groups = [lines[k:k + 2] for k in range(0, len(lines), 2)] or [[]]
        total = sum(len(" ".join(g)) for g in groups) or 1
        start = segment.start
        for group in groups:
            share = (segment.end - segment.start) * len(" ".join(group)) / total
            if group:
                cues.append((start, start + share, "\n".join(group)))
            start += share
    return "\n".join(
        f"{n}\n{_timestamp(a)} --> {_timestamp(b)}\n{text}\n"
        for n, (a, b, text) in enumerate(cues, start=1)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlla il montaggio alle giunzioni.")
    parser.add_argument("cartella", type=Path, help="cartella del video")
    folder = parser.parse_args().cartella.resolve()

    edit, edit_map = folder / EDIT, folder / EDIT_MAP
    if not edit.exists() or not edit_map.exists():
        raise UserError(f"in {folder} mancano {EDIT} o {EDIT_MAP}: lancia prima monta.py")
    data = json.loads(edit_map.read_text(encoding="utf-8"))
    timeline = timeline_from_json(data)
    recordings = [Path(p) for p in data["recordings"]]

    edit_transcript = transcript_path(edit)
    if not edit_transcript.exists() or edit_transcript.stat().st_mtime < edit.stat().st_mtime:
        print("Trascrivo il montaggio…", file=sys.stderr)
        transcribe(edit, folder)
    heard = heard_words(load_segments(edit_transcript))
    silences = load_silences(folder, recordings, [probe(p).duration for p in recordings])
    segments = [load_segments(transcript_path(p)) for p in recordings]
    expected = expected_words(timeline, segments, silences)
    problems = compare(expected, heard, timeline.joins, straddling_words(timeline, segments))

    actual = probe(edit).duration
    print(f"Montaggio: {fmt(actual)}, {len(timeline.joins)} giunzioni controllate.")
    if abs(actual - timeline.duration) > DURATION_TOLERANCE_SEC:
        print(f"Avviso: la durata attesa era {fmt(timeline.duration)}.")
    if problems:
        print(f"Possibili problemi ({len(problems)}), da ascoltare:")
        for p in problems:
            detail = {
                "manca": f"manca «{p.expected}»",
                "in più": f"si sente in più «{p.heard}»",
                "diverso": f"atteso «{p.expected}», sentito «{p.heard}»",
            }[p.kind]
            print(f"- {fmt(p.join)}: {detail}  {p.context}")
    else:
        print("Nessun problema trovato alle giunzioni.")

    (folder / SUBTITLES).write_text(subtitles(load_segments(edit_transcript)), encoding="utf-8")
    print(f"Sottotitoli: {folder / SUBTITLES}")


if __name__ == "__main__":
    main_wrapper(main)
