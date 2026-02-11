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
2. 用户已提供 `标题 + 正文 + 视频(本地路径或URL)`：直接进入视频发布流程。
3. 用户已提供 `标题 + 正文 + 图片(本地路径或URL)`：直接进入图文发布流程。
4. 用户只提供网页 URL：先提取网页内容与图片/视频，再给出可发布草稿，等待用户确认。
5. 信息不全：先补齐缺失信息，不要直接发布。

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

## 常用命令

### 0) 启动 / 测试浏览器（不发布）

默认调试端口为 `9222`，可通过 `--port` 自定义（如 `9223`）。

```bash
# 启动测试浏览器（有窗口，推荐）
python scripts/chrome_launcher.py

# 指定端口启动（例如 9223）
python scripts/chrome_launcher.py --port 9223

# 无头启动测试浏览器
python scripts/chrome_launcher.py --headless

# 指定端口 + 无头
python scripts/chrome_launcher.py --headless --port 9223

# 检查当前登录状态
python scripts/cdp_publish.py check-login

# 指定端口检查登录
python scripts/cdp_publish.py --port 9223 check-login

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
```

### 2) 无头发布 or 有头发布（推荐有窗口发布） 图片 url

```bash
python scripts/publish_pipeline.py --headless \
  --port 9223 \
  --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2"
```

```bash
python scripts/publish_pipeline.py --port 9223 --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2"
```


### 3) 无头发布 or 有头发布  使用本地图片发布

```bash
python scripts/publish_pipeline.py --headless \
  --port 9223 \
  --title-file title.txt \
  --content-file content.txt \
  --images "./images/pic1.jpg" "./images/pic2.jpg"
```

```bash
python scripts/publish_pipeline.py --port 9223 --title-file title.txt \
  --content-file content.txt \
  --images "./images/pic1.jpg" "./images/pic2.jpg"
```

### 3.5) 视频发布（本地视频文件）

```bash
python scripts/publish_pipeline.py --headless \
  --port 9223 \
  --title-file title.txt \
  --content-file content.txt \
  --video "C:/videos/my_video.mp4"
```

```bash
python scripts/publish_pipeline.py --port 9223 --title-file title.txt \
  --content-file content.txt \
  --video "C:/videos/my_video.mp4"
```

### 3.6) 视频发布（视频 URL）

```bash
python scripts/publish_pipeline.py --headless \
  --port 9223 \
  --title-file title.txt \
  --content-file content.txt \
  --video-url "https://example.com/video.mp4"
```

```bash
python scripts/publish_pipeline.py --port 9223 --title-file title.txt \
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

### 5) 自动点赞收藏（用户主动要求）

```bash
# 发布后自动点赞和收藏
python scripts/publish_pipeline.py --headless \
  --port 9223 \
  --title-file title.txt \
  --content-file content.txt \
  --image-urls "URL1" "URL2" \
  --auto-publish \
  --auto-like-collect
```

## 失败处理

- 登录失败：提示用户重新扫码登录并重试。
- 图片下载失败：提示更换图片 URL 或改用本地图片。
- 页面选择器失效：提示检查 `scripts/cdp_publish.py` 中选择器并更新。
