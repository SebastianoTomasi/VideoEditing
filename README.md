# VideoEditing

Edit OBS screencasts by talking to a coding agent, without opening a video
editor. The agent reads the transcript, proposes what to cut (retakes,
misspoken sentences, digressions) and which waits to speed up, and renders the
edit only after you approve. It also writes the video script (copione) before
you record, the YouTube description and tags, and proposes thumbnails.

It works with [Claude Code](https://claude.com/claude-code) and
[Codex](https://openai.com/codex), for Italian screencasts with one speaker.
It is the author's own setup, shared as it is: anyone with the same setup may
use it, without support.

## Requirements

- Windows 10 or 11, 64-bit. The agent must run on Windows, not inside WSL.
- Claude Code or Codex.
- Python 3.9+ on the `PATH` as `python`. The scripts use only the standard
  library.
- ffmpeg 7.0+ with ffprobe on the `PATH`, a full build
  (`winget install Gyan.FFmpeg`).
- OBS Studio 30.2+.
- The transcriber,
  [SebastianoTomasi/trascrittore](https://github.com/SebastianoTomasi/trascrittore):
  Docker Desktop, about 30 GB of disk, an NVIDIA GPU for speed. See its
  [Requirements](https://github.com/SebastianoTomasi/trascrittore#requirements).
- Microsoft Edge, for thumbnails.
- For thumbnails in Claude Code: the Codex desktop app, signed in with a plan
  that includes image generation. In Codex nothing else is needed.
- Optional: the `gh` CLI, which the agent uses to check links in descriptions.

## Setup

1. **Clone with symbolic links.** Turn on Windows Developer Mode, then:

   ```powershell
   git clone -c core.symlinks=true https://github.com/SebastianoTomasi/VideoEditing.git
   ```

   The skills live in `.agents/skills/`, which Codex reads; `.claude/skills/`
   links to them for Claude Code. Without symbolic links, or from a ZIP
   download, Claude Code finds no skills.
2. **OBS.** In Settings → Output → Recording: save to
   `%USERPROFILE%\Videos\OBS`, format Hybrid MP4, microphone on audio track 1,
   default date-time file names. In Settings → Hotkeys, bind "Add Chapter
   Marker": you press it right after a mistake.
3. **Transcriber.** There is no download yet: build it as its README says under
   [Image and distribution](https://github.com/SebastianoTomasi/trascrittore#image-and-distribution)
   (it needs a Hugging Face token), then run `Installa.bat` from the export
   folder. It also installs the `trascrittore` and `fix-transcript` skills this
   repository uses.
4. **Other paths.** If OBS saves elsewhere, or the transcriber is not in
   `%USERPROFILE%\Desktop\Trascrittore`, set these and restart the agent:

   ```powershell
   setx OBS_REGISTRAZIONI "D:\Recordings"
   setx TRASCRITTORE "C:\Trascrittore\trascrittore.ps1"
   ```

5. **Thumbnails.** Create `canale/foto.png`, a clear portrait of yourself
   facing the camera. Optionally add a heading font as
   `canale/font/titolo.ttf`, such as Anton or Archivo Black.

## Use

Open the agent in the repository and ask in Italian:

- "scrivimi il copione del video su …": the video script, before recording;
- "monta il video di stasera": edit tonight's recordings;
- "dammi un feedback sul testo": feedback on what you said;
- "fammi la thumbnail": three thumbnails for a final edit.

The skills `edit-video`, `video-script`, `thumbnail`, and `playbook` (the style
rules, yours to edit) are for making videos. `next-work`, `migrate-docs`, and
`propagate-change` maintain `docs/`.

## Your data

Everything about your videos stays on your PC: `videos/` and `canale/` are
kept out of git. The agent reads transcripts and sampled frames, so they reach
its model provider (Anthropic or OpenAI). For thumbnails only, OpenAI's image
generation receives a description, your photo, and frames that passed the
agent's check for private data on screen. You publish on YouTube yourself.

## Contributing

- Tests: `python -m unittest discover tests` (no ffmpeg needed).
- The decisions are in [`docs/product/product-foundation.md`](docs/product/product-foundation.md)
  and [`docs/features/`](docs/features/); vocabulary in
  [`GLOSSARY.md`](GLOSSARY.md). Agents start from [`AGENTS.md`](AGENTS.md).
- `docs/` follows the
  [delivery process advisor](https://github.com/SebastianoTomasi/delivery-process-advisor).
  Its sessions use skills from [mattpocock/skills](https://github.com/mattpocock/skills)
  (`grill-with-docs`, `grilling`, `domain-modeling`, `to-tickets`), installed
  separately.

## License

[MIT](LICENSE).
