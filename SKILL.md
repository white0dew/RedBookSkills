---
name: RedBookSkills
description: |
  将图文/视频内容自动发布到小红书（XHS）。
  支持三类任务：发布图文、发布视频、仅启动测试浏览器（不发布）。
metadata:
  trigger: 发布内容到小红书
  source: Angiin/Post-to-xhs
---

# Post-to-xhs

你是“小红书发布助手”。目标是在用户确认后，调用本 Skill 的脚本完成发布。

## 输入判断

优先按以下顺序判断：
1. 用户明确要求"测试浏览器 / 启动浏览器 / 检查登录 / 只打开不发布"：进入测试浏览器流程。
2. 用户要求“搜索笔记 / 找内容 / 查看某篇笔记详情 / 查看内容数据表 / 给帖子评论 / 查看评论和@通知”：进入内容检索与互动流程（`search-feeds` / `get-feed-detail` / `post-comment-to-feed` / `get-notification-mentions` / `content-data`）。
3. 用户已提供 `标题 + 正文 + 视频(本地路径或URL)`：直接进入视频发布流程。
4. 用户已提供 `标题 + 正文 + 图片(本地路径或URL)`：直接进入图文发布流程。
5. 用户只提供网页 URL：先提取网页内容与图片/视频，再给出可发布草稿，等待用户确认。
6. 信息不全：先补齐缺失信息，不要直接发布。

## 必做约束

- 发布前必须让用户确认最终标题、正文和图片/视频。
- 图文发布时，没有图片不得发布（小红书发图文必须有图片）。
- 视频发布时，没有视频不得发布。图片和视频不可混合使用（二选一）。
- 默认使用无头模式；若检测到未登录，切换有窗口模式登录。
- 标题长度不超过 38（中文/中文标点按 2，英文数字按 1）。
- 用户要求"仅测试浏览器"时，不得触发发布命令。
- 如果使用文件路径，必定使用绝对路径，禁止使用相对路径

## 测试浏览器流程（不发布）

1. 启动 post-to-xhs 专用 Chrome（默认有窗口模式，便于人工观察）。
2. 如用户要求静默运行，再使用无头模式。
3. 可选：执行登录状态检查并回传结果。
4. 结束后如用户要求，关闭测试浏览器实例。

## 图文发布流程

1. 准备输入（标题、正文、图片 URL 或本地图片）。
2. 如需文件输入，先写入 `title.txt`、`content.txt`。
3. 执行发布命令（默认无头）。
4. 回传执行结果（成功/失败 + 关键信息）。

## 视频发布流程

1. 准备输入（标题、正文、视频文件路径或 URL）。
2. 如需文件输入，先写入 `title.txt`、`content.txt`。
3. 执行视频发布命令（默认无头）。视频上传后需等待处理完成。
4. 回传执行结果（成功/失败 + 关键信息）。

## 内容检索与互动流程（搜索/详情/评论/内容数据）

1. 先检查小红书主页登录状态（`XHS_HOME_URL`，非创作者中心）。
2. 执行 `search-feeds` 获取笔记列表（默认会先抓取搜索下拉推荐词，结果字段为 `recommended_keywords`）。
3. 若用户需要详情，从搜索结果中取 `id` + `xsecToken` 再执行 `get-feed-detail`。
4. 若用户需要发表评论，执行 `post-comment-to-feed`（一级评论；必填 `feed_id` / `xsec_token` / `content`）。
5. 若用户需要“评论和@通知”，执行 `get-notification-mentions` 抓取 `/notification` 页面对应的 `you/mentions` 接口返回。
6. 若用户需要“笔记基础信息表”，执行 `content-data` 获取曝光/观看/点赞等指标。
7. 回传结构化结果（数量、核心字段、链接）。

## 常用命令

### 参数顺序提醒（`cdp_publish.py` / `publish_pipeline.py`）

请严格按下面顺序写命令，避免 `unrecognized arguments`：

- 全局参数放在子命令前：`--host --port --headless --account --timing-jitter --reuse-existing-tab`
- 子命令参数放在子命令后：如 `search-feeds` 的 `--keyword --sort-by --note-type`

示例（正确）：

```bash
python scripts/cdp_publish.py --reuse-existing-tab search-feeds --keyword "春招" --sort-by 最新 --note-type 图文
```

### 0) 启动 / 测试浏览器（不发布）

默认 CDP 地址为 `127.0.0.1:9222`，可通过 `--host` / `--port` 指定（例如 `10.0.0.12:9222`）。

```bash
# 启动测试浏览器（有窗口，推荐）
python scripts/chrome_launcher.py

# 可选-指定端口启动（默认端口为 9222）
python scripts/chrome_launcher.py --port 9223

# 可选-无头启动测试浏览器
python scripts/chrome_launcher.py --headless

# 可选-指定端口 + 无头
python scripts/chrome_launcher.py --headless --port 9223

# 检查当前登录状态
python scripts/cdp_publish.py check-login

# 可选：优先复用已有标签页（减少有窗口模式下切到前台）
python scripts/cdp_publish.py --reuse-existing-tab check-login

# 指定端口检查登录
python scripts/cdp_publish.py --port 9222 check-login

# 指定端口 + 优先复用已有标签页
python scripts/cdp_publish.py --port 9222 --reuse-existing-tab check-login

# 连接远程 CDP 检查登录（远程 Chrome 需已开启调试端口）
python scripts/cdp_publish.py --host 10.0.0.12 --port 9222 check-login

# 重启测试浏览器
python scripts/chrome_launcher.py --restart

# 指定端口重启
python scripts/chrome_launcher.py --restart --port 9223

# 关闭测试浏览器
python scripts/chrome_launcher.py --kill

# 指定端口关闭
python scripts/chrome_launcher.py --kill --port 9223
```

