from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import Settings
from dmm_client import DMMClient
from wp_client import WordPressClient
from template import Renderer
from scrape import fetch_html, extract_description_and_images, extract_specific_elements
import requests
from settings_manager import SettingsManager
from category_manager import CategoryManager
from scheduler import Scheduler
from log_manager import LogManager, LogType, LogLevel


@dataclass
class PostingSettings:
    """投稿設定を管理するデータクラス"""
    title: str = "[title]"
    content: str = "[title]の詳細情報です。"
    eyecatch: str = "sample"
    movie_size: str = "auto"
    poster: str = "package"
    category: str = "jan"
    sort: str = "rank"
    article: str = ""
    status: str = "publish"
    hour: str = "h09"
    overwrite_existing: bool = False
    target_new_posts: int = 10
    floor: str = "videoc"
    keyword: str = ""
    article_type: str = ""
    article_id: str = ""
    from_date: str = ""
    to_date: str = ""
    site: str = "FANZA"
    service: str = "digital"
    hits: int = 10
    maximage: int = 10
    limited_flag: int = 0
    # ブラウザ設定
    use_browser: bool = True
    headless: bool = True
    click_xpath: str = '//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a'
    page_wait_sec: int = 5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostingSettings":
        """辞書からPostingSettingsを作成"""
        processed_data = {}
        for k, v in data.items():
            if k in cls.__annotations__:
                # target_new_postsを数値に変換
                if k == 'target_new_posts' and isinstance(v, str):
                    try:
                        processed_data[k] = int(v)
                    except (ValueError, TypeError):
                        processed_data[k] = 0
                else:
                    processed_data[k] = v
        return cls(**processed_data)

    def to_dict(self) -> Dict[str, Any]:
        """PostingSettingsを辞書に変換"""
        return {k: getattr(self, k) for k in self.__annotations__}

    def merge_with_defaults(self, defaults: "PostingSettings") -> "PostingSettings":
        """デフォルト設定とマージ"""
        merged = PostingSettings()
        for field in self.__annotations__:
            current_value = getattr(self, field)
            default_value = getattr(defaults, field)
            if current_value is not None and current_value != "":
                setattr(merged, field, current_value)
            else:
                setattr(merged, field, default_value)
        return merged


