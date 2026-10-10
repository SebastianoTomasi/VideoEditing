# Architecture foundation

**Status:** accepted

## Scope

The project-wide Architecture decisions for VideoEditing: what is inside the
system and what it only uses, how it reads the transcriber, where each video's
files live, and where the agent instructions live. The components that do the
editing are settled with the `edit-video` feature; the internal design of the
scripts belongs to Implementation.

## Dependencies

- [Primary user](../product/product-foundation.md#primary-user) — the system
  runs only on this PC, driven by a coding agent opened in this repository, so
  the repository is the workspace.
- [Compatibility baseline](../product/product-foundation.md#compatibility-baseline)
  — original recordings are never modified, moved, or deleted, so the system
  only refers to them.
- [Data and privacy](../product/product-foundation.md#data-and-privacy) —
  nothing about a video may go into git or to GitHub, so video folders are kept
  out of git.

## System boundary

Inside the system: the agent instructions, the scripts, and the video folders
in this repository.

Used but not owned: OBS, which produces the recordings; the local transcriber;
ffmpeg; the coding agent and its model provider; YouTube, where the user
publishes by hand.

## Transcriber

The system uses the transcriber only through its launcher commands and the JSON
transcript they write, never through its Docker image or its intermediate
files. It uses it twice: to transcribe each recording that has no transcript
yet, and to transcribe each edit so that its joins can be checked. Transcripts
stay where the transcriber writes them, beside the recording or the edit.

Cut points come from the sentence segments that
[SebastianoTomasi/trascrittore#2](https://github.com/SebastianoTomasi/trascrittore/issues/2)
adds to that JSON. A transcript without segments stops the editing: the agent
says the transcriber must be updated, and works around it in no other way.

## Video folders

Each video has a folder `videos/<YYYY-MM-DD>-<name>/` in this repository,
holding its cut list, its notes, and its edit. Video folders are kept out of
git: nothing about a video is ever committed. Recordings stay where OBS writes
them, with their transcripts, and the folder refers to them by path.

## Agent instructions

The agent instructions are skills in `.agents/skills/`, linked from
`.claude/skills/`, so Claude Code and Codex read the same files.
