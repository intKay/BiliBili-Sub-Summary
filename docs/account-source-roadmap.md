# 账号相关来源与批量总结改进路线

## 目标

把 B站视频分析从“用户手动给单个链接”扩展到：

1. 更便捷地获取字幕。
2. 从同一个 UP 主找到类似视频一起总结。
3. 从关注、收藏、稍后再看、动态等账号相关页面收集候选。
4. 在需要时临时读取本机浏览器登录态，但不保存账号凭据。

这条路线的边界是：项目可以使用用户当前浏览器里已经可见、已经授权的内容；不在仓库、日志、样例或中间产物里保存 cookies、SESSDATA、cookie jar、浏览器 profile、完整登录页面 HTML。

## 来源能力分层

### L0：手动链接

用户直接提供一个或多个视频链接。

适合先做：

- 单视频字幕下载
- 单视频 ASR 兜底
- 单视频 SFC / 信息总结
- 小批量 `videos.txt` 总结

优点是稳定、隐私风险最低。缺点是候选发现需要人工完成。

### L1：公开视频和公开视频列表

从公开视频、UP 主页、公开视频合集、搜索结果里收集候选。

适合做：

- 同一个 UP 主的公开投稿列表
- 同主题关键词筛选
- 同 UP 主多视频合并总结
- 公开视频之间的重复观点、补充观点、变化路线对比

这一层不依赖账号态，应该优先实现。

### L2：浏览器界面提取

用户在已登录浏览器中打开收藏、稍后再看、关注动态、UP 投稿页或搜索结果页，工具只从当前可见页面中提取：

- 视频链接
- 标题
- UP 主
- 时长
- 可见互动数据
- 来源页面类型

推荐作为账号相关来源的首选方案。它不需要导出 cookie，也不需要保存完整页面。实现时优先支持用户手动复制页面文本、复制链接列表、导出书签，后续再考虑浏览器自动化读取当前页面 DOM。

禁止保存：

- 完整登录页面 HTML
- cookies / SESSDATA
- 浏览器 profile
- 私信、通知、账号设置、个人资料等与视频候选无关的内容

### L3：临时登录态读取

当字幕、稍后再看、收藏夹或某些账号可见内容需要登录态时，允许使用临时浏览器登录态，例如：

```powershell
.\.venv\Scripts\python.exe scripts/fetch_subtitles.py fetch "https://www.bilibili.com/video/BV..." --cookies-from-browser chrome
```

原则：

1. 只在命令运行期间让工具访问浏览器已有登录态。
2. 不导出、不复制、不提交 cookie 文件。
3. 命令输出中不打印 cookie、SESSDATA 或请求头。
4. 只保存视频候选、字幕、分析结果和必要时间戳。
5. 出现 DPAPI、浏览器解密、权限错误时，降级到 L2 页面可见提取或手动链接。

这一层适合用于“获取已经有权限的视频字幕”，不适合做大规模账号数据抓取。

### L4：持久化账号凭据

不做。

不在项目里实现保存 cookie jar、SESSDATA、浏览器 profile、完整登录态快照，也不把这类做法写成推荐教程。

## 推荐实现顺序

### 阶段 1：统一字幕入口

新增一个统一入口，目标命令类似：

```powershell
.\.venv\Scripts\python.exe scripts/bili_summary.py fetch-sub "https://www.bilibili.com/video/BV..."
```

行为：

1. 先尝试 `yt-dlp` 字幕。
2. 失败后尝试项目内 B站字幕脚本。
3. 如果没有字幕，提示或自动进入音频下载 + ASR。
4. 下载后自动清洗为 `.clean.txt`。
5. 输出到 `artifacts/runs/<BV>/`。
6. 记录 `manifest.json`，包含来源、字幕语言、是否使用登录态、是否 ASR、失败原因。

可选参数：

```powershell
--cookies-from-browser chrome
--language zh
--page 1
--asr-if-missing
--output-dir artifacts/runs
```

### 阶段 2：批量视频队列

支持一个 `videos.txt` 或 `candidates.json`：

