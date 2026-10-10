"""Shared helpers for the edit-video scripts.

The video folder, the cut list (tagli.json), media probing, measured
silences, transcriber segments, and the edit timeline that monta.py renders
and controlla.py checks. Only the standard library is used.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

CUT_LIST = "tagli.json"
COMPACT_TRANSCRIPT = "trascrizione-compatta.md"
SILENCE_CACHE = "silenzi.json"
EDIT = "montaggio.mp4"
EDIT_MAP = "montaggio.json"
SUBTITLES = "montaggio.srt"

SILENCE_NOISE_DB = -35
SILENCE_MIN_SEC = 0.3

WAIT_TOTAL_SEC = 4.0
WAIT_EDGE_SEC = 1.0
SNAP_TOLERANCE_SEC = 0.75
MARGIN_MIN_SEC = 0.03
MARGIN_MAX_SEC = 0.2

TRANSCRIBER = Path(
    os.environ.get(
        "TRASCRITTORE", r"C:\Users\sebas\Desktop\Trascrittore\trascrittore.ps1"
    )
)

UPDATE_TRANSCRIBER = (
    "La trascrizione non ha i segmenti per frase: va installata la versione "
    "del trascrittore che li scrive (SebastianoTomasi/trascrittore#2)."
)


class UserError(Exception):
    """A problem the user or the agent can fix; the message says how."""


class NoSegments(UserError):
    def __init__(self, path: Path):
        super().__init__(f"{path}: {UPDATE_TRANSCRIBER}")


def main_wrapper(main) -> None:
    """Run a script's main(), turning UserError into exit status 2."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        main()
    except UserError as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        sys.exit(2)


# --- time -------------------------------------------------------------------


def fmt(seconds: float) -> str:
    """12.34 -> '00:12.3'; 3723.4 -> '1:02:03.4'."""
    tenths = int(round(max(seconds, 0.0) * 10))
    hours, rest = divmod(tenths, 36000)
    minutes, rest = divmod(rest, 600)
    secs = rest / 10
    if hours:
        return f"{hours}:{minutes:02d}:{secs:04.1f}"
    return f"{minutes:02d}:{secs:04.1f}"


def parse_time(text: str) -> float:
    """'3:20' or '1:02:03.5' or '200.5' -> seconds."""
    parts = text.strip().split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


# --- cut list -----------------------------------------------------------------


@dataclass(frozen=True)
class Change:
    recording: int
    start: float
    end: float
    action: str  # "cut" or "speed"
    reason: str = ""
    text: str = ""


@dataclass(frozen=True)
class CutList:
    recordings: list[Path]
    changes: list[Change]


def load_cut_list(folder: Path) -> CutList:
    path = folder / CUT_LIST
    if not path.exists():
        raise UserError(f"manca {path}: va creato con l'elenco delle registrazioni")
    data = json.loads(path.read_text(encoding="utf-8"))
    recordings = [Path(p) for p in data.get("recordings", [])]
    if not recordings:
        raise UserError(f"{path}: 'recordings' è vuoto")
    changes = []
    for i, raw in enumerate(data.get("changes", [])):
        try:
            change = Change(
                recording=int(raw.get("recording", 0)),
                start=float(raw["start"]),
                end=float(raw["end"]),
                action=str(raw["action"]),
                reason=str(raw.get("reason", "")),
                text=str(raw.get("text", "")),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise UserError(f"{path}: la modifica {i} non è valida ({error})")
        changes.append(change)
    return CutList(recordings, changes)


def validate_cut_list(cut_list: CutList, durations: list[float]) -> None:
    """Raise UserError on an unknown action, a bad range, or an overlap."""
    by_recording: dict[int, list[Change]] = {}
    for change in cut_list.changes:
        if change.action not in ("cut", "speed"):
            raise UserError(f"azione sconosciuta {change.action!r}: usa 'cut' o 'speed'")
        if not 0 <= change.recording < len(cut_list.recordings):
            raise UserError(f"registrazione {change.recording} inesistente")
        duration = durations[change.recording]
        if not (0 <= change.start < change.end <= duration + 0.05):
            raise UserError(
                f"intervallo {fmt(change.start)}–{fmt(change.end)} fuori dalla "
                f"registrazione {change.recording} (dura {fmt(duration)})"
            )
        by_recording.setdefault(change.recording, []).append(change)
    for recording, changes in by_recording.items():
        changes.sort(key=lambda c: c.start)
        for before, after in zip(changes, changes[1:]):
            if after.start < before.end:
                raise UserError(
                    f"registrazione {recording}: {fmt(before.start)}–{fmt(before.end)} "
                    f"e {fmt(after.start)}–{fmt(after.end)} si sovrappongono"
                )


# --- media ----------------------------------------------------------------------


@dataclass(frozen=True)
class MediaInfo:
    duration: float
    width: int
    height: int
    fps: str  # as ffprobe gives it, e.g. "20/1"


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kwargs
    )


