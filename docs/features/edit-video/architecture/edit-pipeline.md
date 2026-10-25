# Edit a video — components

**Status:** accepted

## Scope

The components that carry out the `edit-video` feature: what each one is
responsible for, which files each writes and reads, and the invariants and
failure behavior they keep. The internal mechanics of the scripts are in the
feature's [Implementation artifact](../implementation/edit-pipeline-mechanics.md);
project-wide boundaries (the transcriber contract, video folders, where agent
instructions live) are in the
[Architecture foundation](../../../architecture/architecture-foundation.md).

## Dependencies

- [Capability](../product/edit-a-video.md#capability) and
  [Cuts and pace](../product/edit-a-video.md#cuts-and-pace) — the components
  below carry them out.
- [Transcriber](../../../architecture/architecture-foundation.md#transcriber)
  — the scripts call the transcriber only through its launcher and read only
  its JSON.
- [Video folders](../../../architecture/architecture-foundation.md#video-folders)
  — every file below lives in the video's folder, out of git.
- [Compatibility baseline](../../../product/product-foundation.md#compatibility-baseline)
  — the cut list alone decides the edit. Recordings are only read, except by
  `importa.py`, which moves them into their video's folder, and
  `originali.py`, which deletes them when the user asks.

## Components

- **The `edit-video` skill:** a `SKILL.md` with the fixed rules and the steps
  of the conversation, followed by the agent. The agent alone writes the
  changes in the cut list and the notes.
- **`importa.py`:** moves the recordings the user confirmed, with their
  transcripts, from the OBS folder into the video's folder, keeping their
  names. It creates the cut list with the recordings when there is none, and
  otherwise changes the moved recordings' paths in the folder's files that name
  them.
- **`originali.py`:** lists the video folders that still hold recordings, and
  moves the recordings of the folders the user names to the Recycle Bin.
- **`fotogrammi.py`:** samples frames of a video into contact sheets, each
  frame labelled with its time, for the frame check and for thumbnail
  candidates.
- **The playbook:** a plain file shared with the other skills; the agent reads
  it and never writes it.
- **`prepara.py`:** for each recording, reads the transcript, measures the
  silences, and reads any OBS markers, then writes the compact transcript the
  agent reads.
- **`monta.py`:** renders the edit from the cut list. It alone writes the
  edit.
- **`controlla.py`:** has the transcriber transcribe the edit, compares the
  text at each join with the cut list, reports the potential problems, and
  writes the subtitles. After a correction it checks only the joins that
  changed since the last check: the transcriber transcribes only the
  stretches of the edit around them, and the subtitles stay as they are.

The scripts depend only on ffmpeg, ffprobe, the transcriber's launcher, the
files in the video folders, and, for `originali.py`, Windows' Recycle Bin.
They never call one another or the agent; the agent runs them.

## Files in a video's folder

| File | Written by | Read by |
|---|---|---|
| the recordings, with their OBS names, until `originali.py` moves them to the Recycle Bin | OBS, moved in by `importa.py` | `prepara.py`, `monta.py`, `controlla.py`, `fotogrammi.py` |
| `<recording> - trascrizione.json`, each recording's transcript | the transcriber, moved in by `importa.py` | `prepara.py`, `controlla.py` |
| `copione.html` (`copione.md` in older folders), the video script, when there is one | the agent, in the `video-script` feature | the agent, for the feedback |
| `tagli.json`, the cut list | `importa.py` with the recordings, then the agent | `monta.py`, `controlla.py`, the agent |
| `tagli-<n>.json`, earlier cut lists | the agent, before it overwrites `tagli.json` | the agent, to go back |
| `trascrizione-compatta.md`, the compact transcript | `prepara.py` | the agent |
| `silenzi.json`, the measured silences, cached per recording | `prepara.py` or `monta.py` | `prepara.py`, `monta.py` |
| `fotogrammi/`, sheets of sampled frames | `fotogrammi.py` | the agent |
| `note.md`, the notes | the agent | the agent, in later sessions |
| `montaggio.mp4`, the edit | `monta.py` | `controlla.py`, the user |
| `montaggio.json`, the pieces of the edit with their times in the edit and in the recordings | `monta.py` | `controlla.py`, the agent, to map the user's corrections |
| the edit's transcript | the transcriber | `controlla.py` |
| `controllo.json`, the pieces of the edit at the last check | `controlla.py` | `controlla.py`, to find the joins that changed |
| `giunzioni.wav`, the stretches of the edit around the joins that changed, and its transcript | `controlla.py`, then the transcriber | the transcriber, then `controlla.py` |
| `montaggio.srt`, the subtitles | `controlla.py` when it checks the whole edit, then the agent corrects what the transcriber misheard | the user |
| `descrizione.txt`, the YouTube description with the chapters | the agent | the user |
| `tag.txt`, the YouTube tags on one line, separated by commas | the agent | the agent, for the upload list; the user |

The cut list names the recordings in order, by path, and lists each stretch
that changes: its from–to in the recording's time, whether it is cut or sped
up, the reason, and the words involved. Every stretch it does not list is
kept.

## Invariants and failures

- The edit depends only on the cut list and the recordings: rendering the same
  cut list again gives the same stretches, in the same order, at the same
  speeds.
- `monta.py` writes the edit to a temporary file and replaces `montaggio.mp4`
  only when the render succeeds, so a failed render leaves the previous edit
  untouched.
- `monta.py` refuses a cut that has no measured silence to fall into, and
  reports it.
- `prepara.py` stops on a transcript without sentence segments and reports
  that the transcriber must be updated.
- When the transcriber is busy, a script waits and retries instead of starting
  a second transcription.
- `controlla.py` writes the subtitles only from a transcript of the whole
  edit.
- `importa.py` never overwrites a file and never moves a recording that is
  already in a video folder. It checks every move before making the first one,
  and reports which recordings moved if one move fails.
- `originali.py` moves recordings only to the Recycle Bin, never deletes them
  for good, and only for the folders the user names.
