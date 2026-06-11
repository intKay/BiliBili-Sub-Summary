# Skill 完整封装与一键安装

## 封装目标

这个 skill 要同时适配三类环境：

- Codex：安装到 `$CODEX_HOME/skills` 或 `~/.codex/skills` 后自动触发。
- 其他 Agent：复制 `PORTABLE_AGENT_PROMPT.md` 作为系统/项目提示词。
- Linux/Windows 本地脚本环境：可运行字幕、ASR、截图计划等 Python helper。

## 当前封装内容

安装脚本会复制：

- `SKILL.md`
- `PORTABLE_AGENT_PROMPT.md`
- `requirements.txt`
- `scripts/*.py`

目标目录：

- Windows 默认：`$HOME\.codex\skills\bilibili-video-analysis`
- Linux 默认：`$HOME/.codex/skills/bilibili-video-analysis`
- 如果设置了 `CODEX_HOME`，则安装到 `$CODEX_HOME/skills/bilibili-video-analysis`

## Windows 一键安装

在项目根目录运行：

```powershell
.\install_skill.ps1
```

如果 Windows 执行策略禁止直接运行 `.ps1`：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install_skill.ps1
```

指定安装位置：

```powershell
.\install_skill.ps1 -InstallRoot "D:\AgentSkills"
```

## Linux/macOS 一键安装

在项目根目录运行：

```bash
chmod +x ./install_skill.sh
./install_skill.sh
```

指定安装位置：

```bash
./install_skill.sh "$HOME/.codex/skills"
```

## 安装 Python helper 依赖

安装 skill 后，进入 skill 目录创建虚拟环境：

```bash
cd ~/.codex/skills/bilibili-video-analysis
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
cd $HOME\.codex\skills\bilibili-video-analysis
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`ffmpeg` 不是 Python 包。只有抽取视频画面时才需要它；单纯生成截图计划不需要。

## 给其他 Agent 的用法

如果目标 Agent 不支持 Codex skill：

1. 打开 `PORTABLE_AGENT_PROMPT.md`。
2. 把代码块里的完整提示词放入该 Agent 的 system prompt、project instruction 或 knowledge base。
3. 把 `scripts/` 目录作为可选工具目录提供给 Agent。
4. 明确告诉 Agent：没有字幕、截图、浏览器或联网能力时，必须请求用户提供证据，不能伪造核查。

## 发布前检查

发布或复制给其他机器前，确认：

- `artifacts/` 不被打包。
- 不包含 cookies、SESSDATA、浏览器 profile、登录页 HTML。
- `SKILL.md` 中的命令可以在 Windows 和 Linux 上找到等价写法。
- `PORTABLE_AGENT_PROMPT.md` 不依赖 Codex 隐藏能力。
- `scripts/plan_visual_screenshots.py` 可以在没有 ffmpeg 时只生成计划。