def probe(path: Path) -> MediaInfo:
    if not path.exists():
        raise UserError(f"non trovo {path}")
    result = run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
            "-of", "json", str(path),
        ]
    )
    if result.returncode != 0:
        raise UserError(f"ffprobe non legge {path}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        raise UserError(f"{path} non ha una traccia video")
    if not any(s.get("codec_type") == "audio" for s in data.get("streams", [])):
        raise UserError(f"{path} non ha una traccia audio")
    return MediaInfo(
        duration=float(data["format"]["duration"]),
        width=int(video["width"]),
        height=int(video["height"]),
        fps=str(video["r_frame_rate"]),
    )


def chapter_markers(path: Path) -> list[float]:
    """Start times of the OBS chapter markers in a recording."""
    result = run(["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(path)])
    if result.returncode != 0:
        return []
    chapters = json.loads(result.stdout or "{}").get("chapters", [])
    return sorted(float(c["start_time"]) for c in chapters if "start_time" in c)


# --- silences -------------------------------------------------------------------

Interval = tuple[float, float]

_SILENCE_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*(-?[\d.]+)")


def parse_silencedetect(stderr: str, duration: float) -> list[Interval]:
    """Turn ffmpeg silencedetect log lines into (start, end) intervals."""
    silences: list[Interval] = []
    start: float | None = None
    for line in stderr.splitlines():
        if (match := _SILENCE_START.search(line)) is not None:
            start = max(0.0, float(match.group(1)))
        elif (match := _SILENCE_END.search(line)) is not None and start is not None:
            silences.append((start, min(float(match.group(1)), duration)))
            start = None
    if start is not None and start < duration:
        silences.append((start, duration))
    return silences


def detect_silences(path: Path, duration: float) -> list[Interval]:
    result = run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
            "-af", f"silencedetect=noise={SILENCE_NOISE_DB}dB:d={SILENCE_MIN_SEC}",
            "-f", "null", "-",
        ]
    )
    if result.returncode != 0:
        raise UserError(f"ffmpeg non misura i silenzi di {path}: {result.stderr[-500:]}")
    return parse_silencedetect(result.stderr, duration)


def load_silences(folder: Path, recordings: list[Path], durations: list[float]) -> list[list[Interval]]:
    """Measured silences per recording, cached in the video folder."""
    cache_path = folder / SILENCE_CACHE
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    settings = f"{SILENCE_NOISE_DB}dB:{SILENCE_MIN_SEC}"
    result = []
    changed = False
    for path, duration in zip(recordings, durations):
        stat = path.stat()
        key = str(path)
        entry = cache.get(key)
        stamp = [stat.st_size, int(stat.st_mtime), settings]
        if entry is None or entry.get("stamp") != stamp:
            print(f"Misuro i silenzi di {path.name}…", file=sys.stderr)
            entry = {"stamp": stamp, "silences": detect_silences(path, duration)}
            cache[key] = entry
            changed = True
        result.append([tuple(s) for s in entry["silences"]])
    if changed:
        cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return result


def silence_covering(silences: list[Interval], start: float, end: float) -> float:
    """Seconds of [start, end] that fall inside measured silences."""
    return sum(max(0.0, min(end, s1) - max(start, s0)) for s0, s1 in silences)


# --- transcripts ----------------------------------------------------------------


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


def transcript_path(media: Path) -> Path:
    """Where the transcriber writes the JSON transcript of a media file."""
    return media.with_name(f"{media.stem} - trascrizione.json")


def load_segments(path: Path) -> list[Segment]:
    if not path.exists():
        raise UserError(f"manca la trascrizione {path}: va lanciato il trascrittore")
    data = json.loads(path.read_text(encoding="utf-8"))
    turns = data.get("turns", [])
    if not any("segments" in turn for turn in turns):
        raise NoSegments(path)
    segments = [
        Segment(float(s["start_sec"]), float(s["end_sec"]), str(s["text"]).strip())
        for turn in turns
        for s in turn.get("segments", [])
    ]
    return sorted(segments, key=lambda s: s.start)


def words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def transcribe(media: Path, out_dir: Path, wait_limit_sec: float = 3600) -> dict:
    """Run the local transcriber on a file and return its JSON summary.

    When another transcription is running (exit status 3, "busy"), wait and
    try again instead of starting a second one.
    """
    if not TRANSCRIBER.exists():
        raise UserError(f"non trovo il trascrittore in {TRANSCRIBER}")
    args = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(TRANSCRIBER),
        "transcribe", str(media), "--speakers", "1", "--out-dir", str(out_dir),
    ]
    deadline = time.monotonic() + wait_limit_sec
    while True:
        result = run(args)
        lines = [line for line in result.stdout.splitlines() if line.strip().startswith("{")]
        summary = json.loads(lines[-1]) if lines else {}
        if summary.get("status") == "busy" or result.returncode == 3:
            if time.monotonic() > deadline:
                raise UserError("il trascrittore è occupato da troppo tempo")
            print("Il trascrittore è occupato: riprovo tra 30 s…", file=sys.stderr)
            time.sleep(30)
            continue
        if result.returncode != 0 or summary.get("status") != "ok":
            message = summary.get("message") or result.stderr.strip()[-500:]
            raise UserError(f"il trascrittore non ha trascritto {media}: {message}")
        return summary


