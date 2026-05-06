# Smart Daily - 智能日报系统

每天早上 10 点自动推送日报到邮箱。

## 功能特点

- 多板块信息聚合：AI/科技、政治、财经、民生等
- 邮件自动推送
- GitHub Actions 定时运行，无需服务器

## 快速开始

1. Fork 本仓库
2. 在 Settings → Secrets 中添加：
   - `EMAIL_USER`: 发送邮件的邮箱
   - `EMAIL_PASS`: 邮箱授权码
   - `EMAIL_TO`: 接收邮件的地址
3. 每天 10 点自动推送

## 自定义信息源

编辑 `feeds/channels.opml` 添加你关注的 RSS 源。
