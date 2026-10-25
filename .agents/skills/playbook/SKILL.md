---
name: playbook
description: The project's playbook for a decent YouTube video, spoken text included. Read it before giving feedback on what was said in a recording, proposing cuts, writing a video script (copione), or proposing thumbnails and titles. The user owns it and may change it at any time.
---

# Playbook

How to make a decent YouTube video for this channel: Italian screencasts with
a webcam in a corner, demoing software and AI coding agents, 5–15 minutes. The
`edit-video`, `video-script` and `thumbnail` skills apply it. The user can
change it at any time; when a rule does not fit a video, say so instead of
forcing it.

Evidence and sources: `docs/sources/youtube-video-guidelines-research.md` and
`docs/sources/youtube-thumbnail-research.md`.

## 1. Spoken text

Use these checks for feedback on a transcript and when writing a video script.
In feedback, report at most five points, the most important first, each with
its time and the words it is about. Say whether a cut can fix it, in which case
it becomes an optional cut, or whether it is advice for the next recording.

1. **The promise comes first.** The problem or the result is stated within the
   first 10–20 seconds, in words that echo the title. YouTube's "intro" figure
   is the share of viewers still watching after 30 seconds.
2. **Show the result early.** In a demo, the finished result is shown or
   described concretely before the work starts ("alla fine avremo X che fa
   Y").
3. **Nothing in front of the promise.** No long greeting, self-introduction or
   channel pitch, no "allora… vediamo… ok, partiamo". One short greeting is
   fine.
4. **Meta-talk is one sentence.** "In questo video vedremo…" is fine as one
   concrete sentence; an agenda of three or more items is not.
5. **Problem before solution.** The question the demo answers, or the obvious
   wrong approach, comes before the solution.
6. **Concrete and on screen.** Each claim is tied to something visible: a
   named file, a command, a number, an output. No "è potentissimo" without
   showing why. When the speaker says "qui" or "questo", the file, line or
   panel is named.
7. **One idea per sentence.** A sentence fits in one breath; flag sentences
   over about 25 words.
8. **Signposts.** Each change of topic has a short spoken signal ("Primo
   passo: …", "Ora che X funziona, passiamo a Y"). These become chapter
   titles.
9. **Fillers: only what stands out.** Flag clusters, long "ehm" and repeated
   tics (cioè, praticamente, diciamo, tipo, allora, niente, vabbè). Leave the
   markers that do work: "cioè" before a real reformulation, "quindi" for a
   consequence. Never flag every "ehm".
10. **No needless apologies or hedges.** "Scusate il casino", "non so se si
    vede", "non sono un esperto" go. A real uncertainty is said once, plainly
    ("l'agente non fa sempre la stessa cosa").
11. **Talk to the viewer.** Direct and conversational ("proviamo", "vedi"),
    with tu or voi used consistently, not impersonal ("si procede a…").
12. **Energy.** Flag long flat stretches and trailing sentences ("vabbè…
    niente…").
13. **Waits.** During an agent wait the speaker either says what the agent is
    doing and what to watch for, or stays silent. Filler talk ("aspettiamo… un
    attimo…") is an optional cut or advice.
14. **Digressions.** A tangent longer than about 30 seconds that does not serve
    the promise is an optional cut, with the reason.
15. **The payoff.** The result is shown and said ("ecco, adesso X funziona"),
    not buried. If the strongest moment comes late, advise showing it at the
    start next time.
16. **The ending.** The video ends within about 20 seconds of the payoff, with
    one concrete next step for the viewer, not a long recap or a generic
    "iscriviti". The last 5–20 seconds carry nothing essential, because
    YouTube's end screens cover them.
17. **Audio.** Flag key words that are mumbled, overlapped or covered by noise:
    they also break the captions.
18. **Against the video script.** When the video has a video script, compare
    what was said with it: a skipped scene, a missing promise, an ending that
    drifted.

## 2. Cuts

These complement the fixed rules of the `edit-video` skill.

- **Cut to the promise.** Propose cutting everything before the first
  statement of the promise, except one short greeting.
- **Retakes.** Keep the last attempt if it is complete; otherwise the most
  fluent complete one.
- **Digressions.** Tangents over about 30 seconds that do not serve the promise
  are optional cuts, with the reason.
- **Chapters.** Never cut the sentence that opens a chapter.
- **Waits.** Speed up silent waits, keeping about 1 second at normal speed at
  the start and at the end, so the viewer sees the agent working.
- **The pace stays natural.** Pauses inside speech and fillers are not cut; at
  most they become advice for the next recording.
- **Not in this version.** Zooms on small text and opening with the result
  (a cold open) are not done in the edit. Give them as advice: "ingrandisci
  il font", "la prossima volta mostra prima il risultato".
- **Chapters for the description.** Built from the spoken signposts: the first
  at 00:00, at least three, each at least 10 seconds long.
- **Audio problems.** Flag clipping, noise, keyboard clatter and jumps in
  level.

## 3. Thumbnails and titles

1. Propose three clearly different variants, each with one line on why:
   **A**, the result, an enlarged crop of the tool or output at work with 2–4
   words; **B**, face and tool, the face on one side and the interface on the
   other; **C**, before and after or one number ("3 ore → 10 min").
2. One message and one focal point, large (about 40 % of the height or more),
   and at most three elements: subject, text, one accent.
3. Show the real thing: a zoomed crop of the interface or the output, never a
   full screenshot with tiny text.
4. Text: 2–4 Italian words (5 at most) on 1–2 lines, uppercase, in the channel
   template's font, white or yellow with a dark outline, with a contrast of at
   least 4.5:1.
5. The text completes the title and never repeats it: title and thumbnail tell
   one story. Without a title yet, propose three titles paired with the three
   thumbnails.
6. Curiosity, not clickbait: everything the thumbnail shows happens in the
   video, early. Nothing sexual, gory, shocking or vulgar.
7. Keep text, numbers and eyes out of the bottom-right corner, where the
   duration badge sits, and at least 20 px from the edges.
8. For technical viewers stay clean: a controlled palette, no red arrows or
   circles, no fake shocked faces.
9. Always the channel template: the content changes, the style does not.
10. No other companies' logos; show the real interface instead.
11. Check each variant at 168×94, 320×180 and 360×202 px, and in grayscale,
    under a mock duration badge. If the text is not readable at 168×94, cut
    words, enlarge, simplify.
12. Generated pictures stay truthful: a generated face looks like the user in
    this video, a sharpened or stylized screenshot shows the same interface and
    result as the video, and nothing shows a feature or a result the video does
    not have. Text is never generated: it comes from the channel template.
13. Deliver 16:9 JPEG files at 3840×2160, never below 1280×720, with the
    preview sheet and the line on why each. Never upload: the user chooses. A
    channel with "advanced features" can test all three in YouTube's Test &
    compare, which picks the winner by watch time.

## Claims to ignore

The research found no support for: "keep videos under 6 minutes", the
"8-second attention span", "remove every ehm", "always show your face", "a
pattern interrupt every N seconds", and background music under explanations.
