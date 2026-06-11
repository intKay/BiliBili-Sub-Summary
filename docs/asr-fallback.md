# ASR 兜底方案

## 目标

当视频没有可下载字幕时，改走：

1. 获取音频
2. 做 ASR 转写
3. 清洗文本
4. 再进入工具类 / 观点类 / 信息类分析

## 成本结论

### 1. 本地 ASR

- 不消耗聊天 token
- 主要消耗 CPU / GPU 时间
- 适合长视频批量转写

### 2. 云端 ASR

- 通常按音频时长计费
- 一般不是按聊天 token 计费
- 真正消耗聊天 token 的，通常是“转写完成后把长文本交给模型总结/核查”

## 当前脚本

- [scripts/transcribe_audio.py](C:/Users/15760/Documents/B站视频总结/scripts/transcribe_audio.py)

统一入口，支持三种后端：

- `faster-whisper`
- `whisper`
- `openai`

## 建议优先级

### 方案 A：本地优先

推荐在后续补这组依赖：

1. `ffmpeg`
2. `faster-whisper`

优点：

- 成本低
- 不吃聊天 token
- 可批量跑

### 方案 B：云端备选

有 `OPENAI_API_KEY` 时，可直接走云端转写。

优点：

- 安装简单
- 上手快

代价：

- 有外部 API 费用
- 长音频会有时长成本

## 命令

自动选择后端：

```powershell
python scripts/transcribe_audio.py "artifacts/example.mp3"
```

指定本地 `faster-whisper`：

```powershell
python scripts/transcribe_audio.py "artifacts/example.mp3" --provider faster-whisper --model base
```

指定 OpenAI 云端转写：

```powershell
python scripts/transcribe_audio.py "artifacts/example.mp3" --provider openai --model gpt-4o-mini-transcribe
```

输出包括：

- `*.transcript.txt`
- `*.segments.json`
- `*.timestamped.txt`

## 当前状态

- `scripts/transcribe_audio.py` 已落地
- `.venv` 已安装 `faster-whisper==1.2.1`
- `small` / `base` / `tiny` 模型已放在 `artifacts/models/`
- 默认使用 `cpu + int8`，避免误走 CUDA 导致 `cublas64_12.dll` 缺失
- `transcribe_audio.py` 未指定 `--model` 时，会优先使用 `artifacts/models/faster-whisper-small`，没有时再退回 `base` / `tiny`
- 已新增 `scripts/download_bilibili_audio.py`，可在不保存 cookies 的前提下通过 B站公开视频 API 下载 DASH 音频
- 已完成真实链路验收：`BV1sjE56YEWp -> artifacts/audio/*.m4a -> faster-whisper -> transcript/segments/timestamped`
- 已完成模型升级对比：短 TTS 样本上 `base` 字符准确率较高；真实 B站视频上 `small` 语句连贯度和专名识别更好，因此默认推荐 `small`

## 已知限制

- `yt-dlp` 在当前环境下访问 B站 playinfo 会遇到 `HTTP 412`，公开 `x/player/playurl` 路线暂时更稳定。
- `yt-dlp --cookies-from-browser chrome` 当前会卡在 Chrome cookie DB 复制权限；Edge 可复制但 DPAPI 解密失败。不要改为导出 cookie jar 到项目目录。
- `tiny` 中文识别只建议粗筛。
- `base` 速度与质量比较均衡，适合快速复核。
- `small` 更慢，但真实视频可读性明显更好，建议作为默认分析模型。
- 对医学、财经、政策、观点核查类视频，即使用 `small` 也不要把 ASR 文本当作逐字稿；关键事实仍要回看原视频或找外部来源。
- 不要把英文音频强制设为 `--language zh`。耶鲁公开课样本用 `--language en` 后输出质量明显正常。
