# 2026-06-10 本地 ASR 环境验收

## 目标

验证本项目已经具备本地离线转写能力，不依赖 OpenAI API。

## 环境

- Python: `3.11.9`
- venv: `.\.venv`
- ASR backend: `faster-whisper==1.2.1`
- 模型路径: `artifacts/models/faster-whisper-tiny`
- 执行设备: `cpu`
- 计算类型: `int8`

## 测试输入

- 本地合成语音: `artifacts/tts-test.wav`
- 生成方式: Windows `System.Speech.Synthesis.SpeechSynthesizer`

测试语句：

> 你好，这是本地语音转写环境测试。今天我们验证 B 站视频总结项目的离线字幕方案。

## 执行命令

```powershell
.\.venv\Scripts\python.exe scripts\transcribe_audio.py artifacts\tts-test.wav --provider faster-whisper --model artifacts\models\faster-whisper-tiny --language zh
```

## 输出结果

生成了以下文件：

- `artifacts/tts-test.transcript.txt`
- `artifacts/tts-test.segments.json`
- `artifacts/tts-test.timestamped.txt`

脚本返回摘要：

```json
{
  "provider": "faster-whisper",
  "model": "artifacts\\models\\faster-whisper-tiny",
  "language": "zh",
  "audio": "artifacts\\tts-test.wav",
  "txt_out": "artifacts\\tts-test.transcript.txt",
  "segments_out": "artifacts\\tts-test.segments.json",
  "timestamped_out": "artifacts\\tts-test.timestamped.txt",
  "segment_count": 2
}
```

转写文本：

> 你好,這是本地語音轉寫環境測試。  
> 今天我們驗證避戰視頻總結項目的離現自目方案。

## 结论

- 本地 ASR 主链路已经跑通。
- 当前默认应使用 `cpu + int8`，避免误走 CUDA 导致 `cublas64_12.dll` 缺失报错。
- 识别质量对合成中文语音可用，但 `tiny` 模型有少量词级误识别；后续如追求更高准确率，可改用 `base` 或 `small`，前提是补齐模型权重下载。
- 本次验收只验证了本地转写能力，尚未完成“从 B 站真实视频稳定拉音频再转写”的整链验收。
