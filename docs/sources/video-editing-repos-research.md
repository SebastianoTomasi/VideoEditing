# Open-source video editing: tools and patterns for a small agent-driven editor

Web research, read-only, done on **2026-10-10**. It surveys open-source projects that remove
silence, edit video by editing a transcript, let a coding agent edit video, describe timelines
declaratively, or add cheap screencast polish, and it checks the ffmpeg and Whisper facts that a
small local system would rely on. Target workflow: Italian, single-speaker OBS screencasts
(~18 min raw, 7–11 min edited) with flubs and retakes removed, silent waits sped up or cut, and
separately recorded scenes joined, on Windows 11 with ffmpeg 8.0.1, Python 3.14, uv, Node 24 and
an NVIDIA GPU.

Conventions: ★ = GitHub stars on 2026-10-10 (rounded) and "pushed" = last push, both from
`https://api.github.com/repos/<owner>/<repo>` unless another link is given. **Stale** = no
commits for more than 18 months. Each row links the pages that support it; "unverified" marks
what could not be checked. Nothing was installed or run: behaviour notes come from docs and
source code. `ayosec.github.io` links are a per-filter mirror generated from the official
FFmpeg 8.0 docs, used where the single-page ffmpeg.org manual was too long to fetch.

## 1. Silence / dead-air removal and speed-up

