"""邮件推送模块 - 支持发送 HTML 格式的日报邮件"""

import os
import random
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


SECTION_STYLES = {
    "AI/科技": {"label": "AI", "color": "#d71920", "bg_light": "#fff2f2"},
    "政治": {"label": "POL", "color": "#1d4ed8", "bg_light": "#eff6ff"},
    "财经": {"label": "FIN", "color": "#dc2626", "bg_light": "#fff1f2"},
    "民生": {"label": "LIFE", "color": "#059669", "bg_light": "#ecfdf5"},
    "科技": {"label": "TECH", "color": "#7c3aed", "bg_light": "#f5f3ff"},
    "其他": {"label": "NEWS", "color": "#525252", "bg_light": "#f5f5f5"},
}

DEFAULT_STYLE = {"label": "NEWS", "color": "#525252", "bg_light": "#f5f5f5"}

SECTION_IMAGES = {
    "AI/科技": [
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1655720828018-edd2daec9349?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1684369176170-463e84248b70?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1531746790095-e5a6645795ed?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1555255707-c07966088b7b?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1507146153580-69a1fe6d8aa1?w=400&h=200&fit=crop",
    ],
    "政治": [
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1575540325296-424c27aedec4?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1569025743873-ea3a9ber647f?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1555848962-6e79363ec58f?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1523292562811-8fa7962a78c8?w=400&h=200&fit=crop",
    ],
    "财经": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1642790106117-e829e14a795f?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1462206092226-f46025ffe607?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=400&h=200&fit=crop",
    ],
    "民生": [
        "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1491438590914-bc09fcaaf77a?w=400&h=200&fit=crop",
    ],
    "科技": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1496065187959-7f07b8353c55?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1488229297570-58520851e868?w=400&h=200&fit=crop",
    ],
    "其他": [
        "https://images.unsplash.com/photo-1504711434969-e33886168d4c?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1432821596592-e2c18b78144f?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400&h=200&fit=crop",
        "https://images.unsplash.com/photo-1586339949216-35c2747cc36d?w=400&h=200&fit=crop",
    ],
}


