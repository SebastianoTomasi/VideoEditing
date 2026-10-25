# Other people may use the repository with the same setup

The repository becomes public, and anyone with the author's setup (Windows,
OBS, ffmpeg, Docker with an NVIDIA GPU, the transcriber, Edge, and Claude Code
or Codex) may use it as it is, for Italian screencasts with one speaker,
without support. The author's personal paths become defaults taken from the
user's profile, which environment variables override, so the author's setup
keeps working with no configuration. The code is released under the MIT
license, like the delivery process advisor it includes.

## Considered options

- **Keeping the repository private:** rejected, because the author wants to
  share it, also with people who use Codex.
- **Publishing it only as an example to read and adapt:** rejected, because the
  skills already run in Claude Code and Codex, and removing the personal paths
  is enough for someone with the same setup to use them.
- **Making it portable, with a configuration file or an installer:** rejected
  for now: a setup step and code to maintain, while users with the same setup
  need neither.

## Consequences

Each user's videos, transcripts, and reference photo stay on their own PC and
out of git, as before. A user whose OBS folder or transcriber launcher is
elsewhere sets `OBS_REGISTRAZIONI` or `TRASCRITTORE`.
