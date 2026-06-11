# BiliBili Sub Summary

这个项目用于建立一个可复用的 B站视频分析工作流，覆盖：

- 人工提供链接
- 账号相关来源：收藏、稍后再看、动态
- 在线检索结果
- 字幕缺失时的音频下载与本地 ASR
- 画面依赖视频的低成本截图计划
- 可迁移到 OpenCode、Hermes、Codex、Fedora、WSL 的 agent skill

项目目标不是保存账号态，而是稳定完成这条链路：

1. 找到值得分析的视频
2. 检查并获取字幕
3. 清洗为可分析文本
4. 按视频类型输出结构化结果
5. 对观点类默认使用 SFC
6. 对视觉依赖视频补充少量关键截图证据

## 输出类型

- 工具类：操作步骤、前置条件、坑点、排错路径
- 观点类：SFC（Summary / Fact Check / Counter）
- 信息类：事实总结、建议、行动清单

## 给 Agent 的一键安装

### Codex / 本地 skill

Windows PowerShell：

```powershell
git clone https://github.com/intKay/BiliBili-Sub-Summary.git
cd BiliBili-Sub-Summary
powershell -NoProfile -ExecutionPolicy Bypass -File .\install_skill.ps1
```

Fedora / Linux / WSL：

```bash
git clone https://github.com/intKay/BiliBili-Sub-Summary.git
cd BiliBili-Sub-Summary
chmod +x ./install_skill.sh
./install_skill.sh
```

默认安装位置：

- Windows：`$HOME\.codex\skills\bilibili-video-analysis`
- Fedora / Linux / WSL：`$HOME/.codex/skills/bilibili-video-analysis`
- 如果设置了 `CODEX_HOME`，则安装到 `$CODEX_HOME/skills/bilibili-video-analysis`

安装后，在 agent 的新会话中请求“使用 bilibili-video-analysis skill 分析 B站视频”即可。

### OpenCode / Hermes / 其他 Agent

如果目标 Agent 不支持 Codex skill 自动发现：

1. 打开 [`skills/bilibili-video-analysis/PORTABLE_AGENT_PROMPT.md`](skills/bilibili-video-analysis/PORTABLE_AGENT_PROMPT.md)。
2. 把其中代码块里的完整提示词复制到 OpenCode、Hermes 或其他 Agent 的 system prompt、project instruction、repository instruction 或 memory 中。
3. 把本仓库的 `scripts/` 目录作为可选工具目录暴露给 Agent。
4. 明确要求 Agent 遵守：没有字幕、截图、浏览器或联网能力时，必须向用户索要证据，不能伪造核查结果。

推荐给 OpenCode / Hermes 的项目指令：

```text
Use the Bilibili video analysis workflow from skills/bilibili-video-analysis/PORTABLE_AGENT_PROMPT.md.
Use scripts/ helpers when available. Do not save cookies, SESSDATA, browser profiles, full logged-in HTML, or private account state.
Prefer subtitles, then ASR, then targeted screenshots for visually dependent videos.
For claim-bearing videos, always include Fact Check and Counter / Boundaries.
```

## Python 环境配置

Windows：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Fedora：

