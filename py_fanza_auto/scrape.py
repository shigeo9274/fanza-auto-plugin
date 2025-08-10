from __future__ import annotations
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from browser import BrowserFetcher
from config import Settings


HEADERS = {"Referer": "https://www.dmm.co.jp", "Cookie": "age_check_done=1"}


def fetch_html(url: str, timeout: int = 30, settings: Optional[Settings] = None) -> str:
    if settings and getattr(settings, "use_browser", False):
        bf = BrowserFetcher(headless=settings.headless, page_wait_sec=settings.page_wait_sec)
        return bf.fetch_after_click(url, settings.click_xpath)
    res = requests.get(url, headers=HEADERS, timeout=timeout)
    res.raise_for_status()
    return res.text


def extract_description_and_images(html: str) -> Tuple[str, List[str], List[str]]:
    soup = BeautifulSoup(html, "lxml")
    text = ""
    # try multiple selectors
    candidates = [
        ("p.mg-b20", "mono"),
        ("p.text-overflow", "pcgame"),
        ("meta[name=description]", "desc_meta"),
        ("p.tx-productComment", "monthly"),
        ("p.summary__txt", "doujin"),
    ]
    for sel, kind in candidates:
        if kind == "desc_meta":
            tag = soup.select_one(sel)
            if tag and tag.get("content"):
                text = tag.get("content")
                break
        else:
            tag = soup.select_one(sel)
            if tag and tag.text.strip():
                text = tag.text.strip()
                break

    # try images generously
    large: List[str] = []
    small: List[str] = []
    for img in soup.select("img"):
        src = img.get("src") or ""
        if not src:
            continue
        if src.endswith(".jpg") or src.endswith(".jpeg"):
            small.append(src)
            # try to convert js- to jp- when applicable
            lsrc = src.replace("js-", "jp-")
            lsrc = lsrc.replace("jm.jpg", "jp.jpg").replace("js.jpg", "jp.jpg")
            large.append(lsrc)
    return text, large, small


def extract_specific_elements(html: str) -> Tuple[str, str]:
    """
    特定の要素のテキストを抽出
    1. /html/body/div[2]/main/div[3]/div[2]/div/div[2]/div[1]/div[2]/div の部分
    2. //*[@id="review"] の部分
    """
    soup = BeautifulSoup(html, "lxml")
    
    # 1つ目の要素（XPathをCSSセレクタに変換）
    # /html/body/div[2]/main/div[3]/div[2]/div/div[2]/div[1]/div[2]/div
    # これは複雑なXPathなので、より柔軟な方法で取得
    element1_text = ""
    try:
        # より確実な方法：深いネストのdivを探す
        all_divs = soup.find_all("div")
        for div in all_divs:
            # 深いネストのdivで、テキストが含まれているものを探す
            if div.get_text(strip=True) and len(div.get_text(strip=True)) > 10:
                # 親要素の階層を確認
                parent_count = 0
                current = div.parent
                while current and current.name == "div":
                    parent_count += 1
                    current = current.parent
                
                # 適切な深さのdivを選択
                if parent_count >= 5:  # 十分に深いネスト
                    element1_text = div.get_text(strip=True)
                    break
                    
        # 上記で見つからない場合は、より一般的なセレクタで探す
        if not element1_text:
            content_divs = soup.select("div[class*='content'], div[class*='detail'], div[class*='info'], div[class*='description']")
            for div in content_divs:
                if div.get_text(strip=True):
                    element1_text = div.get_text(strip=True)
                    break
                    
        # それでも見つからない場合は、テキストが含まれるdivを探す
        if not element1_text:
            for div in all_divs:
                text = div.get_text(strip=True)
                if text and len(text) > 20:  # 十分な長さのテキスト
                    element1_text = text
                    break
                    
    except Exception as e:
        element1_text = f"要素1取得エラー: {e}"
    
    # 2つ目の要素（review ID）
    # //*[@id="review"]
    element2_text = ""
    try:
        review_element = soup.select_one("#review")
        if review_element:
            element2_text = review_element.get_text(strip=True)
        else:
            element2_text = "レビュー要素が見つかりません"
    except Exception as e:
        element2_text = f"要素2取得エラー: {e}"
    
    return element1_text, element2_text
