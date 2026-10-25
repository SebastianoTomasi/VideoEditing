"""List the recordings left in the video folders, or send some to the Recycle Bin.

    python scripts/originali.py                          list them
    python scripts/originali.py --cestina <folder> [...]  send those folders' recordings to the Recycle Bin

A folder's recordings are the ones its tagli.json names that sit in the
folder. Its edit counts as final when descrizione.txt exists, since the agent
writes it when the user says the edit is final. Everything else in the folder
stays, and nothing is deleted for good: the user empties the Recycle Bin.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import CUT_LIST, UserError, main_wrapper  # noqa: E402

VIDEOS = Path(__file__).resolve().parents[1] / "videos"
DESCRIPTION = "descrizione.txt"


@dataclass(frozen=True)
class Holding:
    folder: Path
    recordings: list[Path]
    size: int
    final: bool
    shared_with: list[str]  # the other video folders whose cut list names these recordings


def named_recordings(folder: Path) -> list[Path]:
    """The recordings a folder's cut list names, wherever they are."""
    path = folder / CUT_LIST
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise UserError(f"{path} non è un JSON valido ({error})")
    return [Path(p).resolve() for p in data.get("recordings", [])]


def holdings(videos: Path) -> list[Holding]:
    """The video folders that still hold recordings, in name order."""
    if not videos.is_dir():
        return []
    folders = sorted(p.resolve() for p in videos.iterdir() if p.is_dir())
    named = {folder: named_recordings(folder) for folder in folders}
    result = []
    for folder in folders:
        recordings = [p for p in named[folder] if p.parent == folder and p.is_file()]
        if not recordings:
            continue
        shared_with = [
            other.name for other in folders if other != folder and any(r in named[other] for r in recordings)
        ]
        result.append(
            Holding(
                folder,
                recordings,
                sum(r.stat().st_size for r in recordings),
                (folder / DESCRIPTION).exists(),
                shared_with,
            )
        )
    return result


def size_text(size: int) -> str:
    return f"{size / 1e9:.1f} GB" if size >= 1e9 else f"{size / 1e6:.0f} MB"


def to_recycle_bin(path: Path) -> None:
    """Send one file to the Recycle Bin. Windows asks before deleting it for good."""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    fo_delete = 0x0003
    fof_silent, fof_noconfirmation, fof_allowundo, fof_wantnukewarning = 0x0004, 0x0010, 0x0040, 0x4000
    operation = SHFILEOPSTRUCTW(
        None,
        fo_delete,
        str(path.resolve()) + "\0",  # the list of files ends with two nulls
        None,
        fof_allowundo | fof_noconfirmation | fof_wantnukewarning | fof_silent,
        False,
        None,
        None,
    )
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if result != 0 or operation.fAnyOperationsAborted or path.exists():
        raise UserError(f"non sono riuscito a mettere nel Cestino {path} (codice {result})")


def send_to_recycle_bin(
    chosen: list[Path],
    videos: Path,
    recycle: Callable[[Path], None] = to_recycle_bin,
    report: Callable[[str], None] = print,
) -> int:
    """Send the recordings of the chosen folders to the Recycle Bin; return the bytes they take."""
    by_folder = {holding.folder: holding for holding in holdings(videos)}
    selected = []
    for folder in chosen:
        holding = by_folder.get(folder.resolve())
        if holding is None:
            raise UserError(f"{folder} non ha registrazioni")
        selected.append(holding)
    freed = 0
    for holding in selected:
        for recording in holding.recordings:
            size = recording.stat().st_size
            recycle(recording)
            freed += size
            report(f"Nel Cestino: {holding.folder.name}/{recording.name} ({size_text(size)})")
    return freed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Elenca le registrazioni rimaste nelle cartelle dei video, o le mette nel Cestino."
    )
    parser.add_argument(
        "--cestina", type=Path, nargs="+", metavar="CARTELLA",
        help="cartelle dei video di cui mettere le registrazioni nel Cestino",
    )
    args = parser.parse_args()

    if args.cestina:
        freed = send_to_recycle_bin(args.cestina, VIDEOS)
        print(f"Svuotando il Cestino liberi {size_text(freed)}.")
        return

    found = holdings(VIDEOS)
    if not found:
        print("Nessuna cartella dei video ha ancora registrazioni.")
        return
    for holding in found:
        state = "montaggio definitivo" if holding.final else "montaggio non definitivo"
        count = "1 registrazione" if len(holding.recordings) == 1 else f"{len(holding.recordings)} registrazioni"
        print(f"{holding.folder.name}: {count}, {size_text(holding.size)}, {state}")
        for recording in holding.recordings:
            print(f"  - {recording.name}")
        if holding.shared_with:
            print(f"  usate anche da: {', '.join(holding.shared_with)}")
    print(f"Totale: {size_text(sum(h.size for h in found))}")


if __name__ == "__main__":
    main_wrapper(main)
