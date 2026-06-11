# 2026-06-10 初始验证

## 环境

- 项目目录：`C:\Users\15760\Documents\B站视频总结`
- Python：3.11.9
- 项目虚拟环境：`.venv`
- `yt-dlp`：2026.6.9

## 已验证命令

```powershell
.\.venv\Scripts\python.exe scripts\fetch_subtitles.py list "http://www.bilibili.com/video/av291584001"
.\.venv\Scripts\python.exe scripts\fetch_subtitles.py list "http://www.bilibili.com/video/av513767926"
.\.venv\Scripts\python.exe scripts\fetch_subtitles.py list "http://www.bilibili.com/video/av116720953988617"
```

## 真实候选

| 类型 | 标题 | 链接 | 来源 | 当前结果 |
|---|---|---|---|---|
| 工具类 | 学12分钟就能做出PPT【ppt简易制作教程】干货全拿走，开店就赚钱 | http://www.bilibili.com/video/av291584001 | `bilisearch:PPT 教程` | 可读取元数据；未登录时仅看到 `danmaku xml` |
| 工具类 | PPT小白必看！怎样在PPT中正确插入视频！ | http://www.bilibili.com/video/av567705371 | `bilisearch:PPT 教程` | 仅检索到候选，未进一步验证 |
| 观点类 | 求求大家真的不用太勤奋！尤其是喜欢做笔记的同学！ | http://www.bilibili.com/video/av513767926 | `bilisearch:学习方法 观点` | 可读取元数据；未登录时仅看到 `danmaku xml` |
| 观点类 | 为什么你总是抓不住重点：因为你没有「优先级判断标准」 | http://www.bilibili.com/video/av116300835718715 | `bilisearch:学习方法 观点` | 仅检索到候选，未进一步验证 |
| 信息类 | 6月10日《新闻联播》要点解读及政策动向。 | http://www.bilibili.com/video/av116720953988617 | `bilisearch:新闻 科普 解读` | 可读取元数据；未登录时仅看到 `danmaku xml` |

## 关键发现

1. `yt-dlp` 可以在这台机器上检索 B站公开视频并读取视频元数据。
2. 部分搜索结果会触发 `HTTP 412 Precondition Failed`，说明 B站搜索/元数据链路存在风控。
3. 对已验证的 3 个公开视频，未登录状态下 `--list-subs` 只显示 `danmaku xml`。
4. 这意味着“公开视频直读字幕”并不可靠，真实工作流需要把“浏览器登录态辅助访问”作为重要兜底路径。
5. 使用 `--cookies-from-browser chrome` 进行了 1 次试验，但当前机器返回 `Failed to decrypt with DPAPI`，所以这条路在当前环境下尚未跑通。

## 当前阻塞

- 阻塞 1：B站对部分候选返回 `HTTP 412`
- 阻塞 2：字幕往往需要登录态
- 阻塞 3：本机当前对 Chrome cookie 的 DPAPI 解密失败

## 建议下一步

1. 试 `edge` 或当前实际登录的浏览器，而不是默认 `chrome`
2. 在已登录浏览器中手动打开目标视频页，再用更保守的方式验证
3. 如果字幕仍无法稳定获取，补一条 ASR 兜底路线
4. 用户手动提供 3-5 个高优先级真实链接后，优先验证这些链接而不是泛搜索

