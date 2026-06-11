# B站视频分析工作流

## 目标

从 B站账号相关视频源或在线检索结果中筛选值得看的视频，获取字幕或转写文本，并按需求类型输出：

- 工具类：提炼可操作步骤、前置条件、风险点、排错路径
- 观点类：用 SFC 方法核查观点，包括 Summary、Fact Check、Counter
- 信息类：总结事实信息，形成建议和行动清单

“延迟式游戏”和“提升专注力”只是某个具体视频里的观点示例，不是通用主题。通用方法是 SFC，只默认用于观点类视频。

## 输入来源

按稳定性从高到低：

1. 手动给链接
2. 浏览器中打开收藏、稍后再看、动态后人工或半自动收集链接
3. 在线检索结果
4. 本机临时登录态辅助读取

## 候选筛选原则

优先：

1. 主题高度相关
2. 播放、收藏、点赞、投币等互动质量较高
3. 结构清楚，有章节、资料来源、图表或脚本痕迹
4. UP 主历史内容稳定
5. 有官方字幕或自动字幕

降权：

- 搬运、营销号、纯情绪输出
- 只给结论不给材料
- 标题过度夸张
- 评论区集中指出事实错误且未回应

## 账号读取边界

分层策略：

1. 优先使用手动链接和公开视频列表。
2. 对收藏、稍后再看、关注动态等账号相关来源，优先让用户在已登录浏览器里打开页面，只提取当前可见的视频链接、标题、UP 主、时长、可见互动数据。
3. 如果字幕或页面访问必须使用登录态，允许临时使用 `yt-dlp --cookies-from-browser` 或等价的一次性浏览器登录态读取。
4. 不在工作区保存 cookies、SESSDATA、cookie jar、浏览器 profile、完整登录页面缓存。
5. 账号相关来源的详细路线见 [account-source-roadmap.md](account-source-roadmap.md)。

## 字幕获取路线

首选 `yt-dlp`：

```powershell
python scripts/fetch_subtitles.py list "https://www.bilibili.com/video/BV..."
python scripts/fetch_subtitles.py fetch "https://www.bilibili.com/video/BV..." --output-dir artifacts
```

如需登录态：

```powershell
python scripts/fetch_subtitles.py fetch "https://www.bilibili.com/video/BV..." --cookies-from-browser chrome
```

兜底方案：

1. 无字幕但可获取音频时，使用公开 playurl API 下载 DASH 音频，再考虑 ASR
2. 硬字幕视频必要时再考虑 OCR
3. 如果都不稳定，先基于简介、评论、人工摘录做轻量分析，并明确证据质量

音频下载命令：

```powershell
.\.venv\Scripts\python.exe scripts/download_bilibili_audio.py list "https://www.bilibili.com/video/BV..."
.\.venv\Scripts\python.exe scripts/download_bilibili_audio.py fetch "https://www.bilibili.com/video/BV..." --output-dir artifacts/audio
```

多 P 视频用 `--page` 指定分 P：

```powershell
.\.venv\Scripts\python.exe scripts/download_bilibili_audio.py fetch "https://www.bilibili.com/video/BV..." --page 1 --output-dir artifacts/audio
```

本地 ASR 命令：

```powershell
.\.venv\Scripts\python.exe scripts/transcribe_audio.py "artifacts/audio/example.m4a" --provider faster-whisper --language zh
```

自动选择顺序：`small -> base -> tiny`。如需快速粗筛，可手动指定 `--model artifacts/models/faster-whisper-base`。

语言参数要按音频语言选择：中文视频用 `--language zh`，英文公开课用 `--language en`；如果不确定，可先不传 `--language` 让模型自动检测。

## 三类输出结构

### 工具类

```markdown
# 工具类视频分析

## 一句话用途
## 适用场景
## 操作步骤
## 前置条件
## 常见失败点
## 我建议你的操作路径
## 需要回看核对的时间戳
```

### 观点类：SFC

```markdown
# 观点类视频 SFC 核查

## 视频信息
- 标题：
- UP 主：
- 链接：
- 字幕来源：
- 分析主题：

## S - Summary
- 核心观点：
- 作者的论证链：
- 作者默认前提：
- 关键例子或数据：

## F - Fact Check
| 待核查事实 | 视频中的说法 | 证据状态 | 需要查的来源 | 初步判断 |
|---|---|---|---|---|

## C - Counter
- 反向观点 1：
- 反向观点 2：
- 反向观点 3：
- 作者可能忽略的边界条件：
- 哪些情况下原观点成立：
- 哪些情况下原观点不成立：

## 结论
- 可信度：
- 对我的启发：
- 我该怎么用：
- 不该怎么用：

## 回看时间戳
```

### 信息类

```markdown
# 信息类视频总结

## 关键信息
## 时间线/流程
## 人物、产品、概念
## 对我的建议
## 风险和不确定性
## 后续行动清单
```

## 观点类默认核查点

1. 观点定义是否清楚
2. 概念边界是否稳定
3. 是否区分相关性和因果性
4. 是否给出可核查来源
5. 是否存在反例、边界条件、适用人群差异
6. 视频原话与二次总结是否一致

## 推荐迭代顺序

1. 先做统一字幕入口，让单个视频的字幕/ASR 一条命令完成。
2. 再做批量 URL 队列，从 `videos.txt` 或 `candidates.json` 批量获取可分析文本。
3. 再做同 UP 主公开相似视频收集和排序。
4. 再支持收藏、稍后再看、关注动态等浏览器界面可见内容提取。
5. 最后才考虑更自动化的候选排序和临时登录态增强。

这个顺序更稳，因为账号页结构和登录态都会变，但“字幕获取 -> 文本清洗 -> 分类分析”这条主链更稳定。
