# Edit a video — product

**Status:** accepted

## Scope

What the user can achieve with the `edit-video` feature: going from the
recordings of a video to an approved cut list and its edit, with feedback on
the spoken text, and correcting the edit afterwards. Project-wide promises (who
decides the cuts, privacy, what is never broken) stay in the Product
foundation; how the proposal is shown in the conversation belongs to this
feature's Frontend.

## Dependencies

- [The user decides the cuts](../../../product/product-foundation.md#the-user-decides-the-cuts)
  — this feature renders only a cut list the user approved.
- [Data and privacy](../../../product/product-foundation.md#data-and-privacy)
  — the frame check before the proposal applies that promise.
- [Transcriber](../../../architecture/architecture-foundation.md#transcriber)
  — cut points come from the transcriber's segments, so a transcript without
  them stops the feature.
- [Video folders](../../../architecture/architecture-foundation.md#video-folders)
  — the recordings move into the video's folder, and the cut list, the notes,
  and the edit are written there.
- [Compatibility baseline](../../../product/product-foundation.md#compatibility-baseline)
  — the feature moves a recording only into its video's folder and deletes it
  only when the user asks to delete the originals.
- [Playbook](../../../product/product-foundation.md#playbook) — the feedback on
  the spoken text and the cut proposal follow it.
- [Write a video script](../../video-script/product/write-a-video-script.md#capability)
  — when the video has a script, the feedback compares what was said with it.

## Capability

The user asks the agent to edit a video. The agent identifies the recordings
that make up the video and has the user confirm them, then moves them out of
the OBS folder into the video's folder, so that OBS's folder does not fill up
with recordings already used. It transcribes any
recording that has no transcript yet, checks sampled frames for content that
should not be visible, and proposes a cut list with the estimated length of
the edit. There is no target length: the agent proposes cutting what the video
does not need. With the proposal comes short feedback on the spoken text, at
most five points judged against the playbook: points that a cut can fix become
optional cuts, the others are advice for the next recording. When the video
has a video script, the feedback also compares what was said with it, for
example to point out a skipped scene. The user can also ask for this feedback
alone, on a recording they do not want edited.

Once the user approves the cut list, the edit is rendered into the video's
folder and every join is checked for a word cut in half or a sentence repeated
or missing. The user gets the edit's length and the potential problems the
check found, each with its timestamp in the edit. The agent fixes nothing on
its own: the user listens where needed and says how to fix it.

Afterwards the user can ask for corrections by quoting timestamps of the edit,
ask for a shorter edit, or ask to go back to the previous version. For a
shorter edit, the agent proposes further optional cuts and leaves the rest as
it is. Each video has one cut list and one edit: a correction overwrites both,
after the previous cut list is saved with a number; earlier edits are not
kept. After a correction the edit is rendered and only the joins the
correction added or changed are checked, so the user gets their potential
problems without waiting for the whole edit to be transcribed. The whole edit
is checked again when the user asks, and when the user says the edit is final
if it changed since the last check of the whole edit.

When the disk fills up, the user can ask to delete the originals. The agent
lists the video folders that still hold recordings, with their size and
whether the edit is final, and proposes deleting the recordings of the videos
whose edit is final. Once the user agrees, those recordings go to the Recycle
Bin, which the user empties; everything else in the folders stays. An edit
whose recordings are deleted can no longer be corrected or rendered again.

## Cuts and pace

- Every cut falls inside a silence measured in the recording, never only on a
  transcript time. Where there is no silence, the agent does not cut there and
  says so in the proposal.
- In a retake, the last complete attempt is kept.
- Pauses inside speech stay as they are. Waits, silences longer than about
  5 seconds while something happens on screen, are shortened to about
  4 seconds: about 1 second at normal speed at the start and at the end, so the
  viewer sees the agent working, and the rest sped up without sound.

## What comes with the edit

- The audio is normalized to −14 LUFS.
- Subtitles (`.srt`) for upload to YouTube, taken from the transcript that the
  last check of the whole edit makes. The agent corrects what the transcriber
  misheard, such as names and technical terms, leaves the spoken words
  otherwise as they were said, and asks the user only about what it cannot
  make out.
- A YouTube description, proposed by the agent: the video's promise, what it
  shows, the links the video promises, each checked to open for anyone, and
  chapters with timestamps of the edit.
- YouTube tags, proposed by the agent: about fifteen, on the topic, the tools
  shown, and the everyday Italian words for them, within YouTube's 500
  characters. Tags play a minimal role in discovery
  ([YouTube Help](https://support.google.com/youtube/answer/146402)), so the
  list stays short. Names that only appear in the video, such as the people in
  a demo recording, are left out: as tags they would mislead.
- If the user pressed the OBS marker key while recording, the agent uses the
  markers to find the sentences that went wrong.

## Actors and data

The user, and the agent acting on their requests. The feature handles data
classes declared in
[Data and privacy](../../../product/product-foundation.md#data-and-privacy):
recordings, transcripts, sampled frames, cut lists, notes, edits, and their
subtitles.

## Preconditions

- The recordings are on this PC.
- The local transcriber is installed and produces transcripts with sentence
  segments.

## Outcomes

- **Success:** the edit in the video's folder, rendered from the cut list the
  user approved, with its subtitles; the user is told its length and the
  potential problems found at its joins, and gets the proposed description with
  its chapters and the proposed tags.
- **Rendering fails:** the previous edit stays as it was, and the user is told
  the error.
- **Transcript without sentence segments:** the feature stops, and the user is
  told the transcriber must be updated.
- **Originals deleted:** the recordings the user agreed to delete are in the
  Recycle Bin; a correction asked for afterwards on one of those videos is
  refused, and the user is told why.

## Non-goals

- Shortening pauses inside speech, or jump cuts: apart from waits, the pace
  stays natural.
- Noise reduction, unless the user asks for it.

## Security screening

`security-new-subject-or-data`: dismissed. The feature uses only the actors,
subjects, and data classes declared in
[Data and privacy](../../../product/product-foundation.md#data-and-privacy).
