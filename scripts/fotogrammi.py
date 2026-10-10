"""Sample frames of a video into contact sheets the agent can look at.

    python scripts/fotogrammi.py <video> <output folder> [--ogni 20]
        [--da 0] [--a END] [--ritaglio X,Y,W,H] [--colonne 4] [--righe 3]

Each sheet is a grid of frames, one every --ogni seconds, each labelled with
its time in the video. --ritaglio crops a region first, for example the
webcam. Used for the frame check before a cut proposal and for picking
thumbnail candidates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import UserError, main_wrapper, probe, run  # noqa: E402

FONT = "C\\:/Windows/Fonts/arial.ttf"  # escaped for a filter graph


def sheet_filter(every: float, offset: float, crop: str | None, columns: int, rows: int, width: int) -> str:
    """The filter graph that turns [0:v] into labelled contact sheets [out]."""
    steps = [f"fps=1/{every}"]
    if crop:
        x, y, w, h = crop.split(",")
        steps.append(f"crop={w}:{h}:{x}:{y}")
    steps.append(f"scale={width}:-2")
    steps.append(
        f"drawtext=fontfile='{FONT}':text='%{{pts\\:gmtime\\:{offset:.0f}\\:%H\\\\\\:%M\\\\\\:%S}}'"
        ":x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=4"
    )
    steps.append(f"tile={columns}x{rows}:padding=4:color=gray")
    return f"[0:v]{','.join(steps)}[out]"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fogli di fotogrammi con il tempo stampato sopra.")
    parser.add_argument("video", type=Path)
    parser.add_argument("cartella", type=Path, help="dove scrivere foglio_NN.png")
    parser.add_argument("--ogni", type=float, default=20.0, help="secondi tra un fotogramma e l'altro")
    parser.add_argument("--da", type=float, default=0.0)
    parser.add_argument("--a", type=float, default=None)
    parser.add_argument("--ritaglio", help="X,Y,W,H in pixel del video")
    parser.add_argument("--colonne", type=int, default=4)
    parser.add_argument("--righe", type=int, default=3)
    parser.add_argument("--larghezza", type=int, default=480, help="larghezza di ogni fotogramma")
    args = parser.parse_args()

    info = probe(args.video)
    end = info.duration if args.a is None else min(args.a, info.duration)
    if end <= args.da:
        raise UserError("l'intervallo richiesto è vuoto")
    args.cartella.mkdir(parents=True, exist_ok=True)
    graph = args.cartella / "fogli.grafo.txt"
    graph.write_text(
        sheet_filter(args.ogni, args.da, args.ritaglio, args.colonne, args.righe, args.larghezza),
        encoding="utf-8",
    )
    result = run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{args.da:.3f}", "-t", f"{end - args.da:.3f}", "-i", str(args.video),
        "-/filter_complex", str(graph), "-map", "[out]", "-fps_mode", "vfr",
        str(args.cartella / "foglio_%02d.png"),
    ])
    graph.unlink(missing_ok=True)
    if result.returncode != 0:
        raise UserError(f"ffmpeg non ha estratto i fotogrammi: {result.stderr[-600:]}")
    sheets = sorted(args.cartella.glob("foglio_*.png"))
    per_sheet = args.colonne * args.righe
    print(f"{len(sheets)} fogli in {args.cartella}, {per_sheet} fotogrammi ciascuno, uno ogni {args.ogni:g} s.")


if __name__ == "__main__":
    main_wrapper(main)
