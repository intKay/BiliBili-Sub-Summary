# Agent Instructions

Use `skills/bilibili-video-analysis/SKILL.md` when the host supports Codex-style skills.

If the host does not support skills, load `skills/bilibili-video-analysis/PORTABLE_AGENT_PROMPT.md` into the agent's project instructions, system prompt, memory, rules, or custom instructions.

Do not save cookies, SESSDATA, exported cookie jars, browser profiles, full logged-in HTML, private messages, or account settings.

Prefer this evidence order:

1. User-provided Bilibili URL and visible page context.
2. Official or auto subtitles.
3. Public audio download plus local ASR.
4. Targeted screenshots for visually dependent moments.
5. User-provided transcript, screenshots, or timestamp excerpts.

For claim-bearing videos, always include Fact Check and Counter / Boundaries. If evidence is missing, mark the output as low evidence and ask for the missing material.