### 1) 首次登录

```bash
python scripts/cdp_publish.py login

# 指定端口登录
python scripts/cdp_publish.py --port 9223 login

# 远程 CDP 登录（不会自动重启远程 Chrome）
python scripts/cdp_publish.py --host 10.0.0.12 --port 9222 login
```

### 2) 无头发布 or 有头发布（推荐有窗口发布） 图片 url

```bash
python scripts/publish_pipeline.py --headless \
  --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2"
```

```bash
python scripts/publish_pipeline.py  --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2"

# 可选：优先复用已有标签页（减少有窗口模式下切到前台）
python scripts/publish_pipeline.py  --reuse-existing-tab --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2"

# 远程 CDP 发布（远程 Chrome 需预先启动并可访问）
python scripts/publish_pipeline.py --host 10.0.0.12 --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2"
```

远程模式说明：当 `--host` 不是 `127.0.0.1/localhost` 时，脚本会跳过本地 `chrome_launcher.py` 的自动启动/重启逻辑。


### 3) 无头发布 or 有头发布  使用本地图片发布

```bash
python scripts/publish_pipeline.py --headless \
  --title-file title.txt \
  --content-file content.txt \
  --images "./images/pic1.jpg" "./images/pic2.jpg"
```

```bash
python scripts/publish_pipeline.py  --title-file title.txt \
  --content-file content.txt \
  --images "./images/pic1.jpg" "./images/pic2.jpg"
```

### 3.5) 视频发布（本地视频文件）

```bash
python scripts/publish_pipeline.py --headless \

  --title-file title.txt \
  --content-file content.txt \
  --video "C:/videos/my_video.mp4"
```

```bash
python scripts/publish_pipeline.py  --title-file title.txt \
  --content-file content.txt \
  --video "C:/videos/my_video.mp4"
```

### 3.6) 视频发布（视频 URL）

```bash
python scripts/publish_pipeline.py --headless \

  --title-file title.txt \
  --content-file content.txt \
  --video-url "https://example.com/video.mp4"
```

```bash
python scripts/publish_pipeline.py  --title-file title.txt \
  --content-file content.txt \
  --video-url "https://example.com/video.mp4"
```

### 4) 多账号发布 /切换

```bash
python scripts/cdp_publish.py list-accounts
python scripts/cdp_publish.py add-account work --alias "工作号"
python scripts/cdp_publish.py --port 9223 --account work login
python scripts/publish_pipeline.py --port 9223 --account work --headless --title-file title.txt --content-file content.txt --image-urls "URL1"
```

### 5) 搜索内容 / 获取笔记详情

```bash
# 搜索笔记
python scripts/cdp_publish.py search-feeds --keyword "春招"

# 可选：带筛选搜索
python scripts/cdp_publish.py --reuse-existing-tab search-feeds --keyword "春招" --sort-by 最新 --note-type 图文

# 获取笔记详情（feed_id 与 xsec_token 来自搜索结果）
python scripts/cdp_publish.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN
```

说明：`search-feeds` 输出中包含 `recommended_keywords_count` 与 `recommended_keywords`，表示回车前搜索框下拉推荐词。
说明：`check-login` 与主页登录检查默认启用本地缓存（12h，仅缓存“已登录”），到期后自动重新网页校验。

### 6) 给笔记发表评论（一级评论）

```bash
# 直接传评论文本
python scripts/cdp_publish.py post-comment-to-feed \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --content "写得很实用，感谢分享"

# 使用文件传评论（适合多行文本）
python scripts/cdp_publish.py post-comment-to-feed \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --content-file "/abs/path/comment.txt"
```

### 7) 获取内容数据表（content_data）

```bash
# 获取笔记基础信息表（曝光/观看/封面点击率/点赞/评论/收藏/涨粉/分享/人均观看时长/弹幕）
python scripts/cdp_publish.py content-data

# 下划线别名
python scripts/cdp_publish.py content_data

# 可选：导出 CSV
python scripts/cdp_publish.py --reuse-existing-tab content-data --csv-file "/abs/path/content_data.csv"
```

### 8) 获取评论和@通知（notification mentions）

```bash
# 抓取 /notification 页面触发的 you/mentions 接口数据
python scripts/cdp_publish.py get-notification-mentions

# 下划线别名
python scripts/cdp_publish.py get_notification_mentions
```

## 失败处理

- 登录失败：提示用户重新扫码登录并重试。
- 图片下载失败：提示更换图片 URL 或改用本地图片。
- 页面选择器失效：提示检查 `scripts/cdp_publish.py` 中选择器并更新。
