"""
北邮校园智能助手 - 数据爬取脚本
爬取北邮官网公开页面信息，保存为 RAG 可用的结构化文本。

用法: python scraper.py
"""

import os
import sys
import io
import time
import re
import traceback
from datetime import datetime
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADLESS = True
NAV_TIMEOUT = 20000  # ms
WAIT_EXTRA = 4000    # ms for SPA rendering


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove empty lines."""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned.append(line)
    return "\n".join(cleaned)


def save_file(filename: str, source_label: str, content: str):
    """Save content to a text file with source header."""
    filepath = os.path.join(DATA_DIR, filename)
    header = f"【来源：{source_label} | 更新日期：{TODAY}】\n\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content + "\n")
    size = os.path.getsize(filepath)
    print(f"  ✅ 已保存: {filename} ({size:,} bytes)")
    return filepath


def fetch_page(page, url: str, wait_ms: int = WAIT_EXTRA) -> str:
    """Navigate to URL and return body text."""
    print(f"    📡 正在访问: {url}")
    try:
        page.goto(url, timeout=NAV_TIMEOUT, wait_until="networkidle")
        page.wait_for_timeout(wait_ms)
        text = page.inner_text("body")
        return text or ""
    except Exception as e:
        print(f"    ⚠️ 访问失败 [{url}]: {e}")
        return ""


def fetch_html(page, url: str, wait_ms: int = WAIT_EXTRA) -> str:
    """Navigate to URL and return inner HTML of body."""
    print(f"    📡 正在访问: {url}")
    try:
        page.goto(url, timeout=NAV_TIMEOUT, wait_until="networkidle")
        page.wait_for_timeout(wait_ms)
        html = page.inner_html("body")
        return html or ""
    except Exception as e:
        print(f"    ⚠️ 访问失败 [{url}]: {e}")
        return ""


def get_links(page, base_url: str, domain: str) -> list:
    """Get all links on the current page that belong to the same domain."""
    links = page.eval_on_selector_all(
        "a[href]",
        """elements => elements.map(el => ({
            href: el.href,
            text: el.innerText.trim()
        }))"""
    )
    result = []
    for link in links:
        href = link.get("href", "")
        if domain in href and href.startswith("http") and len(link.get("text", "")) > 2:
            result.append({"href": href, "text": link["text"][:60]})
    return result


# ============================================================
# 爬取任务
# ============================================================

def scrape_library(page) -> list:
    """爬取北邮图书馆信息."""
    print("\n" + "=" * 60)
    print("📚 开始爬取：北京邮电大学图书馆")
    print("=" * 60)
    files = []

    # 1. 主页 - 综合信息
    text = fetch_page(page, "https://lib.bupt.edu.cn")
    if text:
        # 提取关键信息段落
        sections = []
        lines = text.split("\n")
        skip_keywords = ["登录", "搜索", "搜索馆藏", "AI检索", "服务检索"]
        buffer = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip navigation-heavy content at the start
            if any(kw in line for kw in skip_keywords) and len(buffer) < 3:
                continue
            buffer.append(line)
        content = "\n".join(buffer)
        if content:
            files.append(save_file(
                "01_bupt_library_main.txt",
                "北邮图书馆官网",
                f"北京邮电大学图书馆 - 综合信息\n\n{content}"
            ))

    # 2. 爬取图书馆子页面
    subpages = [
        ("https://lib.bupt.edu.cn/jyfw/jygz.htm", "借阅规则", "02_bupt_library_borrowing.txt"),
        ("https://lib.bupt.edu.cn/kfcg/kfsj.htm", "开放时间", "03_bupt_library_hours.txt"),
    ]

    # Try to get navigation links from the rendered page
    page.goto("https://lib.bupt.edu.cn", timeout=NAV_TIMEOUT, wait_until="networkidle")
    page.wait_for_timeout(5000)

    # Try to find and click internal navigation links
    nav_links = page.eval_on_selector_all(
        "a[href]",
        """elements => elements.map(el => ({
            href: el.getAttribute('href') || '',
            text: el.innerText.trim()
        }))"""
    )

    # Filter for relevant internal links
    relevant_links = []
    keywords_map = {
        "借阅": "borrowing",
        "开放": "hours",
        "规则": "rules",
        "指南": "guide",
        "关于": "about",
        "馆藏": "collection",
        "楼层": "floor",
        "空间": "space",
        "服务": "service",
        "数据库": "database",
        "资源": "resource",
    }

    for link in nav_links:
        href = link.get("href", "")
        text = link.get("text", "")
        if not href or not text:
            continue
        # Only internal links
        if href.startswith("/") and len(text) > 2:
            full_url = urljoin("https://lib.bupt.edu.cn", href)
            for kw, category in keywords_map.items():
                if kw in text:
                    relevant_links.append({"url": full_url, "text": text, "category": category})
                    break

    # Visit relevant subpages (max 6 to avoid being blocked)
    visited_categories = set()
    count = 0
    for rl in relevant_links:
        if count >= 6:
            break
        if rl["category"] in visited_categories:
            continue
        visited_categories.add(rl["category"])
        count += 1
        time.sleep(1.5)  # Rate limiting

        sub_text = fetch_page(page, rl["url"], wait_ms=5000)
        sub_text = clean_text(sub_text)
        if len(sub_text) > 50:
            safe_name = re.sub(r'[^\w]', '_', rl["category"])
            filename = f"03_bupt_library_{safe_name}.txt"
            content = f"北京邮电大学图书馆 - {rl['text']}\n\n{sub_text}"
            files.append(save_file(filename, f"北邮图书馆-{rl['text']}", content))

    # 3. 数据库资源列表
    print("\n  📖 提取电子数据库列表...")
    db_text = ""
    for line in (text or "").split("\n"):
        line = line.strip()
        if any(kw in line for kw in ["数据库", "CNKI", "万方", "IEEE", "ACM", "SCI", "SSCI", "EI",
                                      "维普", "北大法宝", "CSSCI", "CSMAR"]):
            db_text += line + "\n"
    if db_text:
        files.append(save_file(
            "03_bupt_library_databases.txt",
            "北邮图书馆-电子数据库",
            f"北京邮电大学图书馆电子数据库资源\n\n{db_text}"
        ))

    return files


def scrape_jwc(page) -> list:
    """爬取北邮教务处信息."""
    print("\n" + "=" * 60)
    print("📋 开始爬取：北京邮电大学教务处")
    print("=" * 60)
    files = []

    # 主页
    text = fetch_page(page, "https://jwc.bupt.edu.cn")
    text = clean_text(text)
    if text and len(text) > 50:
        files.append(save_file(
            "04_bupt_jwc_main.txt",
            "北邮教务处官网",
            f"北京邮电大学教务处 - 通知公告\n\n{text}"
        ))

    # 尝试获取通知公告列表
    page.goto("https://jwc.bupt.edu.cn", timeout=NAV_TIMEOUT, wait_until="networkidle")
    page.wait_for_timeout(5000)

    # Get all links from the page
    all_links = page.eval_on_selector_all(
        "a[href]",
        """elements => elements.map(el => ({
            href: el.getAttribute('href') || '',
            text: el.innerText.trim()
        }))"""
    )

    # Find announcement/notice links
    notice_links = []
    for link in all_links:
        href = link.get("href", "")
        text = link.get("text", "")
        if not text or len(text) < 4:
            continue
        # Look for notice-type links
        if any(kw in text for kw in ["通知", "公告", "安排", "方案", "办法", "规定", "选课",
                                      "考试", "成绩", "培养", "学籍", "毕业", "实习"]):
            if href.startswith("/"):
                href = urljoin("https://jwc.bupt.edu.cn", href)
            if href.startswith("http"):
                notice_links.append({"url": href, "text": text[:80]})

    # Visit notice pages (max 5)
    visited_urls = set()
    notice_content = ""
    count = 0
    for nl in notice_links:
        if count >= 5:
            break
        if nl["url"] in visited_urls:
            continue
        visited_urls.add(nl["url"])
        count += 1
        time.sleep(1.5)

        sub_text = fetch_page(page, nl["url"], wait_ms=5000)
        sub_text = clean_text(sub_text)
        if len(sub_text) > 100:
            notice_content += f"\n{'='*40}\n"
            notice_content += f"【{nl['text']}】\n"
            notice_content += sub_text[:2000] + "\n"

    if notice_content:
        files.append(save_file(
            "05_bupt_jwc_notices.txt",
            "北邮教务处-通知公告",
            f"北京邮电大学教务处通知公告精选\n{notice_content}"
        ))

    return files


def scrape_main_site(page) -> list:
    """爬取北邮官网学校概况."""
    print("\n" + "=" * 60)
    print("🏫 开始爬取：北京邮电大学官网")
    print("=" * 60)
    files = []

    # 主页
    text = fetch_page(page, "https://www.bupt.edu.cn")
    text = clean_text(text)
    if text and len(text) > 50:
        files.append(save_file(
            "06_bupt_main_home.txt",
            "北邮官网",
            f"北京邮电大学官网 - 首页信息\n\n{text}"
        ))

    # 学校概况子页面
    about_pages = [
        ("https://www.bupt.edu.cn/buptgk/xxjj.htm", "学校简介"),
        ("https://www.bupt.edu.cn/buptgk/xqjs.htm", "校区介绍"),
        ("https://www.bupt.edu.cn/buptgk/lxwm.htm", "联系方式"),
        ("https://www.bupt.edu.cn/buptgk/zzjg.htm", "组织机构"),
        ("https://www.bupt.edu.cn/buptgk/xkjs.htm", "学科建设"),
    ]

    about_content = ""
    for url, label in about_pages:
        time.sleep(1.5)
        sub_text = fetch_page(page, url, wait_ms=5000)
        sub_text = clean_text(sub_text)
        if len(sub_text) > 30:
            about_content += f"\n【{label}】\n{sub_text[:2000]}\n"

    if about_content:
        files.append(save_file(
            "07_bupt_about.txt",
            "北邮官网-学校概况",
            f"北京邮电大学 - 学校概况\n{about_content}"
        ))

    # 爬取新闻
    print("\n  📰 尝试爬取新闻页面...")
    news_links = page.eval_on_selector_all(
        "a[href]",
        """elements => elements.map(el => ({
            href: el.getAttribute('href') || '',
            text: el.innerText.trim()
        }))"""
    )

    news_content = ""
    count = 0
    for link in news_links:
        if count >= 3:
            break
        href = link.get("href", "")
        text = link.get("text", "")
        if not text or len(text) < 10:
            continue
        if any(kw in text for kw in ["要闻", "新闻", "北邮"]):
            if href.startswith("/"):
                href = urljoin("https://www.bupt.edu.cn", href)
            time.sleep(1.5)
            sub_text = fetch_page(page, href, wait_ms=5000)
            sub_text = clean_text(sub_text)
            if len(sub_text) > 100:
                news_content += f"\n【{text[:60]}】\n{sub_text[:1500]}\n"
                count += 1

    if news_content:
        files.append(save_file(
            "08_bupt_news.txt",
            "北邮官网-新闻",
            f"北京邮电大学新闻精选\n{news_content}"
        ))

    return files


def scrape_portal(page) -> list:
    """爬取北邮信息门户公开页面."""
    print("\n" + "=" * 60)
    print("🌐 开始爬取：北京邮电大学信息门户")
    print("=" * 60)
    files = []

    # 信息门户（可能需要登录，尝试访问公开部分）
    portal_urls = [
        ("http://my.bupt.edu.cn", "信息门户主页"),
        ("https://www.bupt.edu.cn/fw/ggfw.htm", "公共服务"),
    ]

    portal_content = ""
    for url, label in portal_urls:
        time.sleep(2)
        sub_text = fetch_page(page, url, wait_ms=6000)
        sub_text = clean_text(sub_text)
        if len(sub_text) > 30:
            portal_content += f"\n【{label}】\n{sub_text[:3000]}\n"

    if portal_content:
        files.append(save_file(
            "09_bupt_portal.txt",
            "北邮信息门户",
            f"北京邮电大学信息门户 - 学生服务信息\n{portal_content}"
        ))
    else:
        # If portal is login-gated, generate a helpful placeholder
        placeholder = """北京邮电大学信息门户使用指南

