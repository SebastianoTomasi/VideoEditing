# Edit a video — conversation

**Status:** accepted

## Scope

How the user and the agent interact in the conversation while a video is
edited: how the work starts, what the user sees at each step, and how
corrections are asked for. What the feature promises is in the feature's
[Product artifact](../product/edit-a-video.md); how the cut list is stored and
rendered belongs to Architecture and Implementation.

## Dependencies

- [Capability](../product/edit-a-video.md#capability) — the steps below carry
  that narrative into the conversation.
- [Cuts and pace](../product/edit-a-video.md#cuts-and-pace) and
  [What comes with the edit](../product/edit-a-video.md#what-comes-with-the-edit)
  — the proposal and the report show them.
- [The user decides the cuts](../../../product/product-foundation.md#the-user-decides-the-cuts)
  — nothing is rendered before the user approves the proposal.

## Surface and entry point

The surface is the conversation with a coding agent opened in this
repository. The user starts by naming the video in their own words, for
example "monta il video di stasera". Asking only for feedback on the text of a
recording ("dammi un feedback sul testo di stasera") runs steps 1 and 2, then
gives only the feedback on the spoken text.

## Steps

1. **Recordings.** The agent looks in the folder where OBS saves recordings
   and proposes which recordings make up the video, in order of recording
   time, and the
   name of its folder, for example `videos/2026-10-10-presentazione-advisor/`;
   if the video already has a folder from its video script, it proposes that
   one. A recording already moved for another video is proposed from that
   video's folder. It goes on only after the user confirms, then moves the
   recordings still in the OBS folder, with any transcript, into the video's
   folder, keeping their names.
2. **Transcripts.** For each recording without a transcript, the agent starts
   the transcriber in the background, says so, and continues when the
   transcripts are ready.
3. **Proposal.** The agent shows a table listing only what changes, the cuts
   and the speed-ups, each with its from–to and what happens there; everything
   not listed is kept. A cut that has no measured silence to fall into is
   marked as such. Optional cuts are in a second list. Below the table come the
   estimated length of the edit, what the frame check found, and the feedback
   on the spoken text: at most five points, each either pointing to the
   optional cut that fixes it or given as advice for the next recording.
4. **Approval.** The user approves, possibly with changes, and asks for any
   optional cuts they want. Nothing is rendered before.
5. **Report.** After the first render and its check, the agent gives the
   edit's length and lists the potential problems found at the joins, each
   with its timestamp in the edit. It changes nothing on its own: the user
   listens where needed and says how to fix it.
6. **Corrections.** The user asks for changes by quoting timestamps of the edit
   ("rimetti la frase a 3:20"), asks for a shorter edit, or asks to go back to
   the previous version. For a shorter edit, the agent first proposes further
   optional cuts and waits for the user's choice. Then it updates the cut list,
   renders, checks the joins the correction added or changed, and gives the new
   length and the potential problems found there; it checks the whole edit only
   when the user asks.
7. **Final edit.** When the user says the edit is final, the agent checks the
   whole edit once more if it changed since the last check of the whole edit,
   corrects the subtitles, and writes the YouTube description with its
   chapters and the YouTube tags. It says how many subtitle corrections it
   made and which points it could not make out, each with its timestamp in the
   edit, and which links in the description do not open for anyone, and it
   shows the tags; the subtitles, the description, and the tags are in the
   video's folder.

## Deleting the originals

The user asks in their own words, for example "cancella gli originali". The
agent lists every video folder that still holds recordings: their names and
total size, whether the edit is final, and any other video whose cut list uses
them. It proposes deleting the recordings of the videos whose edit is final
and goes on only after the user agrees. Then it moves them to the Recycle Bin
and says how much space emptying it frees. If the user later asks to correct
one of those edits, the agent says that its recordings are deleted.

## Waiting and empty states

- While the transcriber or the render runs, the agent says what is running and
  goes on when it ends. If the transcriber is busy with another transcription,
  the agent waits for it to finish.
- If no recording matches what the user named, the agent says so and asks
  which files to use.

## What the agent accepts

Corrections quote timestamps of the edit, in minutes and seconds. Asking for a
shorter edit or for the previous version needs no timestamp.

## Failures

- A transcript without sentence segments: the agent stops and says the
  transcriber must be updated.
- A failed render: the agent reports the error, and the previous edit is
  unchanged.
- A recording that cannot be moved, because a file with its name is already
  in the video's folder or it is open in another program: the agent says which
  recordings moved and which did not, and goes on once the user resolves it.
