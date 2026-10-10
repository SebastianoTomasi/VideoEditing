# Edit a video — product

**Status:** proposed

## Scope

What the user can achieve with the `edit-video` feature: going from the
recordings of a video to an approved cut list and its edit, and correcting the
edit afterwards. Project-wide promises (who decides the cuts, privacy, what is
never broken) stay in the Product foundation; how the proposal is shown in the
conversation belongs to this feature's Frontend.

## Dependencies

- [The user decides the cuts](../../../product/product-foundation.md#the-user-decides-the-cuts)
  — this feature renders only a cut list the user approved.
- [Data and privacy](../../../product/product-foundation.md#data-and-privacy)
  — the frame check before the proposal applies that promise.
- [Transcriber](../../../architecture/architecture-foundation.md#transcriber)
  — cut points come from the transcriber's segments, so a transcript without
  them stops the feature.
- [Video folders](../../../architecture/architecture-foundation.md#video-folders)
  — the cut list, the notes, and the edit are written in the video's folder.

## Capability

The user asks the agent to edit a video. The agent identifies the recordings
that make up the video and has the user confirm them. It transcribes any
recording that has no transcript yet, checks sampled frames for content that
should not be visible, and proposes a cut list with the estimated length of
the edit. There is no target length: the agent proposes cutting what the video
does not need. Once the user approves the cut list, the edit is rendered into
the video's folder and every join is checked for a word cut in half or a
sentence repeated or missing. The user gets the edit's length and the
potential problems the check found, each with its timestamp in the edit. The
agent fixes nothing on its own: the user listens where needed and says how to
fix it.

Afterwards the user can ask for corrections by quoting timestamps of the edit,
ask for a shorter edit, or ask to go back to the previous version. For a
shorter edit, the agent proposes further optional cuts and leaves the rest as
it is. Each video has one cut list and one edit: a correction overwrites both,
after the previous cut list is saved with a number; earlier edits are not
kept.

## Preconditions

- The recordings are on this PC.
- The local transcriber is installed and produces transcripts with sentence
  segments.

## Outcomes

- **Success:** the edit in the video's folder, rendered from the cut list the
  user approved, and the user told its length and the potential problems found
  at its joins.
- **Rendering fails:** the previous edit stays as it was, and the user is told
  the error.
- **Transcript without sentence segments:** the feature stops, and the user is
  told the transcriber must be updated.

## Security screening

`security-new-subject-or-data`: dismissed. The feature uses only the actors,
subjects, and data classes declared in
[Data and privacy](../../../product/product-foundation.md#data-and-privacy).
