#!/usr/bin/env python3
"""生成日报/周报/月报/年报并发送邮件"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.update_news import (
    add_bilingual_fields,
    collect_all,
    create_session,
    fetch_opml_rss,
    has_cjk,
    is_ai_related_record,
    load_archive,
    load_title_zh_cache,
    parse_iso,
    sanitize_public_payload,
    utc_now,
)
from notifiers.email_notifier import send_daily_report


# 板块分类关键词
SECTION_KEYWORDS = {
    "AI/科技": [
        "ai", "gpt", "claude", "openai", "anthropic", "llm", "大模型",
        "人工智能", "机器学习", "深度学习", "芯片", "机器人",
    ],
    "政治": [
        "政策", "政府", "国务院", "习近平", "中央", "政治", "外交",
        "两会", "人大", "政协", "立法", "法治",
    ],
    "财经": [
        "股市", "股票", "基金", "经济", "金融", "投资", "央行",
        "美联储", "加息", "降息", "GDP", "通胀", "财经",
    ],
    "民生": [
        "教育", "医疗", "住房", "就业", "养老", "社保", "医保",
        "民生", "房价", "户口", "交通", "环保",
    ],
    "科技": [
        "手机", "电脑", "互联网", "电商", "软件", "硬件", "智能",
        "苹果", "华为", "小米", "特斯拉", "新能源",
    ],
}


def classify_item(item: dict[str, Any]) -> str:
    """根据标题和来源分类新闻到板块"""
    title = str(item.get("title", "")).lower()
    source = str(item.get("source", "")).lower()
    text = f"{title} {source}"

    # 先检查是否为 AI 相关
    if is_ai_related_record(item):
        return "AI/科技"

    # 按关键词匹配其他板块
    for section, keywords in SECTION_KEYWORDS.items():
        if section == "AI/科技":
            continue
        for keyword in keywords:
            if keyword.lower() in text:
                return section

    return "其他"


def dedupe_key(item: dict[str, Any]) -> str:
    """生成新闻去重键，URL 缺失时退化为标题和来源"""
    url = str(item.get("url") or "").strip()
    if url:
        return f"url:{url}"

    title = str(item.get("title_original") or item.get("title") or "").strip().lower()
    source = str(item.get("source") or item.get("site_name") or "").strip().lower()
    published_at = str(item.get("published_at") or "").strip()
    return f"fallback:{title}|{source}|{published_at}"


def generate_report(
    items: list[dict[str, Any]],
    report_type: str = "daily",
) -> dict[str, list[dict[str, Any]]]:
    """生成报告，按板块分类并去重

    Args:
        items: 新闻条目列表
        report_type: 报告类型 (daily/weekly/monthly/yearly)

    Returns:
        按板块分类的新闻字典
    """
    sections: dict[str, list[dict[str, Any]]] = {}
    seen_keys: set[str] = set()  # 全局去重

    for item in items:
        # 按 URL 去重；URL 缺失时用标题、来源和发布时间兜底
        key = dedupe_key(item)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        section = classify_item(item)
        if section not in sections:
            sections[section] = []
        sections[section].append(item)

    # 对每个板块按时间排序
    for section in sections:
        sections[section].sort(
            key=lambda x: parse_iso(x.get("published_at")) or datetime.min,
            reverse=True,
        )

    return sections


def filter_by_time_window(
    items: list[dict[str, Any]],
    hours: int,
) -> list[dict[str, Any]]:
    """按时间窗口过滤新闻"""
    now = utc_now()
    cutoff = now - timedelta(hours=hours)

    filtered = []
    for item in items:
        published = parse_iso(item.get("published_at"))
        if published and published >= cutoff:
            filtered.append(item)

    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(description="生成并发送日报")
    parser.add_argument(
        "--type",
        choices=["daily", "weekly", "monthly", "yearly"],
        default="daily",
        help="报告类型",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="数据目录",
    )
    parser.add_argument(
        "--rss-opml",
        default="feeds/channels.opml",
        help="OPML 文件路径",
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="发送邮件",
    )
    parser.add_argument(
        "--send-email-only",
        action="store_true",
        help="从已生成的报告发送邮件，不重新抓取新闻",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成报告，不发送邮件",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    if args.send_email_only:
        report_path = output_dir / f"report-{args.type}.json"
        if not report_path.exists():
            print(f"报告不存在，无法发送邮件: {report_path}")
            return 1

        report_data = json.loads(report_path.read_text(encoding="utf-8"))
        sections = report_data.get("sections") or {}
        if not isinstance(sections, dict):
            print(f"报告格式无效，缺少 sections: {report_path}")
            return 1

        if args.dry_run:
            print(f"邮件 dry-run: 将从 {report_path} 发送 {args.type} 报告")
            return 0

        print(f"从已生成报告发送邮件: {report_path}")
        success = send_daily_report(sections)
        if success:
            print("邮件发送成功")
            return 0

        print("邮件发送失败")
        return 1

    # 时间窗口
    time_windows = {
        "daily": 24,
        "weekly": 24 * 7,
        "monthly": 24 * 30,
        "yearly": 24 * 365,
    }
    hours = time_windows.get(args.type, 24)

    print(f"生成 {args.type} 报告，时间窗口: {hours} 小时")

    # 创建会话
    session = create_session()
    now = utc_now()

    # 收集新闻
    raw_items, statuses = collect_all(session, now)

    # 加载 OPML 源
    opml_path = Path(args.rss_opml)

    if opml_path.exists():
        rss_items, rss_status, _ = fetch_opml_rss(now, opml_path)
        raw_items.extend(rss_items)
        print(f"从 OPML 获取 {len(rss_items)} 条新闻")

    # 转换为字典格式
    items = []
    for raw in raw_items:
        items.append({
            "id": raw.title[:50],
            "title": raw.title,
            "url": raw.url,
            "source": raw.source,
            "published_at": raw.published_at.isoformat() if raw.published_at else None,
            "site_id": raw.site_id,
            "site_name": raw.site_name,
        })

    # 按时间过滤
    filtered_items = filter_by_time_window(items, hours)
    print(f"时间过滤后: {len(filtered_items)} 条")

    # 去重
    seen_keys = set()
    unique_items = []
    for item in filtered_items:
        key = dedupe_key(item)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_items.append(item)

    print(f"去重后: {len(unique_items)} 条")

    # 添加中文翻译
    title_cache_path = output_dir / "title-zh-cache.json"
    title_cache = load_title_zh_cache(title_cache_path)

    # 转换为带 id 的字典格式（add_bilingual_fields 需要的格式）
    items_with_id = []
    for i, item in enumerate(unique_items):
        item_with_id = {
            "id": f"item_{i}",
            "title": item.get("title", ""),
            "title_original": item.get("title", ""),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "published_at": item.get("published_at"),
            "site_id": item.get("site_id", ""),
            "site_name": item.get("site_name", ""),
        }
        items_with_id.append(item_with_id)

    # 添加双语标题（所有英文新闻都翻译）
    all_items_translated, _, title_cache = add_bilingual_fields(
        items_with_id, items_with_id, session, title_cache, max_new_translations=200
    )

    # 使用中文标题
    for item in all_items_translated:
        # 优先使用中文标题
        zh_title = item.get("title_zh")
        if zh_title:
            item["title"] = zh_title
        elif item.get("title_bilingual"):
            item["title"] = item["title_bilingual"]

    # 保存翻译缓存
    title_cache_path.parent.mkdir(parents=True, exist_ok=True)
    title_cache_path.write_text(
        json.dumps(title_cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 生成报告
    sections = generate_report(all_items_translated, args.type)

    # 打印统计
    print("\n=== 板块统计 ===")
    for section, items in sections.items():
        print(f"{section}: {len(items)} 条")

    # 保存报告
    report_path = output_dir / f"report-{args.type}.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_data = {
        "generated_at": now.isoformat(),
        "report_type": args.type,
        "time_window_hours": hours,
        "sections": sections,
    }
    report_path.write_text(
        json.dumps(sanitize_public_payload(report_data), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n报告已保存: {report_path}")

    # 发送邮件
    if args.send_email and not args.dry_run:
        print("\n发送邮件...")
        success = send_daily_report(sections)
        if success:
            print("邮件发送成功")
        else:
            print("邮件发送失败")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
