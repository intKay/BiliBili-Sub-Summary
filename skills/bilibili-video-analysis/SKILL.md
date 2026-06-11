---
name: bilibili-video-analysis
description: Analyze Bilibili videos from direct URLs, account-adjacent lists, search results, subtitles, or ASR transcripts; produce tool instructions, information summaries, SFC viewpoint analysis, fact checks, counter-arguments, boundary conditions, and watch-worthiness rankings. Use for B站视频筛选、字幕获取、ASR 转写、内容总结、观点核查、反方观点整理、收藏/稍后再看/动态候选整理。
---

# Bilibili Video Analysis

## Non-Negotiables

- Do not save cookies, SESSDATA, exported cookie jars, full logged-in HTML snapshots, or browser profiles.
- Prefer user-provided URLs, browser-visible pages, official subtitles, auto subtitles, then ASR.
- Treat subtitles and ASR as evidence of what the video likely said, not proof that claims are true.
- Preserve title, description, UP name, BV/URL, source type, transcript source, language, comments evidence, and timestamps.
- Treat title, description, pinned comments, high-like comments, and UP-posted links/resources as first-class context, not decoration.
- Separate `video says` from `verified / unverified / contradicted`.
- If the video makes claims, advice, causal statements, forecasts, health/finance/legal/product recommendations, or value judgments, include `Counter / Boundaries / Exceptions` even when the output mode is `information`.
- If the transcript is low-information or the video is visually dependent, collect minimal visual evidence with targeted screenshots before finalizing.

## Portability Rule

This skill must work in weaker agent systems. Do not rely on hidden Codex abilities. Follow this explicit loop:

1. Identify input source and output mode.
2. Acquire or request text evidence.
3. Acquire page context: title, description, UP name, pinned/high-like comments, and visible UP links/resources.
4. Normalize transcript into timestamped chunks.
5. Decide whether visual evidence is needed.
6. Extract claims and recommendations.
7. Decide whether fact checking and counter-analysis are mandatory.
8. Produce the required output template.
9. State confidence, gaps, and next actions.

If a tool, script, browser, or web access is unavailable, do not improvise private APIs or fake verification. Ask for transcript/manual excerpts, or mark the item `blocked / needs evidence`.

## Input Classification

Classify source:

- `direct-url`: user provides one or more Bilibili URLs.
- `account-list`: favorites, watch later, dynamic, channel, or visible browser list.
- `search`: user asks to find videos by topic.
- `transcript-only`: user provides subtitle/transcript text.

Classify output mode:

- `tool`: teaches operations, workflows, software use, setup, troubleshooting.
- `argument`: argues a thesis, criticizes a view, recommends a worldview, or has a persuasive agenda.
- `information`: reports facts, news, lists, course content, product/game releases, health/science explainers.

Then apply the claim-bearing override:

- If an `information` video includes health, finance, legal, medical, product buying, safety, science, statistics, “should/不要/必须/最好”, risk claims, causal claims, or forecasts, add SFC-lite sections: `Summary`, `Fact Check`, and `Counter / Boundaries`.
- If a `tool` video makes strong claims about “best”, “only way”, “must use”, “will fix”, include `Failure Cases / Alternatives`.

Then apply the visual-evidence override:

- If the title, transcript, or user request suggests screens, slides, charts, tables, gameplay, product UI, code, rankings, diagrams, medical images, maps, comparisons, before/after visuals, or step-by-step operations, inspect visual evidence.
- If ASR contains many vague references such as “这个”, “这里”, “如图”, “上面”, “这个表”, “这款”, “左边/右边”, “画面里”, or if key names are ASR-uncertain, inspect visual evidence.
- Do not use large screenshot sweeps by default. Use the low-cost screenshot ladder below.

Then apply the page-context override:

- Always inspect title and description when available.
- Inspect pinned comment and a small set of top/high-like comments when available.
- If the UP posts links, documents, route tables, forms, images, maps, contact links, or external resources in description/comments, summarize what those resources appear to be.
- Do not deeply open every external resource by default. If a resource is likely token-heavy, private, or not needed for the summary, tell the user what it appears to contain and ask them to inspect it manually or approve deeper analysis.

## Evidence Acquisition

### With Local Scripts

Get public page context if the host agent can access it:

- title
- UP name
- description
- stats
- pinned/top comments
- UP-posted links/resources

Check subtitles first:

```powershell
python scripts/fetch_bilibili_subtitles.py list "URL"
python scripts/fetch_bilibili_subtitles.py fetch "URL" --output-dir artifacts
```

If subtitles are missing, download audio:

```powershell
python scripts/download_bilibili_audio.py list "URL"
python scripts/download_bilibili_audio.py fetch "URL" --output-dir artifacts/audio
```

For multi-part videos:

```powershell
python scripts/download_bilibili_audio.py fetch "URL" --page 1 --output-dir artifacts/audio
```

Transcribe:

```powershell
python scripts/transcribe_audio.py "artifacts/audio/example.m4a" --provider faster-whisper --language zh
```

Language rules:

- Chinese audio: `--language zh`
- English audio: `--language en`
- Unknown/mixed audio: omit `--language` for auto-detection.
- Local model preference: `faster-whisper-small -> base -> tiny`.

Normalize subtitle files when needed:

```powershell
python scripts/normalize_subtitles.py "artifacts/example.srt" --txt-out "artifacts/example.clean.txt"
```

Plan low-cost screenshots for visually dependent videos:

```powershell
python scripts/plan_visual_screenshots.py "artifacts/example.srt" --plan-out "artifacts/example.visual-plan.md"
```

If a local video file and `ffmpeg` are available, extract only the planned frames:

```powershell
python scripts/plan_visual_screenshots.py "artifacts/example.srt" --video "artifacts/video/example.mp4" --extract --frames-dir "artifacts/frames/example"
```

### Without Local Scripts

Use this fallback order:

1. Ask user for title, description, top comments, transcript, subtitle file, screenshots, or important timestamp excerpts.
2. If user only has URL, ask them to provide page context and transcript from Bilibili page, browser extension, or manual snippets.
3. If only title/description/comments are available, produce a page-context assessment, not a full video content summary.
4. Mark all analysis as `low evidence` until transcript, screenshots, or subtitles are available.

## Visual Evidence Workflow

Use visual evidence when the video depends on screen content. Keep it cheap by default.

### Low-Cost Screenshot Ladder

1. **No screenshot**: use when the transcript is sufficient and the video is mostly talking-head or lecture audio.
2. **Minimal screenshots**: capture 3 to 5 key frames when visuals may contain important evidence.
3. **Focused screenshots**: capture 6 to 12 frames only when the first set reveals charts, lists, UI steps, code, game titles, or dense slides.
4. **Ask before heavy visual analysis**: get user approval before broad sampling, frame-by-frame review, OCR over many frames, or watching a long video interactively.

### Choosing Key Frames

Prefer timestamps from the transcript:

- intro/title card: around `00:00-00:20`
- major claim changes
- moments containing ASR uncertainty around names, numbers, lists, charts, or product/game titles
- sections where the speaker says “看这里 / 如图 / 这个表 / 画面 / 左边 / 右边”
- final summary/recommendation screen

If transcript timestamps are unavailable, sample:

- `5%`, `25%`, `50%`, `75%`, and `95%` of video duration
- plus the thumbnail/title card if visible

### Visual Evidence Output

When screenshots were used, add:

- `Visual evidence used`: number of frames and timestamp list.
- `What visuals changed`: names, steps, chart values, rankings, UI states, or uncertainty resolved.
- `Still uncertain`: items requiring manual rewatch or OCR.

When screenshots were not used but might help, state:

- `Visual evidence not inspected`: reason and what to screenshot next if higher confidence is needed.

### Tool-Agnostic Instructions

Use whatever the host agent provides:

- browser screenshot at timestamp
- local video frame extraction
- player screenshot
- user-provided screenshots
- OCR only for the few frames that matter

Never spend many visual calls just to be thorough. Screenshot only when it can change the summary, fact check, counter-analysis, or action steps.

## Transcript Handling

For every transcript:

- Remove duplicate filler only when it does not change meaning.
- Keep timestamps around topic shifts and major claims.
- Mark ASR uncertainty for names, numbers, formulas, game titles, medicines, research names, laws, and product specs.
- Do not silently correct ASR hallucinations. Use `疑似 / unclear / needs rewatch`.
- For English transcripts intended for Chinese output, summarize in Chinese but keep key English terms in parentheses when useful.
- If the transcript repeatedly points to visuals, do not treat audio-only summary as complete.

## Page Context Handling

For title, description, and comments:

- Use the title to infer intended audience and promise, but do not treat title claims as verified.
- Use the description to capture itinerary, price, dates, materials, contact methods, disclaimers, and UP-provided links.
- Use pinned/high-like comments to capture corrections, common questions, viewer objections, warnings, and route feedback.
- Mark whether a comment is from the UP or a viewer when known.
- For links/resources, classify them:
  - route/material document
  - signup/contact/payment link
  - map/location list
  - external article
  - image album
  - commercial promotion
  - unclear
- For external resources, give a short `link inventory` first. Ask before deep-reading long documents, many links, or token-heavy pages.
- Do not copy private contact details unnecessarily. Summarize their role instead.

## Claim Extraction Checklist

Before writing the answer, extract:

- Main thesis or purpose.
- Important claims of fact.
- Numbers, dates, studies, definitions, product names, and named sources.
- Advice or action recommendations.
- Hidden assumptions.
- Who the advice applies to.
- Who it may not apply to.
- What evidence is missing.
- What visual evidence might change the conclusion.
- What title/description/comment evidence changes or challenges the transcript.

## Output Templates

### Multi-Video Output

Start with a ranking table:

| Rank | Video | Type | Page context | Transcript source | Visual evidence | Best use | Main risk |
|---:|---|---|---|---|---|---|---|

Then provide one section per video.

### Tool Mode

Return:

- Purpose
- Title/description/comment context
- Suitable scenarios
- Preconditions / required tools
- Step-by-step operation
- Failure points and troubleshooting
- Alternatives
- Recommended path for this user
- Rewatch timestamps
- Visual evidence used / not inspected

### Argument Mode: Full SFC

Return:

- `S - Summary`: thesis, argument chain, assumptions, examples.
- `Page context`: title, description, pinned/high-like comments, UP links.
- `F - Fact Check`: table of factual claims with status and sources needed.
- `C - Counter`: opposing views, boundary conditions, counterexamples, missing cases, when the thesis works, when it fails.
- `Verdict`: confidence, usefulness, what to adopt, what not to adopt.
- `Timestamps`: claims worth rewatching.
- `Visual evidence`: frames inspected or frames still needed.

### Information Mode

Return:

- Key facts
- Page context: title, description, pinned/high-like comments, UP links.
- Timeline / process
- People, products, concepts
- Recommendations or action list
- Risks and uncertainty
- Rewatch timestamps
- Visual evidence used / not inspected

If claim-bearing, append SFC-lite:

- `Fact Check`: what needs verification, what is supported, what is uncertain.
- `Counter / Boundaries`: strongest alternative explanations, exceptions, overstatements, who should not follow the advice.

## Fact Checking Rules

Fact checking is mandatory for:

- Health, medicine, psychology, nutrition, sleep, exercise.
- Finance, law, policy, education credentials, safety.
- Product specs, release dates, prices, benchmarks.
- Scientific claims, statistics, charts, studies.
- Strong claims using “proven”, “必然”, “一定”, “只要”, “唯一”, “最好”.

Use primary or high-quality sources when available:

- papers, PubMed, official guidelines, government statistics
- official product pages, release notes, company statements
- standards bodies, laws, regulations

If no web access:

- Do not fabricate citations.
- Mark `needs verification`.
- List exact search targets, e.g. `study title`, `PMID`, `official guideline`, `product release note`.

## Counter-Argument Rules

Always include counter-analysis when:

- the video gives advice;
- the video says a behavior causes a result;
- the video ranks products/methods;
- the video makes a social, scientific, political, medical, financial, or philosophical claim;
- the user asks for review, audit, skepticism, or “是否靠谱”.

Counter-analysis must include at least:

- strongest opposing interpretation;
- boundary conditions;
- counterexamples;
- missing evidence;
- possible harm if followed blindly;
- what would change the conclusion.

## Quality Gate

Before finalizing, check:

- Did I identify transcript source and confidence?
- Did I inspect title, description, pinned/high-like comments, and UP links when available?
- Did I preserve timestamps?
- Did I separate summary from verification?
- Did I include Counter / Boundaries for any claim-bearing video?
- Did I mark ASR-uncertain names/numbers?
- Did I inspect minimal visual evidence when the video depends on visuals?
- Did I avoid excessive screenshots or broad frame sweeps without user approval?
- Did I avoid saving cookies or private account state?
- Did I tell the user what to verify next?

If any answer lacks required Counter / Boundaries for a claim-bearing video, revise before sending.
