# 新增功能计划：post_comment_to_feed（一级评论）

## 目标
- 在 `scripts/cdp_publish.py` 增加对指定笔记发表评论（一级评论）的 CLI 能力。

## 实施步骤
- [x] 参考 `xiaohongshu-mcp` 的 `post_comment_to_feed` 调用链，确认参数与页面交互选择器。
- [x] 在 `XiaohongshuPublisher` 中实现 `post_comment_to_feed(feed_id, xsec_token, content)`。
- [x] 增加页面可访问性检查（删除/私密/失效等场景提前报错）。
- [x] 在 CLI 中新增 `post-comment-to-feed`（别名 `post_comment_to_feed`）子命令。
- [x] 支持 `--content` 与 `--content-file` 两种内容输入方式。
- [x] 更新 `README.md` 与 `SKILL.md` 的功能说明和命令示例。
- [ ] 冒烟验证：在已登录测试账号上执行新命令并确认评论发出（不做破坏性自动发布流程）。

---

# 新增功能计划：get_notification_mentions（评论和@通知接口）

## 目标
- 在 `scripts/cdp_publish.py` 增加抓取通知页 `you/mentions` 接口数据的 CLI 能力。

## 实施步骤
- [x] 在 `XiaohongshuPublisher` 中实现 `get_notification_mentions(wait_seconds)`。
- [x] 增加通知页 tab 自动点击逻辑，尽量触发 `https://edith.xiaohongshu.com/api/sns/web/v1/you/mentions` 请求。
- [x] 在 CLI 中新增 `get-notification-mentions`（别名 `get_notification_mentions`）子命令。
- [x] 输出结构化结果（请求 URL、条数、分页游标、原始 payload）。
- [x] 更新 `README.md` 与 `SKILL.md` 的功能说明和命令示例。
- [ ] 冒烟验证：在已登录测试账号上执行新命令并确认可抓到 `you/mentions` 返回。

---

# 新增功能计划：search-feeds 下拉推荐词抓取

## 目标
- 在执行 `search-feeds` 时，先输入关键词并抓取下拉推荐词（SEO 相关词），再回车获取 feed 列表。

## 实施步骤
- [x] 在 `scripts/feed_explorer.py` 新增搜索框输入、下拉推荐词抓取与回车提交逻辑。
- [x] 在 `scripts/cdp_publish.py` 的 `search_feeds` 中接入该流程，并保留 URL 导航兜底。
- [x] 在 `search-feeds` JSON 输出中增加 `recommended_keywords_count` 与 `recommended_keywords` 字段。
- [x] 更新 `README.md` 与 `SKILL.md` 的功能说明。
- [ ] 冒烟验证：在已登录测试账号上执行 `search-feeds --keyword "春招"`，确认输出含推荐词且 feed 正常返回。

---

# 新增功能计划：登录状态本地缓存（check_login / check_home_login）

## 目标
- 为 `check_login` 与 `check_home_login` 增加本地文件缓存，默认 12h 内复用登录态，减少重复网页校验。

## 实施步骤
- [x] 在 `scripts/cdp_publish.py` 增加登录缓存读写逻辑（`tmp/login_status_cache.json`）。
- [x] `check_login` / `check_home_login` 接入缓存读取与写入（仅缓存“已登录”结果）。
- [x] 在 `clear_cookies` / `open_login_page` 时清理对应缓存，避免脏状态。
- [x] 缓存策略固定写死为 12h（不新增 CLI 参数）。
- [x] 更新 `README.md` 与 `SKILL.md` 的命令示例与说明。
- [ ] 冒烟验证：执行 `check-login` 两次确认第二次命中缓存；等待缓存过期后验证会自动重新网页校验。
