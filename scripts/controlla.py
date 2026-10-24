"""Check an edit at its joins and write its subtitles.

    python scripts/controlla.py <video folder>              check the whole edit
    python scripts/controlla.py <video folder> --cambiate   only the joins changed since the last check

Has the transcriber transcribe montaggio.mp4, compares the words heard near
each join with the words the cut list keeps there, reports the potential
problems with their time in the edit, checks the duration, and writes
montaggio.srt. With --cambiate it transcribes only the stretches of the edit
around the joins that changed since the last check, recorded in
controllo.json, and leaves montaggio.srt as it is. It fixes nothing.
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
    CHECK_RECORD,
    EDIT,
    EDIT_MAP,
    EXCERPTS,
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
    run,
    timeline_from_json,
    transcribe,
    transcript_path,
    words,
)

JOIN_WINDOW_SEC = 3.0
CONTEXT_WORDS = 4
DURATION_TOLERANCE_SEC = 0.5
SUBTITLE_LINE_CHARS = 42
# --cambiate transcribes 15 s of the edit on each side of a changed join, so the
# join sits in the middle of one of the transcriber's 30 s windows; 30 s of
# silence between two stretches keeps them out of each other's window.
EXCERPT_SEC = 15.0
EXCERPT_GAP_SEC = 30.0
EXCERPT_EDGE_SEC = 5.0  # a stretch is compared only at joins this far from its cut edges
SAME_SEC = 0.01

Word = tuple[str, float]  # a word and its approximate time in the edit
Stretch = tuple[Path, float, float, float, bool]  # recording, from, to, speed, silent


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


def surroundings(timeline: Timeline, recordings: list[Path], t: float) -> list[Stretch]:
    """What the edit plays within EXCERPT_SEC of t, as stretches of its recordings."""
    low, high = t - EXCERPT_SEC, t + EXCERPT_SEC
    result = []
    for piece in timeline.pieces:
        start, end = max(low, piece.out_start), min(high, piece.out_end)
        if end - start < SAME_SEC:
            continue
        src_start = piece.src_start + (start - piece.out_start) * piece.speed
        src_end = piece.src_start + (end - piece.out_start) * piece.speed
        result.append((recordings[piece.recording], src_start, src_end, piece.speed, piece.silent))
    return result


def _same(one: list[Stretch], other: list[Stretch]) -> bool:
    return len(one) == len(other) and all(
        a[0] == b[0] and a[4] == b[4] and all(abs(x - y) < SAME_SEC for x, y in zip(a[1:4], b[1:4]))
        for a, b in zip(one, other)
    )


def changed_joins(
    previous: Timeline, previous_recordings: list[Path], current: Timeline, current_recordings: list[Path]
) -> list[float]:
    """Joins of the current edit whose surroundings no join of the previous edit had.

    Recordings are matched by path, so adding a recording keeps the joins of
    the others; a join that only moved in the edit is not changed.
    """
    before = [surroundings(previous, previous_recordings, j) for j in previous.joins]
    return [
        j for j in current.joins
        if not any(_same(surroundings(current, current_recordings, j), other) for other in before)
    ]


def excerpts(joins: list[float], duration: float) -> list[Interval]:
    """The stretch of the edit within EXCERPT_SEC of each join, even where they overlap."""
    return [(max(0.0, j - EXCERPT_SEC), min(duration, j + EXCERPT_SEC)) for j in joins]


def compare_excerpts(
    expected: list[Word],
    heard: list[list[Word]],
    joins: list[float],
    straddling: list[tuple[float, set[str]]],
    duration: float,
) -> list[Problem]:
    """The problems at the joins, each stretch of excerpts(joins) compared on its own.

    A stretch is compared at its own join and at the others well inside it; a
    problem two stretches find is reported once.
    """
    problems: list[Problem] = []
    seen = set()
    for own, (start, end), stretch_heard in zip(joins, excerpts(joins, duration), heard):
        inside = [j for j in joins if abs(j - own) <= EXCERPT_SEC - EXCERPT_EDGE_SEC]
        kept = [w for w in expected if start <= w[1] <= end]
        for problem in compare(kept, stretch_heard, inside, straddling):
            key = (problem.join, problem.kind, problem.expected, problem.heard)
            if key not in seen:
                seen.add(key)
                problems.append(problem)
    return problems


def write_excerpts(edit: Path, stretches: list[Interval], output: Path) -> None:
    """Write the stretches of the edit's audio into one file, EXCERPT_GAP_SEC of silence apart."""
    mono = "aformat=sample_fmts=s16:sample_rates=16000:channel_layouts=mono"
    chains, labels = [], []
    for k, (start, end) in enumerate(stretches):
        if k:
            chains.append(f"anullsrc=r=16000:cl=mono,atrim=duration={EXCERPT_GAP_SEC},{mono}[g{k}]")
            labels.append(f"[g{k}]")
        chains.append(
            f"[0:a:0]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS,aresample=16000,{mono}[e{k}]"
        )
        labels.append(f"[e{k}]")
    chains.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[out]")
    result = run(["ffmpeg", "-hide_banner", "-y", "-loglevel", "error", "-i", str(edit),
                  "-filter_complex", ";".join(chains), "-map", "[out]", "-c:a", "pcm_s16le", str(output)])
    if result.returncode != 0:
        raise UserError(f"non riesco a estrarre i tratti del montaggio: {result.stderr[-500:]}")


