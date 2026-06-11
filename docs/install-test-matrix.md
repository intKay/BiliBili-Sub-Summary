# Install And Portability Test Matrix

Date: 2026-06-11

## Verified In This Workspace

| Area | Command | Result |
|---|---|---|
| Python syntax | `python -m py_compile scripts/*.py` equivalent on all helper scripts | Passed |
| Windows skill install | `powershell -NoProfile -ExecutionPolicy Bypass -File .\install_skill.ps1 -InstallRoot artifacts\verify-skill-install` | Passed |
| POSIX skill install via Git Bash | `bash ./install_skill.sh artifacts/verify-sh-install` | Passed |
| Screenshot planner | `python scripts/plan_visual_screenshots.py <sample.srt> --plan-out artifacts/test.visual-plan.md` | Passed |
| Git ignore safety | `git check-ignore` for `artifacts/`, `.venv/`, `vendor/` | Passed |

## Portability Reviewed But Not Fully Runtime-Verified Here

| Target | Expected path | Confidence | Notes |
|---|---|---|---|
| Fedora | `install_skill.sh`, `python3 -m venv`, `dnf install python3 python3-pip ffmpeg` | Medium-high | Requires real Fedora host for full package-manager verification. |
| WSL Ubuntu/Debian | `install_skill.sh`, `python3 -m venv`, `apt install python3-venv python3-pip ffmpeg` | Medium-high | Requires real WSL distro for full package-manager verification. |
| macOS | `install_skill.sh`, Homebrew Python/ffmpeg | Medium | Shell script is POSIX `sh`; package command needs Homebrew. |
| OpenCode / Hermes / Claude Code / Gemini CLI / Cursor / Windsurf / Cline / Roo / Aider / Continue | `PORTABLE_AGENT_PROMPT.md` copied into project/system instructions | Medium-high | Prompt-only path should work anywhere, but exact configuration UI differs by tool. |

## Manual Smoke Test For Any New Machine

```bash
git clone https://github.com/intKay/BiliBili-Sub-Summary.git
cd BiliBili-Sub-Summary
./install_skill.sh /tmp/agent-skills
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m py_compile scripts/*.py
```

Windows PowerShell:

```powershell
git clone https://github.com/intKay/BiliBili-Sub-Summary.git
cd BiliBili-Sub-Summary
powershell -NoProfile -ExecutionPolicy Bypass -File .\install_skill.ps1 -InstallRoot artifacts\verify-skill-install
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m py_compile scripts\fetch_subtitles.py scripts\fetch_bilibili_subtitles.py scripts\normalize_subtitles.py scripts\download_bilibili_audio.py scripts\transcribe_audio.py scripts\plan_visual_screenshots.py
```
