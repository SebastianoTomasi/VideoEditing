"""Render a video's edit from its cut list.

    python scripts/monta.py <video folder>            render montaggio.mp4
    python scripts/monta.py <video folder> --stima    only print the length of the edit

The edit replaces montaggio.mp4 only when the render succeeds. Recordings are
only read.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comune import (  # noqa: E402
    EDIT,
    EDIT_MAP,
    MediaInfo,
    Timeline,
    UserError,
    build_timeline,
    fmt,
    load_cut_list,
    load_silences,
    main_wrapper,
    probe,
    run,
    timeline_to_json,
)

FADE_SEC = 0.03
LOUDNESS = "I=-14:TP=-1.5:LRA=11"
NVENC = ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "19", "-b:v", "0"]
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]


def filter_graph(
    timeline: Timeline,
    infos: list[MediaInfo],
    audio_only: bool = False,
    loudnorm: str | None = None,
) -> str:
    """The ffmpeg filter graph of the edit: one chain per piece, then concat.

    Outputs are [vout] (unless audio_only) and [aout].
    """
    target = infos[0]
    chains = []
    for index, piece in enumerate(timeline.pieces):
        length = piece.out_end - piece.out_start
        if not audio_only:
            info = infos[piece.recording]
            pts = "PTS-STARTPTS" if piece.speed == 1 else f"(PTS-STARTPTS)/{piece.speed:.6f}"
            video = f"[{piece.recording}:v:0]trim=start={piece.src_start:.3f}:end={piece.src_end:.3f},setpts={pts}"
            if (info.width, info.height) != (target.width, target.height):
                video += (
                    f",scale={target.width}:{target.height}:force_original_aspect_ratio=decrease"
                    f",pad={target.width}:{target.height}:(ow-iw)/2:(oh-ih)/2"
                )
            video += f",setsar=1,fps={target.fps},format=yuv420p[v{index}]"
            chains.append(video)
        if piece.silent:
            audio = (
                f"anullsrc=r=48000:cl=stereo,atrim=duration={length:.3f},asetpts=PTS-STARTPTS,"
                f"aformat=sample_fmts=fltp:channel_layouts=stereo[a{index}]"
            )
        else:
            fade = min(FADE_SEC, length / 4)
            audio = (
                f"[{piece.recording}:a:0]atrim=start={piece.src_start:.3f}:end={piece.src_end:.3f},"
                "asetpts=PTS-STARTPTS,aresample=48000,"
                "aformat=sample_fmts=fltp:channel_layouts=stereo,"
                f"afade=t=in:d={fade:.3f},afade=t=out:st={max(length - fade, 0):.3f}:d={fade:.3f}[a{index}]"
            )
        chains.append(audio)
    count = len(timeline.pieces)
    if audio_only:
        inputs = "".join(f"[a{i}]" for i in range(count))
        chains.append(f"{inputs}concat=n={count}:v=0:a=1[acat]")
    else:
        inputs = "".join(f"[v{i}][a{i}]" for i in range(count))
        chains.append(f"{inputs}concat=n={count}:v=1:a=1[vout][acat]")
    chains.append(f"[acat]{loudnorm or 'anull'},aresample=48000[aout]")
    return ";\n".join(chains)


def parse_loudnorm(stderr: str) -> dict:
    """The JSON block that loudnorm prints in its measuring pass."""
    blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr)
    if not blocks:
        raise UserError("ffmpeg non ha stampato le misure del volume")
    return json.loads(blocks[-1])


def measure_loudness(inputs: list[str], graph_path: Path, timeline, infos) -> str:
    graph_path.write_text(
        filter_graph(timeline, infos, audio_only=True, loudnorm=f"loudnorm={LOUDNESS}:print_format=json"),
        encoding="utf-8",
    )
    result = run(["ffmpeg", "-hide_banner", "-nostats", *inputs, "-/filter_complex", str(graph_path),
                  "-map", "[aout]", "-f", "null", "-"])
    if result.returncode != 0:
        raise UserError(f"la misura del volume è fallita: {result.stderr[-800:]}")
    m = parse_loudnorm(result.stderr)
    return (
        f"loudnorm={LOUDNESS}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true:print_format=summary"
    )


def render(folder: Path, inputs: list[str], graph_path: Path, output: Path) -> str:
    """Encode with NVENC, or with libx264 when NVENC is not available."""
    common = ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
              "-movflags", "+faststart"]
    for name, codec in (("h264_nvenc", NVENC), ("libx264", X264)):
        result = run(["ffmpeg", "-hide_banner", "-y", "-loglevel", "error", *inputs,
                      "-/filter_complex", str(graph_path), "-map", "[vout]", "-map", "[aout]",
                      *codec, *common, str(output)])
        if result.returncode == 0:
            return name
        if name == "h264_nvenc" and re.search(r"nvenc|cuda|nvcuda|No capable devices", result.stderr, re.I):
            print(f"NVENC non disponibile, uso libx264: {result.stderr.strip()[-300:]}", file=sys.stderr)
            continue
        raise UserError(f"il render è fallito: {result.stderr[-800:]}")
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monta il video dalla sua lista dei tagli.")
    parser.add_argument("cartella", type=Path, help="cartella del video, con tagli.json")
    parser.add_argument("--stima", action="store_true", help="stampa solo la durata, senza render")
    args = parser.parse_args()
    folder = args.cartella.resolve()

    cut_list = load_cut_list(folder)
    infos = [probe(path) for path in cut_list.recordings]
    durations = [info.duration for info in infos]
    silences = load_silences(folder, cut_list.recordings, durations)
    timeline = build_timeline(cut_list, durations, silences)

    for path, info in zip(cut_list.recordings[1:], infos[1:]):
        if (info.width, info.height, info.fps) != (infos[0].width, infos[0].height, infos[0].fps):
            timeline.warnings.append(
                f"{path.name} è {info.width}×{info.height} a {info.fps} fps: "
                f"la adatto a {infos[0].width}×{infos[0].height} a {infos[0].fps}"
            )
    for warning in timeline.warnings:
        print(f"Avviso: {warning}")
    if timeline.refusals:
        raise UserError(
            "questi tagli non cadono in un silenzio misurato, sposta i loro bordi:\n- "
            + "\n- ".join(timeline.refusals)
        )

    total = sum(durations)
    print(f"Montaggio: {fmt(timeline.duration)} (registrazioni: {fmt(total)}), "
          f"{len(timeline.pieces)} pezzi, {len(timeline.joins)} giunzioni.")
    if args.stima:
        return

    inputs = [arg for path in cut_list.recordings for arg in ("-i", str(path))]
    graph_path = folder / "montaggio.grafo.txt"
    started = time.monotonic()
    print("Misuro il volume…", file=sys.stderr)
    loudnorm = measure_loudness(inputs, graph_path, timeline, infos)
    graph_path.write_text(filter_graph(timeline, infos, loudnorm=loudnorm), encoding="utf-8")
    temporary = folder / "montaggio.tmp.mp4"
    print("Render in corso…", file=sys.stderr)
    encoder = render(folder, inputs, graph_path, temporary)
    try:
        os.replace(temporary, folder / EDIT)
    except PermissionError:
        raise UserError(
            f"non riesco a sostituire {EDIT}: forse è aperto in un lettore. "
            f"Il nuovo montaggio è in {temporary.name}"
        )
    (folder / EDIT_MAP).write_text(
        json.dumps(timeline_to_json(timeline, cut_list.recordings, encoder), indent=1, ensure_ascii=False),
        encoding="utf-8",
    )
    graph_path.unlink(missing_ok=True)
    print(f"Fatto: {folder / EDIT} ({encoder}, {time.monotonic() - started:.0f} s).")


if __name__ == "__main__":
    main_wrapper(main)
