"""Move a video's recordings from the OBS folder into the video's folder.

    python scripts/importa.py <video folder> <recording> [<recording> ...]

Each recording keeps its OBS name and moves with its transcripts
("<name> - trascrizione.json" and ".txt"). A recording already in a video
folder stays where it is. Every JSON file of the folder (cut lists, edit map,
check record, silence cache, transcripts) is pointed at the moved recordings,
and a folder without tagli.json gets one with the recordings in the order
given and no changes. Nothing is ever overwritten: every move is checked
before the first one.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import shutil
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import CUT_LIST, UserError, main_wrapper  # noqa: E402

VIDEOS = Path(__file__).resolve().parents[1] / "videos"
TRANSCRIPT_INFIX = " - trascrizione."


def path_key(path: str | Path) -> str:
    """A path as Windows compares it: absolute, backslashes, any case."""
    return os.path.normcase(os.path.abspath(path))


def transcripts_of(recording: Path) -> list[Path]:
    """The transcriber's files beside a recording, such as '<name> - trascrizione.json'."""
    prefix = (recording.stem + TRANSCRIPT_INFIX).casefold()
    return sorted(p for p in recording.parent.iterdir() if p.is_file() and p.name.casefold().startswith(prefix))


def plan_moves(folder: Path, recordings: list[Path], videos: Path) -> list[tuple[Path, Path]]:
    """(source, target) of every file to move; raises before anything moves."""
    moves: list[tuple[Path, Path]] = []
    targets: set[str] = set()
    for recording in recordings:
        if not recording.is_file():
            raise UserError(f"non trovo {recording}")
        if recording.resolve().is_relative_to(videos.resolve()):
            continue
        for source in [recording, *transcripts_of(recording)]:
            target = folder / source.name
            if target.exists() or path_key(target) in targets:
                raise UserError(f"{target} esiste già: non sposto niente, per non sovrascriverlo")
            targets.add(path_key(target))
            moves.append((source, target))
    return moves


def move_file(source: Path, target: Path) -> None:
    """Move a file without ever replacing one; across drives, copy it and then delete it."""
    if target.exists():
        raise FileExistsError(errno.EEXIST, "esiste già", str(target))
    try:
        os.rename(source, target)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.copy2(source, target)
        source.unlink()


def _strings(value) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)


def _replaced(value, pairs: dict[str, str]):
    if isinstance(value, str):
        return pairs.get(value, value)
    if isinstance(value, list):
        return [_replaced(item, pairs) for item in value]
    if isinstance(value, dict):
        return {pairs.get(key, key): _replaced(item, pairs) for key, item in value.items()}
    return value


def new_path(text: str, moved: dict[str, Path]) -> str | None:
    """The new path of a string that names a moved file, with the same slashes."""
    names = {target.name.casefold() for target in moved.values()}
    if not any(text.casefold().endswith(name) for name in names):
        return None
    try:
        target = moved.get(path_key(text))
    except (OSError, ValueError):
        return None
    if target is None:
        return None
    return str(target) if "\\" in text else target.as_posix()


def repoint(path: Path, moved: dict[str, Path]) -> bool:
    """Point one JSON file at the moved files, keeping its layout. True if it changed."""
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except ValueError:
        print(f"Salto {path.name}: non è un JSON valido", file=sys.stderr)
        return False
    pairs = {text: new for text in set(_strings(data)) if (new := new_path(text, moved))}
    if not pairs:
        return False
    expected = _replaced(data, pairs)
    text = raw
    for old, new in pairs.items():
        for ascii_only in (False, True):
            text = text.replace(json.dumps(old, ensure_ascii=ascii_only), json.dumps(new, ensure_ascii=ascii_only))
    if json.loads(text) != expected:
        text = json.dumps(expected, indent=1, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return True


def import_recordings(
    folder: Path, recordings: list[Path], videos: Path, report: Callable[[str], None] = print
) -> list[Path]:
    """Move the recordings into the folder and return their paths, in order."""
    folder.mkdir(parents=True, exist_ok=True)
    moves = plan_moves(folder, recordings, videos)
    moved: dict[str, Path] = {}
    failure = None
    for source, target in moves:
        try:
            move_file(source, target)
        except OSError as error:
            failure = f"non riesco a spostare {source}: {error}"
            break
        moved[path_key(source)] = target
        report(f"Spostato {source.name}")

    if moved:
        for path in sorted(folder.glob("*.json")):
            if repoint(path, moved):
                report(f"Aggiornato {path.name}")
    paths = [moved.get(path_key(recording), recording) for recording in recordings]
    cut_list = folder / CUT_LIST
    if not cut_list.exists():
        data = {"recordings": [path.as_posix() for path in paths], "changes": []}
        cut_list.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report(f"Scritto {CUT_LIST} con {len(paths)} registrazioni")
    if failure:
        raise UserError(f"{failure}. Le registrazioni che seguono sono rimaste dove erano.")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Sposta le registrazioni di un video nella sua cartella.")
    parser.add_argument("cartella", type=Path, help="cartella del video, creata se manca")
    parser.add_argument("registrazioni", type=Path, nargs="+", help="le registrazioni del video, in ordine")
    args = parser.parse_args()
    recordings = list(dict.fromkeys(path.resolve() for path in args.registrazioni))
    paths = import_recordings(args.cartella.resolve(), recordings, VIDEOS)
    print("Registrazioni:")
    for path in paths:
        print(f"- {path.as_posix()}")


if __name__ == "__main__":
    main_wrapper(main)
