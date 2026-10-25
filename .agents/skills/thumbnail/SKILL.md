---
name: thumbnail
description: Propose three YouTube thumbnails, and titles when needed, for one of the user's videos whose edit is final. Use when the user says an edit is final or asks for a thumbnail, a miniatura, a copertina, or a title for a video ("fammi la thumbnail", "proponimi i titoli").
---

# Propose a thumbnail

When the edit of a video is final, you propose three clearly different
thumbnails, plus three titles if the user has none. The accepted spec is
`docs/features/thumbnail/product/propose-a-thumbnail.md`. The style rules are
in the playbook skill (`.agents/skills/playbook/SKILL.md`), section 3: read it
first. Talk to the user in Italian.

## What may leave this PC

For thumbnails only, Codex's image generation, which runs at OpenAI, may
receive:
- a text description;
- the reference photo `canale/foto.png`;
- the user's face taken from the recordings;
- frames that passed the frame check, which excludes anything `note.md` flags.

Nothing else. Text is never generated: it comes from the channel template, so
that the font and the Italian words are exact. Never upload anything: the user
chooses and uploads.

## What you work with

- **The video's folder** `videos/<…>/`: `montaggio.mp4`, `montaggio.json`, the
  edit's transcript, and `note.md` with the frame check.
- **The channel folder** `canale/`, out of git:
  - `foto.png`, the reference photo;
  - `font/titolo.ttf`, the heading font. Without it the template falls back to
    Impact; say so once;
  - `modello/miniatura.html`, the approved channel template, once there is one.
- **The starting template** `.agents/skills/thumbnail/modello/miniatura.html`,
  used until the user approves a channel template.

## Steps

1. **Brief.** Write:
   - the promise of the video in one sentence, from the edit's transcript;
   - the title, or three proposed titles;
   - the three concepts A, B and C of the playbook, each with 2–4 Italian
     words that complete the title.
2. **Candidates.** Run
   `python scripts/fotogrammi.py <folder>/montaggio.mp4 <folder>/fotogrammi/miniature --ogni 10`.
   Add `--ritaglio X,Y,W,H` for a sheet of the webcam. Pick the frames that
   show the result or the interface at work, and take full-resolution stills
   with `ffmpeg -ss <t> -i <folder>/montaggio.mp4 -frames:v 1 <folder>/fotogrammi/<name>.png`,
   cropping with `-vf crop=w:h:x:y` where useful.
3. **Pictures.** For B, generate the face from the reference photo. For A and
   C, generate a sharper or stylized screenshot, or an illustration, only when
   it makes the thumbnail clearer than the real frame.
   - Write a prompt file that starts with `$imagegen` and says: what the
     picture shows; its composition; for a face, "keep the person's identity,
     face, hair and beard exactly as in the attached photo"; and "no text,
     letters, logos or watermarks". Ask for the shape of the slot it fills:
     for the face of B, a portrait (2:3) with the person centred, head and
     shoulders, on a plain background close to the channel's base colour; for
     a full background, landscape 16:9 with the empty space where the words
     go.
   - In Claude Code, run
     `python scripts/miniature.py genera <folder> --prompt <file> --nome B --immagine canale/foto.png`,
     adding `--immagine <frame>` for each frame you send. If `codex.exe` is
     missing, ask the user to do this step in Codex.
   - In Codex, the built-in generation takes no file paths: first open
     `canale/foto.png` and each frame you send with `view_image`, then use
     `$imagegen` with the prompt, saying which attached image is the reference
     for the face. Codex saves the picture under
     `$CODEX_HOME/generated_images/`, by default `~/.codex/generated_images/`:
     copy it into `<folder>/immagini/` named as `genera` names its copies,
     `<name>-<n>`, for example `immagini/B-1.png`.
4. **Layouts.** Copy the template into `<folder>/miniatura-A.html`, `-B.html`
   and `-C.html`. For each, set `data-layout`, fill the slots with images by
   paths relative to the folder, and remove the slots the layout does not use.
   Write the words with one of them accented. Keep everything out of the
   bottom-right corner, where the duration badge sits.
5. **Render and look.** Run
   `python scripts/miniature.py render <folder>/miniatura-A.html <folder>/miniatura-B.html <folder>/miniatura-C.html`,
   then
   `python scripts/miniature.py anteprima <folder>/miniatura-A.jpg <folder>/miniatura-B.jpg <folder>/miniatura-C.jpg --uscita <folder>/anteprima.png`,
   and look at the preview. If the words cannot be read at the smallest size,
   or the subject is unclear, shorten, enlarge, simplify, and render again.
6. **Deliver.** Give the user the three JPEG files and the preview, with one
   line each: the concept, the words, and the times of the source frames. Add
   the titles if you proposed them. The user chooses.
7. **Upload list.** Once the user has chosen, list what to upload to YouTube,
   in this order: the video `montaggio.mp4`, the subtitles `montaggio.srt`,
   the title, the description, the chosen thumbnail's JPEG, and the tags.
   Link the files, the description's `descrizione.txt` included: the user
   copies long text from the file. Put the title and the line of `tag.txt`
   each in its own code block, so each is copied in one gesture. End with
   whatever `note.md` still leaves open before publishing,
   such as a link that does not open for anyone.

## The channel template

With the first video, propose the template's style:
- a heavy OFL font, Anton or Archivo Black;
- two or three restrained colours in `:root`;
- white or yellow words with a dark outline.

Once the user approves it, copy it to `canale/modello/` and use it for every
video. Change it only when the user asks.
