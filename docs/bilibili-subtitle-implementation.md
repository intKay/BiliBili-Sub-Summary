# B站字幕实现笔记

## 来源

本项目的字幕实现参考了 `Bilibili Evolved` 中这几处源码：

- `registry/lib/components/video/subtitle/download/utils.ts`
- `registry/lib/components/video/subtitle/download/index.ts`
- `registry/lib/components/video/subtitle/subtitle-converter.ts`
- `src/components/video/ass-utils.ts`

核心思路不是抓页面 DOM，而是走两段 API：

1. `x/web-interface/view?bvid=...`
2. `x/player/wbi/v2?aid=...&cid=...`

然后从 `subtitle.subtitles` 中挑一个 `subtitle_url` 下载 JSON。

## 我们的实现

脚本位置：

- [scripts/fetch_bilibili_subtitles.py](C:/Users/15760/Documents/B站视频总结/scripts/fetch_bilibili_subtitles.py)

支持：

- URL/BV 号输入
- 多 P 视频的 `--page`
- 列出字幕语言
- 下载 `json`
- 转换为 `ass`

## 命令

列出字幕：

```powershell
python scripts/fetch_bilibili_subtitles.py list "https://www.bilibili.com/video/BV..."
```

下载 JSON：

```powershell
python scripts/fetch_bilibili_subtitles.py fetch "https://www.bilibili.com/video/BV..." --format json --output-dir artifacts
```

下载 ASS：

```powershell
python scripts/fetch_bilibili_subtitles.py fetch "https://www.bilibili.com/video/BV..." --format ass --output-dir artifacts
```

## 当前样例验证

已验证公开元数据接口可正常解析：

- `BV1va5kzaEDw`
- `BV1sjE56YEWp`
- `BV1P7411C7Gz`

但这 3 个样例在 `x/player/wbi/v2` 返回中的字幕数目前都是 `0`，所以暂时不是脚本失效，而是这些视频本身没有可下载字幕。

## 后续可扩展

1. 接 ASR 兜底
2. 接浏览器登录态页面提取
3. 支持批量链接清单

