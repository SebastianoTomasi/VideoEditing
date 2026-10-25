# Write a video script — product

**Status:** accepted

## Scope

What the user can achieve with the `video-script` feature: getting the video
script (copione) of a video written before recording it. How the video is
edited afterwards belongs to the `edit-video` feature, which uses the script
when it gives feedback on the spoken text.

## Dependencies

- [Playbook](../../../product/product-foundation.md#playbook) — the script
  follows it.
- [Video folders](../../../architecture/architecture-foundation.md#video-folders)
  — the script is the first file in the video's folder.

## Capability

On request, before recording, the agent writes the video script and saves it
as `copione.html` in a new folder for the video, `videos/<YYYY-MM-DD>-<name>/`;
the edit later uses the same folder. It gives the user the page's link, which
the user opens as a browser dock in OBS to read while recording. Like the
script written for the advisor
presentation on 2026-10-10, it holds:

- the target length, used for planning only: the edit does not enforce it;
- the scenes, with the sentences to say more or less as written and what to
  show on screen;
- a "before recording" list, such as OBS at 1920×1080, the app sidebar closed,
  and the webcam placed where it covers nothing;
- the recording rules that help the edit: after a mistake, stop, press the
  marker key, and say the whole sentence again; stay silent during waits.

When the video is edited, the feedback on the spoken text compares what the
user said with the script, for example to point out a skipped scene.

## Actors and data

The user, and the agent acting on their requests. Video scripts are among the
data classes declared in
[Data and privacy](../../../product/product-foundation.md#data-and-privacy).

## Outcome

A `copione.html` in the video's folder, written by the agent and changed as the
user asks.

## Security screening

`security-new-subject-or-data`: dismissed. The feature uses only the actors,
subjects, and data classes declared in
[Data and privacy](../../../product/product-foundation.md#data-and-privacy).
