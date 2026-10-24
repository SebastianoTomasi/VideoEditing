# Edit a video — script mechanics

**Status:** accepted

## Scope

How the `edit-video` scripts work inside, with the starting values the user
delegated, to be calibrated on the first videos. What each script is
responsible for and guarantees is in the feature's
[components](../architecture/edit-pipeline.md).

## Dependencies

- [Components](../architecture/edit-pipeline.md#components) and
  [Invariants and failures](../architecture/edit-pipeline.md#invariants-and-failures)
  — the mechanics below satisfy them.

## Runtime

Python 3 standard library only, run with the system `python`, with no virtual
environment. External tools are called with argument lists, never through a
shell, so paths with spaces work.

## prepara.py

- Silences come from `ffmpeg … -af silencedetect`, starting at −35 dB and
  0.3 s, cached in the video's folder.
- Each line of the compact transcript is one transcriber segment,
  `[start–end] (+pause) text`, in the recording's seconds.
- A possible retake is a segment followed, among the next three that start
  within 30 s of it, by one that repeats it: the earlier is a prefix of the
  later, their first ten words share a run of at least four, or their texts
  are at least 80 % similar (`difflib`). The window counts from the start of
  the attempt because the transcriber may stretch its last word over the pause
  that follows.
- Audio without text is a gap between segments with at least 1.5 s of sound
  outside measured silences: speech the transcriber may have dropped. Shorter
  sounds are mostly fillers and breaths.
- A wait is a measured silence longer than 5 s.
- OBS markers come from `ffprobe -show_chapters` and are printed where they
  fall.

## monta.py

- One ffmpeg run renders the whole edit: one input per recording, one
  `trim`/`atrim` chain per kept stretch, joined with `concat`. The filter graph
  goes in a file passed with `-/filter_complex`, because Windows limits a
  command line to 32,767 characters.
- Each cut edge moves to the nearest point inside a measured silence, leaving
  30–200 ms of silence beside the speech, and every join gets a 30 ms audio
  fade-out and fade-in.
- A wait keeps 1 s at normal speed at each end; the middle plays at the speed
  that makes the whole wait last 4 s, with the video through `setpts` and the
  audio replaced with silence.
- Loudness: a first `loudnorm` pass measures, and the render applies it in
  linear mode to −14 LUFS and −1.5 dBTP, at 48 kHz.
- Video is encoded with `h264_nvenc` at high quality, keeping the first
  recording's resolution and frame rate; other recordings are scaled and
  converted to match, with a warning. Audio is AAC.

- `--stima` stops after building the timeline: it prints the length of the
  edit and refuses cuts with no silence, for the proposal.
- `montaggio.json` records every piece with its times in the edit and in its
  recording, so that controlla.py and the agent can map edit times back.

## fotogrammi.py

- One frame every `--ogni` seconds (20 by default), optionally cropped, scaled
  to 480 px wide, labelled with its time by `drawtext`, and tiled 4×3 into
  `foglio_NN.png`.

## controlla.py

- After the transcriber transcribes the edit, the words around each join are
  compared with the words the cut list keeps there. A missing or repeated
  sentence, or a word that does not match, becomes a potential problem with
  its time in the edit.
- Word times are estimated by spreading a segment's words over its spoken
  parts, skipping the measured silences inside it. Extra words heard near a
  join that belong to a sentence the cut edge goes through are not reported,
  because which of its words stay cannot be told; missing or different words
  still are.
- `ffprobe` checks the edit's duration against the one the cut list predicts.
- `montaggio.srt` is written from the segments of the edit's transcript, only
  when the whole edit is checked.
- Every check saves the edit map it checked in `controllo.json`. With
  `--cambiate`, a join has changed when what the edit plays within 15 s of it,
  as stretches of the recordings matched by path, matches no join of the saved
  map; a join that only moved in the edit is unchanged. Without
  `controllo.json`, `--cambiate` checks the whole edit.
- Each changed join gets its own stretch of the edit, 15 s on each side, so it
  sits in the middle of one of the transcriber's 30 s windows. The stretches
  go into one 16 kHz mono `giunzioni.wav`, 30 s of silence apart so that no
  window holds two of them, and the transcriber runs once. The heard words get
  back their time in the edit. Each stretch is compared on its own with the
  words the cut list keeps there, at the changed joins at least 5 s from its
  cut edges, and a problem two stretches find is reported once.

Most of these choices come from the research in
[video-editing-repos-research.md](../../../sources/video-editing-repos-research.md).
