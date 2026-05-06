"""邮件推送模块 - 支持发送 HTML 格式的日报邮件"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from typing import Any


def get_email_config() -> dict[str, Any]:
    """从环境变量读取邮件配置"""
    return {
        "smtp_server": os.environ.get("EMAIL_SMTP", "smtp.163.com"),
        "smtp_port": int(os.environ.get("EMAIL_PORT", 465)),
        "username": os.environ.get("EMAIL_USER", ""),
        "password": os.environ.get("EMAIL_PASS", ""),
        "from_name": os.environ.get("EMAIL_FROM_NAME", "Smart Daily"),
        "to_addr": os.environ.get("EMAIL_TO", ""),
    }


def render_email_html(
    title: str,
    date_str: str,
    sections: list[dict[str, Any]],
) -> str:
    """渲染邮件 HTML 内容

    Args:
        title: 邮件标题
        date_str: 日期字符串
        sections: 板块列表，每个板块包含 name 和 items

    Returns:
        HTML 字符串
    """
    sections_html = ""
    for section in sections:
        section_name = section.get("name", "未分类")
        items = section.get("items", [])

        if not items:
            continue

        items_html = ""
        for item in items[:10]:  # 每个板块最多10条
            item_title = item.get("title", "")
            item_url = item.get("url", "")
            item_source = item.get("source", "")
            items_html += f"""
            <li style="margin-bottom: 8px;">
              <a href="{item_url}" style="color: #1a73e8; text-decoration: none;">{item_title}</a>
              <span style="color: #999; font-size: 12px;"> - {item_source}</span>
            </li>
            """

        sections_html += f"""
        <div style="margin-bottom: 24px;">
          <h2 style="color: #333; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">
            {section_name}
          </h2>
          <ul style="list-style: none; padding-left: 0;">
            {items_html}
          </ul>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                 max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
      <div style="background-color: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h1 style="color: #1a73e8; margin-top: 0;">{title}</h1>
        <p style="color: #666; font-size: 14px;">{date_str}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 16px 0;">
        {sections_html}
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
          由 Smart Daily 自动生成 | <a href="https://github.com" style="color: #1a73e8;">项目地址</a>
        </p>
      </div>
    </body>
    </html>
    """
    return html


def send_email(
    subject: str,
    html_content: str,
    config: dict[str, Any] | None = None,
) -> bool:
    """发送邮件

    Args:
        subject: 邮件主题
        html_content: HTML 内容
        config: 邮件配置，不传则从环境变量读取

    Returns:
        是否发送成功
    """
    if config is None:
        config = get_email_config()

    if not config.get("username") or not config.get("password") or not config.get("to_addr"):
        print("错误：邮件配置不完整，请检查 EMAIL_USER, EMAIL_PASS, EMAIL_TO")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((config.get("from_name", "Smart Daily"), config["username"]))
    msg["To"] = config["to_addr"]

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"]) as server:
            server.login(config["username"], config["password"])
            server.sendmail(config["username"], [config["to_addr"]], msg.as_string())
        print(f"邮件发送成功: {subject}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


def send_daily_report(items_by_section: dict[str, list[dict[str, Any]]]) -> bool:
    """发送日报邮件

    Args:
        items_by_section: 按板块分类的新闻条目

    Returns:
        是否发送成功
    """
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")
    title = f"Smart Daily 日报 - {date_str}"

    sections = [{"name": name, "items": items} for name, items in items_by_section.items()]

    html = render_email_html(title, date_str, sections)
    return send_email(title, html)


# 测试代码
if __name__ == "__main__":
    # 测试发送
    test_sections = {
        "AI/科技": [
            {"title": "OpenAI 发布 GPT-5", "url": "https://example.com/1", "source": "OpenAI"},
            {"title": "Claude 4 发布", "url": "https://example.com/2", "source": "Anthropic"},
        ],
        "财经": [
            {"title": "美联储宣布降息", "url": "https://example.com/3", "source": "华尔街日报"},
        ],
    }

    print("测试邮件发送...")
    print("请确保已配置环境变量: EMAIL_USER, EMAIL_PASS, EMAIL_TO")
    # send_daily_report(test_sections)