```powershell
.\.venv\Scripts\python.exe scripts/bili_summary.py fetch-batch samples/videos.txt
```

每个候选保存：

```json
{
  "url": "https://www.bilibili.com/video/BV...",
  "title": "",
  "up_name": "",
  "source": "manual | up-public | browser-visible | watch-later | favorite | following",
  "topic": "",
  "priority": 0,
  "notes": ""
}
```

输出批量状态表：

- `ready`: 已有可分析文本
- `missing_subtitle`: 无字幕，等待 ASR
- `asr_ready`: 已转写
- `blocked_login`: 需要登录态或浏览器页面
- `blocked_evidence`: 需要用户提供页面/截图/链接

### 阶段 3：同 UP 主类似视频收集

目标命令类似：

```powershell
.\.venv\Scripts\python.exe scripts/bili_summary.py collect-up "UP主页URL" --keyword "AI 编程" --limit 20
```

候选排序信号：

1. 标题关键词匹配。
2. 视频简介关键词匹配。
3. 分区/合集/系列标题相近。
4. 时长适中，太短或太长降权。
5. 播放、收藏、点赞等可见互动数据。
6. 有字幕或字幕可获取。

输出：

- `artifacts/candidates/up-<mid>-<topic>.json`
- `artifacts/candidates/up-<mid>-<topic>.md`

后续总结方式：

```powershell
.\.venv\Scripts\python.exe scripts/bili_summary.py summarize-batch artifacts/candidates/up-xxx.json --mode information
```

总结重点：

- 这个 UP 对同一主题的核心观点
- 每个视频负责的子问题
- 重复内容和新增内容
- 哪几个视频最值得优先看
- 哪些观点需要事实核查或反方视角

### 阶段 4：浏览器界面提取

先做低技术、低风险版本：

```powershell
.\.venv\Scripts\python.exe scripts/extract_visible_bili_links.py --from-text artifacts/input/page-copy.txt --source watch-later
```

支持输入：

- 用户复制的页面文本
- 用户复制的一批链接
- 浏览器书签导出
- 手动保存的仅含链接和标题的简化文本

只输出候选清单，不保存完整页面。

后续再做浏览器自动化版本：

```powershell
.\.venv\Scripts\python.exe scripts/extract_visible_bili_links.py --from-browser chrome --source favorite
```

自动化版本只读取当前标签页可见的链接和标题；默认不滚动到底、不抓取隐藏内容、不进入私信/通知/账号设置。

### 阶段 5：关注、收藏、稍后再看

推荐入口顺序：

1. 用户打开页面，使用 L2 浏览器界面提取。
2. 如果页面需要登录但浏览器已经登录，仍只提取可见候选。
3. 如果字幕下载需要登录态，再对具体视频使用 L3 `--cookies-from-browser`。
4. 不做持久化账号同步。

每种来源记录来源类型：

- `favorite`: 收藏夹
- `watch-later`: 稍后再看
- `following`: 关注动态
- `history`: 历史记录
- `up-public`: UP 公开视频
- `search`: 搜索结果

## 需要用户逐项决定的点

1. 统一入口命令名：`bili_summary.py` 还是拆成多个脚本。
2. 缺字幕时是否默认自动 ASR，还是每次先询问。
3. 批量任务默认处理多少个视频，建议先从 5 个开始。
4. 浏览器界面提取先支持“用户复制页面文本”，还是直接做浏览器自动化。
5. 同 UP 主类似视频排序是否更看重关键词、播放量、收藏量、发布时间，还是字幕可用性。
6. 批量总结输出更偏“看不看推荐”，还是“知识库卡片”。

## 最小可用版本

MVP 只需要三件事：

1. `fetch-sub`：单视频字幕/ASR 一键入口。
2. `fetch-batch`：从 `videos.txt` 批量获取可分析文本。
3. `extract-visible`：从用户复制的收藏/稍后再看页面文本里提取 BV 链接和标题。

MVP 不需要直接操作账号 API，也不需要保存登录态。

