"""
恋爱军师 - 案例采集爬虫
支持从小红书、知乎、豆瓣等平台采集恋爱相关真实案例
用于辅助AI分析判断
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

CASES_DIR = Path(__file__).parent.parent / "cases"
CASES_DIR.mkdir(exist_ok=True)


class CaseCollector:
    def __init__(self):
        self.session = requests.Session() if requests else None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.keywords = [
            "恋爱聊天记录分析",
            "暧昧期怎么聊",
            "对方到底喜不喜欢我",
            "恋爱军师",
            "聊天记录求助",
            "表白时机",
            "怎么追女生",
            "怎么追男生",
            "恋爱建议",
            "关系判断",
            "该不该继续",
            "分手挽回",
            "冷处理怎么办",
            "忽冷忽热",
            "聊天没话题",
        ]

    def _save_case(self, case_data, source):
        case_id = hashlib.md5(
            f"{source}_{case_data.get('title', '')}_{case_data.get('content', '')[:100]}".encode()
        ).hexdigest()[:12]
        case_data["id"] = case_id
        case_data["source"] = source
        case_data["collected_at"] = datetime.now().isoformat()
        filepath = CASES_DIR / f"{source}_{case_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)
        return case_id

    def search_zhihu(self, keyword, max_results=5):
        if not self.session or not BeautifulSoup:
            print("[ERROR] 需要安装 requests 和 beautifulsoup4: pip install requests beautifulsoup4")
            return []
        cases = []
        url = f"https://www.zhihu.com/search?type=content&q={keyword}"
        try:
            resp = self.session.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select(".SearchResult-Card")[:max_results]
            for item in items:
                title_el = item.select_one(".ContentItem-title a")
                content_el = item.select_one(".content")
                if title_el and content_el:
                    case = {
                        "title": title_el.get_text(strip=True),
                        "content": content_el.get_text(strip=True)[:2000],
                        "url": f"https://www.zhihu.com{title_el.get('href', '')}",
                        "keyword": keyword,
                    }
                    case_id = self._save_case(case, "zhihu")
                    cases.append({**case, "id": case_id})
                    time.sleep(1)
        except Exception as e:
            print(f"[ZHIHU ERROR] {e}")
        return cases

    def search_douban(self, keyword, max_results=5):
        if not self.session or not BeautifulSoup:
            print("[ERROR] 需要安装 requests 和 beautifulsoup4: pip install requests beautifulsoup4")
            return []
        cases = []
        url = f"https://www.douban.com/search?q={keyword}&cat=1005"
        try:
            headers = {**self.headers, "Referer": "https://www.douban.com/"}
            resp = self.session.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select(".result")[:max_results]
            for item in items:
                title_el = item.select_one(".title a")
                content_el = item.select_one(".content")
                if title_el:
                    case = {
                        "title": title_el.get_text(strip=True),
                        "content": content_el.get_text(strip=True)[:2000] if content_el else "",
                        "url": title_el.get("href", ""),
                        "keyword": keyword,
                    }
                    case_id = self._save_case(case, "douban")
                    cases.append({**case, "id": case_id})
                    time.sleep(2)
        except Exception as e:
            print(f"[DOUBAN ERROR] {e}")
        return cases

    def search_xiaohongshu(self, keyword, max_results=5):
        if not self.session:
            print("[ERROR] 需要安装 requests: pip install requests")
            return []
        cases = []
        print(f"[INFO] 小红书搜索: {keyword}")
        print("[INFO] 小红书有反爬机制，建议使用以下方式获取数据：")
        print("  1. 手动搜索并复制内容到 cases/ 目录")
        print("  2. 使用小红书开放平台API（需申请开发者权限）")
        print("  3. 使用Selenium模拟浏览器操作（见下方 selenium 模式）")
        return cases

    def collect_from_text(self, title, content, tags=None, source="manual"):
        case = {
            "title": title,
            "content": content,
            "tags": tags or [],
            "keyword": "manual_input",
        }
        case_id = self._save_case(case, source)
        return {**case, "id": case_id}

    def batch_search(self, keywords=None, sources=None, max_per_source=3):
        keywords = keywords or self.keywords[:5]
        sources = sources or ["zhihu", "douban"]
        all_cases = []
        for kw in keywords:
            for source in sources:
                print(f"\n[SEARCH] {source} - {kw}")
                if source == "zhihu":
                    results = self.search_zhihu(kw, max_per_source)
                elif source == "douban":
                    results = self.search_douban(kw, max_per_source)
                elif source == "xiaohongshu":
                    results = self.search_xiaohongshu(kw, max_per_source)
                else:
                    continue
                all_cases.extend(results)
                time.sleep(3)
        summary = {
            "total": len(all_cases),
            "sources": sources,
            "keywords": keywords,
            "collected_at": datetime.now().isoformat(),
            "cases": all_cases,
        }
        summary_path = CASES_DIR / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n[DONE] 共采集 {len(all_cases)} 条案例，保存至 {summary_path}")
        return all_cases

    def load_cases(self):
        all_cases = []
        for f in CASES_DIR.glob("*.json"):
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if "cases" in data:
                    all_cases.extend(data["cases"])
                else:
                    all_cases.append(data)
        return all_cases


class SeleniumCollector:
    def __init__(self):
        self.driver = None

    def setup(self, headless=True):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self.driver = webdriver.Chrome(options=options)
            return True
        except ImportError:
            print("[ERROR] 需要安装 selenium: pip install selenium")
            return False
        except Exception as e:
            print(f"[ERROR] Chrome驱动初始化失败: {e}")
            return False

    def search_xiaohongshu(self, keyword, max_results=5):
        if not self.driver:
            print("[ERROR] 请先调用 setup() 初始化浏览器")
            return []
        cases = []
        try:
            self.driver.get(f"https://www.xiaohongshu.com/search_result?keyword={keyword}")
            time.sleep(5)
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys

            items = self.driver.find_elements(By.CSS_SELECTOR, ".note-item")[:max_results]
            for item in items:
                try:
                    title = item.find_element(By.CSS_SELECTOR, ".title").text
                    content = item.find_element(By.CSS_SELECTOR, ".desc").text
                    case = {
                        "title": title,
                        "content": content[:2000],
                        "keyword": keyword,
                    }
                    case_id = CaseCollector()._save_case(case, "xiaohongshu")
                    cases.append({**case, "id": case_id})
                except Exception:
                    continue
        except Exception as e:
            print(f"[XIAOHONGSHU SELENIUM ERROR] {e}")
        return cases

    def close(self):
        if self.driver:
            self.driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="恋爱军师 - 案例采集爬虫")
    parser.add_argument("--mode", choices=["search", "manual", "selenium", "load"], default="search",
                        help="运行模式: search=批量搜索, manual=手动输入, selenium=浏览器模式, load=加载已有案例")
    parser.add_argument("--keyword", type=str, default=None, help="搜索关键词")
    parser.add_argument("--source", type=str, nargs="+", default=["zhihu", "douban"],
                        help="数据源: zhihu, douban, xiaohongshu")
    parser.add_argument("--max", type=int, default=3, help="每个来源最大采集数")
    parser.add_argument("--title", type=str, default=None, help="手动模式: 标题")
    parser.add_argument("--content", type=str, default=None, help="手动模式: 内容")
    parser.add_argument("--tags", type=str, nargs="+", default=None, help="手动模式: 标签")

    args = parser.parse_args()
    collector = CaseCollector()

    if args.mode == "search":
        keywords = [args.keyword] if args.keyword else collector.keywords[:5]
        collector.batch_search(keywords=keywords, sources=args.source, max_per_source=args.max)
    elif args.mode == "manual":
        if not args.title or not args.content:
            print("[ERROR] 手动模式需要 --title 和 --content 参数")
            return
        result = collector.collect_from_text(args.title, args.content, args.tags)
        print(f"[DONE] 案例已保存, ID: {result['id']}")
    elif args.mode == "selenium":
        sel = SeleniumCollector()
        if sel.setup(headless=False):
            keyword = args.keyword or "恋爱聊天记录分析"
            results = sel.search_xiaohongshu(keyword, args.max)
            print(f"[DONE] 采集 {len(results)} 条小红书案例")
            sel.close()
    elif args.mode == "load":
        cases = collector.load_cases()
        print(f"[INFO] 已加载 {len(cases)} 条案例")
        for c in cases[:10]:
            print(f"  - [{c.get('source', '?')}] {c.get('title', '无标题')[:50]}")


if __name__ == "__main__":
    main()
