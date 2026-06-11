# 2026-06-10 ASR 模型准确率升级记录

## 目标

提升本地 B站音频转写准确率，并确定默认推荐模型。

## 新增模型

下载到本地：

- `artifacts/models/faster-whisper-base`
- `artifacts/models/faster-whisper-small`

模型文件大小：

- `base/model.bin`: `145217532` bytes
- `small/model.bin`: `483546902` bytes

## 标准样本对比

测试输入：

- `artifacts/tts-test.wav`

标准文本：

```text
你好，这是本地语音转写环境测试。今天我们验证 B 站视频总结项目的离线字幕方案。
```

轻量繁简归一后的结果：

| 模型 | CER | 字符准确率 | 核心问题 |
|---|---:|---:|---|
| `tiny` | `0.1143` | `0.8857` | 把 `B站`、`字幕` 等词识别错 |
| `base` | `0.0286` | `0.9714` | 约 1 个核心错字 |
| `small` | `0.0571` | `0.9429` | 把 `B站` 识别为同音词 |

## 真实 B站样本对比

测试输入：

- `BV1sjE56YEWp`
- 音频：`artifacts/audio/30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].m4a`

结果：

- `base` 用时约 `4 分 12 秒`，`segment_count=523`
- `small` 用时约 `9 分 41 秒`，`segment_count=613`

真实视频开头抽查：

- `tiny`：主题能看出，但错词密集，专名很不稳定。
- `base`：比 `tiny` 明显更好，能识别 `微軟`、`安布雷拉`、`克里斯` 等部分专名，但仍有较多错词。
- `small`：真实视频可读性最好，输出为简体，句子更连贯，能识别 `微软`、`安布雷拉`、`重置版` 等关键表达。

## 结论

- 默认分析模型改为优先 `faster-whisper-small`。
- 如果只做快速粗筛，可以手动指定 `--model artifacts/models/faster-whisper-base`。
- `tiny` 只保留为最低成本 fallback，不建议用于观点核查或事实密集视频。

## 脚本改动

`scripts/transcribe_audio.py` 现在未指定 `--model` 时会自动选择：

1. `artifacts/models/faster-whisper-small`
2. `artifacts/models/faster-whisper-base`
3. `artifacts/models/faster-whisper-tiny`
4. `base`
