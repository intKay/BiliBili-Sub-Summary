# 视觉依赖视频的低成本截图策略

## 目标

截图不是为了“看起来完整”，而是为了补字幕/ASR 无法表达的证据：图表、地图、UI、代码、排行榜、参数、价格、步骤、医学图示、游戏画面和产品对比。

## 截图梯度

1. 不截图：纯访谈、播客、口播，转写已足够。
2. 最小截图：3-5 张，用于确认标题卡、关键 claim、图表/列表、结尾总结。
3. 聚焦截图：6-12 张，仅当第一轮发现密集 UI、代码、地图、表格、排行榜时。
4. 重视觉分析：全片抽帧、逐帧 OCR、长时间观看，必须先问用户。

## 选帧时机

优先用字幕/ASR 时间戳，而不是平均抽样：

- 字幕出现“如图、看这里、这个表、画面、左边、右边、上面、下面”。
- ASR 对关键名字、数字、榜单、产品名、药名、路线、价格不确定。
- 视频进入新步骤、新章节、总结页。
- 工具类视频出现界面变化、按钮、报错、代码片段。
- 旅游/路线视频出现地图、路线表、价格表、注意事项。
- 产品/游戏视频出现参数页、对比页、实机画面。

没有时间戳时，再退回 `5% / 25% / 50% / 75% / 95%` 的五点采样。

## 本项目低成本实现

先生成截图计划：

```powershell
.\.venv\Scripts\python.exe scripts/plan_visual_screenshots.py artifacts/example.srt --plan-out artifacts/example.visual-plan.md
```

Linux/macOS：

```bash
python scripts/plan_visual_screenshots.py artifacts/example.srt --plan-out artifacts/example.visual-plan.md
```

如果已经有本地视频文件，并且安装了 `ffmpeg`，再抽取计划中的关键帧：

```powershell
.\.venv\Scripts\python.exe scripts/plan_visual_screenshots.py artifacts/example.srt --video artifacts/video/example.mp4 --extract --frames-dir artifacts/frames/example
```

这个脚本只做三件事：

- 从字幕/转写中找视觉提示词和 ASR 不确定点。
- 合并相近时间点，默认输出 5 个关键帧。
- 可选调用 `ffmpeg` 抽图。

## 输出要求

最终总结里要写清楚：

- 是否用了视觉证据。
- 截了几帧、哪些时间戳。
- 视觉证据改变了哪些判断。
- 仍然需要人工回看的画面。

如果没有截图，也要说明原因，并列出下一步最值得截的时间点。
