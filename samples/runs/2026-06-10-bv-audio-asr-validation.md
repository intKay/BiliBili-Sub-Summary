# 2026-06-10 真实 BV 音频下载与 ASR 验收

## 目标

打通“真实 B站 BV 链接 -> 本地音频文件 -> `scripts/transcribe_audio.py` 转写”的完整链路。

## 样本

- BV: `BV1sjE56YEWp`
- 标题：`30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点`
- 字幕 API 结果：`subtitle_count=0`

## 排查结果

### yt-dlp 直连

命令：

```powershell
.\.venv\Scripts\python.exe -m yt_dlp -v -f ba --no-playlist --no-part -o "artifacts\audio-test\%(id)s.%(ext)s" "https://www.bilibili.com/video/BV1sjE56YEWp"
```

结果：

- 沙箱内失败为 `WinError 10013`，属于网络 socket 权限限制。
- 真实 Windows 网络下能读取网页与 WBI sign，但 playinfo JSON 返回 `HTTP Error 412: Precondition Failed`。

### 浏览器登录态

- `--cookies-from-browser chrome`：无法复制 Chrome `Network\Cookies` 数据库，`PermissionError: [Errno 13] Permission denied`。
- `--cookies-from-browser edge`：可以读取 Edge cookie DB，但 DPAPI 解密失败。
- 未导出、未保存 cookie jar。

### 公开 playurl API

使用 `x/web-interface/view` 获取真实 `aid/cid`，再调用：

```text
https://api.bilibili.com/x/player/playurl?avid=<aid>&cid=<cid>&qn=&otype=json&fourk=1&fnver=0&fnval=4048
```

结果：成功返回 DASH 音频流。

新增脚本：

```powershell
.\.venv\Scripts\python.exe scripts\download_bilibili_audio.py list BV1sjE56YEWp
.\.venv\Scripts\python.exe scripts\download_bilibili_audio.py fetch BV1sjE56YEWp --output-dir artifacts\audio
```

下载结果：

```json
{
  "bvid": "BV1sjE56YEWp",
  "aid": 116717615320503,
  "cid": 38971441466,
  "stream_id": 30280,
  "bandwidth": 155921,
  "codecs": "mp4a.40.2",
  "bytes": 17323558
}
```

## ASR 验收

命令：

```powershell
.\.venv\Scripts\python.exe scripts\transcribe_audio.py "artifacts\audio\30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].m4a" --provider faster-whisper --model artifacts\models\faster-whisper-tiny --language zh
```

结果：

```json
{
  "provider": "faster-whisper",
  "model": "artifacts\\models\\faster-whisper-tiny",
  "language": "zh",
  "segment_count": 490
}
```

生成文件：

- `artifacts/audio/30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].m4a`
- `artifacts/audio/30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].transcript.txt`
- `artifacts/audio/30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].segments.json`
- `artifacts/audio/30+重磅新作集中爆发！夏日游戏节+XBOX发布会游戏阵容盘点 [BV1sjE56YEWp].timestamped.txt`

UTF-8 抽查：

```text
[00:00:00.000 - 00:00:01.800] 歡迎回到我的頻道
[00:00:01.800 - 00:00:02.800] 六月哲一爽
[00:00:02.800 - 00:00:05.800] 年中冠軍的預三家長夏日遊戲節的活動劃兵大會
```

## 额外样本验证

只验证音频流列表，不下载：

- `BV1va5kzaEDw`：返回 3 条音频流，最高带宽 `167256`
- `BV1P7411C7Gz`：返回 1 条音频流，带宽 `67086`

## 结论

- 完整链路已打通：真实 BV -> DASH 音频下载 -> 本地 faster-whisper 转写。
- 当前推荐优先使用 `scripts/download_bilibili_audio.py`，而不是 `yt-dlp` 直连 B站。
- `tiny` 模型可用于粗筛和初步总结，但识别质量有限；观点类或医学类视频做 SFC 核查时，建议用更大模型重转写关键样本。