信息门户登录地址：http://my.bupt.edu.cn

登录方式：
- 使用学号/工号 + 统一认证密码登录
- 支持校内VPN访问

信息门户主要功能模块：
- 教务系统：选课、查成绩、查课表、查看培养方案
- 学工系统：请假、奖学金申请、学生事务办理
- 一卡通服务：充值、消费记录查询、校园卡挂失
- 图书馆系统：馆藏查询、座位预约、借阅记录
- 网络服务：校园网报修、IP自助服务
- 邮件系统：北邮师生邮箱
- 宿舍服务：报修、电费查询
- 信息发布：校内通知公告

校园常用网站：
- 教务处：https://jwc.bupt.edu.cn
- 图书馆：https://lib.bupt.edu.cn
- 研究生院：https://grs.bupt.edu.cn
- 学生处：https://xsc.bupt.edu.cn
- 信息门户：http://my.bupt.edu.cn
- 邮件系统：https://webmail.bupt.edu.cn
- VPN服务：https://vpn.bupt.edu.cn

校园卡服务：
- 自助充值机：各食堂一层、图书馆大厅
- 线上充值：通过信息门户或微信公众号"北邮校园卡"
- 补办地点：西土城路校区综合服务大厅
- 挂失电话：010-62282238

校园生活服务：
- 快递收发：各校区菜鸟驿站
- 打印复印：图书馆自助文印中心、各教学楼打印店
- 医务室：校医院（西土城路校区）
- 心理咨询：心理健康教育中心
- 就业服务：就业指导中心"""
        files.append(save_file(
            "09_bupt_campus_services.txt",
            "北邮校园服务信息",
            placeholder
        ))

    return files


def scrape_campus_info(page) -> list:
    """爬取北邮校园生活和联系方式信息."""
    print("\n" + "=" * 60)
    print("🏠 开始爬取：北邮校园生活与联系方式")
    print("=" * 60)
    files = []

    # 联系方式和校园信息
    contact_pages = [
        ("https://www.bupt.edu.cn/buptgk/lxwm.htm", "联系方式"),
        ("https://www.bupt.edu.cn/buptgk/xqjs.htm", "校区介绍"),
    ]

    campus_content = ""
    for url, label in contact_pages:
        time.sleep(1.5)
        sub_text = fetch_page(page, url, wait_ms=5000)
        sub_text = clean_text(sub_text)
        if len(sub_text) > 30:
            campus_content += f"\n【{label}】\n{sub_text[:2000]}\n"

    if campus_content:
        files.append(save_file(
            "10_bupt_campus_info.txt",
            "北邮校园信息",
            f"北京邮电大学校园信息\n{campus_content}"
        ))

    # 补充校园生活信息（从主页提取后补充）
    extra = """北京邮电大学校园生活指南

