# Edit a video — conversation

**Status:** proposed

## Scope

How the user and the agent interact in the conversation while a video is
edited: how the work starts, what the user sees at each step, and how
corrections are asked for. What the feature promises is in the feature's
[Product artifact](../product/edit-a-video.md); how the cut list is stored and
rendered belongs to Architecture and Implementation.

## Dependencies

- [Capability](../product/edit-a-video.md#capability) — the steps below carry
  that narrative into the conversation.
- [The user decides the cuts](../../../product/product-foundation.md#the-user-decides-the-cuts)
  — nothing is rendered before the user approves the proposal.

## Surface and entry point

The surface is the conversation with a coding agent opened in this
repository. The user starts by naming the video in their own words, for
example "monta il video di stasera".

## Steps

1. **Recordings.** The agent looks in `C:\Users\sebas\Videos\OBS` and proposes
   which recordings make up the video, in order of recording time, and the
   name of its folder, for example `videos/2026-10-10-presentazione-advisor/`.
   It goes on only after the user confirms.
2. **Transcripts.** For each recording without a transcript, the agent starts
   the transcriber in the background, says so, and continues when the
   transcripts are ready.
3. **Proposal.** The agent shows a table listing only what changes, the cuts
   and the speed-ups, each with its from–to and what happens there; everything
   not listed is kept. Optional cuts are in a second list. Below the table come
   the estimated length of the edit and what the frame check found.
4. **Approval.** The user approves, possibly with changes, and asks for any
   optional cuts they want. Nothing is rendered before.
5. **Report.** After rendering and checking, the agent gives the edit's length
   and lists the potential problems found at the joins, each with its
   timestamp in the edit. It changes nothing on its own: the user listens where
   needed and says how to fix it.
6. **Corrections.** The user asks for changes by quoting timestamps of the edit
   ("rimetti la frase a 3:20"), asks for a shorter edit, or asks to go back to
   the previous version. For a shorter edit, the agent first proposes further
   optional cuts and waits for the user's choice. Then it updates the cut list,
   renders, checks, and reports again.

## Failures

- A transcript without sentence segments: the agent stops and says the
  transcriber must be updated.
- A failed render: the agent reports the error, and the previous edit is
  unchanged.
