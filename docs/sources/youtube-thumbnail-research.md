# YouTube thumbnails: specs, practices and a local recipe

Web research, read-only, done on **2026-10-10**. It gathers what an editing agent needs to propose a thumbnail for each video: YouTube's official specs and features, thumbnail best practices, local tools to build one, and a minimal recipe. Target: Italian long-form (5–15 min) landscape screencasts recorded with OBS, webcam in a corner, demoing the author's software and AI coding agents; Windows 11, ffmpeg 8, Python 3.14 with uv, Node 24, NVIDIA GPU. Constraint: recordings and frames stay on this PC (only the coding agent reads frames), so online image generators are out.

Conventions: **[official]** = YouTube or Google page; **[secondary]** = practitioner, vendor, press or data study (observational: correlation, not cause); unmarked links are project docs or source code. ★ = GitHub stars on 2026-10-10 from `https://api.github.com/repos/<owner>/<repo>`. Nothing was installed or run. `ayosec.github.io` links are a per-filter mirror of the official FFmpeg 8.0 filter docs.

## 1. YouTube specs and features

**Image file**
- 16:9; resolution **3840×2160** recommended, minimum width **640 px**; "image formats such as JPG or PNG"; "as large as possible", since it is also the embedded player's preview image [official: Video thumbnails][h72431]. The Italian version of the page also lists GIF [official][h72431it].
- Size limit **50 MB** when uploading from a computer, **2 MB** from mobile (10 MB for podcasts) [official][h72431]. The cap rose from 2 MB to serve 4K thumbnails on TV, announced 2025-10-29 [official: YouTube Blog][blogtv]. The Data API `thumbnails.set` also accepts 50 MB of `image/jpeg` or `image/png` [official](https://developers.google.com/youtube/v3/docs/thumbnails/set).
- YouTube serves resized copies at 120×90, 320×180, 480×360, 640×480 and 1280×720 [official](https://developers.google.com/youtube/v3/docs/thumbnails).
- YouTube Studio's Ask Studio "analyzes your video's transcript and themes to suggest thumbnails" [official][h72431]: a generative service, outside this project's constraint unless the user decides otherwise.

**Eligibility and quotas**
- Custom thumbnails need a verified account [official][h72431]. They are an *intermediate* feature (phone verification) with a limited daily quota that rises with *advanced* features; A/B testing is *advanced* (ID or video verification, or enough channel history); videos over 15 min are also intermediate [official: feature access][h9890437]. The error "Daily custom thumbnail limit reached" means retry in 24 h [official][h72431].

**Policy**
- Not allowed: pornographic imagery; sexual acts, fetishes or other sexually gratifying imagery; nudity; unwanted sexualization; "violent imagery that intends to shock or disgust"; blood or gore; "vulgar or lewd language"; "a thumbnail that misleads viewers to think they're about to view something that's not in the video". A violation removes the thumbnail and may bring a strike; pornography may terminate the channel; three strikes in 90 days may terminate it; borderline thumbnails may be age-restricted or removed without a strike [official: Thumbnails policy][h9229980].
- "Maliciously misleading titles, thumbnails, descriptions, or imagery" count as malicious clickbait under the spam policy [official](https://support.google.com/youtube/answer/2801973?hl=en); repeat offences can remove custom-thumbnail privileges for 30 days [official][h72431].

**Where thumbnails appear, and how big**
- Thumbnails compete on the homepage, in "Up next" on the watch page, in search results and in subscription feeds; the CTR metric excludes external websites and end screens; "Half of all channels and videos on YouTube have an impressions CTR that can range between 2% and 10%" [official: CTR FAQ][h7628154]. They are also the embedded player's preview [official][h72431] and appear on TV, where 4K is the goal [official][blogtv].
- YouTube publishes no on-screen sizes. One third-party guide gives: desktop sidebar ≈168 px wide, desktop home 320–360, search 240–360, mobile home ≈ full width (~360), TV 400–600 [secondary: TubeCore, 2026-04](https://tubecore.xpanddigital.io/blog/youtube-thumbnail-size-guide). The smallest common case, ≈168×94, is 13% of 1280×720.
- The video-duration badge covers the bottom-right corner: keep text and subjects out of it [secondary: Snappa, 2026-09](https://snappa.com/blog/youtube-thumbnail-mistakes/). No official page was found; TubeCore's "roughly 100 x 30 pixels" clear zone does not state its scale.

**Test & compare (A/B)**
- Up to **3** thumbnails and/or titles (title only, thumbnail only, or pairs); the option with the highest **watch time** is then shown to all viewers, because YouTube optimises "for overall watch time over other metrics, like click-through-rate"; outcomes: *Winner* ("based on watch time share"), *Performed same*, *Inconclusive* (the first upload stays) [official: A/B test][h16391400].
- "True, concurrent A/B/C tests", unlike third-party tools that run sequentially and "often only optimize for click-through rate" [official][h13861714]. A test completes within two weeks; computer-only in YouTube Studio; needs advanced features; not for Shorts, scheduled lives, premieres until they end, made-for-kids, mature-audience, private or 18+ videos [official][h16391400].
- If any variant is below 720p, all variants are downscaled to 480p; variants "too similar to each other" make tests run longer; results show on the video's Details page and Reach tab [official][h16391400], [official][h13861714].

## 2. Best practices

**Official** ("Thumbnail & title tips" [official][h12340300])
- Decide who it is for: subscribers respond to familiar features, casual viewers to universal actions and emotions, "like a shocked face".
- Apply the rule of thirds, then overlay branding and descriptive text; "use a font that's easy to read"; "Try not to make the design too complex"; colour catches the eye, "but too much can overwhelm it".
- "Thumbnails show up differently across devices"; take pictures during the shoot to have options; try refreshed thumbnails on older videos; "90% of the best-performing videos have custom thumbnails".
- Titles must be accurate; the examples show title and thumbnail "working together to create interest and tell a story".
- Since the A/B winner is chosen by watch time [h16391400] and misleading thumbnails are banned [h9229980], the thumbnail's promise must be paid off, early, in the video.

**Practitioners [secondary]**
- MrBeast production handbook (leaked 2024, authenticity unconfirmed): every video starts from the title and thumbnail, which set the viewer's expectations; unmet expectations make viewers click away [Simon Willison](https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/).
- Chucky Appleby (MrBeast's packaging lead) on YouTube's own Creator Advice podcast, 2024-03-07 ([official host: YouTube Blog](https://blog.youtube/creator-and-artist-stories/renes-top-five-on-youtube-march-7-2024-edition/)): "Make your thumbnail easy to understand"; check it at the small size it is shown at; keep face, colours and format consistent; trust brings viewers back; test many variants (closed-mouth smiles gave slightly more watch time) [Social Media Today](https://www.socialmediatoday.com/news/youtube-shares-insights-mrbeasts-team-creates-compelling-thumbnail/709817/).
- Paddy Galloway (YouTube strategist; AI-generated summary of an interview, wording unverified): simple enough to register in seconds while scrolling, four or five words, bright saturated colours, short phrases that open a curiosity gap [videohighlight](https://videohighlight.com/v/dAR3d6xnG0o).

**Data studies [secondary]** (views relative to channel baselines, not CTR)
- Eden, 507,478 long-form videos, Aug 2025–Aug 2026: a face in 84.2% of breakouts vs 82.2% of underperformers; no difference in brightness, contrast, saturation or warm colours; the largest text gap is at 4–6 words (30.6% vs 26.5%); text repeats the title verbatim in only 6.3% and shares no word with it in 39% [Eden](https://eden.so/blog/what-makes-a-good-youtube-thumbnail/).
- 1of10, 300K viral 2025 videos: faces and no faces perform similarly overall; faces helped only above a subscriber threshold; results vary by niche [SEJ, 2025-12-22](https://www.searchenginejournal.com/do-faces-help-youtube-thumbnails-heres-what-the-data-says/563944/).
- vidIQ, 500 breakouts in 30 niches, July 2026: faces in 69% (80% of the top 50); most use three words or fewer; high contrast is rarer among the biggest breakouts (56% → 46%) [vidIQ](https://vidiq.com/research/youtube-thumbnail-study/) (the page refused automated reading; figures from search excerpts).
- Thumbnail Bench, 11,223 covers from 1,043 channels over 100K subscribers: 71% show a face (neutral 35%, happy 32%, shocked 11%); 77% carry text, median 4 words, mostly white (68%), capitals (62%) and outlined, shadowed or boxed (73%) [Net Influencer, 2026-09-21](https://www.netinfluencer.com/?p=53558).

**Tech, software and AI tools** [secondary: vendor guidance; no data found]
- "Educational thumbnails optimize for clarity": show the code or the real interface, a before/after or the final result; one coding channel reportedly lost CTR after copying shocked faces and red circles (anecdote) [Thumbfast, 2026-03](https://thumbfa.st/posts/best-thumbnail-maker-for-education-tutorials).
- The product dominates and "the face goes to the side, not the centre"; cooler, controlled palette; "three to five at most" words; "one hard number does more than any adjective"; "Restraint reads as credible"; arrows, circles and shock faces read as low quality to technical viewers [1of10](https://1of10.com/thumbnail-generator/tech).
- A measurable floor borrowed from web accessibility: text contrast ≥ 4.5:1, ≥ 3:1 for large text [W3C WCAG 2.2](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html); not a YouTube rule.

## 3. Local production options

**Candidate frames with ffmpeg 8**

| Need | Filter | Notes |
|---|---|---|
| Screen changes | `select='gt(scene,0.3)'` | score 0–1, "between 0.3 and 0.5 is generally a sane choice" ([select](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Multimedia/select.html)); stored as `lavfi.scene_score` ([f_select.c](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/f_select.c)); screencasts may need less (untested) |
| One typical frame per batch | `thumbnail=n=300` | "most representative frame" of each n frames, default 100; large n costs memory ([thumbnail](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/thumbnail.html)) |
| Regular sampling | `fps=1/2` | frame i ≈ second 2·i |
| Contact sheet for the agent | `scale=320:-2,tile=6x5` | ([tile](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/tile.html)) |
| Sharp webcam frames | `crop=W:H:X:Y,blurdetect` | since FFmpeg 5.1 ([blurdetect](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/blurdetect.html)); key `lavfi.blur`, higher = blurrier ([vf_blurdetect.c](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/vf_blurdetect.c)) |
| Times of picked frames | `metadata=print:file=x.txt`, `showinfo` | ([metadata](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Multimedia/metadata.html)); `showinfo` logs `pts_time` ([showinfo](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/showinfo.html)) |
| Face crop and upscale | `crop=w:h:x:y,scale=iw*2:ih*2:flags=lanczos` | ([crop](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/crop.html)); current FFmpeg docs deprecate `flags` algorithms in favour of a `scaler` option ([scaler](https://ffmpeg.org/ffmpeg-scaler.html)) |

Use `-fps_mode vfr` with `select` ([ffmpeg](https://ffmpeg.org/ffmpeg.html)). The webcam is scaled down in the OBS composite, so its crop may be small (actual size unknown). Better face sources, simplest first: a ~10 s full-screen webcam scene of deliberate expressions at the end of each recording (applies "take pictures during your shoot" [official][h12340300]); or a separate webcam file from the Source Record plugin, "a filter that allows you to record a source" (Windows; 0.4.8 of 2026-03-26; GPL-2.0; ★660) [OBS forum](https://obsproject.com/forum/resources/source-record.1285/).

**Composing the image**

| Option | Effort | Quality | Dependencies | Windows friendliness |
|---|---|---|---|---|
| ffmpeg `drawtext` + `overlay` | low for one line, high for polish | basic: no wrapping documented; `borderw`, `box`, shadow ([drawtext](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/drawtext.html)) | none new; `fontfile` needed without fontconfig | fine, but escaping `:` and `'` (Italian apostrophes) is painful: use `textfile=` (UTF-8) |
| Pillow (Python) | medium: hand layout, measure with `textbbox` | good: `stroke_width`/`stroke_fill` outlines, alpha compositing ([ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)); variable fonts via `set_variation_by_axes` ([ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html)) | `uv add pillow`; MIT-CMU; 12.3.0 of 2026-07-01 ([PyPI](https://pypi.org/project/pillow/)); Pillow 12 is the only line listed for 3.14 ([support](https://pillow.readthedocs.io/en/stable/installation/python-support.html)) | excellent (wheels) |
| ImageMagick 7 | medium | good | `winget install ImageMagick.Q16-HDRI`, 7.1.2-33 ([download](https://imagemagick.org/download/)); ImageMagick License ([license](https://imagemagick.org/license/)) | ok; `magick` replaces `convert`, which is no longer shipped on Windows ([porting](https://imagemagick.org/porting/)); shell quoting |
| **HTML/CSS template + Playwright** | low–medium; one reusable template; agents write HTML/CSS easily (assumption) | best: flex/grid, `-webkit-text-stroke` with `paint-order: stroke fill` ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/paint-order)), shadows, filters, local `@font-face` | `playwright`, Apache-2.0, ★97k; Python 1.63.0 lists 3.14 ([PyPI](https://pypi.org/project/playwright/)); installed Edge/Chrome via `channel="msedge"`, else a bundled Chromium of a few hundred MB ([browsers](https://playwright.dev/docs/browsers)) | good; Edge is removable in the EU ([secondary: Pureinfotech](https://pureinfotech.com/uninstall-microsoft-edge-chromium-windows-10)), so check it exists |
| html2image (Python) | low | as HTML, less control | MIT, ★455; wraps headless Chrome or Edge; `size=(w, h)` ([GitHub](https://github.com/vgalin/html2image)) | tested on Windows |
| Satori + sharp (Node) | medium | good; CSS subset (flex, grid, block) | MPL-2.0, ★14k; HTML/CSS → SVG, PNG via sharp; TTF/OTF/WOFF, no WOFF2 ([GitHub](https://github.com/vercel/satori)) | good; no browser |
| Chrome/Edge command line | low | as HTML | `--headless --screenshot --window-size=1280,720` writes `screenshot.png` ([Chrome](https://developer.chrome.com/blog/headless-chrome)) | ok; less control than Playwright |

**Optional local helpers**
- **Cut-out**: rembg (MIT, ★25.0k, 2.0.85 of 2026-09-20; README: Python ≥ 3.11, < 3.14, so give it its own environment: `uvx --python 3.13 --from "rembg[cpu,cli]" rembg i -m birefnet-portrait face.png face_cut.png`) ([PyPI](https://pypi.org/project/rembg/), [GitHub](https://github.com/danielgatis/rembg)). Models download once to `~/.rembg`. The default `bria-rmbg` (~1.02 GB) has a BRIA licence that "requires a paid agreement for commercial use"; for a monetised channel use `birefnet-portrait` (BiRefNet, MIT, [GitHub](https://github.com/ZhengPeng7/BiRefNet)) or `u2net_human_seg` (U-2-Net, Apache-2.0; u2net 176 MB, u2netp 4.7 MB, [GitHub](https://github.com/xuebinqin/U-2-Net)). Never the `withoutbg` or `atlascloud` backends: they send images to a server. GPU needs `rembg[gpu]` with onnxruntime-gpu, CUDA and cuDNN; CPU is enough for a few stills. Check hair edges.
- **Upscale**: Lanczos suffices for 2×. Real-ESRGAN ncnn-vulkan (MIT, ★2.3k, last push 2024-05) is a Windows exe using Vulkan, `-s 2|3|4` ([GitHub](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan)); GAN upscalers can invent facial texture (general caveat, untested). Avoid GFPGAN for a monetised channel: its licence bundles NVIDIA StyleGAN2 terms limiting use to non-commercial and CC BY-NC-SA code ([LICENSE](https://raw.githubusercontent.com/TencentARC/GFPGAN/master/LICENSE)).
- **Expression scoring**: MediaPipe Face Landmarker "predicts 52 blendshape scores" ([docs](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker)); `mediapipe` 1.1.0 of 2026-10-06 (Apache-2.0) ships Python 3.14 Windows wheels ([PyPI](https://pypi.org/project/mediapipe/)). Simpler: the agent looks at a contact sheet.

**Fonts** (all SIL OFL; kind and subsets from each family's `METADATA.pb` in google/fonts)

| Font | Kind | Subsets | Note |
|---|---|---|---|
| [Anton](https://raw.githubusercontent.com/google/fonts/main/ofl/anton/METADATA.pb) | condensed display sans, one weight | latin, latin-ext, vietnamese | "optimised for use as bold display font" ([description](https://raw.githubusercontent.com/google/fonts/main/ofl/anton/DESCRIPTION.en_us.html)); condensed fits long Italian words |
| [Bebas Neue](https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/METADATA.pb) | condensed display, one weight | latin, latin-ext | "suitable for headlines, captions, and packaging" ([description](https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/DESCRIPTION.en_us.html)) |
| [Archivo Black](https://raw.githubusercontent.com/google/fonts/main/ofl/archivoblack/METADATA.pb) | heavy sans, one weight | latin, latin-ext | single file, simplest for Pillow/ffmpeg |
| [Montserrat](https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/METADATA.pb) | geometric sans, variable weight 100–900 | latin, latin-ext, cyrillic, vietnamese | set weight 800–900 explicitly |
| [Inter](https://raw.githubusercontent.com/google/fonts/main/ofl/inter/METADATA.pb) | UI sans, variable weight 100–900 | latin, latin-ext, greek, cyrillic, vietnamese | close to software UIs; set 800–900 |

OFL FAQ: graphics made with an OFL font are not subject to the OFL (1.13) and stay yours (1.1.1); logos and video titling are allowed (1.1); attribution is not required (1.1.2); only selling the fonts by themselves is barred (1.6) ([OFL FAQ](https://openfontlicense.org/ofl-faq/)). Italian needs only Latin-1 letters (à è é ì ò ù È): test-render "È À É Ì Ò Ù L'IA" once per font.

**Open-source thumbnail projects**

| Repo | ★, licence | How it works | Fit here |
|---|---|---|---|
| [liustack/beastcover](https://github.com/liustack/beastcover) | 5, MIT, archived 2026-09-29 | Agent skill + CLI; 14 HTML cover templates "rendered in a local Chromium" via Playwright; YouTube 1280×720 preset; optional Openverse photos and OpenAI/Gemini scene painting | closest pattern; keep external options off |
| [AgriciDaniel/claude-youtube](https://github.com/AgriciDaniel/claude-youtube) | 443, MIT | Claude Code skill; the thumbnail command writes a brief: 3 A/B variants, hex colours, composition, title–thumbnail synergy check; images only through an optional Gemini MCP | borrow the brief format |
| [charlesdove977/ez-thumb](https://github.com/charlesdove977/ez-thumb) | 4 (page), MIT | Concepts and a "Four Cs" score from competitor thumbnails gathered with Apify (required) | external service; no |
| [darkzOGx/youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent) | 4.2k, MIT | Multi-agent channel automation; credits GPT Image and Gemini image models, gradient fallback | external models; no |
| [frinyvonnick/node-html-to-image](https://github.com/frinyvonnick/node-html-to-image) | 887, Apache-2.0 | Puppeteer + Handlebars, HTML → image | building block |

No mature project builds thumbnails from a recording's own frames; a small script (ffmpeg + HTML template + Playwright) is the simplest fit.

## 4. Recommended minimal local recipe

**Inputs**: the rendered edit (`edit.mp4`); its Italian title and a one-sentence promise; the transcript with times, if the editing step made one; the webcam rectangle `W:H:X:Y` (measure once per OBS layout); the channel template (fonts, 2–3 colours, logo spot).

1. **Brief.** Write the promise and three clearly different concepts: **A** result first (zoomed crop of the working output or tool + 2–3 words); **B** face + tool (expressive face to one side, tool UI or logo on the other, 1–3 words); **C** before/after or one hard number ("3 ore → 10 min"). The text adds what the title does not say.
2. **Candidates.** Make contact sheets of screen changes and of the webcam; also look where the transcript shows the result. The agent reads the sheets and picks 2–3 times per concept:
   ```text
   ffmpeg -i edit.mp4 -vf "select='gt(scene,0.3)',metadata=print:file=scenes.txt,scale=480:-2,tile=4x4" -fps_mode vfr screens_%02d.png
   ffmpeg -i edit.mp4 -vf "fps=1/2,crop=W:H:X:Y,scale=320:-2,tile=6x5" -fps_mode vfr faces_%02d.png
   ffmpeg -i edit.mp4 -vf "fps=2,crop=W:H:X:Y,blurdetect,metadata=print:file=blur.txt" -f null -
   ```
   Cell k (0-based) of `faces_NN.png` ≈ second 2·(30·(NN−1)+k). Keep `file=` paths relative: a `C:` colon would need filtergraph escaping.
3. **Full-resolution stills**: `ffmpeg -ss T -i edit.mp4 -frames:v 1 shot_T.png`; face: `-vf "crop=W:H:X:Y,scale=iw*2:ih*2:flags=lanczos"`; optional cut-out with rembg (§3).
4. **Compose** one HTML file per variant at 1280×720 CSS px from the channel template: fonts and images by relative path (no external URLs, so rendering makes no network request; if a font fails to load, embed it as a `data:` URI, not verified here); background in a brand colour or a darkened, blurred frame; main subject ≥ ~40% of the height (heuristic); 1–2 lines of uppercase text with cap height ≥ ~100 px (derived: ≈13 px at 168×94), white or yellow with a dark outline; no text, number, logo or eyes in the bottom-right ≈20%×15% (badge estimate) or within 20 px of the edges.
5. **Render** at 3840×2160 with Playwright for Python:
   ```python
   from pathlib import Path
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch(channel="msedge")  # else: playwright install chromium
       page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=3)
       for v in "ABC":
           page.goto(Path(f"thumb_{v}.html").resolve().as_uri())
           page.evaluate("document.fonts.ready.then(() => 1)")
           page.screenshot(path=f"thumb_{v}.jpg", type="jpeg", quality=90)
       browser.close()
   ```
   `device_scale_factor` defaults to 1 and screenshot `scale` to `"device"` ([class-browser](https://playwright.dev/docs/api/class-browser), [class-page](https://playwright.dev/docs/api/class-page)). Check each file ≤ 50 MB; if it will be uploaded from a phone, also export a 1280×720 copy ≤ 2 MB.
6. **Check at small size**: scale each variant with `flags=area` to 168×94, 320×180 and 360×202, plus a `format=gray` copy, side by side (`hstack=inputs=3`), with a dark `drawbox` in the bottom-right as a mock duration badge. Pass: text readable and subject recognisable at 168×94, text contrast ≥ 4.5:1, the three variants distinct at a glance. Else cut words, enlarge, simplify, re-render.
7. **Deliver** `thumb_A/B/C.jpg`, the preview sheet and one line per variant (concept, words, source times). The user chooses and uploads; with advanced features, all three go into Test & compare.

## 5. Summary for the agent sheet

1. Propose 3 clearly different variants per video (result first · face + tool · before/after or one number), each with a one-line rationale.
2. Stay local: ffmpeg for frames, an HTML/CSS template rendered by Playwright with installed Edge (or Pillow); no online generators, no rembg cloud backends, no external URLs in templates.
3. Output 16:9 JPEG at 3840×2160 (1280×720 CSS px × 3), quality ≈ 90, ≤ 50 MB; never below 1280×720 (A/B downscales everything to 480p otherwise).
4. One message, one focal point: the working tool/result or the face, large (≥ ~40% of the height); at most 3 elements: subject, text, one accent or logo.
5. Show the real thing: a zoomed crop of the UI or output, a before/after, or one hard number; never a full-screen screenshot with tiny text.
6. The face is optional (data are mixed for small channels): sharp, expressive, matching the video's tone, placed to the side; pick it from a webcam contact sheet.
7. Text: 2–4 Italian words (5 at most), 1–2 lines, uppercase heavy OFL font (Anton, Archivo Black, Bebas Neue, Montserrat/Inter 800–900), white or yellow with a dark outline, contrast ≥ 4.5:1.
8. The text complements the title (outcome, number, stakes) and never repeats it; title and thumbnail tell one story.
9. Curiosity, not clickbait: everything shown must happen in the video, early; no sexual, gory, shock or vulgar content.
10. Keep text, numbers, logos and eyes out of the bottom-right corner (duration badge) and ≥ 20 px from the edges.
11. For technical viewers stay clean and restrained: controlled palette, no red arrows or circles, no fake shock faces.
12. Reuse one channel template (fonts, palette, logo spot) across videos; vary the content, not the system.
13. Check every variant at 168×94, 320×180 and 360×202, plus grayscale, with a mock badge: text readable and subject clear at 168×94, or cut, enlarge, simplify and re-render.
14. Deliver thumb_A/B/C.jpg, the preview sheet and the rationale (concept, words, source timestamps); never upload: the user chooses.
15. Custom thumbnails need a phone-verified channel; Test & compare (winner by watch time) needs advanced features and runs only from a computer.

## 6. Open questions and uncertainties

- The webcam overlay size in the OBS layout is unknown: it decides whether a face crop is usable or the user should add a short full-screen "thumbnail expressions" scene or the Source Record plugin. Whether the user wants their face in thumbnails at all is undecided.
- No channel brand exists yet (colours, font, logo, layout): the first thumbnails will set it.
- Is YouTube's own Ask Studio thumbnail generation acceptable? It runs on YouTube's side after upload but is a generative service, which the constraint as written excludes.
- Test & compare needs advanced features; without them, swapping thumbnails over time is a sequential comparison, which YouTube says can give different results than a concurrent test.
- Spec drift: the English page lists JPG or PNG while the Italian one adds GIF; the 50 MB limit applies to computer uploads only. On-screen sizes and the badge size are third-party estimates; Creator Insider videos were not reviewed (video only).
- Evidence is observational and mixed on faces and word counts; none is specific to tech, software or Italian-language channels; the vidIQ page could not be read directly.
- Using third-party product logos (for example of the AI tools demoed) was not researched for trademark or brand-guideline limits.
- Untested here: rembg on Python 3.14 (its README says < 3.14 although onnxruntime 1.31.0 ships 3.14 wheels) and its GPU path; scene and blur thresholds on real screencasts; `file://` font loading in Edge.

[h72431]: https://support.google.com/youtube/answer/72431?hl=en
[h72431it]: https://support.google.com/youtube/answer/72431?hl=it
[h9890437]: https://support.google.com/youtube/answer/9890437?hl=en
[h9229980]: https://support.google.com/youtube/answer/9229980?hl=en
[h7628154]: https://support.google.com/youtube/answer/7628154?hl=en
[h16391400]: https://support.google.com/youtube/answer/16391400?hl=en
[h13861714]: https://support.google.com/youtube/answer/13861714?hl=en
[h12340300]: https://support.google.com/youtube/answer/12340300?hl=en
[blogtv]: https://blog.youtube/news-and-events/new-features-to-help-creators/
