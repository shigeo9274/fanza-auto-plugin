from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import requests
import time
import json
from pathlib import Path
import logging


@dataclass
class DMMClient:
    api_id: str
    affiliate_id: str
    base: str = "https://api.dmm.com/affiliate/v3"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """APIリクエストを実行（リトライ機能付き）"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                url = f"{self.base}/{path}"
                print(f"APIリクエスト: {url} (試行 {attempt + 1}/{self.max_retries})")
                
                res = requests.get(url, params=params, timeout=self.timeout)
                res.raise_for_status()
                
                result = res.json()
                print(f"APIレスポンス取得成功: {path}")
                return result
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                print(f"タイムアウトエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指数バックオフ
                    continue
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                print(f"リクエストエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                last_exception = e
                print(f"予期しないエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
        
        # すべてのリトライが失敗
        error_msg = f"APIリクエストが失敗しました: {path}"
        if last_exception:
            error_msg += f" - エラー: {last_exception}"
        raise Exception(error_msg)

    def item_list(
        self,
        site: str,
        service: str,
        floor: str,
        keyword: str = "",
        sort: str = "date",
        gte_date: Optional[str] = None,
        lte_date: Optional[str] = None,
        article: Optional[str] = None,
        article_id: Optional[str] = None,
        hits: int = 100,
        offset: int = 1,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "api_id": self.api_id,
            "affiliate_id": self.affiliate_id,
            "site": site,
            "service": service,
            "floor": floor,
            "keyword": keyword,
            "sort": sort,
            "output": "json",
            "hits": hits,
            "offset": offset,
        }
        if article and article_id:
            params["article"] = article
            params["article_id"] = article_id
        if gte_date:
            params["gte_date"] = gte_date
        if lte_date:
            params["lte_date"] = lte_date
        return self._get("ItemList", params)

    def floor_list(self, use_cache: bool = True, cache_file: str = "floor_cache.json") -> Dict[str, Any]:
        """フロア一覧を取得（キャッシュ機能付き）"""
        # キャッシュファイルのパス
        cache_path = Path(cache_file)
        
        # キャッシュを使用する場合
        if use_cache and cache_path.exists():
            try:
                # キャッシュの有効期限をチェック（24時間）
                cache_age = time.time() - cache_path.stat().st_mtime
                if cache_age < 24 * 60 * 60:  # 24時間以内
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        print(f"キャッシュからフロア一覧を読み込みました（{cache_age/3600:.1f}時間前）")
                        return cached_data
                else:
                    print("キャッシュが古いため、APIから再取得します")
            except Exception as e:
                print(f"キャッシュ読み込みエラー: {e}")
        
        try:
            # APIからフロア一覧を取得
            params = {
                "api_id": self.api_id, 
                "affiliate_id": self.affiliate_id, 
                "output": "json"
            }
            
            print(f"フロア一覧をAPIから取得中... (API ID: {self.api_id[:8]}..., Affiliate ID: {self.affiliate_id[:8]}...)")
            result = self._get("FloorList", params)
            
            # レスポンスの妥当性をチェック
            if not self._validate_floor_response(result):
                raise Exception("フロア一覧のレスポンスが不正です")
            
            # キャッシュに保存
            if use_cache:
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"フロア一覧をキャッシュに保存しました: {cache_path}")
                except Exception as e:
                    print(f"キャッシュ保存エラー: {e}")
            
            return result
            
        except Exception as e:
            print(f"フロア一覧取得エラー: {e}")
            # キャッシュが存在する場合はフォールバック
            if cache_path.exists():
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        print(f"API取得失敗、キャッシュから読み込み: {e}")
                        return cached_data
                except Exception as cache_e:
                    print(f"キャッシュフォールバックも失敗: {cache_e}")
            
            raise e

    def _validate_floor_response(self, response: Dict[str, Any]) -> bool:
        """フロア一覧レスポンスの妥当性をチェック"""
        try:
            # 基本的な構造チェック
            if not isinstance(response, dict):
                return False
            
            if 'result' not in response:
                return False
            
            result = response['result']
            if 'site' not in result:
                return False
            
            sites = result['site']
            if not isinstance(sites, list) or len(sites) == 0:
                return False
            
            # フロア情報の存在チェック
            floor_count = 0
            for site in sites:
                if 'service' in site:
                    for service in site['service']:
                        if 'floor' in service:
                            for floor in service['floor']:
                                if 'name' in floor and 'code' in floor:
                                    floor_count += 1
            
            if floor_count == 0:
                return False
            
            print(f"フロア一覧検証完了: {floor_count}件のフロア情報を確認")
            return True
            
        except Exception as e:
            print(f"フロアレスポンス検証エラー: {e}")
            return False

    def get_floor_summary(self) -> Dict[str, Any]:
        """フロア一覧のサマリー情報を取得"""
        try:
            floor_data = self.floor_list()
            
            if 'result' not in floor_data or 'site' not in floor_data['result']:
                return {}
            
            summary = {
                'total_floors': 0,
                'floors_by_site': {},
                'floors_by_service': {},
                'floor_codes': []
            }
            
            sites = floor_data['result']['site']
            for site in sites:
                site_name = site.get('name', 'Unknown')
                summary['floors_by_site'][site_name] = 0
                
                if 'service' in site:
                    for service in site['service']:
                        service_name = service.get('name', 'Unknown')
                        if service_name not in summary['floors_by_service']:
                            summary['floors_by_service'][service_name] = 0
                        
                        if 'floor' in service:
                            for floor in service['floor']:
                                floor_name = floor.get('name', '')
                                floor_code = floor.get('code', '')
                                
                                if floor_name and floor_code:
                                    summary['total_floors'] += 1
                                    summary['floors_by_site'][site_name] += 1
                                    summary['floors_by_service'][service_name] += 1
                                    summary['floor_codes'].append({
                                        'name': floor_name,
                                        'code': floor_code,
                                        'site': site_name,
                                        'service': service_name
                                    })
            
            return summary
            
        except Exception as e:
            print(f"フロアサマリー取得エラー: {e}")
            return {}

    def download_media(self, url: str, headers: Optional[Dict[str, str]] = None, max_retries: int = 3) -> Optional[bytes]:
        """メディアファイルをダウンロードする（リトライ機能付き）"""
        for attempt in range(max_retries):
            try:
                default_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.dmm.co.jp/',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                if headers:
                    default_headers.update(headers)
                
                print(f"download_media: ダウンロード中: {url} (試行 {attempt + 1}/{max_retries})")
                response = requests.get(url, headers=default_headers, timeout=30, stream=True)
                response.raise_for_status()
                
                # コンテンツタイプをチェック
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"download_media: 警告 - Content-Typeが画像ではありません: {content_type}")
                
                # ストリーミングでダウンロード
                media_bytes = b""
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        media_bytes += chunk
                
                if media_bytes:
                    print(f"download_media: ダウンロード完了: {len(media_bytes)}バイト")
                    return media_bytes
                else:
                    print(f"download_media: ダウンロード失敗 - データが受信されませんでした")
                    if attempt < max_retries - 1:
                        print(f"download_media: リトライ中... ({attempt + 2}/{max_retries})")
                        continue
                    else:
                        print(f"download_media: すべてのリトライ試行が失敗しました")
                        return None
                        
            except requests.exceptions.Timeout:
                print(f"download_media: タイムアウトエラー (試行 {attempt + 1})")
                if attempt < max_retries - 1:
                    print(f"download_media: リトライ中... ({attempt + 2}/{max_retries})")
                    continue
                else:
                    print(f"download_media: タイムアウトによりすべてのリトライ試行が失敗しました")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"download_media: リクエストエラー (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"download_media: リトライ中... ({attempt + 2}/{max_retries})")
                    continue
                else:
                    print(f"download_media: リクエストエラーによりすべてのリトライ試行が失敗しました")
                    return None
            except Exception as e:
                print(f"download_media: 予期しないエラー (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"download_media: リトライ中... ({attempt + 2}/{max_retries})")
                    continue
                else:
                    print(f"download_media: 予期しないエラーによりすべてのリトライ試行が失敗しました")
                    return None
        
        return None

    def get_sample_images(self, item: Dict[str, Any]) -> List[str]:
        """アイテムからサンプル画像URLのリストを取得"""
        sample_urls = []
        sample_image_data = item.get('sampleImageURL', {})
        
        if isinstance(sample_image_data, dict):
            # 辞書形式の場合、すべてのURLを収集
            for size, urls in sample_image_data.items():
                if isinstance(urls, list):
                    sample_urls.extend(urls)
                elif isinstance(urls, str):
                    sample_urls.append(urls)
        elif isinstance(sample_image_data, str):
            # 文字列の場合、カンマ区切りとして処理
            sample_urls = [url.strip() for url in sample_image_data.split(',') if url.strip()]
        
        return [url for url in sample_urls if url]

    def get_package_image(self, item: Dict[str, Any]) -> Optional[str]:
        """アイテムからパッケージ画像URLを取得"""
        image_data = item.get('imageURL', {})
        
        if isinstance(image_data, dict):
            # 辞書形式の場合、最初のURLを使用
            first_urls = list(image_data.values())[0] if image_data else []
            if isinstance(first_urls, list) and first_urls:
                return first_urls[0]
            elif isinstance(first_urls, str):
                return first_urls
        elif isinstance(image_data, str):
            return image_data
        
        return None

