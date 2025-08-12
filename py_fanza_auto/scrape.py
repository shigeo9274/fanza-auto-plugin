from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
import requests
import re
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
        # まず、指定されたXPathパスのJSONから説明文を取得を試行
        print(f"extract_specific_elements: XPathパス /html/body/div[2]/main/div[3]/div[2]/div/script[1] からJSON取得を試行")
        
        # XPathパスに対応する要素を探す
        script_elements = soup.find_all("script")
        target_script = None
        
        # 指定されたパスに近い位置のscriptタグを探す
        for script in script_elements:
            if script.string and ("product" in script.string.lower() or "description" in script.string.lower() or "comment" in script.string.lower()):
                target_script = script
                print(f"extract_specific_elements: 対象のscriptタグを発見")
                break
        
        if target_script and target_script.string:
            try:
                # JSONデータを抽出
                script_content = target_script.string.strip()
                print(f"extract_specific_elements: script内容の最初の200文字: {script_content[:200]}...")
                
                # JSONオブジェクトを探す
                json_start = script_content.find('{')
                json_end = script_content.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = script_content[json_start:json_end + 1]
                    print(f"extract_specific_elements: JSON文字列を抽出: {json_str[:200]}...")
                    
                    # JSONをパース
                    import json
                    try:
                        json_data = json.loads(json_str)
                        print(f"extract_specific_elements: JSONパース成功")
                        
                        # 説明文の可能性があるフィールドを探す
                        description_fields = ['description', 'comment', 'summary', 'text', 'content', 'detail', 'info']
                        for field in description_fields:
                            if field in json_data and json_data[field]:
                                element1_text = str(json_data[field])
                                element1_source = f"JSON - {field}"
                                print(f"extract_specific_elements: JSONから説明文を取得: {field} = {element1_text[:100]}...")
                                break
                        
                        # 説明文が見つからない場合、ネストされたオブジェクトも探す
                        if not element1_text:
                            for key, value in json_data.items():
                                if isinstance(value, dict):
                                    for sub_field in description_fields:
                                        if sub_field in value and value[sub_field]:
                                            element1_text = str(value[sub_field])
                                            element1_source = f"JSON - {key}.{sub_field}"
                                            print(f"extract_specific_elements: ネストされたJSONから説明文を取得: {key}.{sub_field} = {element1_text[:100]}...")
                                            break
                                    if element1_text:
                                        break
                        
                    except json.JSONDecodeError as e:
                        print(f"extract_specific_elements: JSONパースエラー: {e}")
                        
            except Exception as e:
                print(f"extract_specific_elements: JSON処理エラー: {e}")
        
        # JSONから説明文が取得できない場合は、従来の方法を試行
        if not element1_text:
            print(f"extract_specific_elements: JSONから説明文が取得できないため、従来の方法を試行")
            
            # 設定されたセレクタを試行
            for selector in description_selectors:
                if selector.startswith("meta"):
                    tag = soup.select_one(selector)
                    if tag and tag.get("content"):
                        element1_text = tag.get("content")
                        element1_source = f"{selector} - meta description"
                        print(f"extract_specific_elements: meta description found: {element1_text[:100]}...")
                        break
                else:
                    tag = soup.select_one(selector)
                    if tag and tag.get_text(strip=True):
                        element1_text = tag.get_text(strip=True)
                        element1_source = f"{selector} - found"
                        print(f"extract_specific_elements: selector {selector} found: {element1_text[:100]}...")
                        break
            
            # 上記で見つからない場合は、より詳細な説明文を探す
            if not element1_text or len(element1_text) < 50:  # 短すぎる場合は再検索
                print(f"extract_specific_elements: 短い説明文または見つからないため、詳細検索を実行")
                
                # より具体的なセレクタを試行
                detailed_selectors = [
                    "div.productComment",
                    "div.product-comment", 
                    "div.product_comment",
                    "div.comment",
                    "div.description",
                    "div.detail",
                    "div.info",
                    "div.content",
                    "p.comment",
                    "p.description",
                    "p.detail",
                    "p.info"
                ]
                
                for selector in detailed_selectors:
                    tag = soup.select_one(selector)
                    if tag:
                        text = tag.get_text(strip=True)
                        if text and len(text) > 50:  # より長いテキストを優先
                            element1_text = text
                            element1_source = f"{selector} - detailed search"
                            print(f"extract_specific_elements: detailed selector {selector} found: {element1_text[:100]}...")
                            break
                
                # それでも見つからない場合は、長いテキストを含む要素を探す
                if not element1_text or len(element1_text) < 50:
                    print(f"extract_specific_elements: 長いテキストを含む要素を検索中...")
                    all_divs = soup.find_all(["div", "p", "span"])
                    
                    # テキストの長さでソートして、最も長いものを選択
                    text_elements = []
                    for elem in all_divs:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 50 and not any(skip in text.lower() for skip in ['copyright', '利用規約', 'プライバシー', 'cookie']):
                            text_elements.append((text, elem.name, len(text)))
                    
                    if text_elements:
                        # 長さでソートして最長のものを選択
                        text_elements.sort(key=lambda x: x[2], reverse=True)
                        element1_text = text_elements[0][0]
                        element1_source = f"{text_elements[0][1]} - longest text ({text_elements[0][2]} chars)"
                        print(f"extract_specific_elements: longest text found: {element1_text[:100]}...")
        
        # 説明文が見つからない場合
        if not element1_text:
            element1_text = "説明文が見つかりません"
            element1_source = "該当なし"
            print(f"extract_specific_elements: 説明文が見つかりません")
        else:
            print(f"extract_specific_elements: 最終的な説明文: {element1_text[:100]}... (全{len(element1_text)}文字)")
            
    except Exception as e:
        element1_text = f"説明文取得エラー: {e}"
        element1_source = "エラー"
        print(f"extract_specific_elements: 説明文取得エラー: {e}")
    
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


