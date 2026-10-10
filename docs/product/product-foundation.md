# Product foundation

**Status:** accepted

## Scope

The project-wide Product decisions for VideoEditing: what the system is for,
who uses it, which recordings it handles, what it delivers, how the user keeps
control of the cuts, how the data is protected, and what is never broken. How
one video is edited step by step belongs to the feature artifacts under
`docs/features/`; how the system is built, including how it uses the
transcriber, belongs to Architecture and Implementation.

## Purpose

VideoEditing turns the user's raw OBS recordings into a video ready to publish,
without opening a video editor. A coding agent reads the transcript, proposes
what to cut (retakes, misspoken sentences, digressions) and which waits to
speed up, and joins the recordings in order; scripts render the edit and check
it. The user decides; the agent does the work.

Without it, every video costs the user hours of manual editing, or never comes
out.

## Capabilities

- **Edit a video:** the cut list is proposed and approved, the edit is rendered
  and checked, and corrections follow on request
  ([edit-video](../features/edit-video/product/edit-a-video.md)).
- **Feedback on the spoken text:** the agent judges what the user says against
  written guidance on making a decent YouTube video.
- **Thumbnail:** the agent proposes a thumbnail for the video.

## Primary user

The only user is the project's author, on this PC, asking a coding agent
(Claude Code, possibly Codex) opened in this repository. The system may assume
that ffmpeg, Docker with GPU access, and the local transcriber are installed,
and that the user can read a table of timestamps. It has no graphical
interface, no installer, and no support for anyone else's machine.

## Recordings handled

Only the user's OBS screencasts: the screen with the webcam in a corner, one
speaker (the user), in Italian. A video can be made of several recordings,
typically one per scene, joined in order.

## Destination

The user publishes the edits on YouTube as landscape (16:9) long-form videos of
about 5–15 minutes; the same file may also go to LinkedIn.

## What the user gets

For each video, a finished MP4, the edit, with its cut list kept beside it, so
the user can ask for changes and have it rendered again.

## The user decides the cuts

The agent never cuts on its own. Before rendering, it proposes the cut list:
what each stretch contains and whether to keep it, cut it, or speed it up,
with the estimated length of the edit. It renders only after the user
approves. Afterwards the user can ask for corrections by quoting timestamps of
the edit ("put back the sentence at 3:20"), and the agent renders again.

## Data and privacy

The system handles the recordings, which show the user's face, voice, and
screen, and the screen can show other people's data, secrets, and unrelated
projects. It also handles the transcripts, the cut lists and notes, the edits,
and frames sampled from the recordings.

- Everything about a video (recordings, transcripts, cut lists, notes, edits)
  stays on this PC, and none of it goes into git or to GitHub. The agent reads
  transcripts and sampled frames, so those pass through its model provider
  (Anthropic or OpenAI) like any file it opens; nothing else is sent to an
  external service. The user publishes by hand.
- Before proposing the cut list, the agent samples frames and flags what should
  not be visible, such as the sidebar with other sessions, email addresses,
  keys, or client data. The check is a sample, not a guarantee. The system does
  not blur: a flagged stretch is cut or recorded again.
- The user is the only actor, and the agent acts only on the user's requests.
  People whose data may appear on screen are subjects: their data is what the
  user is not free to publish, and the flags exist for it.

## Compatibility baseline

The system promises the user that:

- an original recording is never modified, moved, or deleted;
- the same cut list always yields the same edit: the same stretches, in the
  same order, at the same speeds.

## Non-goals

These are outside the product for now; each would need a new decision:

- a version for other people or other machines, including a graphical
  interface or an installer;
- recordings with several voices (meetings, interviews), phone footage, and
  languages other than Italian;
- vertical videos and shorts;
- exporting a timeline to a video editor such as DaVinci Resolve or Premiere;
- blurring parts of the screen;
- writing the script of a recording.