# --- edit timeline --------------------------------------------------------------


@dataclass(frozen=True)
class Piece:
    """A stretch of one recording as it appears in the edit."""

    recording: int
    src_start: float
    src_end: float
    speed: float  # 1.0 is normal speed
    silent: bool  # the audio is replaced with silence
    out_start: float
    out_end: float


@dataclass
class Timeline:
    pieces: list[Piece]
    joins: list[float]  # edit times where the content jumps
    warnings: list[str]
    refusals: list[str]

    @property
    def duration(self) -> float:
        return self.pieces[-1].out_end if self.pieces else 0.0


def _margin(silence: Interval) -> float:
    return min(MARGIN_MAX_SEC, max(MARGIN_MIN_SEC, (silence[1] - silence[0]) / 2))


def _silence_near(t: float, silences: list[Interval], edge: int) -> Interval | None:
    """The measured silence containing t, or else the one whose start (edge 0)
    or end (edge 1) is closest to t within tolerance."""
    best: tuple[float, Interval] | None = None
    for silence in silences:
        s0, s1 = silence
        distance = 0.0 if s0 <= t <= s1 else abs(t - silence[edge])
        if distance <= SNAP_TOLERANCE_SEC and (best is None or distance < best[0]):
            best = (distance, silence)
    return None if best is None else best[1]


def snap_cut_start(t: float, silences: list[Interval]) -> float | None:
    """Where kept speech may end before a cut that the agent put at t.

    The edge goes inside the silence that follows the speech, keeping up to
    200 ms of it after the speech; None when no silence is near.
    """
    silence = _silence_near(t, silences, edge=0)
    if silence is None:
        return None
    s0, s1 = silence
    return min(s0 + _margin(silence), (s0 + s1) / 2)


def snap_cut_end(t: float, silences: list[Interval]) -> float | None:
    """Where kept speech may start again after a cut that the agent ended at t.

    The edge goes inside the silence that precedes the speech, keeping up to
    200 ms of it before the speech; None when no silence is near.
    """
    silence = _silence_near(t, silences, edge=1)
    if silence is None:
        return None
    s0, s1 = silence
    return max(s1 - _margin(silence), (s0 + s1) / 2)