def _fill_missing_images(section_name: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pool = list(SECTION_IMAGES.get(section_name, SECTION_IMAGES["其他"]))
    random.shuffle(pool)
    pool_idx = 0
    for item in items:
        if not item.get("image_url"):
            item["image_url"] = pool[pool_idx % len(pool)]
            pool_idx += 1
    return items


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _render_source(source: str, style: dict[str, str]) -> str:
    return (
        f'<span style="display:inline-block;background-color:{style["bg_light"]};'
        f'color:{style["color"]};font-size:11px;font-weight:700;'
        f'line-height:16px;padding:0 6px;border-radius:2px;">{source}</span>'
    )


def _render_hero_item(item: dict[str, Any], style: dict[str, str]) -> str:
    title = _html_escape(item.get("title", ""))
    url = _html_escape(item.get("url", ""))
    source = _html_escape(item.get("source", ""))
    image_url = _html_escape(str(item.get("image_url") or ""))

    return (
        f'<tr><td style="padding:0 24px 14px 24px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-bottom:2px solid #111111;">'
        f'<tr>'
        f'<td width="260" valign="top" style="padding:0 18px 16px 0;">'
        f'<a href="{url}" style="text-decoration:none;">'
        f'<img src="{image_url}" width="260" height="156" alt="" '
        f'style="display:block;width:260px;height:156px;object-fit:cover;border:0;">'
        f'</a>'
        f'</td>'
        f'<td valign="top" style="padding:0 0 16px 0;">'
        f'<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
        f'font-size:12px;line-height:16px;margin-bottom:8px;">{_render_source(source, style)}</div>'
        f'<a href="{url}" style="display:block;color:#111111;text-decoration:none;'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
        f'font-size:21px;font-weight:800;line-height:1.28;">{title}</a>'
        f'<div style="margin-top:10px;color:#8a8a8a;font-family:-apple-system,BlinkMacSystemFont,'
        f'\'Segoe UI\',Roboto,sans-serif;font-size:12px;line-height:18px;">今日重点</div>'
        f'</td>'
        f'</tr>'
        f'</table>'
        f'</td></tr>'
    )


def _render_list_item(item: dict[str, Any], index: int, style: dict[str, str]) -> str:
    title = _html_escape(item.get("title", ""))
    url = _html_escape(item.get("url", ""))
    source = _html_escape(item.get("source", ""))
    image_url = _html_escape(str(item.get("image_url") or ""))

    return (
        f'<tr>'
        f'<td valign="top" width="34" style="padding:14px 10px 14px 0;'
        f'border-bottom:1px solid #eeeeee;color:{style["color"]};'
        f'font-family:Georgia,serif;font-size:22px;font-weight:700;line-height:1;">'
        f'{index:02d}</td>'
        f'<td valign="top" style="padding:14px 14px 14px 0;border-bottom:1px solid #eeeeee;">'
        f'<a href="{url}" style="display:block;color:#1f1f1f;text-decoration:none;'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
        f'font-size:15px;font-weight:700;line-height:1.45;">{title}</a>'
        f'<div style="margin-top:7px;font-family:-apple-system,BlinkMacSystemFont,'
        f'\'Segoe UI\',Roboto,sans-serif;font-size:12px;line-height:16px;">'
        f'{_render_source(source, style)}</div>'
        f'</td>'
        f'<td valign="top" width="128" style="padding:14px 0;border-bottom:1px solid #eeeeee;">'
        f'<a href="{url}" style="text-decoration:none;">'
        f'<img src="{image_url}" width="128" height="78" alt="" '
        f'style="display:block;width:128px;height:78px;object-fit:cover;border:0;">'
        f'</a>'
        f'</td>'
        f'</tr>'
    )


def _render_section(section_name: str, items: list[dict[str, Any]]) -> str:
    style = SECTION_STYLES.get(section_name, DEFAULT_STYLE)
    display_items = _fill_missing_images(section_name, [dict(i) for i in items[:6]])
    if not display_items:
        return ""

    header = (
        f'<tr><td style="padding:32px 24px 16px 24px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr>'
        f'<td style="border-top:4px solid #111111;padding-top:12px;">'
        f'<span style="display:inline-block;background-color:{style["color"]};'
        f'color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
        f'font-size:11px;font-weight:800;line-height:18px;padding:0 7px;letter-spacing:0.4px;">'
        f'{_html_escape(style["label"])}</span>'
        f'<span style="padding-left:10px;color:#111111;font-family:-apple-system,BlinkMacSystemFont,'
        f'\'Segoe UI\',Roboto,sans-serif;font-size:22px;font-weight:800;line-height:26px;">'
        f'{_html_escape(section_name)}</span>'
        f'</td>'
        f'<td align="right" style="border-top:4px solid #111111;padding-top:15px;color:#8a8a8a;'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
        f'font-size:12px;">{len(display_items)} 条精选</td>'
        f'</tr>'
        f'</table>'
        f'</td></tr>'
    )

    list_rows = "".join(
        _render_list_item(item, index, style)
        for index, item in enumerate(display_items[1:], start=2)
    )
    list_table = (
        f'<tr><td style="padding:0 24px 4px 24px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'{list_rows}'
        f'</table>'
        f'</td></tr>'
    )

    return header + _render_hero_item(display_items[0], style) + list_table


def render_email_html(
    title: str,
    date_str: str,
    sections: list[dict[str, Any]],
) -> str:
    total_count = sum(len(s.get("items", [])) for s in sections)
    section_count = sum(1 for s in sections if s.get("items"))

    stats_chips = ""
    for s in sections:
        s_items = s.get("items", [])
        if not s_items:
            continue
        s_name = s.get("name", "")
        s_style = SECTION_STYLES.get(s_name, DEFAULT_STYLE)
        stats_chips += (
            f'<td style="padding:4px 9px;background-color:#ffffff;'
            f'border:1px solid #e5e5e5;color:#111111;font-size:12px;font-weight:700;">'
            f'<span style="color:{s_style["color"]};">{_html_escape(s_style["label"])}</span> '
            f'{_html_escape(s_name)} {min(len(s_items), 6)}</td>'
            f'<td style="width:6px;"></td>'
        )

    sections_html = ""
    for section in sections:
        if not section.get("items"):
            continue
        sections_html += _render_section(section.get("name", "未分类"), section["items"])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f3f3f3;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f3f3f3;">
<tr><td align="center" style="padding:24px 10px;">

<table width="640" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;width:100%;">

<!-- 顶部横幅 -->
<tr><td style="background-color:#ffffff;padding:28px 30px 22px 30px;border-top:6px solid #111111;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="font-size:30px;font-weight:900;color:#111111;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;letter-spacing:0;">
{_html_escape(title)}
</td></tr>
<tr><td style="padding-top:8px;font-size:13px;color:#777777;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
{_html_escape(date_str)}
</td></tr>
<tr><td style="padding-top:14px;">
<table cellpadding="0" cellspacing="0" border="0"><tr>
{stats_chips}
</tr></table>
</td></tr>
</table>
</td></tr>

<!-- 正文区域 -->
<tr><td style="background-color:#ffffff;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
{sections_html}
<tr><td style="height:20px;"></td></tr>
</table>
</td></tr>

<!-- 底部 -->
<tr><td style="background-color:#fafbfc;padding:18px 24px;border-radius:0 0 12px 12px;border-top:1px solid #eef0f2;">
<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="font-size:11px;color:#aaa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
今日共收录 {total_count} 条 · 涵盖 {section_count} 个板块<br>
由 Smart Daily 自动生成
</td>
<td align="right" style="font-size:11px;color:#aaa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
✦ Powered by AI
</td>
</tr></table>
</td></tr>

</table>

</td></tr>
</table>
</body>
</html>"""
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


if __name__ == "__main__":
    test_sections = {
        "AI/科技": [
            {"title": "OpenAI 发布 GPT-5：多模态能力大幅跃升", "url": "https://example.com/1", "source": "OpenAI", "image_url": "https://picsum.photos/400/200?1"},
            {"title": "Claude 4 发布，推理能力再创新高", "url": "https://example.com/2", "source": "Anthropic", "image_url": "https://picsum.photos/400/200?2"},
            {"title": "Google DeepMind 发布 Gemini 3", "url": "https://example.com/3", "source": "Google", "image_url": None},
            {"title": "Meta 开源新一代 LLM Llama 5", "url": "https://example.com/4", "source": "Meta AI", "image_url": "https://picsum.photos/400/200?4"},
            {"title": "Hugging Face 推出模型市场 2.0", "url": "https://example.com/10", "source": "Hugging Face", "image_url": None},
            {"title": "微软 Copilot 接入 GPT-5，Office 全线升级", "url": "https://example.com/11", "source": "微软", "image_url": "https://picsum.photos/400/200?11"},
        ],
        "政治": [
            {"title": "中美贸易谈判取得阶段性进展", "url": "https://example.com/5", "source": "新华社", "image_url": None},
            {"title": "欧盟通过新数据法案，全球科技巨头承压", "url": "https://example.com/6", "source": "澎湃新闻", "image_url": None},
            {"title": "G7 峰会聚焦 AI 监管框架", "url": "https://example.com/12", "source": "新华社", "image_url": None},
            {"title": "东盟外长会议就南海问题发表联合声明", "url": "https://example.com/13", "source": "澎湃新闻", "image_url": None},
            {"title": "国务院发布新一轮稳经济政策", "url": "https://example.com/14", "source": "人民日报", "image_url": None},
            {"title": "联合国大会通过全球 AI 治理决议", "url": "https://example.com/15", "source": "新华社", "image_url": None},
        ],
        "财经": [
            {"title": "美联储宣布降息 25 个基点", "url": "https://example.com/7", "source": "华尔街日报", "image_url": "https://picsum.photos/400/200?7"},
            {"title": "A 股三大指数集体收涨，成交额突破万亿", "url": "https://example.com/8", "source": "第一财经", "image_url": None},
            {"title": "比特币突破 12 万美元创历史新高", "url": "https://example.com/16", "source": "CoinDesk", "image_url": "https://picsum.photos/400/200?16"},
            {"title": "英伟达市值超越苹果成全球第一", "url": "https://example.com/17", "source": "Bloomberg", "image_url": "https://picsum.photos/400/200?17"},
            {"title": "央行下调 MLF 利率 10 个基点", "url": "https://example.com/18", "source": "财新网", "image_url": None},
            {"title": "日元跌破 160 关口，日央行按兵不动", "url": "https://example.com/19", "source": "华尔街日报", "image_url": None},
        ],
        "科技": [
            {"title": "苹果发布 Vision Pro 2，售价下调 40%", "url": "https://example.com/9", "source": "爱范儿", "image_url": "https://picsum.photos/400/200?9"},
            {"title": "特斯拉 FSD V13 在中国获批上路", "url": "https://example.com/20", "source": "36氪", "image_url": "https://picsum.photos/400/200?20"},
            {"title": "华为发布鸿蒙 5.0，生态应用突破百万", "url": "https://example.com/21", "source": "IT之家", "image_url": None},
            {"title": "三星推出新一代折叠屏手机", "url": "https://example.com/22", "source": "少数派", "image_url": "https://picsum.photos/400/200?22"},
            {"title": "SpaceX 星舰第七次试飞成功回收", "url": "https://example.com/23", "source": "爱范儿", "image_url": "https://picsum.photos/400/200?23"},
            {"title": "台积电 2nm 工艺正式量产", "url": "https://example.com/24", "source": "IT之家", "image_url": None},
        ],
        "民生": [
            {"title": "全国高考报名人数再创新高", "url": "https://example.com/25", "source": "新华社", "image_url": None},
            {"title": "多地出台房贷利率下调新政", "url": "https://example.com/26", "source": "澎湃新闻", "image_url": None},
            {"title": "端午假期全国旅游收入同比增长 15%", "url": "https://example.com/27", "source": "人民日报", "image_url": None},
            {"title": "北京地铁新线路开通，日均客流预计增百万", "url": "https://example.com/28", "source": "新京报", "image_url": None},
            {"title": "国家医保局公布新一批集采药品名单", "url": "https://example.com/29", "source": "新华社", "image_url": None},
            {"title": "教育部推行中小学 AI 素养课程试点", "url": "https://example.com/30", "source": "人民日报", "image_url": None},
        ],
    }

    today = datetime.now()
    sections_list = [{"name": name, "items": items} for name, items in test_sections.items()]
    html = render_email_html(f"Smart Daily 日报 - {today.strftime('%Y年%m月%d日')}", today.strftime("%Y年%m月%d日"), sections_list)

    preview_path = os.path.join(os.path.dirname(__file__), "..", "data", "email_preview.html")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"预览文件已生成: {os.path.abspath(preview_path)}")
    print(f"HTML 大小: {len(html.encode('utf-8'))} 字节")
