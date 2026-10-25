"""Thumbnail helpers: generate pictures with Codex, render layouts, preview.

    python scripts/miniature.py genera <video folder> --prompt <file> --nome B [--immagine <file>]...
    python scripts/miniature.py render <layout.html>...
    python scripts/miniature.py anteprima <a.jpg> <b.jpg> <c.jpg> --uscita <anteprima.png>

genera runs Codex's image generation with the prompt and the attached images,
then copies the new pictures into <video folder>/immagini/. render turns each
HTML layout into a 3840×2160 JPEG with Edge. anteprima shows the thumbnails at
the small sizes YouTube uses, also in grayscale, under a mock duration badge.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import UserError, main_wrapper, run  # noqa: E402

EDGE_PATHS = [
    Path(os.environ[var]) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
    for var in ("ProgramFiles(x86)", "ProgramFiles")
    if os.environ.get(var)
]
CODEX_BIN = Path(os.environ.get("LOCALAPPDATA", "")) / "OpenAI" / "Codex" / "bin"
CODEX_IMAGES = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "generated_images"
PREVIEW_SIZES = [(168, 94), (320, 180), (360, 202)]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def find_codex() -> Path:
    """The codex.exe that the Codex app installs, newest first."""
    candidates = sorted(CODEX_BIN.glob("*/codex.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise UserError(
            f"non trovo codex.exe in {CODEX_BIN}: genera le immagini da Codex con $imagegen"
        )
    return candidates[0]


def new_images(since: float) -> list[Path]:
    if not CODEX_IMAGES.exists():
        return []
    return sorted(
        (p for p in CODEX_IMAGES.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES and p.stat().st_mtime >= since),
        key=lambda p: p.stat().st_mtime,
    )


def generate(folder: Path, prompt_file: Path, name: str, images: list[Path]) -> list[Path]:
    codex = find_codex()
    prompt = prompt_file.read_text(encoding="utf-8")
    args = [str(codex), "exec", "--skip-git-repo-check", "-s", "read-only", "-C", str(folder)]
    for image in images:
        if not image.exists():
            raise UserError(f"non trovo l'immagine {image}")
        args += ["-i", str(image)]
    since = time.time() - 1
    try:
        result = run(args + ["-"], input=prompt, timeout=900)
    except subprocess.TimeoutExpired:
        raise UserError("Codex non ha finito entro 15 minuti")
    if result.returncode != 0:
        raise UserError(f"Codex non ha generato l'immagine: {result.stderr.strip()[-600:]}")
    found = new_images(since)
    if not found:
        raise UserError("Codex ha finito senza salvare immagini: genera da Codex con $imagegen")
    target = folder / "immagini"
    target.mkdir(exist_ok=True)
    copies = []
    for number, source in enumerate(found, start=1):
        copy = target / f"{name}-{number}{source.suffix.lower()}"
        shutil.copy2(source, copy)
        copies.append(copy)
    return copies


def find_edge() -> Path:
    """Edge where Windows installs it, or else on the PATH."""
    for path in EDGE_PATHS:
        if path.exists():
            return path
    found = shutil.which("msedge")
    if not found:
        raise UserError("non trovo Edge: installa Microsoft Edge")
    return Path(found)


def render(layout: Path) -> Path:
    """Render an HTML layout at 1280×720 CSS pixels, scale 3, into a JPEG."""
    edge = find_edge()
    png = layout.with_suffix(".png")
    jpg = layout.with_suffix(".jpg")
    with tempfile.TemporaryDirectory() as profile:
        try:
            result = run([
                str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
                "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
                "--window-size=1280,720", "--force-device-scale-factor=3",
                "--virtual-time-budget=5000", f"--screenshot={png}", layout.resolve().as_uri(),
            ], timeout=120)
        except subprocess.TimeoutExpired:
            raise UserError(f"Edge non ha finito di renderizzare {layout}")
    if not png.exists():
        raise UserError(f"Edge non ha renderizzato {layout}: {result.stderr.strip()[-400:]}")
    converted = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(png),
                     "-q:v", "2", str(jpg)])
    png.unlink(missing_ok=True)
    if converted.returncode != 0:
        raise UserError(f"ffmpeg non ha convertito {png}: {converted.stderr[-300:]}")
    return jpg


def preview_graph(count: int) -> str:
    """Each thumbnail on one row: the three small sizes and a grayscale copy."""
    chains = []
    height = max(h for _, h in PREVIEW_SIZES)
    for i in range(count):
        outputs = "".join(f"[s{i}_{k}]" for k in range(len(PREVIEW_SIZES) + 1))
        chains.append(f"[{i}:v]split={len(PREVIEW_SIZES) + 1}{outputs}")
        tiles = []
        for k, (w, h) in enumerate(PREVIEW_SIZES + [(320, 180)]):
            gray = ",format=gray,format=rgb24" if k == len(PREVIEW_SIZES) else ""
            badge = f"drawbox=x={w - w // 6 - 4}:y={h - h // 7 - 4}:w={w // 6}:h={h // 7}:color=black@0.8:t=fill"
            chains.append(
                f"[s{i}_{k}]scale={w}:{h}:flags=area{gray},{badge},"
                f"pad={w + 12}:{height + 12}:6:6:color=white[t{i}_{k}]"
            )
            tiles.append(f"[t{i}_{k}]")
        chains.append(f"{''.join(tiles)}hstack=inputs={len(tiles)}[row{i}]")
    rows = "".join(f"[row{i}]" for i in range(count))
    chains.append(f"{rows}vstack=inputs={count}[out]" if count > 1 else "[row0]null[out]")
    return ";\n".join(chains)


def preview(thumbnails: list[Path], output: Path) -> None:
    graph = output.with_suffix(".grafo.txt")
    graph.write_text(preview_graph(len(thumbnails)), encoding="utf-8")
    inputs = [arg for path in thumbnails for arg in ("-i", str(path))]
    result = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
                  "-/filter_complex", str(graph), "-map", "[out]", "-frames:v", "1", str(output)])
    graph.unlink(missing_ok=True)
    if result.returncode != 0:
        raise UserError(f"ffmpeg non ha creato l'anteprima: {result.stderr[-600:]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Strumenti per le thumbnail.")
    sub = parser.add_subparsers(dest="comando", required=True)
    gen = sub.add_parser("genera", help="genera un'immagine con Codex")
    gen.add_argument("cartella", type=Path)
    gen.add_argument("--prompt", type=Path, required=True)
    gen.add_argument("--nome", required=True, help="per esempio B: diventa immagini/B-1.png")
    gen.add_argument("--immagine", type=Path, action="append", default=[])
    ren = sub.add_parser("render", help="trasforma i layout HTML in JPEG")
    ren.add_argument("layout", type=Path, nargs="+")
    pre = sub.add_parser("anteprima", help="foglio di anteprima a misure piccole")
    pre.add_argument("miniature", type=Path, nargs="+")
    pre.add_argument("--uscita", type=Path, required=True)
    args = parser.parse_args()

    if args.comando == "genera":
        for path in generate(args.cartella.resolve(), args.prompt, args.nome, args.immagine):
            print(f"Immagine: {path}")
    elif args.comando == "render":
        for layout in args.layout:
            print(f"Thumbnail: {render(layout)}")
    else:
        preview(args.miniature, args.uscita)
        print(f"Anteprima: {args.uscita}")


if __name__ == "__main__":
    main_wrapper(main)
