---
name: video-script
description: Write the video script (copione) of one of the user's YouTube screencasts before they record it. Use when the user asks for a copione, a script, or an outline of what to say and show in a video they are about to record ("scrivimi il copione", "preparami la scaletta del video").
---

# Write a video script

You write `copione.md` for a video the user is about to record: what to say
and show, scene by scene, so that the video works and the recording is easy to
edit. The accepted spec is
`docs/features/video-script/product/write-a-video-script.md`. Write the script
and talk to the user in Italian.

## Before writing

Read the playbook skill (`.agents/skills/playbook/SKILL.md`), sections 1 and
2: the script applies them. Ask only what you cannot find yourself: the topic,
the promise (the problem the video solves or the result it shows), the demo,
and the target length. Read any material the user points you to, such as a
repository, an earlier transcript, or notes.

## The script

Create `videos/<YYYY-MM-DD>-<name>/`, with the date of the planned recording,
and write `copione.md` there. The folder stays out of git, and the edit later
uses the same folder. The script holds:

- **The title line, the target length and the promise in one sentence.** The
  length is for planning only: the edit does not enforce it.
- **"Prima di registrare":**
  - OBS at 1920×1080, recording in Hybrid MP4 with the marker key assigned
    (the user's is Ctrl + <, bound to OBS "Add chapter marker");
  - the app sidebar closed, and text enlarged (Ctrl +) in every app shown;
  - the webcam placed where it covers nothing important;
  - the windows and the repository ready;
  - nothing private on screen: other sessions, email, keys, client data.
- **"Durante la ripresa":** the rules that make the edit reliable.
  - After a mistake, stop, press the marker key (Ctrl + <), pause two seconds,
    and say the whole sentence again.
  - Stay silent while the AI works: the edit speeds up those waits.
  - The recording may stop between scenes.
- **The scenes, numbered.** For each scene:
  - what to show on screen;
  - the sentences to say more or less as written, in quotes, with the rest
    written as directions;
  - any message or command to paste, in a code block;
  - roughly how long it lasts.

Shape the scenes with the playbook:
- the first scene states the promise within 10–20 seconds and shows or
  describes the result;
- a short spoken signpost opens each scene;
- the last scene shows the payoff, gives one next step, and ends within about
  20 seconds of it.

Never copy anything private you find, such as keys or client data, into the
script.

## Done

Show the user the path, the scenes, and the total length, then change the
script as they ask. When the video is edited, the `edit-video` skill compares
what was said with this script.
