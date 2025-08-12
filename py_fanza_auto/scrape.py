from __future__ import annotations
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from browser import BrowserFetcher
from config import Settings


HEADERS = {"Referer": "https://www.dmm.co.jp", "Cookie": "age_check_done=1"}


def fetch_html(url: str, timeout: int = 30, settings: Optional[Settings] = None) -> str:
    if settings and getattr(settings, "use_browser", False):
        print(f"DEBUG: Chrome設定詳細 - use_browser={settings.use_browser}, headless={settings.headless}, page_wait_sec={settings.page_wait_sec}, click_xpath={settings.click_xpath}")
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


def extract_specific_elements(html: str, settings: Optional[Settings] = None) -> Tuple[str, str]:
    """
    特定の要素のテキストを抽出し、取得場所を表示
    1. 説明文の取得
    2. レビューの取得
    """
    soup = BeautifulSoup(html, "lxml")
    
    # デフォルトのセレクタ
    default_description_selectors = [
        "meta[name=description]",
        "p.tx-productComment",
        "p.summary__txt",
        "p.mg-b20",
        "p.text-overflow",
        "div[class*='description']",
        "div[class*='detail']",
        "div[class*='info']",
        "div[class*='content']"
    ]
    
    default_review_selectors = [
        "#review",
        "div[class*='review']",
        "div[class*='comment']",
        "div[class*='user']"
    ]
    
    # 設定からセレクタを取得
    description_selectors = getattr(settings, 'description_selectors', default_description_selectors) if settings else default_description_selectors
    review_selectors = getattr(settings, 'review_selectors', default_review_selectors) if settings else default_review_selectors
    
    # 1つ目の要素（説明文）の取得
    element1_text = ""
    element1_source = ""
    
    try:
        # 設定されたセレクタを試行
        for selector in description_selectors:
            if selector.startswith("meta"):
                tag = soup.select_one(selector)
                if tag and tag.get("content"):
                    element1_text = tag.get("content")
                    element1_source = f"{selector} - meta description"
                    break
            else:
                tag = soup.select_one(selector)
                if tag and tag.get_text(strip=True):
                    element1_text = tag.get_text(strip=True)
                    element1_source = f"{selector} - found"
                    break
        
        # 上記で見つからない場合は、深いネストのdivを探す
        if not element1_text:
            all_divs = soup.find_all("div")
            for div in all_divs:
                text = div.get_text(strip=True)
                if text and len(text) > 10:
                    # 親要素の階層を確認
                    parent_count = 0
                    current = div.parent
                    while current and current.name == "div":
                        parent_count += 1
                        current = current.parent
                    
                    # 適切な深さのdivを選択
                    if parent_count >= 5:
                        element1_text = text
                        element1_source = f"深いネストのdiv (階層{parent_count})"
                        break
        
        # それでも見つからない場合は、テキストが含まれるdivを探す
        if not element1_text:
            for div in all_divs:
                text = div.get_text(strip=True)
                if text and len(text) > 20:
                    element1_text = text
                    element1_source = "長いテキストを含むdiv"
                    break
                    
        if not element1_text:
            element1_text = "説明文が見つかりません"
            element1_source = "該当なし"
            
    except Exception as e:
        element1_text = f"説明文取得エラー: {e}"
        element1_source = "エラー"
    
    # 2つ目の要素（レビュー）の取得
    element2_text = ""
    element2_source = ""
    
    try:
        # 設定されたレビューセレクタを試行
        for selector in review_selectors:
            tag = soup.select_one(selector)
            if tag and tag.get_text(strip=True):
                element2_text = tag.get_text(strip=True)
                element2_source = f"{selector} - found"
                break
        
        if not element2_text:
            element2_text = "レビューが見つかりません"
            element2_source = "該当なし"
            
    except Exception as e:
        element2_text = f"レビュー取得エラー: {e}"
        element2_source = "エラー"
    
    return element1_text, element2_text
