# Claude Code 集成指南

本项目可作为 Claude Code 的 Skill 使用，让 AI 助手能够自动发布内容到小红书，或仅启动测试浏览器（不发布）。

## 安装

将项目复制到 Claude Code 的 skills 目录：

```bash
cp -r Post-to-xhs ~/.claude/skills/post-to-xhs
```

## 创建 SKILL.md

在 `~/.claude/skills/post-to-xhs/` 目录下创建 `SKILL.md` 文件：

```markdown
# 小红书内容发布

根据用户输入自动判断发布方式，简化发布流程。

## 工作流程

- 用户要求“启动浏览器/检查登录/仅测试不发布” → 进入测试浏览器流程
- 用户提供完整内容 + 图片/图片URL → 直接进入发布流程
- 用户提供网页 URL → WebFetch 提取内容和图片 → 适当总结 → 发布流程

## 测试浏览器命令（不发布）

```bash
# 启动测试浏览器（有窗口，推荐）
python scripts/chrome_launcher.py

# 无头启动测试浏览器
python scripts/chrome_launcher.py --headless

# 检查登录状态
python scripts/cdp_publish.py check-login

# 重启测试浏览器
python scripts/chrome_launcher.py --restart

# 关闭测试浏览器
python scripts/chrome_launcher.py --kill
```

## 发布命令

### 无头模式（推荐）

```bash
python scripts/publish_pipeline.py --headless \
    --title-file title.txt \
    --content-file content.txt \
    --image-urls "URL1" "URL2"
```

### 有窗口模式

```bash
python scripts/publish_pipeline.py \
    --title-file title.txt \
    --content-file content.txt \
    --image-urls "URL1" "URL2"
```

## 标题规则

标题长度 ≤ 38，计算规则：
- 中文字符和中文标点：每个计 2
- 英文字母/数字/空格/ASCII标点：每个计 1

## 注意事项

- 发布前必须让用户确认内容
- 小红书发布必须有图片
- 如需登录，脚本会自动切换到有窗口模式
- 用户仅要求测试浏览器时，不执行发布命令
```

## 使用示例

配置完成后，在 Claude Code 中可以这样使用：

```
用户: 发布这个链接到小红书 https://example.com/article

Claude: [使用 WebFetch 提取内容和图片]
        [总结内容，生成标题]
        [请求用户确认]
        [执行发布脚本]

用户: 帮我先打开小红书测试浏览器，不要发布

Claude: [执行 python scripts/chrome_launcher.py]
        [执行 python scripts/cdp_publish.py check-login]
        [回传浏览器和登录状态]
```

## 账号管理

支持多账号发布：

```bash
# 添加账号
python scripts/cdp_publish.py add-account work --alias "工作账号"

# 登录账号
python scripts/cdp_publish.py --account work login

# 使用指定账号发布
python scripts/publish_pipeline.py --account work --headless ...
```