def heard_in_excerpts(segments: list[Segment], stretches: list[Interval]) -> list[list[Word]]:
    """The words heard in the file of write_excerpts, by stretch, with their time in the edit.

    A word heard in the silence between two stretches goes to the nearer one.
    """
    offsets, cursor = [], 0.0
    for start, end in stretches:
        offsets.append(cursor)
        cursor += end - start + EXCERPT_GAP_SEC
    result: list[list[Word]] = [[] for _ in stretches]
    for word, t in heard_words(segments):
        k = max((i for i, offset in enumerate(offsets) if offset - EXCERPT_GAP_SEC / 2 <= t), default=0)
        start, end = stretches[k]
        result[k].append((word, min(max(start + t - offsets[k], start), end)))
    return result


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
    parser.add_argument("--cambiate", action="store_true",
                        help="controlla solo le giunzioni cambiate dall'ultimo controllo")
    args = parser.parse_args()
    folder = args.cartella.resolve()

    edit, edit_map, record = folder / EDIT, folder / EDIT_MAP, folder / CHECK_RECORD
    if not edit.exists() or not edit_map.exists():
        raise UserError(f"in {folder} mancano {EDIT} o {EDIT_MAP}: lancia prima monta.py")
    data = json.loads(edit_map.read_text(encoding="utf-8"))
    timeline = timeline_from_json(data)
    recordings = [Path(p) for p in data["recordings"]]
    silences = load_silences(folder, recordings, [probe(p).duration for p in recordings])
    segments = [load_segments(transcript_path(p)) for p in recordings]
    expected = expected_words(timeline, segments, silences)
    straddling = straddling_words(timeline, segments)

    targeted = args.cambiate and record.exists()
    if args.cambiate and not targeted:
        print("Nessun controllo precedente: controllo tutto il montaggio.", file=sys.stderr)
    if targeted:
        previous = json.loads(record.read_text(encoding="utf-8"))
        joins = changed_joins(timeline_from_json(previous), [Path(p) for p in previous["recordings"]],
                              timeline, recordings)
        problems = []
        if joins:
            stretches = excerpts(joins, timeline.duration)
            audio = folder / EXCERPTS
            write_excerpts(edit, stretches, audio)
            print(f"Trascrivo {fmt(sum(end - start for start, end in stretches))} del montaggio…",
                  file=sys.stderr)
            transcribe(audio, folder)
            heard = heard_in_excerpts(load_segments(transcript_path(audio)), stretches)
            problems = compare_excerpts(expected, heard, joins, straddling, timeline.duration)
        checked = f"{len(joins)} giunzioni cambiate dall'ultimo controllo, su {len(timeline.joins)}"
    else:
        edit_transcript = transcript_path(edit)
        if not edit_transcript.exists() or edit_transcript.stat().st_mtime < edit.stat().st_mtime:
            print("Trascrivo il montaggio…", file=sys.stderr)
            transcribe(edit, folder)
        problems = compare(expected, heard_words(load_segments(edit_transcript)), timeline.joins, straddling)
        checked = f"{len(timeline.joins)} giunzioni controllate"

    actual = probe(edit).duration
    print(f"Montaggio: {fmt(actual)}, {checked}.")
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

    if targeted:
        print(f"Sottotitoli non riscritti: {SUBTITLES} lo riscrive il controllo completo.")
    else:
        (folder / SUBTITLES).write_text(subtitles(load_segments(edit_transcript)), encoding="utf-8")
        print(f"Sottotitoli: {folder / SUBTITLES}")
    record.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main_wrapper(main)
