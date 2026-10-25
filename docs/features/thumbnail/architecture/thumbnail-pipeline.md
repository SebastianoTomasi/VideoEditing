# Propose a thumbnail — components

**Status:** accepted

## Scope

The components that carry out the `thumbnail` feature, the files they write
and read, and how they keep the privacy rule. What the thumbnails must look
like is in the playbook; what the feature promises is in its
[Product artifact](../product/propose-a-thumbnail.md).

## Dependencies

- [Making the image](../product/propose-a-thumbnail.md#making-the-image) — the
  components below generate pictures and lay out text accordingly.
- [Image generation](../../../architecture/architecture-foundation.md#image-generation)
  and [Channel folder](../../../architecture/architecture-foundation.md#channel-folder)
  — how Codex is reached and where the channel's files live.
- [Components](../../edit-video/architecture/edit-pipeline.md#components) —
  candidate frames come from `fotogrammi.py`.

## Components

- **The `thumbnail` skill:** the brief, the choice of frames, the prompts for
  generated pictures, the layouts, and the upload list, followed by the agent.
- **The starting template** `.agents/skills/thumbnail/modello/miniatura.html`:
  an HTML page at 1280×720 CSS pixels with three layouts (A, B, C), slots for
  pictures and words, and the channel colours and font in one place. The
  approved channel template is a copy of it in `canale/modello/`.
- **`miniature.py genera`:** runs `codex exec` with the agent's prompt and the
  attached images, and copies the pictures Codex saves into the video's
  folder. In Codex the agent uses `$imagegen` directly instead.
- **`miniature.py render`:** turns each layout into a 3840×2160 JPEG with Edge
  in headless mode.
- **`miniature.py anteprima`:** a sheet with each thumbnail at 168×94, 320×180
  and 360×202 px and in grayscale, under a mock duration badge.

## Files

| File | Written by | Read by |
|---|---|---|
| `canale/foto.png`, the reference photo | the user, copied once | `miniature.py genera` |
| `canale/font/titolo.ttf`, the heading font | the user | the layouts |
| `canale/modello/miniatura.html`, the approved template | the agent, once approved | the agent |
| `<video>/fotogrammi/miniature/`, candidate sheets | `fotogrammi.py` | the agent |
| `<video>/immagini/`, generated pictures | `miniature.py genera` or Codex | the layouts |
| `<video>/miniatura-A.html` … `-C.html`, the layouts | the agent | `miniature.py render` |
| `<video>/miniatura-A.jpg` … `-C.jpg`, the thumbnails | `miniature.py render` | the user |
| `<video>/anteprima.png`, the preview sheet | `miniature.py anteprima` | the agent, the user |

## Invariants and failures

- Only the prompt, the reference photo, and the frames the agent attaches
  reach Codex; the layouts and their text are rendered on this PC.
- Layouts load fonts and pictures by relative path only, so rendering makes no
  network request.
- Without `codex.exe`, `genera` stops and the agent asks the user to run that
  step in Codex; layouts and rendering still work.
- Without Edge, `render` stops and says so.
