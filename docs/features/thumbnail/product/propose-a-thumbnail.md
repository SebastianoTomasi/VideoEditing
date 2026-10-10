# Propose a thumbnail — product

**Status:** accepted

## Scope

What the user can achieve with the `thumbnail` feature: getting thumbnails,
and titles when needed, proposed for a video whose edit is final. Editing the
video belongs to the `edit-video` feature; what may leave this PC while a
thumbnail is made is fixed by the Product foundation.

## Dependencies

- [Data and privacy](../../../product/product-foundation.md#data-and-privacy)
  — image generation may receive only a text description, the reference photo,
  the user's face from the recordings, and frames that passed the frame check.
- [Playbook](../../../product/product-foundation.md#playbook) — the proposals
  follow it.
- [Image generation](../../../architecture/architecture-foundation.md#image-generation)
  and [Channel folder](../../../architecture/architecture-foundation.md#channel-folder)
  — how images are generated and where the reference photo and the channel
  template live.
- [Capability](../../edit-video/product/edit-a-video.md#capability) — the
  thumbnail starts from the final edit and the recordings it comes from.

## Capability

When the user says the edit of a video is final, the agent proposes three
clearly different thumbnails, each with one line on why:

- **A, the result:** an enlarged crop of the tool or the result at work, with
  2–4 words;
- **B, face and tool:** the user's face on one side, the interface on the
  other;
- **C, before and after, or one number:** for example "3 ore → 10 min".

The text of a thumbnail completes the title and never repeats it. If the user
already has a title, the agent uses it; otherwise it proposes three titles
paired with the three thumbnails, so that YouTube's Test & compare can try the
pairs.

The thumbnails are JPG files at 3840×2160 in the video's folder, with a
preview sheet that shows them at the small sizes YouTube uses, under a mock
duration badge. The agent never uploads anything: the user chooses.

## Channel style

With the first video the agent proposes a channel template: a heavy OFL font
such as Anton or Archivo Black, two or three restrained colours, and white or
yellow text with a dark outline. Once the user approves it, every thumbnail
uses it: the content changes, the style does not.

## Making the image

The pictures in a thumbnail may be generated: the user's face, drawn from the
reference photo and, when useful, from frames of the recordings; a sharper or
stylized version of a screenshot that passed the frame check; an illustration
described in words. Text and layout are never generated: they come from the
channel template and are turned into an image on this PC, so the font and the
Italian text are always exact. Background removal and other companies' logos
are not used; the real interface is shown instead.

## Preconditions

- The video has an edit the user has declared final.
- A reference photo of the user is in the channel folder.

## Non-goals

- A full-screen webcam scene recorded for the thumbnails.
- Uploading thumbnails or using YouTube's own thumbnail suggestions (Ask
  Studio): the user does that in YouTube Studio, if they want.

## Security screening

`security-new-subject-or-data`: dismissed. Thumbnails and the reference photo
are among the data classes declared in
[Data and privacy](../../../product/product-foundation.md#data-and-privacy).
