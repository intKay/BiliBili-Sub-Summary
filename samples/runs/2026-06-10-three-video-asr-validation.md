# 2026-06-10 三个真实视频 ASR 测试

## 目标

测试三个用户给出的 B站视频在当前工作流下的表现：

1. 字幕 API 检查
2. DASH 音频下载
3. 默认 `faster-whisper-small` 转写
4. 抽查转写质量

## 样本总览

| BV | 标题 | 语言 | 时长 | 字幕 API | 音频 | ASR |
|---|---|---|---:|---:|---:|---:|
| `BV1P7411C7Gz` | `【公开课】耶鲁大学：哲学-死亡` 第 1 P | 英文 | `2776s` | `0` | 成功 | 成功 |
| `BV1sjE56YEWp` | `30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点` | 中文 | `889s` | `0` | 成功 | 成功 |
| `BV1va5kzaEDw` | `【医学博士】每天3点睡，多少天会死？...` | 中文 | `275s` | `0` | 成功 | 成功 |

## 字幕检查

三个样本通过 `scripts/fetch_bilibili_subtitles.py list` 检查，公开字幕 API 都返回：

```text
subtitle_count=0
```

因此全部走音频下载与 ASR。

## 音频下载

### 耶鲁公开课

这是 26 P 合集。当前测试第 1 P：

- page: `1`
- part: `[第1集] 课程介绍`
- duration: `2776`
- audio stream: `30216`
- output: `artifacts/audio/【公开课】耶鲁大学：哲学-死亡.p1 [BV1P7411C7Gz].m4a`
- bytes: `23271597`

命令：

```powershell
.\.venv\Scripts\python.exe scripts\download_bilibili_audio.py fetch "https://www.bilibili.com/video/BV1P7411C7Gz" --page 1 --output-dir artifacts\audio
```

### 游戏节盘点

此前已下载：

- duration: `889`
- output: `artifacts/audio/30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].m4a`
- bytes: `17323558`

### 医学博士睡眠视频

- duration: `275`
- audio stream: `30280`
- output: `artifacts/audio/【医学博士】每天3点睡，多少天会死？｜晚睡晚起，算熬夜吗？｜睡得少和睡得晚，哪个伤害更大 [BV1va5kzaEDw].m4a`
- bytes: `5746952`

## ASR 结果

### 耶鲁公开课

第一次误用 `--language zh`，结果混乱。更正为 `--language en` 后正常。

命令：

```powershell
.\.venv\Scripts\python.exe scripts\transcribe_audio.py "artifacts\audio\【公开课】耶鲁大学：哲学-死亡.p1 [BV1P7411C7Gz].m4a" --provider faster-whisper --language en
```

结果：

- model: `artifacts/models/faster-whisper-small`
- segment_count: `1163`
- end: `2775.0`
- runtime: about `15m 06s`

抽查：

```text
[00:00:00.000 - 00:00:19.520] Alright, so this is Philosophy 176, the Classes on Death.
[00:00:19.520 - 00:00:26.320] My name is Shelley Kagan and the very first thing I want to do is to invite you to call
[00:00:26.320 - 00:00:28.000] me Shelley.
```

结论：英文音频必须使用 `--language en` 或自动检测；强制 `zh` 会严重劣化。

### 游戏节盘点

命令：

```powershell
.\.venv\Scripts\python.exe scripts\transcribe_audio.py "artifacts\audio\30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].m4a" --provider faster-whisper --model artifacts\models\faster-whisper-small --language zh
```

结果：

- model: `artifacts/models/faster-whisper-small`
- segment_count: `613`
- end: `879.64`
- runtime: about `9m 41s`

抽查质量：可用于主题总结和游戏清单初筛，但游戏名/专名仍需回看校对。

### 医学博士睡眠视频

命令：

```powershell
.\.venv\Scripts\python.exe scripts\transcribe_audio.py "artifacts\audio\【医学博士】每天3点睡，多少天会死？｜晚睡晚起，算熬夜吗？｜睡得少和睡得晚，哪个伤害更大 [BV1va5kzaEDw].m4a" --provider faster-whisper --language zh
```

结果：

- model: `artifacts/models/faster-whisper-small`
- segment_count: `169`
- end: `273.0`
- runtime: about `2m 44s`

抽查：

```text
[00:00:00.000 - 00:00:02.400] 每天坚持晚上三点睡
[00:00:02.400 - 00:00:03.800] 多少天会死
[00:00:11.000 - 00:00:11.900] 1964年
```

结论：整体可读，适合做信息总结和事实核查清单；医学和统计数据仍需外部来源核对。

## 结论

- 三个视频的公开字幕 API 都不可用。
- `scripts/download_bilibili_audio.py` 对单 P 和多 P 第 1 P 都能正常下载音频。
- `faster-whisper-small` 默认模型可用。
- 语言参数是准确率关键：
  - 中文视频：`--language zh`
  - 英文公开课：`--language en`
  - 不确定语言：先不传 `--language` 让模型检测
- 对事实密集内容，ASR 文本可以作为分析底稿，但不能当作逐字可靠证据。