def build_timeline(
    cut_list: CutList,
    durations: list[float],
    silences: list[list[Interval]],
    min_piece_sec: float = 0.05,
) -> Timeline:
    """Turn the cut list into the pieces of the edit, in order."""
    validate_cut_list(cut_list, durations)
    raw: list[tuple[int, float, float, float, bool]] = []
    warnings: list[str] = []
    refusals: list[str] = []
    for index, duration in enumerate(durations):
        quiet = silences[index]
        changes = sorted((c for c in cut_list.changes if c.recording == index), key=lambda c: c.start)
        cursor = 0.0  # where the next piece starts in the recording
        floor = 0.0  # end of the previous change: a cut never moves before it
        for position, change in enumerate(changes):
            where = f"registrazione {index + 1}, {fmt(change.start)}–{fmt(change.end)}"
            ceiling = changes[position + 1].start if position + 1 < len(changes) else duration
            if change.action == "cut":
                start = 0.0 if change.start <= 0.05 else snap_cut_start(change.start, quiet)
                end = duration if change.end >= duration - 0.05 else snap_cut_end(change.end, quiet)
                if start is None or end is None:
                    side = "l'inizio" if start is None else "la fine"
                    refusals.append(f"{where}: {side} del taglio non cade in un silenzio misurato")
                    continue
                start, end = max(start, floor), min(end, ceiling)
                if start > cursor:
                    raw.append((index, cursor, start, 1.0, False))
                cursor = max(cursor, start, end)
                floor = cursor
            else:
                length = change.end - change.start
                if length <= WAIT_TOTAL_SEC:
                    warnings.append(f"{where}: attesa troppo corta per accelerarla, resta com'è")
                    continue
                middle_start = max(change.start + WAIT_EDGE_SEC, cursor)
                middle_end = change.end - WAIT_EDGE_SEC
                speed = (middle_end - middle_start) / (WAIT_TOTAL_SEC - 2 * WAIT_EDGE_SEC)
                covered = silence_covering(quiet, middle_start, middle_end)
                if covered < 0.8 * (middle_end - middle_start):
                    warnings.append(
                        f"{where}: solo il {covered / (middle_end - middle_start):.0%} "
                        "dell'attesa è silenzio, controlla che non ci sia parlato"
                    )
                if middle_start > cursor:
                    raw.append((index, cursor, middle_start, 1.0, False))
                raw.append((index, middle_start, middle_end, speed, True))
                cursor = middle_end
                floor = change.end  # the wait's last second stays at normal speed
        if duration > cursor:
            raw.append((index, cursor, duration, 1.0, False))

    pieces: list[Piece] = []
    joins: list[float] = []
    out = 0.0
    jumped = False  # the content jumps between the last kept piece and this one
    previous: tuple[int, float] | None = None
    for recording, start, end, speed, silent in raw:
        if previous is not None and (previous[0] != recording or abs(previous[1] - start) > 1e-6):
            jumped = True
        previous = (recording, end)
        if end - start < min_piece_sec:
            continue
        if pieces and jumped:
            joins.append(out)
        jumped = False
        length = (end - start) / speed
        pieces.append(Piece(recording, start, end, speed, silent, out, out + length))
        out += length
    return Timeline(pieces, joins, warnings, refusals)


def timeline_to_json(timeline: Timeline, recordings: list[Path], encoder: str) -> dict:
    return {
        "recordings": [str(p) for p in recordings],
        "duration": round(timeline.duration, 3),
        "encoder": encoder,
        "pieces": [asdict(p) for p in timeline.pieces],
        "joins": [round(j, 3) for j in timeline.joins],
        "warnings": timeline.warnings,
    }


def timeline_from_json(data: dict) -> Timeline:
    pieces = [Piece(**p) for p in data["pieces"]]
    return Timeline(pieces, list(data["joins"]), list(data.get("warnings", [])), [])


def edit_to_source(timeline: Timeline, t: float) -> tuple[int, float] | None:
    """Map a time of the edit back to (recording, time in that recording)."""
    for piece in timeline.pieces:
        if piece.out_start <= t <= piece.out_end:
            return piece.recording, piece.src_start + (t - piece.out_start) * piece.speed
    return None