```bash
sudo dnf install -y python3 python3-pip ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

WSL：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

`ffmpeg` 只有在抽取关键帧或处理音视频时需要；只生成截图计划不需要。

## 项目结构

- [docs/workflow.md](docs/workflow.md)：完整工作流说明
- [skills/bilibili-video-analysis/SKILL.md](skills/bilibili-video-analysis/SKILL.md)：可迁移为正式 Codex skill 的草案
- [scripts/fetch_subtitles.py](scripts/fetch_subtitles.py)：字幕检查与下载
- [scripts/fetch_bilibili_subtitles.py](scripts/fetch_bilibili_subtitles.py)：基于 Bilibili Evolved 实现思路的 B 站字幕脚本
- [scripts/normalize_subtitles.py](scripts/normalize_subtitles.py)：`srt`/`vtt` 清洗为纯文本
- [scripts/download_bilibili_audio.py](scripts/download_bilibili_audio.py)：无字幕时通过公开视频 API 下载 DASH 音频
- [scripts/transcribe_audio.py](scripts/transcribe_audio.py)：无字幕时的 ASR 转写入口
- [scripts/plan_visual_screenshots.py](scripts/plan_visual_screenshots.py)：视觉依赖视频的低成本截图计划与可选抽帧
- [docs/visual-evidence.md](docs/visual-evidence.md)：截图时机和成本梯度
- [docs/skill-packaging.md](docs/skill-packaging.md)：skill 封装、一键安装与跨 Agent 使用方式
- [samples/video_candidates.md](samples/video_candidates.md)：真实试跑候选记录
- [samples/runs/README.md](samples/runs/README.md)：试跑记录格式

## 建议使用方式

先拿 3-5 个真实链接试跑，确认字幕链路和输出质量，再考虑安装为正式本地 skill。

### 1. 检查字幕

```powershell
.\.venv\Scripts\python.exe scripts/fetch_subtitles.py list "https://www.bilibili.com/video/BV..."
```

### 2. 下载字幕

```powershell
.\.venv\Scripts\python.exe scripts/fetch_subtitles.py fetch "https://www.bilibili.com/video/BV..." --output-dir artifacts
```

如需读取本机浏览器登录态但不落 cookie 文件：

```powershell
.\.venv\Scripts\python.exe scripts/fetch_subtitles.py fetch "https://www.bilibili.com/video/BV..." --cookies-from-browser chrome
```

### 3. 清洗字幕文本

```powershell
.\.venv\Scripts\python.exe scripts/normalize_subtitles.py artifacts/example.zh-Hans.srt --txt-out artifacts/example.clean.txt
```

### 4. 无字幕时下载音频

```powershell
.\.venv\Scripts\python.exe scripts/download_bilibili_audio.py list "https://www.bilibili.com/video/BV..."
.\.venv\Scripts\python.exe scripts/download_bilibili_audio.py fetch "https://www.bilibili.com/video/BV..." --output-dir artifacts/audio
```

该脚本不读取或保存 cookies，优先使用 B站公开视频 API 的 DASH 音频流。
多 P 视频可加 `--page 1` 指定分 P。

### 5. 无字幕时转写音频

```powershell
.\.venv\Scripts\python.exe scripts/transcribe_audio.py artifacts/audio/example.m4a --provider faster-whisper --language zh
```

`transcribe_audio.py` 会优先使用本地 `artifacts/models/faster-whisper-small`，没有时再退回 `base` / `tiny`。如果要强制使用某个模型，可以加：

```powershell
--model artifacts/models/faster-whisper-base
```

### 6. 视觉依赖视频生成截图计划

```powershell
.\.venv\Scripts\python.exe scripts/plan_visual_screenshots.py artifacts/example.srt --plan-out artifacts/example.visual-plan.md
```

如果已经有本地视频文件并安装了 `ffmpeg`，可按计划抽关键帧：

```powershell
.\.venv\Scripts\python.exe scripts/plan_visual_screenshots.py artifacts/example.srt --video artifacts/video/example.mp4 --extract --frames-dir artifacts/frames/example
```

### 7. 安装为本地 skill

Windows:

```powershell
.\install_skill.ps1
```

Linux/macOS:

```bash
chmod +x ./install_skill.sh
./install_skill.sh
```

## 当前状态

- 已迁移工作流文档与 skill 草案
- 已补字幕检查/下载与清洗脚本
- 已完成第一轮真实 B站链接检索与字幕可用性验证，记录见 [samples/runs/2026-06-10-initial-validation.md](samples/runs/2026-06-10-initial-validation.md)
- 项目内 `.venv` 已安装 `yt-dlp`
- 当前主要阻塞不是安装，而是 B站字幕登录态与本机 DPAPI 解密失败
- 已补基于 `Bilibili Evolved` 思路的独立字幕脚本，说明见 [docs/bilibili-subtitle-implementation.md](docs/bilibili-subtitle-implementation.md)
- 已补 ASR 兜底脚本与成本说明，见 [docs/asr-fallback.md](docs/asr-fallback.md)
- 已打通真实链路 `BV -> DASH 音频 -> 本地 faster-whisper 转写`，记录见 [samples/runs/2026-06-10-bv-audio-asr-validation.md](samples/runs/2026-06-10-bv-audio-asr-validation.md)
- 已完成模型升级对比，真实视频默认推荐 `faster-whisper-small`，记录见 [samples/runs/2026-06-10-asr-model-accuracy-upgrade.md](samples/runs/2026-06-10-asr-model-accuracy-upgrade.md)
- 已完成三个真实视频测试，记录见 [samples/runs/2026-06-10-three-video-asr-validation.md](samples/runs/2026-06-10-three-video-asr-validation.md)

## 安全边界

- 不在项目内保存 cookies、SESSDATA、浏览器 profile 或完整登录页面缓存
- 只记录视频链接、标题、字幕来源、分析结果和必要的时间戳
- 下载得到的字幕和中间产物默认放在 `artifacts/`，并保持不提交
- 第三方源码镜像 `vendor/` 默认不提交；需要溯源时优先引用上游项目链接或文档说明
