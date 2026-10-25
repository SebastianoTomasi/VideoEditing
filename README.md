# VideoEditing

Edit OBS screencasts by talking to a coding agent, without opening a video
editor. The agent reads the transcript of your recordings, proposes what to
cut (retakes, misspoken sentences, digressions) and which waits to speed up,
and renders the edit only after you approve. It can also give feedback on what
you said, write the script of a video before you record it, write the YouTube
description and tags, and propose thumbnails.

It works with [Claude Code](https://claude.com/claude-code) and
[Codex](https://openai.com/codex), for Italian screencasts with one speaker.
It is the author's own setup, shared as it is: anyone with the same setup may
use it, without support.

## What you need

- Windows 10 or 11.
- [OBS](https://obsproject.com/), saving recordings to
  `%USERPROFILE%\Videos\OBS`, or to the folder you put in the
  `OBS_REGISTRAZIONI` environment variable.
- Python 3 (the scripts use only the standard library).
- [ffmpeg](https://ffmpeg.org/) and ffprobe on the `PATH`.
- The transcriber,
  [SebastianoTomasi/trascrittore](https://github.com/SebastianoTomasi/trascrittore),
  which runs in Docker Desktop with an NVIDIA GPU. Its installer also installs
  the `trascrittore` and `fix-transcript` skills that this repository relies
  on. If its launcher is not at
  `%USERPROFILE%\Desktop\Trascrittore\trascrittore.ps1`, set the `TRASCRITTORE`
  environment variable to the path of `trascrittore.ps1`.
- Microsoft Edge, which turns thumbnail layouts into images.
- Claude Code or Codex. Thumbnail pictures are generated with Codex's image
  generation: in Codex the agent uses it directly; in Claude Code it needs the
  [Codex app](https://openai.com/codex) installed.

## Setup

1. Clone the repository. The skills live in `.agents/skills/`, which Codex
   reads; `.claude/skills/` holds symbolic links to them for Claude Code. On
   Windows, turn on Developer Mode and clone with
   `git clone -c core.symlinks=true <url>`, otherwise the links arrive as
   plain text files and Claude Code finds no skills.
2. For thumbnails, put a portrait of yourself in `canale/foto.png`, and
   optionally a heading font in `canale/font/titolo.ttf`.
3. Open Claude Code or Codex in the repository and ask in Italian, for example:
   - "scrivimi il copione del video su …" — the script of a video to record;
   - "monta il video di stasera" — edit tonight's recordings;
   - "dammi un feedback sul testo" — feedback on what you said;
   - "fammi la thumbnail" — three thumbnails for a final edit.

## Your data

Everything about your videos stays on your PC: `videos/` and `canale/` are
kept out of git. The agent reads transcripts and sampled frames, so they pass
through its model provider (Anthropic or OpenAI) like any file it opens. Only
for thumbnails, OpenAI's image generation receives a text description, your
reference photo, and frames of your recordings that passed the agent's check
for private data on screen. You publish on YouTube yourself.

## For contributors

- The tests use only the standard library: `python -m unittest discover tests`.
- `docs/` holds the product and design decisions, organized by the
  [delivery process advisor](https://github.com/SebastianoTomasi/delivery-process-advisor);
  start from [`AGENTS.md`](AGENTS.md). The vocabulary is in
  [`GLOSSARY.md`](GLOSSARY.md).

## License

[MIT](LICENSE).
