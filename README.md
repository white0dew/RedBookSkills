# RedBookSkills

自动发布内容到小红书（Xiaohongshu/RED）的命令行工具，也支持仅启动测试浏览器（不发布）。
通过 Chrome DevTools Protocol (CDP) 实现自动化发布，支持多账号管理、无头模式运行、自动搜索素材、点赞评论等功能。

## 功能特性
- **自动化发布**：自动填写标题、正文、上传图片
- **话题标签自动写入**：识别正文最后一行 `#标签`，然后逐渐写入
- **多账号支持**：支持管理多个小红书账号，各账号 Cookie 隔离
- **无头模式**：支持后台运行，无需显示浏览器窗口
- **图片下载**：支持从 URL 自动下载图片，自动添加 Referer 绕过防盗链
- **登录检测**：自动检测登录状态，未登录时自动切换到有窗口模式扫码

## 安装

### 环境要求

- Python 3.10+
- Google Chrome 浏览器
- Windows 操作系统（目前仅测试 Windows）

### 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 首次登录

```bash
python scripts/cdp_publish.py login
```

在弹出的 Chrome 窗口中扫码登录小红书。

### 2. 启动/测试浏览器（不发布）

```bash
# 启动测试浏览器（有窗口，推荐）
python scripts/chrome_launcher.py

# 无头启动测试浏览器
python scripts/chrome_launcher.py --headless

# 检查当前登录状态
python scripts/cdp_publish.py check-login

# 重启测试浏览器
python scripts/chrome_launcher.py --restart

# 关闭测试浏览器
python scripts/chrome_launcher.py --kill
```

### 3. 发布内容

```bash
# 无头模式（推荐）
python scripts/publish_pipeline.py --headless \
    --title "文章标题" \
    --content "文章正文" \
    --image-urls "https://example.com/image.jpg"

# 有窗口模式（可预览）
python scripts/publish_pipeline.py \
    --title "文章标题" \
    --content "文章正文" \
    --image-urls "https://example.com/image.jpg"

# 从文件读取内容
python scripts/publish_pipeline.py --headless \
    --title-file title.txt \
    --content-file content.txt \
    --image-urls "https://example.com/image.jpg"

# 正文最后一行可放话题标签（最多 10 个）
# 例如 content.txt 最后一行：
# #春招 #26届 #校招 #求职 #找工作

# 使用本地图片
python scripts/publish_pipeline.py --headless \
    --title "文章标题" \
    --content "文章正文" \
    --images "C:\path\to\image.jpg"

# 发布后自动点赞和收藏
python scripts/publish_pipeline.py --headless \
    --title "文章标题" \
    --content "文章正文" \
    --image-urls "https://example.com/image.jpg" \
    --auto-publish \
    --auto-like-collect
```

### 4. 多账号管理

```bash
# 列出所有账号
python scripts/cdp_publish.py list-accounts

# 添加新账号
python scripts/cdp_publish.py add-account myaccount --alias "我的账号"

# 登录指定账号
python scripts/cdp_publish.py --account myaccount login

# 使用指定账号发布
python scripts/publish_pipeline.py --account myaccount --headless \
    --title "标题" --content "正文" --image-urls "URL"

# 设置默认账号
python scripts/cdp_publish.py set-default-account myaccount

# 切换账号（清除当前登录，重新扫码）
python scripts/cdp_publish.py switch-account
```

## 命令参考

### 话题标签（publish_pipeline.py）

- 从正文中提取规则：若“最后一个非空行”全部由 `#标签` 组成，则提取为话题标签并从正文移除。
- 标签输入策略：逐个输入 `#标签`，等待 `3` 秒，再发送 `Enter` 进行确认。
- 建议数量：`1-10` 个标签；超过平台限制时请手动精简。
- 示例（正文最后一行）：`#春招 #26届 #校招 #春招规划 #面试`

### publish_pipeline.py

统一发布入口，一条命令完成全部流程。

```bash
python scripts/publish_pipeline.py [选项]

选项:
  --title TEXT           文章标题
  --title-file FILE      从文件读取标题
  --content TEXT         文章正文
  --content-file FILE    从文件读取正文
  --image-urls URL...    图片 URL 列表
  --images FILE...       本地图片文件列表
  --headless             无头模式（无浏览器窗口）
  --account NAME         指定账号
  --auto-publish         自动点击发布（跳过确认）
  --auto-like-collect    发布后自动点赞和收藏笔记
```

### cdp_publish.py

底层发布控制，支持分步操作。

```bash
# 检查登录状态
python scripts/cdp_publish.py check-login

# 填写表单（不发布）
python scripts/cdp_publish.py fill --title "标题" --content "正文" --images img.jpg

# 点击发布按钮
python scripts/cdp_publish.py click-publish

# 账号管理
python scripts/cdp_publish.py login
python scripts/cdp_publish.py list-accounts
python scripts/cdp_publish.py add-account NAME [--alias ALIAS]
python scripts/cdp_publish.py remove-account NAME [--delete-profile]
python scripts/cdp_publish.py set-default-account NAME
python scripts/cdp_publish.py switch-account
```

### chrome_launcher.py

Chrome 浏览器管理。

```bash
# 启动 Chrome
python scripts/chrome_launcher.py
python scripts/chrome_launcher.py --headless

# 重启 Chrome
python scripts/chrome_launcher.py --restart

# 关闭 Chrome
python scripts/chrome_launcher.py --kill
```

## 支持各种 Skill 工具

本项目可作为 Claude Code、OpenCode 等支持 Skill 的工具使用，只需将项目复制到 `.claude/skills/post-to-xhs/` 目录，并添加 `SKILL.md` 文件即可。

详见 [docs/claude-code-integration.md](docs/claude-code-integration.md)

## 注意事项

1. **仅供学习研究**：请遵守小红书平台规则，不要用于违规内容发布
2. **登录安全**：Cookie 存储在本地 Chrome Profile 中，请勿泄露
3. **选择器更新**：如果小红书页面结构变化导致发布失败，需要更新 `cdp_publish.py` 中的选择器

## RoadMap
- [x] 支持更多账号管理功能
- [x] 支持发布功能
- [] 增加发布后自动互动功能（点赞、收藏）
- [] 支持自动评论、点赞
- [] 支持素材检索功能
- [ ] 增加更多错误处理机制


## 许可证

MIT License

## 致谢
灵感来自：[Post-to-xhs](https://github.com/Angiin/Post-to-xhs)