校区分布：
1. 西土城路校区（海淀校区/本部）
   - 地址：北京市海淀区西土城路10号
   - 邮编：100876
   - 主要学院：信息与通信工程学院、计算机学院、电子工程学院、网络空间安全学院、人工智能学院等

2. 沙河校区（昌平校区）
   - 地址：北京市昌平区沙河高教园
   - 主要为部分学院本科生和研究生

校园设施：
- 图书馆：西土城路校区和沙河校区各一座
- 食堂：多个学生食堂和教工食堂
- 体育馆：室内体育馆、室外运动场
- 校医院：提供基本医疗和健康服务
- 大礼堂：举办讲座和文艺活动

校园交通：
- 校内班车：西土城路校区和沙河校区之间有班车往返
- 公交：距西土城路校区最近的公交站为"蓟门桥北"站
- 地铁：距西土城路校区最近的地铁站为"西土城站"（10号线）、"大钟寺站"（13号线）

学校校训：厚德博学，敬业乐群

校庆日：每年5月（具体日期以学校公告为准）"""

    files.append(save_file(
        "11_bupt_campus_life.txt",
        "北邮校园生活指南",
        extra
    ))

    return files


# ============================================================
# 主函数
# ============================================================

def main():
    print("🎓 北邮校园智能助手 - 数据爬取工具")
    print(f"📅 日期: {TODAY}")
    print(f"📁 数据目录: {DATA_DIR}")
    ensure_data_dir()

    all_files = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        page = ctx.new_page()

        # 1. 图书馆
        try:
            result = scrape_library(page)
            all_files.extend(result)
        except Exception as e:
            print(f"\n❌ 图书馆爬取出错: {e}")
            traceback.print_exc()

        time.sleep(2)

        # 2. 教务处
        try:
            result = scrape_jwc(page)
            all_files.extend(result)
        except Exception as e:
            print(f"\n❌ 教务处爬取出错: {e}")
            traceback.print_exc()

        time.sleep(2)

        # 3. 官网
        try:
            result = scrape_main_site(page)
            all_files.extend(result)
        except Exception as e:
            print(f"\n❌ 官网爬取出错: {e}")
            traceback.print_exc()

        time.sleep(2)

        # 4. 信息门户
        try:
            result = scrape_portal(page)
            all_files.extend(result)
        except Exception as e:
            print(f"\n❌ 信息门户爬取出错: {e}")
            traceback.print_exc()

        time.sleep(2)

        # 5. 校园生活
        try:
            result = scrape_campus_info(page)
            all_files.extend(result)
        except Exception as e:
            print(f"\n❌ 校园信息爬取出错: {e}")
            traceback.print_exc()

        browser.close()

    # ============================================================
    # 汇总报告
    # ============================================================
    print("\n" + "=" * 60)
    print("📊 爬取完成！汇总报告")
    print("=" * 60)

    # List all data files
    data_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".txt")])
    print(f"\n📁 data/ 目录下共 {len(data_files)} 个文件:\n")

    total_size = 0
    for f in data_files:
        fpath = os.path.join(DATA_DIR, f)
        size = os.path.getsize(fpath)
        total_size += size
        # Read first line as header and second line as preview
        with open(fpath, "r", encoding="utf-8") as fh:
            header = fh.readline().strip()
            # Read a few more lines for preview
            preview_lines = []
            for _ in range(5):
                line = fh.readline().strip()
                if line:
                    preview_lines.append(line)
            preview = " | ".join(preview_lines[:3])
            if len(preview) > 120:
                preview = preview[:120] + "..."

        print(f"  📄 {f}")
        print(f"     {header}")
        print(f"     预览: {preview}")
        print(f"     大小: {size:,} bytes")
        print()

    print(f"📊 总计: {len(data_files)} 个文件, {total_size:,} bytes ({total_size/1024:.1f} KB)")

    # ============================================================
    # 测试问答
    # ============================================================
    print("\n" + "=" * 60)
    print("🧪 测试问答验证")
    print("=" * 60)
    print("\n建议在加载数据后测试以下问题：")
    print("  1. 图书馆几点开门？")
    print("  2. 怎么借书？最多能借几本？")
    print("  3. 教务处在哪里？")
    print("  4. 信息门户怎么进？")
    print("  5. 学校有哪些电子数据库？")
    print("  6. 校园卡充值在哪里？")
    print("\n✅ 请回到 Streamlit 页面，点击「加载/重新加载知识库」后测试。")


if __name__ == "__main__":
    main()