@dataclass
class Engine:
    settings: Settings
    dmm: DMMClient
    wp: WordPressClient
    renderer: Renderer
    settings_manager: SettingsManager
    category_manager: CategoryManager
    scheduler: Scheduler
    log_manager: LogManager
    _posting_settings_cache: Optional[Dict[str, PostingSettings]] = None
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(minutes=5)

    @classmethod
    def from_settings(cls, s: Settings) -> "Engine":
        # SettingsManagerのインスタンスを作成
        base_dir = os.path.dirname(os.path.abspath(__file__))
        settings_manager = SettingsManager(base_dir)
        
        # 新しい機能のインスタンスを作成
        category_manager = CategoryManager(settings_manager)
        
        # Scheduler用のデフォルト設定を作成
        from scheduler import ScheduleConfig
        default_schedule_config = ScheduleConfig()
        
        scheduler = Scheduler(default_schedule_config)
        log_manager = LogManager(log_dir=str(base_dir))
        
        return cls(
            settings=s,
            dmm=DMMClient(s.dmm_api_id, s.dmm_affiliate_id),
            wp=WordPressClient(s.wp_base_url, s.wp_username, s.wp_app_password),
            renderer=Renderer(),
            settings_manager=settings_manager,
            category_manager=category_manager,
            scheduler=scheduler,
            log_manager=log_manager,
        )

    def _get_default_posting_settings(self) -> PostingSettings:
        """デフォルトの投稿設定を取得"""
        # 基本設定から値を取得（存在しない場合はデフォルト値を使用）
        # Settingsクラスに存在しない属性に対しては、デフォルト値を直接設定
        default_service = "digital"
        default_floor = "videoc"
        default_keyword = ""
        default_article_type = ""
        default_article_id = ""
        default_from_date = ""
        default_to_date = ""
        default_site = "FANZA"
        default_hits = 10
        
        print(f"_get_default_posting_settings: デフォルトサービス: {default_service}")
        print(f"_get_default_posting_settings: デフォルトフロア: {default_floor}")
        print(f"_get_default_posting_settings: デフォルトキーワード: {default_keyword}")
        
        return PostingSettings(
            title="[title]",
            content="[title]の詳細情報です。",
            eyecatch="sample",
            movie_size="auto",
            poster="package",
            category="jan",
            sort="rank",
            article="",
            status="publish",
            hour="h09",
            overwrite_existing=False,
            target_new_posts=10,
            floor=default_floor,
            keyword=default_keyword,
            article_type=default_article_type,
            article_id=default_article_id,
            from_date=default_from_date,
            to_date=default_to_date,
            site=default_site,
            service=default_service,
            hits=default_hits,
            maximage=10,
            limited_flag=0,
            # ブラウザ設定
            use_browser=True,
            headless=True,
            click_xpath='//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a',
            page_wait_sec=5
        )

    def _load_posting_settings(self, post_setting_num: str = "1") -> PostingSettings:
        """投稿設定を読み込み、キャッシュを活用"""
        try:
            # キャッシュが有効かチェック
            if (self._posting_settings_cache and 
                self._cache_timestamp and 
                datetime.now() - self._cache_timestamp < self._cache_ttl):
                
                if post_setting_num in self._posting_settings_cache:
                    cached_settings = self._posting_settings_cache[post_setting_num]
                    print(f"_load_posting_settings: キャッシュから設定{post_setting_num}を取得")
                    return cached_settings
            
            # キャッシュが無効な場合はファイルから読み込み
            print(f"_load_posting_settings: ファイルから設定{post_setting_num}を読み込み")
            
            # 現在の設定から投稿設定を取得
            print(f"_load_posting_settings: self.settingsの型: {type(self.settings)}")
            print(f"_load_posting_settings: self.settingsの内容: {self.settings}")
            
            if hasattr(self.settings, 'post_settings') and self.settings.post_settings:
                post_settings = self.settings.post_settings
                print(f"_load_posting_settings: settings.post_settingsから取得: {len(post_settings)}件")
                print(f"_load_posting_settings: 利用可能な設定: {list(post_settings.keys())}")
                print(f"_load_posting_settings: post_settingsの型: {type(post_settings)}")
                
                if post_setting_num in post_settings:
                    setting_data = post_settings[post_setting_num]
                    print(f"_load_posting_settings: 設定{post_setting_num}のデータ: {setting_data}")
                    print(f"_load_posting_settings: 設定{post_setting_num}のデータ型: {type(setting_data)}")
                    
                    try:
                        posting_settings = PostingSettings.from_dict(setting_data)
                        print(f"_load_posting_settings: 設定{post_setting_num}の読み込み完了")
                        print(f"_load_posting_settings: タイトル: {posting_settings.title}")
                        print(f"_load_posting_settings: コンテンツ: {posting_settings.content[:50]}...")
                    except Exception as e:
                        print(f"_load_posting_settings: PostingSettings.from_dictでエラー: {e}")
                        import traceback
                        print(f"_load_posting_settings: エラー詳細: {traceback.format_exc()}")
                        posting_settings = self._get_default_posting_settings()
                else:
                    print(f"_load_posting_settings: 設定{post_setting_num}が見つからないため、デフォルト設定を使用")
                    posting_settings = self._get_default_posting_settings()
            else:
                print(f"_load_posting_settings: settings.post_settingsが存在しないため、デフォルト設定を使用")
                print(f"_load_posting_settings: settingsの属性: {dir(self.settings)}")
                if hasattr(self.settings, 'post_settings'):
                    print(f"_load_posting_settings: post_settingsの値: {self.settings.post_settings}")
                posting_settings = self._get_default_posting_settings()
            
            # デフォルト設定とマージ
            default_settings = self._get_default_posting_settings()
            posting_settings = posting_settings.merge_with_defaults(default_settings)
            
            # サービスパラメータの最終確認
            if not posting_settings.service or posting_settings.service.strip() == "":
                posting_settings.service = "digital"
                print(f"_load_posting_settings: サービスパラメータが空のため、デフォルト値 'digital' を設定")
            
            print(f"_load_posting_settings: 最終的なサービスパラメータ: {posting_settings.service}")
            
            # キャッシュを更新
            if not self._posting_settings_cache:
                self._posting_settings_cache = {}
            self._posting_settings_cache[post_setting_num] = posting_settings
            self._cache_timestamp = datetime.now()
            
            return posting_settings
            
        except Exception as e:
            print(f"_load_posting_settings: 設定読み込みエラー: {e}")
            self.log_manager.error(LogType.SYSTEM, f"投稿設定読み込みエラー: {e}")
            
            # エラーが発生した場合はデフォルト設定を使用
            default_settings = self._get_default_posting_settings()
            print(f"_load_posting_settings: デフォルト設定を使用")
            return default_settings

    def _clear_settings_cache(self):
        """設定キャッシュをクリア"""
        self._posting_settings_cache = None
        self._cache_timestamp = None
        print("_clear_settings_cache: 設定キャッシュをクリアしました")

    def _convert_service_to_english(self, service: str) -> str:
        """サービスパラメータを英語に変換"""
        service_map = {
            "デジタル": "digital",
            "パッケージ": "package",
            "両方": "both",
            "digital": "digital",
            "package": "package",
            "both": "both"
        }
        # サービスが空文字列またはNoneの場合はデフォルト値を返す
        if not service or service.strip() == "":
            return "digital"
        return service_map.get(service, service)
    
    def _convert_sort_to_english(self, sort: str) -> str:
        """ソートパラメータを英語に変換"""
        sort_map = {
            "発売日順": "date",
            "名前順": "name",
            "価格順": "price",
            "レビュー順": "review",
            "人気順": "rank"
        }
        return sort_map.get(sort, sort)
    
    def _convert_article_to_english(self, article: str) -> str:
        """記事パラメータを英語に変換"""
        article_map = {
            "シリーズ": "series",
            "出演者": "actress",
            "ジャンル": "genre",
            "監督": "director",
            "メーカー": "maker",
            "レーベル": "label"
        }
        return article_map.get(article, article)

    def search_items(self, posting_settings: Optional[PostingSettings] = None) -> Tuple[List[Dict[str, Any]], int]:
        # paginate gathering until posting_settings.hits reached
        items: List[Dict[str, Any]] = []
        offset = 1
        remaining = posting_settings.hits if posting_settings else 10
        total_count = 0
        
        # 投稿設定が指定されていない場合はデフォルト設定を使用
        if not posting_settings:
            posting_settings = self._get_default_posting_settings()
        
        while remaining > 0:
            # サービスパラメータの処理を改善
            service_param = self._convert_service_to_english(posting_settings.service)
            print(f"search_items: サービスパラメータ: {posting_settings.service} -> {service_param}")
            
            resp = self.dmm.item_list(
                site=posting_settings.site,
                service=service_param,
                floor=posting_settings.floor,
                keyword=posting_settings.keyword,
                sort=self._convert_sort_to_english(posting_settings.sort),
                gte_date=(posting_settings.from_date + "T00:00:00") if posting_settings.from_date else None,
                lte_date=(posting_settings.to_date + "T23:59:59") if posting_settings.to_date else None,
                article=self._convert_article_to_english(posting_settings.article_type) if posting_settings.article_type else None,
                article_id=posting_settings.article_id or None,
                hits=min(100, remaining),
                offset=offset,
            )
            result = resp.get("result", {})
            total_count = int(result.get("total_count", 0))
            batch = result.get("items", [])
            if not batch:
                break
            items.extend(batch)
            remaining = posting_settings.hits - len(items)
            # next page
            offset += len(batch)
            if offset > total_count:
                break
        return items[: posting_settings.hits], total_count

    def download_media(self, url: str) -> Optional[bytes]:
        """URLからメディアをダウンロードする"""
        try:
            # DMMクライアントのdownload_mediaメソッドを使用
            print(f"download_media: ダウンロード開始: {url}")
            media_bytes = self.dmm.download_media(url)
            if media_bytes:
                print(f"download_media: ダウンロード完了: {len(media_bytes)}バイト")
            else:
                print(f"download_media: ダウンロード失敗 - データが受信されませんでした")
            return media_bytes
        except Exception as e:
            print(f"download_media: ダウンロードエラー: {e}")
            return None

    def build_content(self, item: Dict[str, Any], posting_settings: Optional[PostingSettings] = None) -> Tuple[str, str, Optional[bytes], Optional[str]]:
        try:
            print(f"build_content: 開始: {item.get('title', 'No title')}")
            
            # 投稿設定が指定されていない場合は、デフォルト設定を使用
            if not posting_settings:
                posting_settings = self._get_default_posting_settings()
            
            print(f"build_content: 投稿設定を使用: {posting_settings.to_dict()}")
            
            # Chromeを使った詳細情報の取得（説明文とレビュー）
            chrome_description = ""
            chrome_review = ""
            if hasattr(posting_settings, 'use_browser') and posting_settings.use_browser:
                try:
                    detail_url = item.get('URL', '')
                    if detail_url:
                        print(f"build_content: Chromeで詳細情報を取得中: {detail_url}")
                        # GUIの設定を使用（設定ファイルから読み込み）
                        browser_settings = Settings.load()
                        print(f"build_content: ブラウザ設定読み込み - headless={browser_settings.headless}, use_browser={browser_settings.use_browser}")
                        print(f"build_content: 設定オブジェクト詳細 - {browser_settings}")
                        
                        # ChromeでHTMLを取得
                        html = fetch_html(detail_url, settings=browser_settings)
                        if html:
                            # 説明文とレビューを抽出
                            chrome_description, chrome_review = extract_specific_elements(html)
                            print(f"build_content: Chrome取得完了 - 説明文: {len(chrome_description)}文字, レビュー: {len(chrome_review)}文字")
                        else:
                            print(f"build_content: ChromeでHTML取得失敗")
                except Exception as e:
                    print(f"build_content: Chrome詳細情報取得エラー: {e}")
                    # エラーが発生しても処理を続行
            
            # タイトルの構築
            title_template = posting_settings.title
            title = self.renderer.replace_variables(title_template, item)
            print(f"build_content: タイトル構築完了: {title}")
            
            # コンテンツの構築
            content_template = posting_settings.content
            
            # 新しいレンダリング機能を使用してコンテンツを生成
            affiliate_url = item.get('affiliateURL', '')
            movie_size = posting_settings.movie_size
            
            content = self.renderer.render_template(
                template_content=content_template,
                item=item,
                affiliate_url=affiliate_url,
                movie_size=movie_size
            )
            
            # Chromeで取得した詳細情報をコンテンツに追加
            if chrome_description and chrome_description != "要素1取得エラー: ":
                content += f"\n\n<h3>詳細情報</h3>\n<div class='detail-content'>\n{chrome_description}\n</div>"
                print(f"build_content: 詳細情報を追加: {len(chrome_description)}文字")
            
            # レビュー情報を追加（固定テキストの場合は表示しない）
            if chrome_review and chrome_review != "レビュー要素が見つかりません" and chrome_review != "要素2取得エラー: ":
                # 固定のレビューテキストが含まれている場合は表示しない
                fixed_review_texts = [
                    "ユーザーレビューレビューが掲載されるたび10ポイントゲットこの作品に最初のレビューを書いてみませんか？他のユーザーにあなたの感想を伝えましょうレビューを書く / 編集する",
                    "レビューが掲載されるたび10ポイントゲット",
                    "この作品に最初のレビューを書いてみませんか？",
                    "他のユーザーにあなたの感想を伝えましょう"
                ]
                
                # 固定テキストが含まれているかチェック
                is_fixed_text = any(fixed_text in chrome_review for fixed_text in fixed_review_texts)
                
                if not is_fixed_text:
                    content += f"\n\n<h3>レビュー・コメント</h3>\n<div class='review-content'>\n{chrome_review}\n</div>"
                    print(f"build_content: レビュー情報を追加: {len(chrome_review)}文字")
                else:
                    print(f"build_content: 固定レビューテキストをスキップ: {chrome_review[:50]}...")
            else:
                print(f"build_content: レビュー情報なしまたはエラー")
            
            print(f"build_content: コンテンツ構築完了: {len(content)}文字")
            
            # メディアの構築
            media_bytes = None
            media_name = None
            
            # アイキャッチ設定に基づいてメディアを選択
            eyecatch_setting = posting_settings.eyecatch
            media_url = None
            media_name = None
            
            if eyecatch_setting == "sample" and item.get("sampleImageURL"):
                # DMMクライアントのget_sample_imagesメソッドを使用
                sample_urls = self.dmm.get_sample_images(item)
                if sample_urls:
                    media_url = sample_urls[0]  # 最初のサンプル画像を使用
                    media_name = f"{item.get('content_id', 'unknown')}_sample.jpg"
            elif eyecatch_setting == "package" and item.get("imageURL"):
                # DMMクライアントのget_package_imageメソッドを使用
                media_url = self.dmm.get_package_image(item)
                if media_url:
                    media_name = f"{item.get('content_id', 'unknown')}_package.jpg"
            elif eyecatch_setting == "1" and item.get("sampleImageURL"):
                # 1番目のサンプル画像
                sample_urls = self.dmm.get_sample_images(item)
                if sample_urls:
                    media_url = sample_urls[0]
                    media_name = f"{item.get('content_id', 'unknown')}_sample1.jpg"
            elif eyecatch_setting == "99" and item.get("sampleImageURL"):
                # 99番目のサンプル画像（存在する場合）
                sample_urls = self.dmm.get_sample_images(item)
                if len(sample_urls) >= 99:
                    media_url = sample_urls[98]  # 0ベースインデックス
                    media_name = f"{item.get('content_id', 'unknown')}_sample99.jpg"
                elif sample_urls:
                    # 99番目が存在しない場合は最初の画像を使用
                    media_url = sample_urls[0]
                    media_name = f"{item.get('content_id', 'unknown')}_sample1.jpg"
            else:
                # デフォルトはsample
                sample_urls = self.dmm.get_sample_images(item)
                if sample_urls:
                    media_url = sample_urls[0]
                    media_name = f"{item.get('content_id', 'unknown')}_sample.jpg"
            
            if media_url:
                try:
                    print(f"build_content: メディアダウンロード中: {media_url}")
                    media_bytes = self.download_media(media_url)
                    if media_bytes:
                        print(f"build_content: メディアダウンロード完了: {len(media_bytes)}バイト")
                    else:
                        print(f"build_content: メディアダウンロード失敗 - データが受信されませんでした")
                        media_name = None
                except Exception as e:
                    print(f"build_content: メディアダウンロードエラー: {e}")
                    import traceback
                    print(f"build_content: メディアダウンロードエラー詳細: {traceback.format_exc()}")
                    media_bytes = None
                    media_name = None
                    # ログに記録
                    self.log_manager.error(LogType.ERROR, f"メディアダウンロードエラー: {e}")
            else:
                print(f"build_content: アイキャッチ設定 {eyecatch_setting} のメディアURLが見つかりません")
            
            return title, content, media_bytes, media_name
            
        except Exception as e:
            print(f"build_content: エラー発生: {e}")
            import traceback
            print(f"build_content: エラー詳細: {traceback.format_exc()}")
            # ログに記録
            self.log_manager.error(LogType.ERROR, f"build_content error: {e}")
            raise
    
    def _generate_sample_images_html(self, item: Dict[str, Any]) -> str:
        """サンプル画像のHTMLを生成"""
        # DMMクライアントのget_sample_imagesメソッドを使用
        sample_urls = self.dmm.get_sample_images(item)
        
        if not sample_urls:
            return ''
        
        html = '<div class="sample-images">'
        for img_url in sample_urls:
            if img_url:
                html += f'<img src="{img_url}" alt="サンプル画像" style="max-width: 200px; height: auto; margin: 5px;" />'
        html += '</div>'
        return html
    
    def _generate_act_info_html(self, item: Dict[str, Any]) -> str:
        """出演者情報のリスト形式HTMLを生成"""
        actresses = item.get('actress', [])
        if not actresses:
            return ''
        
        html = '<ul class="actress-info">'
        for actress in actresses:
            name = actress.get('name', '')
            if name:
                html += f'<li>{name}</li>'
        html += '</ul>'
        return html
    
    def _generate_act_table_html(self, item: Dict[str, Any]) -> str:
        """出演者情報のテーブル形式HTMLを生成"""
        actresses = item.get('actress', [])
        if not actresses:
            return ''
        
        html = '<table class="actress-table" style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background-color: #f8f9fa;"><th style="border: 1px solid #dee2e6; padding: 8px;">出演者</th></tr>'
        for actress in actresses:
            name = actress.get('name', '')
            if name:
                html += f'<tr><td style="border: 1px solid #dee2e6; padding: 8px;">{name}</td></tr>'
        html += '</table>'
        return html

    def _extract_tags(self, item: Dict[str, Any]) -> List[str]:
        """アイテムからタグを抽出する"""
        tags = []
        
        # 出演者名をタグとして追加
        actresses = item.get('actress', [])
        for actress in actresses:
            name = actress.get('name', '')
            if name:
                tags.append(name)
        
        # ジャンルをタグとして追加
        genres = item.get('genre', [])
        for genre in genres:
            name = genre.get('name', '')
            if name:
                tags.append(name)
        
        # シリーズ名をタグとして追加
        series = item.get('series', [])
        for series_item in series:
            name = series_item.get('name', '')
            if name:
                tags.append(name)
        
        # メーカー名をタグとして追加
        maker = item.get('maker', {})
        if maker and 'name' in maker:
            tags.append(maker['name'])
        
        # レーベル名をタグとして追加
        label = item.get('label', {})
        if label and 'name' in label:
            tags.append(label['name'])
        
        return tags

    def post_one(self, item: Dict[str, Any], posting_settings: Optional[PostingSettings] = None) -> Optional[int]:
        try:
            print(f"post_one: コンテンツ構築開始: {item.get('title', 'No title')}")
            title, content, media_bytes, media_name = self.build_content(item, posting_settings)
            print(f"post_one: タイトル: {title}")
            print(f"post_one: コンテンツ長: {len(content)}")
            
            slug = item.get("content_id")
            print(f"post_one: スラッグ: {slug}")
            
            # 投稿設定から上書き設定を取得
            overwrite_enabled = False
            if posting_settings:
                overwrite_enabled = posting_settings.overwrite_existing
            else:
                # 投稿設定が指定されていない場合は、デフォルト設定を使用
                posting_settings = self._get_default_posting_settings() # デフォルト設定を使用
                overwrite_enabled = posting_settings.overwrite_existing
            
            print(f"post_one: 上書き設定: {overwrite_enabled}")
            
            # 重複チェックと上書き処理
            existing_post_id = None
            if slug:
                print(f"post_one: 重複チェック中...")
                exists = self.wp.get_post_by_slug(slug)
                if exists:
                    existing_post_id = exists.get('id')
                    if overwrite_enabled:
                        print(f"post_one: 既存投稿を上書きします: ID {existing_post_id}")
                        # 既存の投稿を更新
                        try:
                            # 更新用のデータを準備
                            update_data = {
                                "title": title,
                                "content": content,
                                "status": posting_settings.status
                            }
                            
                            print(f"post_one: 更新データ準備完了 - タイトル: {title}, ステータス: {update_data['status']}")
                            
                            # 投稿を更新
                            updated_post = self.wp.update_post(existing_post_id, update_data)
                            print(f"post_one: 既存投稿を更新しました: ID {existing_post_id}")
                            
                            # カテゴリとタグの設定（新規作成時と同様）
                            try:
                                if posting_settings.category == "jan":
                                    # JANコードベースのカテゴリ設定
                                    jan_code = item.get("JANCode")
                                    if jan_code:
                                        self.category_manager.set_categories_by_jan(existing_post_id, jan_code)
                                        print(f"post_one: JANコードベースのカテゴリ設定完了: {jan_code}")
                                elif posting_settings.category == "custom":
                                    # カスタムカテゴリ設定
                                    custom_categories = getattr(posting_settings, 'custom_categories', [])
                                    if custom_categories:
                                        self.category_manager.set_custom_categories(existing_post_id, custom_categories)
                                        print(f"post_one: カスタムカテゴリ設定完了: {custom_categories}")
                                
                                # タグの設定
                                tags = self._extract_tags(item)
                                if tags:
                                    self.wp.set_post_tags(existing_post_id, tags)
                                    print(f"post_one: タグ設定完了: {tags}")
                                    
                            except Exception as e:
                                print(f"post_one: カテゴリ・タグ設定エラー: {e}")
                                self.log_manager.warning(LogType.CATEGORY, f"カテゴリ・タグ設定エラー: {e}")
                            
                            # サムネイルも更新
                            if media_bytes and media_name:
                                try:
                                    self.wp.upload_media(media_name, media_bytes)
                                    print(f"post_one: サムネイル更新完了")
                                except Exception as e:
                                    print(f"post_one: サムネイル更新エラー: {e}")
                            
                            # ログに記録
                            self.log_manager.info(LogType.POSTING, f"投稿更新完了: ID {existing_post_id}, タイトル: {title}")
                            
                            return existing_post_id
                        except Exception as e:
                            print(f"post_one: 投稿更新エラー: {e}")
                            import traceback
                            print(f"post_one: エラー詳細: {traceback.format_exc()}")
                            self.log_manager.error(LogType.ERROR, f"投稿更新エラー: {e}")
                            return None
                    else:
                        print(f"post_one: 既に存在する投稿: {existing_post_id} (上書き無効)")
                        self.log_manager.info(LogType.POSTING, f"既存投稿スキップ: ID {existing_post_id}, タイトル: {title}")
                        return None
                else:
                    print(f"post_one: 重複なし、新規作成可能")
            
            print(f"post_one: WordPressに投稿作成中...")
            post_status = posting_settings.status if posting_settings else "publish"
            post = self.wp.create_post(title=title, content=content, status=post_status, slug=slug)
            post_id = int(post.get("id"))
            print(f"post_one: 投稿作成成功: ID {post_id}")
            
            # カテゴリとタグの設定
            try:
                if posting_settings.category == "jan":
                    # JANコードベースのカテゴリ設定
                    jan_code = item.get("JANCode")
                    if jan_code:
                        self.category_manager.set_categories_by_jan(post_id, jan_code)
                        print(f"post_one: JANコードベースのカテゴリ設定完了: {jan_code}")
                elif posting_settings.category == "custom":
                    # カスタムカテゴリ設定
                    custom_categories = getattr(posting_settings, 'custom_categories', [])
                    if custom_categories:
                        self.category_manager.set_custom_categories(post_id, custom_categories)
                        print(f"post_one: カスタムカテゴリ設定完了: {custom_categories}")
                
                # タグの設定
                tags = self._extract_tags(item)
                if tags:
                    self.wp.set_post_tags(post_id, tags)
                    print(f"post_one: タグ設定完了: {tags}")
                    
            except Exception as e:
                print(f"post_one: カテゴリ・タグ設定エラー: {e}")
                self.log_manager.warning(LogType.CATEGORY, f"カテゴリ・タグ設定エラー: {e}")
            
            if media_bytes and media_name:
                print(f"post_one: メディアアップロード中: {media_name}")
                media = self.wp.upload_media(media_name, media_bytes)
                media_id = int(media.get("id"))
                print(f"post_one: メディアアップロード成功: ID {media_id}")
                
                print(f"post_one: アイキャッチ画像設定中...")
                self.wp.set_featured_media(post_id, media_id)
                print(f"post_one: アイキャッチ画像設定完了")
            else:
                print(f"post_one: メディアなし")
            
            # ログに記録
            self.log_manager.info(LogType.POSTING, f"投稿作成完了: ID {post_id}, タイトル: {title}")
            
            return post_id
            
        except Exception as e:
            print(f"post_one: エラー発生: {e}")
            import traceback
            print(f"post_one: エラー詳細: {traceback.format_exc()}")
            self.log_manager.error(LogType.ERROR, f"post_one error: {e}")
            raise

    def run_once(self, post_setting_num: str = "1") -> List[int]:
        created: List[int] = []
        offset = 1
        batch_size = 100  # 一度に処理するアイテム数
        
        # ログに実行開始を記録
        self.log_manager.info(LogType.SYSTEM, f"run_once開始: 設定番号 {post_setting_num}")
        
        # 投稿設定を読み込み
        try:
            posting_settings = self._load_posting_settings(post_setting_num)
            print(f"run_once: 投稿設定{post_setting_num}を読み込み: {posting_settings.to_dict()}")
        except Exception as e:
            print(f"run_once: 投稿設定読み込みエラー: {e}")
            self.log_manager.error(LogType.ERROR, f"投稿設定読み込みエラー: {e}")
            # エラーが発生した場合はデフォルト設定を使用
            posting_settings = self._get_default_posting_settings()
            print(f"run_once: デフォルト設定を使用")
        
        # 目標投稿数が設定されている場合の処理
        target_count = posting_settings.target_new_posts
        # 文字列の場合は数値に変換
        if isinstance(target_count, str):
            try:
                target_count = int(target_count)
            except (ValueError, TypeError):
                target_count = 0
        elif not isinstance(target_count, int):
            target_count = 0
            
        if target_count > 0:
            print(f"run_once: 目標投稿数: {target_count}件")
            self.log_manager.info(LogType.SYSTEM, f"目標投稿数: {target_count}件")
        
        # 目標投稿数に達するまで繰り返し処理
        consecutive_failures = 0  # 連続失敗回数
        max_consecutive_failures = 5  # 最大連続失敗回数
        
        while True:
            # 目標投稿数に達したかチェック
            if target_count > 0 and len(created) >= target_count:
                print(f"run_once: 目標投稿数 {target_count}件に達しました")
                self.log_manager.info(LogType.SYSTEM, f"目標投稿数 {target_count}件に達しました")
                break
            
            # 連続失敗回数が上限に達した場合
            if consecutive_failures >= max_consecutive_failures:
                print(f"run_once: 連続失敗回数が上限({max_consecutive_failures}回)に達しました。処理を停止します")
                self.log_manager.warning(LogType.SYSTEM, f"連続失敗回数が上限({max_consecutive_failures}回)に達しました")
                break
            
            # DMM APIからアイテムを取得
            try:
                print(f"run_once: DMM API呼び出し中 - オフセット: {offset}, バッチサイズ: {batch_size}")
                items, total = self.search_items_with_offset(offset, batch_size, posting_settings)
                
                if not items:
                    print(f"run_once: オフセット {offset} でアイテムが見つかりません")
                    consecutive_failures += 1
                    offset += batch_size
                    continue
                
                print(f"run_once: バッチ {offset}: {len(items)}件のアイテムを取得")
                self.log_manager.info(LogType.SYSTEM, f"バッチ {offset}: {len(items)}件のアイテムを取得")
                
                # アイテムを順次処理
                batch_created = 0  # このバッチで作成された投稿数
                for i, item in enumerate(items, 1):
                    try:
                        print(f"run_once: アイテム{i}を処理中: {item.get('title', 'No title')}")
                        post_id = self.post_one(item, posting_settings)
                        
                        if post_id:
                            created.append(post_id)
                            batch_created += 1
                            consecutive_failures = 0  # 成功したら失敗カウントをリセット
                            print(f"run_once: 投稿作成成功: ID {post_id}")
                            self.log_manager.info(LogType.POSTING, f"投稿作成成功: ID {post_id}, タイトル: {item.get('title', 'No title')}")
                            
                            # 目標投稿数に達したかチェック
                            if target_count > 0 and len(created) >= target_count:
                                print(f"run_once: 目標投稿数 {target_count}件に達しました")
                                self.log_manager.info(LogType.SYSTEM, f"目標投稿数 {target_count}件に達しました")
                                return created
                        else:
                            print(f"run_once: アイテム{i}は既に存在するか、作成に失敗")
                            self.log_manager.info(LogType.POSTING, f"アイテム{i}は既に存在するか、作成に失敗: {item.get('title', 'No title')}")
                            
                    except Exception as e:
                        print(f"run_once: アイテム{i}でエラー: {e}")
                        import traceback
                        print(f"run_once: エラー詳細: {traceback.format_exc()}")
                        self.log_manager.error(LogType.ERROR, f"アイテム{i}でエラー: {e}")
                        consecutive_failures += 1
                        continue
                
                # このバッチで投稿が作成されなかった場合
                if batch_created == 0:
                    consecutive_failures += 1
                    print(f"run_once: バッチ {offset} で投稿が作成されませんでした。連続失敗回数: {consecutive_failures}")
                
                # 次のバッチに進む
                offset += batch_size
                
                # 進捗状況をログに記録
                print(f"run_once: 現在の進捗 - 作成済み: {len(created)}件, 目標: {target_count}件, 連続失敗: {consecutive_failures}回")
                self.log_manager.info(LogType.SYSTEM, f"進捗状況 - 作成済み: {len(created)}件, 目標: {target_count}件, 連続失敗: {consecutive_failures}回")
                
            except Exception as e:
                print(f"run_once: DMM API呼び出しでエラー: {e}")
                import traceback
                print(f"run_once: エラー詳細: {traceback.format_exc()}")
                self.log_manager.error(LogType.ERROR, f"DMM API呼び出しエラー: {e}")
                consecutive_failures += 1
                offset += batch_size
                continue
        
        print(f"run_once: 完了。{len(created)}件の投稿を作成")
        self.log_manager.info(LogType.SYSTEM, f"run_once完了: {len(created)}件の投稿を作成")
        return created

    def search_items_with_offset(self, offset: int, batch_size: int, posting_settings: PostingSettings) -> Tuple[List[Dict[str, Any]], int]:
        """指定されたオフセットからアイテムを検索する"""
        try:
            # 投稿設定から検索設定を取得
            floor = posting_settings.floor
            keyword = posting_settings.keyword
            sort = posting_settings.sort
            article_type = posting_settings.article_type
            article_id = posting_settings.article_id
            from_date = posting_settings.from_date
            to_date = posting_settings.to_date
            
            # サービスパラメータの処理を改善
            service_param = self._convert_service_to_english(posting_settings.service)
            print(f"search_items_with_offset: サービスパラメータ: {posting_settings.service} -> {service_param}")
            
            resp = self.dmm.item_list(
                site=posting_settings.site,
                service=service_param,
                floor=floor,
                keyword=keyword,
                sort=self._convert_sort_to_english(sort),
                gte_date=(from_date + "T00:00:00") if from_date else None,
                lte_date=(to_date + "T23:59:59") if to_date else None,
                article=self._convert_article_to_english(article_type) if article_type else None,
                article_id=article_id or None,
                hits=batch_size,
                offset=offset,
            )
            result = resp.get("result", {})
            total_count = int(result.get("total_count", 0))
            items = result.get("items", [])
            return items, total_count
        except Exception as e:
            print(f"search_items_with_offset: エラー: {e}")
            return [], 0

    def run_test(self, post_setting_num: str = "1") -> str:
        """テスト実行"""
        try:
            print("run_test: 開始")
            self.log_manager.info(LogType.SYSTEM, "run_test開始")
            
            # SettingsManagerから投稿設定を取得
            try:
                posting_settings = self._load_posting_settings(post_setting_num)
                print(f"run_test: 投稿設定{post_setting_num}を使用: {posting_settings.to_dict()}")
                print(f"run_test: タイトル: {posting_settings.title}")
                print(f"run_test: コンテンツ: {posting_settings.content[:50]}...")
                print(f"run_test: 上書き: {posting_settings.overwrite_existing}")
            except Exception as e:
                print(f"run_test: 投稿設定読み込みエラー: {e}")
                self.log_manager.error(LogType.ERROR, f"投稿設定読み込みエラー: {e}")
                # エラーが発生した場合はデフォルト値を使用
                posting_settings = self._get_default_posting_settings()
                print(f"run_test: デフォルト設定を使用")
            
            # アイテムを検索
            items, total = self.search_items(posting_settings)
            print(f"run_test: 検索結果: {total}件")
            self.log_manager.info(LogType.SCRAPING, f"検索結果: {total}件")
            
            if not items:
                self.log_manager.warning(LogType.SCRAPING, "アイテムが見つかりませんでした")
                return "アイテムが見つかりませんでした。"
            
            # 最初のアイテムでテスト
            item = items[0]
            print(f"run_test: テストアイテム: {item.get('title', 'No title')}")
            self.log_manager.info(LogType.SCRAPING, f"テストアイテム: {item.get('title', 'No title')}")
            
            # コンテンツを構築
            title, content, media_bytes, media_name = self.build_content(item, posting_settings)
            
            result = []
            result.append(f"--- Item 1 ---")
            result.append(f"Title: {item.get('title', 'No title')}")
            result.append(f"CID: {item.get('content_id', 'No ID')}")
            result.append(f"URL: {item.get('URL', 'No URL')}")
            result.append(f"LargeImage: {item.get('imageURL', 'No image')}")
            result.append(f"Desc(len): {len(item.get('comment', ''))}")
            result.append(f"Large imgs: {len([item.get('imageURL')] if item.get('imageURL') else [])}")
            result.append(f"Small imgs: {len([item.get('sampleImageURL')] if item.get('sampleImageURL') else [])}")
            result.append(f"Total items found: {total}")
            result.append(f"Items to process: {min(len(items), posting_settings.hits)}")
            result.append("")
            result.append("--- HTML Preview ---")
            result.append(content)
            result.append("--- End HTML Preview ---")
            
            self.log_manager.info(LogType.SYSTEM, "run_test完了")
            return "\n".join(result)
            
        except Exception as e:
            print(f"run_test: エラー発生: {e}")
            import traceback
            print(f"run_test: エラー詳細: {traceback.format_exc()}")
            self.log_manager.error(LogType.ERROR, f"run_test error: {e}")
            return f"テスト実行エラー: {e}"

    def rewrite_post(self, post_id: int, item: Dict[str, Any]) -> bool:
        """既存投稿をリライトする"""
        try:
            print(f"rewrite_post: 投稿 {post_id} のリライト開始")
            self.log_manager.info(LogType.SYSTEM, f"投稿 {post_id} のリライト開始")
            
            # 投稿設定を取得（デフォルト設定を使用）
            posting_settings = self._get_default_posting_settings()
            
            # コンテンツを構築
            title, content, media_bytes, media_name = self.build_content(item, posting_settings)
            
            # 投稿を更新
            update_data = {
                "title": title,
                "content": content
            }
            
            # メディアがある場合はアップロードしてアイキャッチに設定
            if media_bytes and media_name:
                try:
                    media_id = self.wp.upload_media(media_name, media_bytes)
                    if media_id:
                        update_data["featured_media"] = media_id
                        print(f"rewrite_post: メディアアップロード成功: {media_id}")
                except Exception as e:
                    print(f"rewrite_post: メディアアップロードエラー: {e}")
            
            # 投稿を更新
            self.wp.update_post(post_id, update_data)
            print(f"rewrite_post: 投稿 {post_id} の更新完了")
            self.log_manager.info(LogType.SYSTEM, f"投稿 {post_id} のリライト完了")
            
            return True
            
        except Exception as e:
            print(f"rewrite_post: エラー: {e}")
            self.log_manager.error(LogType.ERROR, f"投稿 {post_id} のリライトエラー: {e}")
            return False