def get_mp4_url_from_cid(cid: str) -> str:
    """CIDからMP4ファイルのURLを取得（PHPプラグインのgetMp4FromCid相当）"""
    if not cid:
        return ""
    
    base_url = "https://cc3001.dmm.co.jp/litevideo/freepv/"
    middle_url = f"{cid[0]}/{cid[:3]}/{cid}/{cid}"
    
    # 試行するMP4ファイルのパターン（PHPプラグインと同じ順序）
    mp4_patterns = [
        f"{middle_url}_mhb_w.mp4",
        f"{middle_url}_mhb_s.mp4", 
        f"{middle_url}_dmb_w.mp4",
        f"{middle_url}_dmb_s.mp4",
        f"{middle_url}_dm_w.mp4",
        f"{middle_url}_dm_s.mp4",
        f"{middle_url}_sm_w.mp4",
        f"{middle_url}_sm_s.mp4"
    ]
    
    for pattern in mp4_patterns:
        mp4_url = base_url + pattern
        if check_mp4_url(mp4_url):
            return mp4_url
    
    return ""

def get_mp4_url_from_movie_url(movie_url: str) -> str:
    """動画URLからMP4ファイルのURLを取得（PHPプラグインのgetMp4Url相当）"""
    if not movie_url:
        return ""
    
    # URLからCIDを抽出
    cid_match = re.search(r'cid=([^/]+)', movie_url)
    if not cid_match:
        return ""
    
    cid = cid_match.group(1)
    return get_mp4_url_from_cid(cid)

def check_mp4_url(mp4_url: str) -> bool:
    """MP4ファイルのURLが有効かチェック（PHPプラグインのcheckUrl相当）"""
    try:
        response = requests.head(mp4_url, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_sample_movie_url(item: Dict[str, Any]) -> str:
    """サンプル動画のMP4 URLを取得（PHPプラグインのgetSampleMovie2相当）"""
    # DMM APIからsampleMovieURLを取得
    sample_movie_url = item.get('sampleMovieURL', {})
    
    if isinstance(sample_movie_url, dict):
        # 辞書形式の場合、size_720_480を優先
        movie_url = sample_movie_url.get('size_720_480', '')
        if movie_url:
            mp4_url = get_mp4_url_from_movie_url(movie_url)
            if mp4_url:
                return mp4_url
    
    # sampleMovieURLがない場合、content_idから直接取得を試行
    content_id = item.get('content_id', '')
    if content_id:
        # まず、content_idから3文字削除したものを試行
        short_cid = content_id[:-3] if len(content_id) > 3 else content_id
        mp4_url = get_mp4_url_from_cid(short_cid)
        if mp4_url:
            return mp4_url
        
        # 次に、元のcontent_idを試行
        mp4_url = get_mp4_url_from_cid(content_id)
        if mp4_url:
            return mp4_url
    
    return ""

def generate_sample_movie_html(mp4_url: str, poster_url: str = "", title: str = "") -> str:
    """サンプル動画のHTMLを生成（PHPプラグインのgetSampleMovie2相当）"""
    if not mp4_url:
        return ""
    
    poster_attr = f' poster="{poster_url}"' if poster_url else ""
    title_attr = f' alt="{title}"' if title else ""
    
    html = f'''<!-- wp:html -->
<p style="text-align:center;">
<video src="{mp4_url}"{poster_attr} controls width="100%" height="100%" style="cursor:pointer; object-fit:cover;"{title_attr}></video>
</p>
<!-- /wp:html -->'''
    
    return html