| Project | ★ · pushed · license | Core idea; input → output | How it is driven | Deps · Windows | Simplest idea to borrow |
|---|---|---|---|---|---|
| [auto-editor](https://github.com/WyattBlue/auto-editor) | 5.5k · 2026-10-10 · Unlicense; release 31.7.2 of 2026-10-03 ([API](https://api.github.com/repos/WyattBlue/auto-editor/releases/latest)) | Labels each timebase unit active/inactive (default: peak ≥ 0.04 of full scale; also motion, black, subtitle, word methods), then cuts, speeds or exports it. Media or timeline file → rendered media, NLE project or timeline ([ref/edit](https://auto-editor.com/ref/edit)) | `--margin 0.2s` default, `0.3s,1.5sec` = before,after; `-w:0 speed:8` speeds inactive parts with pitch kept (atempo chain); manual `--cut`, `--keep`, `--set-speed SPEED,START,STOP` in frames or with `sec`; `--edit none` = ranges only; `--preview` dry run; `--export premiere`, `resolve`, `resolve-fcp7`, `final-cut-pro`, `shotcut`, `kdenlive`, `clip-sequence`, `v1`–`v3` ([options](https://auto-editor.com/ref/options), [ranges](https://auto-editor.com/docs/range-syntax), [export skill](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/skills/auto-editor-export/SKILL.md), [audio.nim](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/src/render/audio.nim)) | Nim; renders in-process through its own bindings to a statically built FFmpeg 9.0.2 with x264, whisper.cpp and NVENC headers ([ffmpeg.nim](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/src/ffmpeg.nim), [ae.nimble](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/ae.nimble)). One unsigned Windows .exe; no longer on pip ([installing](https://auto-editor.com/installing)). **Licence-key gate:** without a key, multi-source renders shrink to 720×576 and multi-source exports are refused; one source renders free up to 3200×1800 ([license.nim](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/src/license.nim), [31.4.0 notes](https://github.com/WyattBlue/auto-editor/releases/tag/31.4.0)) | The v1 timeline, documented as stable for other programs: `{"version":"1","source":"in.mp4","timebase":"30/1","chunks":[[start,end,speed],…]}`, contiguous ticks from 0, speed 0 = cut; `auto-editor x.v1 -o out.mkv` renders it ([v1](https://auto-editor.com/docs/v1)) |
| [jumpcutter](https://github.com/carykh/jumpcutter) | 3.1k · 2024-02-28 · MIT · **abandoned** (README: not actively updated) | A frame is loud if its chunk peak ÷ file peak ≥ `silent_threshold` 0.03; keeps `frame_margin` 1; silent chunks play at `silent_speed` 5, loud at `sounded_speed` 1 ([source](https://raw.githubusercontent.com/carykh/jumpcutter/master/jumpcutter.py)) | `python jumpcutter.py --input_file in.mp4 --silent_speed 999999` (999999 ≈ jump cut) | Dumps every frame to JPG, stretches audio with the audiotsm phase vocoder; `shell=True` command strings break on paths with spaces | A 400-sample fade-in/out at every chunk edge |
| [unsilence](https://github.com/lagmoellertim/unsilence) | 595 · 2023-03-28 · MIT · stale | `silencedetect=noise=-35dB:d=0.5`, then each interval re-encoded with `setpts`, one `atempo` and `volume`, joined with the concat demuxer `-c copy`; no fades ([detect](https://raw.githubusercontent.com/lagmoellertim/unsilence/master/unsilence/lib/detect_silence/DetectSilence.py), [render](https://raw.githubusercontent.com/lagmoellertim/unsilence/master/unsilence/lib/render_media/RenderIntervalThread.py)) | `unsilence in.mp4 out.mp4 -as 1 -ss 6`; defaults `-sl -35`, `-stt 0.5`, `-sit 0.3`, `-st 0.25`, `-sv 0.5` ([args](https://raw.githubusercontent.com/lagmoellertim/unsilence/master/unsilence/command_line/ParseArguments.py)) | `pipx install unsilence`; README advises Windows Terminal | Interval clean-up: merge short intervals, move each boundary 0.25 s into the silence |
| [Remsi](https://github.com/bambax/Remsi) | 179 · 2022-09-16 · MIT · stale | Turns `silencedetect` output into ONE ffmpeg command: `select='between(t,a,b)+…',setpts=N/FRAME_RATE/TB` and `aselect=…,asetpts=N/SR/TB` ([remsi.py](https://raw.githubusercontent.com/bambax/Remsi/master/remsi.py)) | `ffmpeg -i IN -af silencedetect=n=-50dB:d=1 -f null - 2>&1 \| python remsi.py > cmd` | Python + ffmpeg; no margin, no fades | Generate the whole render as one command |
| [video-remove-silence](https://github.com/excitoon/video-remove-silence) | 114 · 2020-09-11 · MIT · abandoned | Compresses each silence instead of cutting it: new length = `c + s·log(d+1) + l·d` (defaults keep 10 %), crossfaded edges ([script](https://raw.githubusercontent.com/excitoon/video-remove-silence/master/video-remove-silence)) | `--threshold-level -40 --threshold-duration 0.2` | Ships a `.cmd` wrapper | A duration-mapping function for waits |
| [Silero VAD](https://github.com/snakers4/silero-vad) | 10.4k · v6.2.3 of 2026-09-23 · MIT | Neural speech timestamps; an alternative to loudness thresholds when typing or fan noise sits above the threshold (inference) | `get_speech_timestamps(read_audio(p), load_silero_vad(), return_seconds=True)`; defaults threshold 0.5, `min_silence_duration_ms` 100, `speech_pad_ms` 30 ([utils_vad.py](https://raw.githubusercontent.com/snakers4/silero-vad/master/src/silero_vad/utils_vad.py)) | torch ≥ 1.12 or ONNX extras | Invert the speech timestamps to get the waits |

## 2. Transcript-based editing and word timestamps

| Project | ★ · pushed · license | Core idea; input → output | How it is driven | Deps · Windows | Simplest idea to borrow |
|---|---|---|---|---|---|
| [AutoCut](https://github.com/mli/autocut) | 7.8k · 2024-10-05 · Apache-2.0 · stale | Whisper → `.srt` + `.md` checklist; tick the lines to keep; `autocut -c` renders with MoviePy, merging kept sentences less than 0.5 s apart ([cut.py](https://raw.githubusercontent.com/mli/autocut/main/autocut/cut.py)) | The `.md` holds a "done editing" checkbox, a `<video>` tag, then one `- [ ] [index,MM:SS] text` line per subtitle, parsed with `- +\[([ xX])\] +(.*)` ([utils.py](https://raw.githubusercontent.com/mli/autocut/main/autocut/utils.py), [fixture](https://raw.githubusercontent.com/mli/autocut/main/test/content/test_md.md)); flags `-t`, `-c`, `-d` (watch a folder), `--lang` (default zh, Italian listed), `--whisper-mode whisper\|faster\|openai` ([main.py](https://raw.githubusercontent.com/mli/autocut/main/autocut/main.py)) | pip `autocut-sub`, Docker CPU/CUDA images. Probably broken today (read, not run): imports `moviepy.editor`, removed in MoviePy 2 ([v2 notes](https://zulko.github.io/moviepy/getting_started/updating_to_v2.html)); `faster` mode passes language names that faster-whisper rejects | A Markdown checklist of sentences that both a person and an agent can edit |
| [videogrep](https://github.com/antiboredom/videogrep) | 3.5k · 2024-04-19 · "Anti-Capitalist" MIT variant (not OSI) · stale | Regex search over transcripts → supercut; word timings from Vosk ([transcribe.py](https://raw.githubusercontent.com/antiboredom/videogrep/master/videogrep/transcribe.py)) | `videogrep --input v.mp4 --search 'x' --search-type fragment -p 0.1`; `.mpv.edl`, `.m3u` or FCP `.xml` outputs instead of a render ([videogrep.py](https://raw.githubusercontent.com/antiboredom/videogrep/master/videogrep/videogrep.py)) | MoviePy < 2, Vosk; Italian Vosk models exist ([models](https://alphacephei.com/vosk/models)) | Preview without rendering: an mpv EDL (`# mpv EDL v0` + `path,start,duration` lines, played with `mpv edl://…`) |
| [audapolis](https://github.com/bugbakery/audapolis) | 1.9k · v0.3.1 of 2025-11-26 · AGPL-3.0 · low activity | Word-processor-style editor for spoken media with local Vosk; exports OTIO ([otio.py](https://raw.githubusercontent.com/bugbakery/audapolis/main/server/app/otio.py)) | GUI only | Electron 13, Python < 3.11 server; Windows .exe | An edit is a list of `{source_file, source_start, length}` clips |
| [Kdenlive speech editor](https://docs.kdenlive.org/en/effects_and_filters/speech_to_text.html) | 5.8k (GitHub mirror) · 26.08.0 of 2026-08-31 · GPL-3.0 | VOSK or Whisper transcript; delete selected text, insert a selection in the timeline, remove non-speech zones (VOSK only) | GUI | Windows builds | Explicit "no speech" entries in the transcript |
| [FunClip](https://github.com/modelscope/FunClip) | 6.4k · 2026-10-08 · MIT | FunASR (Chinese/English); stage 2 keeps the quoted text spans ([videoclipper.py](https://raw.githubusercontent.com/modelscope/FunClip/main/funclip/videoclipper.py)) | `--stage 2 --dest_text 'a#b'` | No Italian | The agent quotes the text to keep; a tool resolves the times |
| [Rescript](https://github.com/wassgha/rescript) | 922 · 2026-10-05 · PolyForm Noncommercial | Browser/Electron text editor over Whisper word timings; filler and ≥ 0.3 s pause removal; FCPXML, Premiere/Resolve XML, AAF export ([README](https://raw.githubusercontent.com/wassgha/rescript/main/README.md)) | GUI | — | One silence rule over gaps between words |

| Engine | ★ · status · license | Word timing | Italian | Notes for this setup |
|---|---|---|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 25.8k · v1.2.1, pushed 2026-10-10 · MIT | `word_timestamps=True` → `segment.words` with `start`, `end`, `word`; cross-attention + DTW ([transcribe.py](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/faster_whisper/transcribe.py)) | Whisper multilingual | `vad_filter=True` uses Silero with defaults `min_silence_duration_ms=2000`, `speech_pad_ms=400` ([vad.py](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/faster_whisper/vad.py)), close to the ~2 s retake pause, so set them explicitly. GPU needs cuBLAS and cuDNN 9 for CUDA 12 (Windows DLLs via Purfview's whisper-standalone-win, [README](https://github.com/SYSTRAN/faster-whisper)); ctranslate2 4.8.2 ships Python 3.14 Windows wheels ([PyPI](https://pypi.org/pypi/ctranslate2/4.8.2/json)) |
| [WhisperX](https://github.com/m-bain/whisperX) | 24.5k · v3.8.6 of 2026-05-25 · BSD-2-Clause | faster-whisper + VAD + wav2vec2 forced alignment; JSON `segments[].words[]` with `word`, `start`, `end`, `score` ([alignment.py](https://raw.githubusercontent.com/m-bain/whisperX/main/whisperx/alignment.py)) | Default aligner `VOXPOPULI_ASR_BASE_10K_IT` (torchaudio; fine-tuned on 91 h of Italian, CC BY-NC 4.0, no WER published, [torchaudio](https://docs.pytorch.org/audio/stable/generated/torchaudio.pipelines.VOXPOPULI_ASR_BASE_10K_IT.html)); `jonatasgrosman/wav2vec2-large-xlsr-53-italian` reports WER 9.41 on Common Voice 6 ([card](https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-italian)) | `requires-python >=3.10,<3.14`, so not Python 3.14 ([pyproject](https://raw.githubusercontent.com/m-bain/whisperX/main/pyproject.toml)). README limits: tokens like "2014." get no timing of their own (current code interpolates them), overlapping speech; Windows GPU needs CUDA toolkit 12.8 ([README](https://github.com/m-bain/whisperX)) |
| [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped) | 2.9k · pushed 2026-09-28 · AGPL-3.0 (LICENSE file) | DTW on cross-attention, per-word confidence; `detect_disfluencies=True` inserts `[*]` tokens ([README](https://raw.githubusercontent.com/linto-ai/whisper-timestamped/master/README.md)) | Multilingual | `[*]` is a cheap flub candidate |
| [stable-ts](https://github.com/jianfch/stable-ts) | 2.3k · **archived** 2026-05-30 · MIT | Timestamp stabilisation, silence suppression, `align()` of known text | Multilingual | Development paused |
| [CrisperWhisper](https://github.com/nyrahealth/CrisperWhisper) | 1.4k · pushed 2026-09-22 · code MIT, weights non-commercial | Verbatim: keeps fillers, repetitions, false starts ([README](https://raw.githubusercontent.com/nyrahealth/CrisperWhisper/main/README.md)) | **Unverified** (model card lists en, de) | Fast path is Linux-first |
| [auto-editor whisper](https://auto-editor.com/docs/subcommands/whisper) | part of auto-editor | whisper.cpp ggml models; `--split-words` gives one word per cue; text/srt/json ([skill](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/skills/auto-editor-transcribe/SKILL.md)) | `-l LANG` (docs show only en, ja) | Same binary as the cutter; a sidecar `.srt` plus `--edit subtitle` keeps only subtitled parts |
| [ffmpeg `whisper` filter](https://ffmpeg.org/ffmpeg-filters.html#whisper) | new in FFmpeg 8.0 ([Changelog](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog)) | whisper.cpp; `format=text\|srt\|json`, `use_gpu` (default true), `vad_model`; no prompt option ([options](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Audio/whisper.html)) | `language` option | Needs a build with whisper: gyan.dev has it in *full* builds only ([builds](https://www.gyan.dev/ffmpeg/builds/)); BtbN removed it ("Disable Whisper", [commit](https://github.com/BtbN/FFmpeg-Builds/commit/bfcf840)) |

Transcript caveats that matter for retakes: whisper-timestamped's README warns that Whisper
tends to leave out disfluencies (fillers, hesitations, repetitions) and that an untranscribed
disfluency shifts the next word's start; the Whisper paper lists repeat loops and hallucinated
text among its failure modes ([paper](https://ar5iv.labs.arxiv.org/html/2212.04356)), which VAD
reduces ([WhisperX README](https://github.com/m-bain/whisperX)). Agent projects therefore treat
ASR word boundaries as approximate: clean-cut lists four failure modes of word times (late
start, inflated span, merged repeat, phantom token) and open-edit only cuts where a probe
measured a gap (section 3). No source tests whether Whisper keeps both copies of a sentence
repeated after a ~2 s pause.

## 3. Agent-driven editing (the pattern to copy)

| Project | ★ · pushed · license | What the agent does; input → output | Instruction files and edit file | Deps · Windows | Simplest idea to borrow |
|---|---|---|---|---|---|
| [video-use](https://github.com/browser-use/video-use) (browser-use) | **28.6k** · 2026-10-08 · MIT · created 2026-04-12 | Folder of takes → `<videos>/edit/final.mp4`. Transcribe each take once (word-level, diarised) → pack into `takes_packed.md` → the agent proposes a 4–8 sentence plan and waits for approval → writes `edl.json` → `render.py` → self-evaluates every cut, at most 3 passes ([README](https://github.com/browser-use/video-use)) | One `SKILL.md` (~400 lines): 12 hard rules, an 8-step process, cut craft, EDL format, `project.md` session memory, anti-patterns ([SKILL.md](https://raw.githubusercontent.com/browser-use/video-use/main/SKILL.md)). EDL: `{version, sources{name: path}, ranges[{source, start, end, beat, quote, reason}], grade, overlays[], subtitles, total_duration_s}`. Packed lines look like `[002.52-005.36] S0 text`, phrases split on ≥ 0.5 s silence ([pack_transcripts.py](https://raw.githubusercontent.com/browser-use/video-use/main/helpers/pack_transcripts.py)) | Python (requests, librosa, matplotlib, pillow, numpy), ffmpeg, **ElevenLabs Scribe API (cloud)** ([transcribe.py](https://raw.githubusercontent.com/browser-use/video-use/main/helpers/transcribe.py)); Scribe lists Italian in its ≤ 5 % WER tier ([ElevenLabs](https://elevenlabs.io/docs/capabilities/speech-to-text)). Install docs cover macOS/Linux ([install.md](https://raw.githubusercontent.com/browser-use/video-use/main/install.md)); open Windows PRs fix ffmpeg filter-path escaping, UTF-8 console crashes and `uv sync` symlink privilege ([issues](https://github.com/browser-use/video-use/issues?q=windows)). No speed field in the EDL (a PR proposes one) | Closest existing match to this workflow: packed transcript + JSON EDL + hard rules + `timeline_view.py` (filmstrip, RMS waveform and word labels in one PNG, [source](https://raw.githubusercontent.com/browser-use/video-use/main/helpers/timeline_view.py)). Replace Scribe with local word-level ASR |
| [takecut](https://github.com/Abdalkaderdev/takecut) | **0** · 2026-10-09 (created 2026-10-08) · MIT | Local skills for Claude Code, Codex, Gemini CLI, Cursor: faster-whisper transcript (prompted with Italian fillers) → `cleanup.py` proposes drops (silence, pause, filler, retake, stutter) → EDL JSON → render with fades and loudnorm ([cleanup.py](https://raw.githubusercontent.com/Abdalkaderdev/takecut/main/skills/video-cleanup/scripts/cleanup.py)) | EDL: `{sources, transcripts, drop[{start, end, reason, text}], fade: 0.015, loudnorm: true, lufs: -16}`. Retake rule: consecutive segments ≤ 6 s apart, similarity ≥ 0.8 or the earlier is a prefix of the later → cut the earlier, keep the later; Italian fillers `ehm, eh, uhm, mmm` | uv, faster-whisper, ffmpeg; its docs install ffmpeg on Windows with `winget install Gyan.FFmpeg` (not checked) | Almost this exact workflow, but two days old and untested |
| [open-edit](https://github.com/veedstudio/open-edit) (VEED) | 1.6k · 2026-10-07 · Apache-2.0 | Clips → MP4 under `runs/<key>/`: transcribe → `speech-probe` (noise floor, real gaps) → `edl.json` → `apply-edl` (one encode, frame-snapped, `--crossfade <ms>`) → `retime-transcript` ([CUT.md](https://raw.githubusercontent.com/veedstudio/open-edit/main/.claude/skills/open-edit/CUT.md)) | A short `SKILL.md` router sends the agent to step sheets (`CUT.md`, `TRANSCRIPTION.md`, …). EDL: `{sources{id: path}, transcripts?, ranges[{source, start, end, note}]}`. Rules: measure cut points rather than taking them from the transcript; no gap, no cut; never re-transcribe the assembled cut; refuse sources whose fps or colour differ | Node ≥ 20.18, ffmpeg, VEED transcription or local WhisperX; README documents Windows 10+ and Windows CI | "Two clocks": the transcript decides what to cut, a silence probe decides exactly where |
| [claude-youtube-editor](https://github.com/hassancs91/claude-youtube-editor) (`clean-cut` skill) | 328 · 2026-08-18 · MIT | Talking head → word transcript (AssemblyAI, cloud), takes split on gaps > 0.8 s → `cuts.json` → 720p previews → `verify_cut.py` → human audit in a local editor (hard gate) → final render ([clean-cut](https://raw.githubusercontent.com/hassancs91/claude-youtube-editor/main/.claude/skills/clean-cut/SKILL.md)) | `cuts.json` = `{project, clip_order[], clips[{id, file, duration, keeps[{s, e, text, gap}], cuts[{s, e, text, note, cat}], fluff_suggestions[]}], styles, flags}`, `cat` ∈ retake, false_start, filler, long_pause, dead_air. Retakes: grep for spoken slates, keep the winning take, cut the first copy of a doubled phrase; compress pauses to ~0.45–0.5 s | Python 3.10+, Node 18+, ffmpeg; Windows venv commands in README | Cut categories, and re-transcribing the preview to diff it against the words meant to be kept |
| [cut-video](https://github.com/louisedesadeleer/cut-video) (Tella) | 108 · 2026-07-09 · MIT | One `SKILL.md`: proxy → Whisper → Montreal Forced Aligner → cut list → re-transcribe each kept window to check its edges → render ([SKILL.md](https://raw.githubusercontent.com/louisedesadeleer/cut-video/main/SKILL.md)) | **Whole-line retakes:** fuzzy 4-gram similarity > 0.7 within 60 s, plus matching sentence openers; keep the last take unless it is flubbed. Silence threshold = noise floor (10th-percentile RMS) + 6 dB. Render: `trim`/`atrim` + `concat` in a filter-script file; the author advises against `select`; above ~500 trims, stream-copied segments + concat demuxer | macOS-oriented (VideoToolbox, Homebrew), English defaults | The retake rule fits "pause, then repeat the whole sentence" |
| [ButterCut](https://github.com/barefootford/buttercut) | 601 · 2026-09-23 · PolyForm Noncommercial 1.0.0 with a commercial-output exception (README; API says NOASSERTION) | Footage "libraries" → WhisperX transcripts (CPU, float32) → cut YAML → `export.rb --editor fcpx\|premiere\|resolve` → XML opened in the NLE; no rendering ([transcribe_job.rb](https://raw.githubusercontent.com/barefootford/buttercut/main/lib/buttercut/transcribe_job.rb)) | `CLAUDE.md` → `AGENTS.md` (never modify source video; flag judgment calls; change data only through the Library class) + 16 skills. Cut YAML: `clips[{source_file, in_point, out_point, mute?, dialogue, visual_description}]` in `HH:MM:SS.ss`; transcript JSON is the timing truth and is never edited ([schema](https://raw.githubusercontent.com/barefootford/buttercut/main/skills/cut/cut_yaml_schema.md)) | Ruby + Python + ffmpeg; README: Apple Silicon focus, Windows "not a priority"; AGENTS.md mentions Windows via Git Bash | Hand the rough cut to an NLE as XML for human finishing |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | **66.1k** · 2026-10-03 · AGPL-3.0 | Large agentic production system: YAML pipelines (e.g. `screen-demo`), 100+ tools, Remotion/HyperFrames/ffmpeg renderers | Stub `CLAUDE.md`, `AGENTS.md`, `CODEX.md`… all point to one `AGENT_GUIDE.md`; `edit_decisions` JSON checked by a JSON Schema, cuts `{id, source, in_seconds, out_seconds, speed?, reason?}` ([guide](https://raw.githubusercontent.com/calesthio/OpenMontage/main/AGENT_GUIDE.md)) | Heavy; PowerShell setup path in README | Validate the edit file with a JSON Schema; per-cut `speed` |
| [auto-editor skills](https://github.com/WyattBlue/auto-editor/tree/master/skills) | (auto-editor) | `npx skills add WyattBlue/auto-editor` installs `auto-editor`, `-effects`, `-export`, `-transcribe` | Choose the edit method, set pace with `--margin`/`--smooth`, run `--preview` before a long render ([SKILL.md](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/skills/auto-editor/SKILL.md)) | Windows binary | A ready instruction sheet for the cutter |
| [Diffusion Studio editor](https://github.com/diffusionstudio/editor) | 3.3k · v0.210.0 of 2026-10-08 · MPL-2.0 | Desktop editor driven over MCP or a `diffusion` CLI that answers in JSON; projects are JSX | Tiny skill → in-app guide: `probe`, `waveform`, `filmstrip`, `transcribe`, `grab`; `check` + `capture` after each stage; render only when asked ([skill](https://raw.githubusercontent.com/diffusionstudio/skills/main/editor/SKILL.md)) | Windows x64 installer | Cheap ways for the agent to look at footage |
| [HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen) | **60.3k** · 2026-10-10 · Apache-2.0 | HTML + GSAP → MP4 with headless Chrome + ffmpeg; overlays and titles, not cutting | Router skill + on-demand skills; `hyperframes snapshot --at <sec>` checks a frame | Node 22+, Chrome; Windows unverified | A frame snapshot at a timestamp as a check |
| [Remotion skills](https://github.com/remotion-dev/skills) | 5.0k · 2026-10-07 · no LICENSE file seen; Remotion is free for individuals and companies of ≤ 3 employees ([license](https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md)) | 12 skills for React-based video (`npx skills add remotion-dev/skills`, [docs](https://www.remotion.dev/docs/ai/skills)) | `/remotion-best-practices` routes to focused skills; captions as `Caption {text, startMs, endMs, timestampMs, confidence}` via `@remotion/whisper-webgpu` ([captions](https://raw.githubusercontent.com/remotion-dev/skills/main/skills/remotion-captions/SKILL.md)) | Node | A router skill over small focused sheets |
| [VideoDB Director](https://github.com/video-db/Director) | 1.6k · 2026-01-23 · MIT | Chat UI + reasoning engine orchestrating 20+ agents on the VideoDB cloud | Agents are Python classes registered in a handler; needs `VIDEO_DB_API_KEY` + an LLM key ([env sample](https://raw.githubusercontent.com/video-db/Director/main/backend/.env.sample)) | Windows via WSL | Little for a local system |

Also seen: [FableCut](https://github.com/ronak-create/FableCut) (715★, MIT): one `project.json`
timeline edited by both user and agent, with a `revision` counter;
[everything-claude-code `video-editing`](https://raw.githubusercontent.com/affaan-m/everything-claude-code/main/skills/video-editing/SKILL.md):
a `cuts.txt` of `start,end,label` rows cut with `-ss/-to -c copy` (so on keyframes) after
`silencedetect=noise=-30dB:d=2`; Kinocut, formerly [mcp-video](https://github.com/KyaniteLabs/mcp-video)
(199★, Apache-2.0): MCP tools with dry runs that refuse to overwrite an input.

How these projects instruct the agent:
- **Router plus step sheets.** A short `SKILL.md`/`CLAUDE.md` lists the steps and points to one
  sheet per step; per-agent files (`AGENTS.md`, `CODEX.md`) are stubs pointing to one guide.
- **A work folder per video**, never the tool's folder and never the sources (`<videos>/edit/`,
  `runs/<key>/`).
- **The edit file is a JSON list of ranges in source seconds** (`{source, start, end, reason}`),
  sometimes with `speed`, a cut category, or the quoted words.
- **Two clocks:** the word transcript decides *what* to cut; silence or energy measurement
  decides exactly *where*.
- **Approval gates:** a plain-language plan before cutting, the user's go before the final render.
- **Self-checks without ears:** low-res preview, filmstrip/waveform images at each cut, ffprobe
  duration against the EDL, loudness numbers, re-transcribe and diff.

## 4. Declarative timelines and interchange

| Project / format | ★ · recency · license | Core idea; input → output | How it is driven | Deps · Windows | Simplest idea to borrow |
|---|---|---|---|---|---|
| auto-editor timelines ([v1](https://auto-editor.com/docs/v1), [v2](https://auto-editor.com/docs/v2), [v3](https://auto-editor.com/docs/v3)) | see §1 | v1: one source, linear, contiguous `[start,end,speed]` ticks, stable; v2: `effects` list + `clips [start,end,effectIdx]`, gaps cut; v3: multi-source layers `{src,start,dur,offset,stream,effects}`, only partially stable | `auto-editor edit.v1 -o out.mp4`; `--export v1` to inspect an automatic edit | One binary | Write v1 directly and get rendering and NLE export for free |
| [editly](https://github.com/mifi/editly) | 5.5k · last commit 2025-02-20 ([commits](https://github.com/mifi/editly/commits/master)) · MIT · stale | JSON5 spec of clips with layers (`{type:"video", path, cutFrom, cutTo}`) → MP4 via ffmpeg; a clip whose `duration` is shorter than its cut is sped up to fit ([README](https://raw.githubusercontent.com/mifi/editly/master/README.md)) | `editly spec.json5 --keep-source-audio --out out.mp4`; transitions on and source audio off by default | Native `canvas` and `gl` have no prebuilt Windows binaries for Node 24 (ABI 137): canvas 2.11.2 stops at ABI 120, gl 8.1.6 at 127 ([canvas](https://api.github.com/repos/Automattic/node-canvas/releases/tags/v2.11.2), [gl](https://api.github.com/repos/stackgl/headless-gl/releases/tags/v8.1.6)) | A flat `{path, cutFrom, cutTo}` list in seconds |
| [MoviePy](https://github.com/Zulko/moviepy) | 15.0k · v2.2.1 of 2025-05-21 · MIT | Python API: `subclipped`, `with_section_cut_out`, `with_speed_scaled`, `vfx.MultiplySpeed`, `afx.AudioFadeIn/Out`, `concatenate_videoclips` ([Clip API](https://zulko.github.io/moviepy/reference/reference/moviepy.Clip.Clip.html)) | Python script | Frames pass through numpy, slower than ffmpeg (README); PyPI classifiers stop at 3.11 ([PyPI](https://pypi.org/pypi/moviepy/json)) | Its verbs as vocabulary only |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | 2.0k · v0.18.1 of 2025-11-09 · Apache-2.0 | `.otio` JSON: Timeline → Stack → Tracks → Clips/Gaps; `source_range` in frames at a rate; speed as `LinearTimeWarp.time_scalar` ([schema](https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-serialized-schema.html)) | Core reads/writes only `.otio`/`.otioz`/`.otiod`; `pip install OpenTimelineIO-Plugins` adds cmx3600, fcp (FCP7 XML), aaf…; FCPX XML is separate ([PyPI](https://pypi.org/pypi/OpenTimelineIO-Plugins/json)) | No cp314 Windows wheels for 0.18.1 ([files](https://pypi.org/pypi/OpenTimelineIO/0.18.1/json)); a hand-written `.otio` needs no library | One JSON file for Resolve ≥ 18.5 (export documented, import only via a manual mirror), Premiere (beta, Oct 2024) and Kdenlive ≥ 25.04 ([OTIO wiki](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/wiki/AWS-Picchu-Edit-OTIO-Conversion-Notes), [Adobe](https://community.adobe.com/t5/premiere-pro-beta-discussions/now-in-beta-otio-import-and-export/m-p/14985932), [Kdenlive](https://kdenlive.org/news/releases/25.04.0/)) |
| [LosslessCut](https://github.com/mifi/lossless-cut) | 44.4k · v3.69.0 of 2026-06-04 · GPL-2.0 | Keyframe (lossless) cutting and merging; smart cut is experimental; detection via `silencedetect`, `blackdetect`, `select='gt(scene,X)'` ([ffmpeg.ts](https://raw.githubusercontent.com/mifi/lossless-cut/master/src/main/ffmpeg.ts)) | Imports CSV, CMX3600 EDL, FCP7 XML, FCPXML, OTIO, SRT…; exports CSV/TSV/SRT/chapters ([menu.ts](https://raw.githubusercontent.com/mifi/lossless-cut/master/src/main/menu.ts)); CSV = `start,end,label` in seconds ([docs](https://raw.githubusercontent.com/mifi/lossless-cut/master/docs/index.md)); experimental `--http-api` on 127.0.0.1:8080 ([api.md](https://raw.githubusercontent.com/mifi/lossless-cut/master/docs/api.md)) | Windows `.7z` or Microsoft Store ([installation](https://raw.githubusercontent.com/mifi/lossless-cut/master/docs/installation.md)) | The agent writes a 3-column CSV; the user reviews the segments in a GUI |
| [MLT](https://github.com/mltframework/mlt) / `melt` | 1.9k · v7.42.0 of 2026-10-03 · LGPL-2.1 | MLT XML is the Shotcut and Kdenlive project format; `melt edit.mlt -profile … -consumer avformat:out.mp4` renders it headlessly ([melt](https://www.mltframework.org/docs/melt/)); `timewarp` producer for speed | `<producer>` + `<playlist><entry in out>`; in/out accept clock strings ([blog](https://mltframework.org/blog/time_properties/)) | melt.exe ships inside Shotcut and Kdenlive on Windows (forum sources); default profile is dv_pal, so pass one | One file both renders and opens in Shotcut |
| CMX3600 EDL · FCP7 XML · FCPXML | formats | EDL: plain text, no frame rate, one video track in the OTIO adapter ([adapter](https://github.com/OpenTimelineIO/otio-cmx3600-adapter)); FCP7 XML: root `xmeml`, Apple doc retired ([Apple](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/Basics/Basics.html)); FCPXML: rational-second times ([Apple](https://developer.apple.com/documentation/professional-video-applications/timing-attributes.md)) | Generated by auto-editor `--export`, OTIO plugins, videogrep | Resolve *free* import of FCPXML/OTIO not confirmed from a primary source | Let auto-editor or OTIO write them; never hand-write XML |
| ffmpeg concat script ([formats](https://ffmpeg.org/ffmpeg-formats.html#concat-1)) | built in | `ffconcat version 1.0` + `file` / `inpoint` / `outpoint` lines: a keep-list ffmpeg reads directly | `ffmpeg -f concat -safe 0 -i list.txt …` | — | Fine for joining whole scene files; for cutting, see the keyframe caveat in §6 |

## 5. Screencast polish (cheap add-ons)

- **Loudness.** `loudnorm` defaults: I −24, LRA 7, TP −2; dynamic mode upsamples to 192 kHz, so
  set `-ar 48000` ([docs](https://ffmpeg.org/ffmpeg-filters.html#loudnorm)). Linear (pass-2)
  mode needs all four `measured_*` values, measured LRA ≤ target LRA and measured TP + offset ≤
  target TP, otherwise it silently stays dynamic; `stats_file` exists only from 8.1
  ([af_loudnorm.c 8.0](https://raw.githubusercontent.com/FFmpeg/FFmpeg/release/8.0/libavfilter/af_loudnorm.c)).
  Targets in use: video-use I −14, TP −1, LRA 11 ([render.py](https://raw.githubusercontent.com/browser-use/video-use/main/helpers/render.py));
  takecut −16 LUFS; Apple Podcasts ≈ −16 LKFS, TP ≤ −1 dBFS ([Apple](https://podcasters.apple.com/support/893-audio-requirements));
  YouTube's upload page gives no LUFS target ([YouTube](https://support.google.com/youtube/answer/1722171)),
  so the common "−14 LUFS for YouTube" figure has only secondary sources. [ffmpeg-normalize](https://slhck.info/ffmpeg-normalize/usage/cli-options/)
  (1.5k★, MIT) automates both passes.
- **Noise reduction.** `afftdn` (default `nr` 12 dB, `nf` −50 dB; documented example
  `afftdn=nr=10:nf=-40`; can sample a noise profile with `asendcmd … afftdn sn start/stop`) and
  `anlmdn` need no files ([afftdn](https://ffmpeg.org/ffmpeg-filters.html#afftdn)). `arnndn`
  needs an RNNoise model, forces 48 kHz and takes `mix` from −1 to 1; models come from
  [GregorR/rnnoise-models](https://raw.githubusercontent.com/GregorR/rnnoise-models/master/README.md)
  (`sh` = speech + recording noise; no licence file; last push 2018). Escape the drive colon in
  the path or run from the model's folder. [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet)
  (4.8k★, MIT/Apache, last push 2024-10) ships a Windows CLI in v0.5.6 (2023-08-31) with
  `-a/--atten-lim-db` to cap the reduction ([release](https://api.github.com/repos/Rikorose/DeepFilterNet/releases/latest)).
  No new denoise filter appears in the 8.0, 8.1 or 9.0 Changelogs.
- **Subtitles.** Burn with `subtitles=edit.srt:force_style='…'` (libass, in gyan essentials and
  full) ([subtitles](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/subtitles.html));
  inside a filter option `:` and `\` must be escaped, so `C\:/…` or a relative path
  ([escaping](https://ffmpeg.org/ffmpeg-filters.html#Notes-on-filtergraph-escaping)); this is what
  most of video-use's Windows PRs fix. Soft subs: MP4 needs `-c:s mov_text`, MKV takes SRT/ASS
  ([movenc.c](https://raw.githubusercontent.com/FFmpeg/FFmpeg/release/8.0/libavformat/movenc.c));
  YouTube accepts a sidecar `.srt` ([YouTube](https://support.google.com/youtube/answer/2734698)).
- **Cursor zoom.** The Screen-Studio-like tools found all zoom in post from their own capture data:
  [Cap](https://github.com/CapSoftware/Cap) (23.2k★, AGPL-3.0, Windows; zooms from recorded
  clicks; paid plan for commercial use, [cap.so](https://cap.so)),
  [OpenScreen](https://github.com/siddharthvaddem/openscreen) (39.9k★, MIT, **archived**; fork
  [EtienneLescot/openscreen](https://github.com/EtienneLescot/openscreen) 4.0k★),
  [Recordly](https://github.com/webadderallorg/Recordly) (33.1k★, AGPL-3.0, Windows 10+). Auto
  zoom on an imported OBS file is undocumented for all three. At record time in OBS,
  [obs-zoom-to-mouse](https://github.com/BlankSourceCode/obs-zoom-to-mouse) (1.2k★, last push
  2024-06, no licence) zooms a Display Capture source on a hotkey. Without cursor data, ffmpeg
  `crop`/`zoompan` with time expressions can apply zooms the agent chooses
  ([zoompan](https://ffmpeg.org/ffmpeg-filters.html#zoompan); its default output is 720p/25 fps).
- **Retakes and fillers.** No mature open-source "keep the last take" tool exists; takecut and
  cut-video (§3) implement simple similarity rules, clean-cut adds spoken slates. Commercial
  context only: [Descript](https://www.descript.com/ai/remove-retakes),
  [Gling](https://www.gling.ai/), [TimeBolt](https://www.timebolt.io/).
- **OBS-side helpers.** The "Add chapter marker" hotkey (also obs-websocket `CreateRecordChapter`)
  writes chapters into Hybrid MP4 (OBS 30.2+) and Hybrid MOV (32.0+); they are written at
  finalisation, so a crash loses them ([OBS KB](https://obsproject.com/kb/hybrid-mp4)); read
  them with `ffprobe -show_chapters -of json` ([ffprobe](https://ffmpeg.org/ffprobe.html)).
  Advanced output mode records up to 6 audio tracks, e.g. the mic alone
  ([OBS KB](https://obsproject.com/kb/multiple-audio-track-recording-guide)); auto-editor's
  `--edit audio:stream=0` analyses one track ([ref/edit](https://auto-editor.com/ref/edit)).
- **Speed and polish of renders.** NVENC: `-hwaccel cuda -hwaccel_output_format cuda … -c:v
  h264_nvenc -preset p4` ([NVIDIA](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.0/ffmpeg-with-nvidia-gpu/index.html));
  `xfade` softens jump cuts but needs constant frame rate and identical size, pixel format and
  timebase ([xfade](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/xfade.html)).

## 6. Technical facts verified

**Cutting accuracy.**
- With `-ss` as an input option ffmpeg lands on the seek point before the position; when
  transcoding with accurate seek (default) the extra part is decoded and discarded, with stream
  copy it is kept, so `-c copy` cuts start at the previous keyframe
  ([ffmpeg.html](https://ffmpeg.org/ffmpeg.html#Main-options)). The concat demuxer's `inpoint`
  works best with intra-frame codecs; otherwise the decoded output can include frames before
  it; `outpoint` is exclusive; all files need the same streams and codecs
  ([formats](https://ffmpeg.org/ffmpeg-formats.html#concat-1)).
- Robust re-encode options:
  1. **One filtergraph**: per kept range `[0:v]trim=start=A:end=B,setpts=PTS-STARTPTS[vN]` and
     `[0:a]atrim=start=A:end=B,asetpts=PTS-STARTPTS,afade=…[aN]`, then
     `[v0][a0][v1][a1]…concat=n=N:v=1:a=1[v][a]`. trim/atrim keep the original timestamps, hence
     setpts ([trim](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Video/trim.html));
     concat needs every segment to start at 0 with the same streams and parameters, resolution
     converted explicitly, and mixed frame rates give VFR output
     ([concat](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Multimedia/concat.html)).
     Extra scene files are extra `-i` inputs; per-range speed goes in the same chains.
  2. **select/aselect**: `select='between(t,A,B)+between(t,C,D)',setpts=N/FRAME_RATE/TB` and
     `aselect=…,asetpts=N/SR/TB` (Remsi); `FRAME_RATE` is defined only for constant-frame-rate
     video ([setpts](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Multimedia/setpts.html),
     [select](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Multimedia/select.html)); no
     per-range fades or speeds, and cut-video's author reports audio-sync trouble with it.
  3. **Per-range files**: re-encode each range (`-ss` before `-i`, `-t`, fades) and join with the
     concat demuxer `-c copy` (video-use's render.py, unsilence). AAC works in fixed-size
     frames, so each piece is padded and joins can show tiny gaps (trac #4676,
     [archive](https://ffmpeg.org/pipermail/ffmpeg-trac/2015-June/028610.html)); keeping
     intermediate audio as PCM and encoding once would avoid it (suggestion, untested).
- **Many segments.** Windows caps a command line at 32,767 characters
  ([CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)),
  so put the graph in a file: `-/filter_complex graph.txt` (FFmpeg ≥ 7.0,
  [Changelog](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog)); in 8.0
  `-filter_complex_script` is marked "deprecated, use -/filter_complex instead"
  ([ffmpeg_opt.c](https://raw.githubusercontent.com/FFmpeg/FFmpeg/release/8.0/fftools/ffmpeg_opt.c)).
  Reported limits: 894 parts from one input ran at < 0.01×–0.1× realtime, ~300 parts were
  noticeably faster and < 100 parts ran faster than realtime (FFmpeg 3.4.6, trac #8533,
  [archive](https://ffmpeg.org/pipermail/ffmpeg-trac/2020-February/053015.html)); trimming
  inside one big graph used ~16 GB against ~4 GB for pre-cut files on 4K input (trac #9073,
  [archive](https://ffmpeg.org/pipermail/ffmpeg-trac/2021-January/056909.html)). An 18-minute
  take with a few dozen ranges is far below these sizes.

**Clicks at cut points.** Fades in use: video-use 30 ms `afade` in/out on every segment
(hard rule, [render.py](https://raw.githubusercontent.com/browser-use/video-use/main/helpers/render.py));
auto-editor a 3 ms micro-fade at every real clip edge ([audio.nim](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/src/render/audio.nim));
takecut 15 ms; jumpcutter 400 samples; open-edit crossfades joins (`--crossfade 40` in its
example); unsilence and Remsi none. Cut placement: video-use prefers gaps ≥ 400 ms, accepts
150–400 ms after a visual check, calls < 150 ms unsafe, pads edges 30–200 ms and never cuts
inside a word ([SKILL.md](https://raw.githubusercontent.com/browser-use/video-use/main/SKILL.md));
auto-editor pads kept parts with `--margin` (default 0.2 s, `before,after` form) and merges
fragments with `--smooth` (default `0.2s,0.1s`) ([options](https://auto-editor.com/ref/options)).
`afade` defaults to the `tri` curve and, without `d`, to 44100 samples, so always pass `d`;
`acrossfade` overlaps by default ([afade](https://ffmpeg.org/ffmpeg-filters.html#afade-1)).

**Speeding up a segment.** Video: `setpts=0.5*PTS` doubles speed (docs example,
[setpts](https://ayosec.github.io/ffmpeg-filters-docs/8.0/Filters/Multimedia/setpts.html)).
Audio: `atempo` accepts 0.5–100.0; above 2 it skips samples instead of blending, so chain
instances if that matters ([atempo](https://ffmpeg.org/ffmpeg-filters.html#atempo)). auto-editor
builds an atempo chain for `speed` (pitch kept) and `asetrate`+`aresample` for `varispeed`
(pitch follows) ([audio.nim](https://raw.githubusercontent.com/WyattBlue/auto-editor/master/src/render/audio.nim));
jumpcutter time-stretches each chunk with a phase vocoder (silent 5×, sounded 1×); unsilence uses
one `atempo` per interval (silent 6×). For a silent wait, plain silence is an equally good
soundtrack (suggestion).

**silencedetect.** Logs at info level on stderr `silence_start: T` and
`silence_end: T | silence_duration: D`, prefixed by `channel: N | ` in mono mode
([af_silencedetect.c](https://raw.githubusercontent.com/FFmpeg/FFmpeg/release/8.0/libavfilter/af_silencedetect.c));
defaults `noise=-60dB` (0.001) and `d=2` s; also sets `lavfi.silence_*` metadata
([docs](https://ffmpeg.org/ffmpeg-filters.html#silencedetect)). Thresholds in the wild:
auto-editor peak 0.04 of full scale per frame (≈ −28 dBFS) with 0.2 s margin; jumpcutter 0.03
of the file's own peak, 1-frame margin; unsilence −35 dB / 0.5 s; takecut −35 dB / 0.6 s; Remsi
example −50 dB / 1 s; everything-claude-code −30 dB / 2 s; cut-video noise floor + 6 dB, 0.14 s.

**Word-level timestamps.** faster-whisper's `word_timestamps=True` takes word times from
cross-attention + DTW, as openai/whisper's [timing.py](https://raw.githubusercontent.com/openai/whisper/main/whisper/timing.py)
does (which also caps long words near pauses); with `vad_filter` times are mapped back to the
original timeline; `hallucination_silence_threshold` (off by default) skips silence around
probable hallucinations when word timestamps are on
([transcribe.py](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/faster_whisper/transcribe.py)).
WhisperX aligns each segment with a wav2vec2 model (Italian default: VoxPopuli base, above),
interpolates words it cannot align (`--interpolate_method nearest` by default) and offers
`--suppress_numerals` because wav2vec2 aligns digits poorly
([__main__.py](https://raw.githubusercontent.com/m-bain/whisperX/main/whisperx/__main__.py)). Its
paper evaluated English only: at a 200 ms collar, word precision/recall on AMI rose from
78.9/52.1 (Whisper) to 84.1/60.3 ([paper](https://arxiv.org/html/2303.00747v2)). The CrisperWhisper
paper notes that a pause before a token can be folded into its timing
([paper](https://arxiv.org/html/2408.16589v1)), one more reason to snap edges to measured silence.

## 7. Simplest ideas worth borrowing (ranked by usefulness ÷ effort)

1. **Word-level transcript per take, cached** (all projects; video-use rule "never re-transcribe").
   `transcribe.py`: ~15 lines of faster-whisper (`language="it"`, `word_timestamps=True`,
   `vad_filter=True` with explicit `min_silence_duration_ms`) → `edit/transcripts/<take>.json`;
   or expose the word timings the existing Docker transcriber may already compute.
2. **Hard rules in the instruction sheet** (video-use, open-edit, ButterCut). `EDIT.md` with ~10
   rules: never touch sources, work in `edit/`, never cut inside a word, cut only in measured
   silence, pad 30–200 ms, fade every boundary, show the plan and wait for "ok", preview before
   final, report numbers instead of claiming to have listened, append to `edit/project.md`.
3. **Packed phrase transcript as the agent's reading view** (video-use). `pack.py` writes
   `edit/takes.md`, one line per phrase split on ≥ 0.5 s gaps, e.g.
   `[012.40-015.10] (+2.1s) testo…`, so retakes and waits are visible at a glance.
4. **One list of ranges with speed as the edit file** (auto-editor v1, OpenMontage, video-use).
   The agent writes `edit/edl.json` = `[{start, end, speed, reason, quote}]` (speed 0 = cut); a
   ~30-line script converts seconds to ticks and runs `auto-editor edl.v1 -o preview.mp4`, or
   builds one `trim`/`atrim`/`concat` graph file for ffmpeg.
5. **Keep the last take** (takecut, cut-video, clean-cut). `retakes.py` lists candidates:
   consecutive phrases ≤ 6 s apart whose `difflib.SequenceMatcher` ratio is ≥ 0.8, or where the
   earlier is a prefix of the later; the agent confirms each and cuts from the earlier phrase's
   start to the later phrase's start ([difflib](https://docs.python.org/3/library/difflib.html)).
6. **Speed waits up rather than cutting them** (auto-editor `-w:0 speed:N`, jumpcutter,
   video-remove-silence). Each word gap > ~3 s becomes a range with `speed = gap / 3`, keeping
   ~0.4 s at normal speed on both sides; rendered with `setpts=PTS/S` + an `atempo` chain or silence.
7. **Join scenes losslessly first** (unsilence's join, LosslessCut merge). `ffmpeg -f concat
   -safe 0 -i scenes.txt -c copy joined.mkv` for files with identical OBS settings; everything
   after is single-source, which also avoids auto-editor's multi-source cap.
8. **Two clocks for exact edges** (open-edit, cut-video). After choosing ranges from words, move
   each edge into the nearest `silencedetect` interval on the mic track and refuse a cut where
   there is none.
9. **Mark flubs while recording**: bind OBS "Add chapter marker" to a key, record Hybrid MP4,
   read `ffprobe -show_chapters -of json`, and point the agent at the phrases before each marker.
10. **Two-pass loudnorm last**: pass 1 `loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json`, pass 2
    with the measured values, `linear=true`, `-ar 48000`; optionally `afftdn=nr=10:nf=-40` first.
11. **Self-check pack** (video-use, clean-cut, Diffusion Studio). `check.py`: ffprobe duration
    against the EDL sum, one PNG per cut (frames ±1.5 s + waveform), `ebur128` numbers, and an
    optional re-transcription of the preview diffed against the kept words.
12. **GPU previews**: 720p `h264_nvenc -preset p4` for drafts, libx264 CRF 18–20 for the final.
13. **Subtitles from the same word timings** (video-use): map
    `word.start − range.start + range.output_offset` into an SRT; upload it as a sidecar, mux it
    with `-c:s mov_text`, or burn it from a relative path.
14. **NLE hand-off only when needed**: `auto-editor joined.mkv … --export resolve` (single source
    is free), a core-only `.otio` file, or a `start,end,label` CSV for LosslessCut.
15. **Cursor zoom at record time** with obs-zoom-to-mouse; zooms in post only for windows the
    agent picks, with `crop` + `overlay=enable='between(t,T0,T1)'`.

## 8. Open questions / uncertainties

- Whether the existing transcriber can emit word or segment timings (WhisperX's aligner produces
  them; its current JSON keeps only speaker turns). Not checked; it decides whether a second
  transcriber is needed.
- Whether Whisper keeps both copies of a sentence repeated after a ~2 s pause, in Italian:
  untested anywhere. Test one real take with VAD on/off and an Italian filler prompt (takecut's
  approach); CrisperWhisper's Italian support and licence fit are unverified.
- Italian word-timing accuracy: no published numbers for WhisperX's Italian aligner; overriding
  it with the jonatasgrosman model via `--align_model` is inferred from the code, not tested.
- Python 3.14: WhisperX (< 3.14) and OpenTimelineIO (no cp314 wheels) need a uv-pinned 3.13;
  MoviePy classifiers stop at 3.11; faster-whisper's ctranslate2 is fine.
- auto-editor: NVENC in the Windows .exe, Italian `whisper -l it`, the full list and price of
  licence-gated features, and v1 speed chunks on real footage are all unverified.
- ffprobe reading OBS Hybrid MP4 chapter markers is untested; the user's ffmpeg 8.0.1 build may
  lack the `whisper` filter (check `ffmpeg -hide_banner -filters`).
- Many-segment performance figures come from FFmpeg 3.4.6 (2020) and one 4K report, not 8.0;
  the size and audibility of AAC join gaps with the concat demuxer were not measured.
- cut-video's warning about `select` and audio sync is the author's claim, not ffmpeg's docs.
- Resolve *free* import of FCPXML/OTIO, Premiere's OTIO GA version, and Kdenlive's EDL/XML import
  were not confirmed from primary sources.
- Windows behaviour of video-use (fixes pending in PRs), open-edit (README claims Windows CI),
  HyperFrames and takecut was not checked; takecut is two days old and has no users yet.
- The FFmpeg trac wiki and ticket pages were blocked by bot protection; tickets were read through
  the ffmpeg.org mailing-list archive instead.
