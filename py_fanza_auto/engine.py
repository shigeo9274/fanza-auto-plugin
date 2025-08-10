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
class Engine:
    settings: Settings
    dmm: DMMClient
    wp: WordPressClient
    renderer: Renderer
    settings_manager: SettingsManager
    category_manager: CategoryManager
    scheduler: Scheduler
    log_manager: LogManager

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

    def search_items(self) -> Tuple[List[Dict[str, Any]], int]:
        # paginate gathering until settings.hits reached
        items: List[Dict[str, Any]] = []
        offset = 1
        remaining = self.settings.hits
        total_count = 0
        while remaining > 0:
            resp = self.dmm.item_list(
                site=self.settings.site,
                service=self.settings.service,
                floor=self.settings.floor,
                keyword=self.settings.keyword,
                sort=self.settings.sort,
                gte_date=(self.settings.from_date + "T00:00:00") if self.settings.from_date else None,
                lte_date=(self.settings.to_date + "T23:59:59") if self.settings.to_date else None,
                article=self.settings.article_type or None,
                article_id=self.settings.article_id or None,
                hits=min(100, remaining),
                offset=offset,
            )
            result = resp.get("result", {})
            total_count = int(result.get("total_count", 0))
            batch = result.get("items", [])
            if not batch:
                break
            items.extend(batch)
            remaining = self.settings.hits - len(items)
            # next page
            offset += len(batch)
            if offset > total_count:
                break
        return items[: self.settings.hits], total_count

    def download_media(self, url: str) -> Optional[bytes]:
        """URLからメディアをダウンロードする"""
        try:
            import requests
            print(f"download_media: ダウンロード開始: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            media_bytes = response.content
            print(f"download_media: ダウンロード完了: {len(media_bytes)}バイト")
            return media_bytes
        except Exception as e:
            print(f"download_media: ダウンロードエラー: {e}")
            return None

    def build_content(self, item: Dict[str, Any], posting_settings: Dict[str, Any] = None) -> Tuple[str, str, Optional[bytes], Optional[str]]:
        try:
            print(f"build_content: 開始: {item.get('title', 'No title')}")
            
            # 投稿設定が指定されていない場合は、SettingsManagerからデフォルト設定を取得
            if not posting_settings:
                try:
                    post_settings = self.settings_manager.load_post_settings()
                    if "post_settings" in post_settings and "1" in post_settings["post_settings"]:
                        setting = post_settings["post_settings"]["1"]
                        posting_settings = {
                            "title": setting.get("title", "[title]"),
                            "content": setting.get("content", "[title]の詳細情報です。"),
                            "eyecatch": setting.get("eyecatch", "sample"),
                            "movie_size": setting.get("movie_size", "auto"),
                            "poster": setting.get("poster", "package"),
                            "category": setting.get("category", "jan"),
                            "sort": setting.get("sort", "rank"),
                            "article": setting.get("article", ""),
                            "status": setting.get("status", "publish"),
                            "hour": setting.get("hour", "h09"),
                            "overwrite_existing": setting.get("overwrite_existing", False)
                        }
                        print(f"build_content: SettingsManagerからデフォルト設定を読み込みました")
                    else:
                        # デフォルト設定が見つからない場合は、ハードコードされたデフォルト値を使用
                        posting_settings = {
                            "title": "[title]",
                            "content": "[title]の詳細情報です。",
                            "eyecatch": "sample",
                            "movie_size": "auto",
                            "poster": "package",
                            "category": "jan",
                            "sort": "rank",
                            "article": "",
                            "status": "publish",
                            "hour": "h09",
                            "overwrite_existing": False
                        }
                        print(f"build_content: デフォルト設定が見つからないため、ハードコードされたデフォルト値を使用します")
                except Exception as e:
                    print(f"build_content: デフォルト設定読み込みエラー: {e}")
                    # エラーが発生した場合は、ハードコードされたデフォルト値を使用
                    posting_settings = {
                        "title": "[title]",
                        "content": "[title]の詳細情報です。",
                        "eyecatch": "sample",
                        "movie_size": "auto",
                        "poster": "package",
                        "category": "jan",
                        "sort": "rank",
                        "article": "",
                        "status": "publish",
                        "hour": "h09",
                        "overwrite_existing": False
                    }
            
            print(f"build_content: 投稿設定を使用: {posting_settings}")
            
            # タイトルの構築
            title_template = posting_settings.get("title", "[title]")
            title = self.renderer.replace_variables(title_template, item)
            print(f"build_content: タイトル構築完了: {title}")
            
            # コンテンツの構築
            content_template = posting_settings.get("content", "[title]の詳細情報です。")
            
            # 新しいレンダリング機能を使用してコンテンツを生成
            affiliate_url = item.get('affiliateURL', '')
            movie_size = posting_settings.get("movie_size", "auto")
            
            content = self.renderer.render_template(
                template_content=content_template,
                item=item,
                affiliate_url=affiliate_url,
                movie_size=movie_size
            )
            print(f"build_content: コンテンツ構築完了: {len(content)}文字")
            
            # メディアの構築
            media_bytes = None
            media_name = None
            
            # アイキャッチ設定に基づいてメディアを選択
            eyecatch_setting = posting_settings.get("eyecatch", "sample")
            media_url = None
            media_name = None
            
            if eyecatch_setting == "sample" and item.get("sampleImageURL"):
                # sampleImageURLは辞書形式なので、適切なキーからURLを取得
                sample_urls = item["sampleImageURL"]
                if isinstance(sample_urls, dict):
                    # 辞書の場合は最初のURLを使用
                    media_url = list(sample_urls.values())[0] if sample_urls else None
                else:
                    media_url = sample_urls
                media_name = f"{item.get('content_id', 'unknown')}_sample.jpg"
            elif eyecatch_setting == "package" and item.get("imageURL"):
                # imageURLも辞書形式の可能性
                package_urls = item["imageURL"]
                if isinstance(package_urls, dict):
                    # 辞書の場合は最初のURLを使用
                    media_url = list(package_urls.values())[0] if package_urls else None
                else:
                    media_url = package_urls
                media_name = f"{item.get('content_id', 'unknown')}_package.jpg"
            elif eyecatch_setting == "1" and item.get("sampleImageURL"):
                sample_urls = item["sampleImageURL"]
                if isinstance(sample_urls, dict):
                    # 辞書の場合は最初のURLを使用
                    media_url = list(sample_urls.values())[0] if sample_urls else None
                else:
                    media_url = sample_urls
                media_name = f"{item.get('content_id', 'unknown')}_sample1.jpg"
            elif eyecatch_setting == "99" and item.get("sampleImageURL"):
                sample_urls = item["sampleImageURL"]
                if isinstance(sample_urls, dict):
                    # 辞書の場合は最初のURLを使用
                    media_url = list(sample_urls.values())[0] if sample_urls else None
                else:
                    media_url = sample_urls
                media_name = f"{item.get('content_id', 'unknown')}_sample99.jpg"
            else:
                # デフォルトはsample
                sample_urls = item.get("sampleImageURL")
                if isinstance(sample_urls, dict):
                    # 辞書の場合は最初のURLを使用
                    media_url = list(sample_urls.values())[0] if sample_urls else None
                else:
                    media_url = sample_urls
                media_name = f"{item.get('content_id', 'unknown')}_sample.jpg"
            
            if media_url:
                try:
                    print(f"build_content: メディアダウンロード中: {media_url}")
                    media_bytes = self.download_media(media_url)
                    print(f"build_content: メディアダウンロード完了: {len(media_bytes) if media_bytes else 0}バイト")
                except Exception as e:
                    print(f"build_content: メディアダウンロードエラー: {e}")
                    media_bytes = None
                    media_name = None
            
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
        sample_images = item.get('sampleImageURL', {})
        if not sample_images:
            return ''
        
        # DMM APIから返されるsampleImageURLは辞書形式
        # 例: {"large": "url1", "medium": "url2"}
        if isinstance(sample_images, dict):
            # 辞書の値（URL）を取得
            img_urls = list(sample_images.values())
        elif isinstance(sample_images, str):
            # 文字列の場合はカンマ区切りとして処理
            img_urls = [img.strip() for img in sample_images.split(',') if img.strip()]
        else:
            img_urls = []
        
        if not img_urls:
            return ''
        
        html = '<div class="sample-images">'
        for img_url in img_urls:
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

    def post_one(self, item: Dict[str, Any], posting_settings: Dict[str, Any] = None) -> Optional[int]:
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
                overwrite_enabled = posting_settings.get("overwrite_existing", False)
            else:
                # 投稿設定が指定されていない場合は、デフォルト設定を使用
                overwrite_enabled = self.settings.overwrite_existing
            
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
                            # 更新用のデータを準備（カテゴリ・タグは既存のまま）
                            update_data = {
                                "title": title,
                                "content": content,
                                "status": posting_settings.get("status", self.settings.post_status) if posting_settings else self.settings.post_status
                            }
                            
                            print(f"post_one: 更新データ準備完了 - タイトル: {title}, ステータス: {update_data['status']}")
                            
                            # 投稿を更新
                            updated_post = self.wp.update_post(existing_post_id, update_data)
                            print(f"post_one: 既存投稿を更新しました: ID {existing_post_id}")
                            
                            # サムネイルも更新
                            if self.settings.post_thumbnail == "自動設定" and media_bytes and media_name:
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
            post_status = posting_settings.get("status", self.settings.post_status) if posting_settings else self.settings.post_status
            post = self.wp.create_post(title=title, content=content, status=post_status, slug=slug)
            post_id = int(post.get("id"))
            print(f"post_one: 投稿作成成功: ID {post_id}")
            
            # カテゴリとタグの設定
            try:
                if posting_settings and "category" in posting_settings:
                    category_setting = posting_settings["category"]
                    if category_setting == "jan":
                        # JANコードベースのカテゴリ設定
                        jan_code = item.get("JANCode")
                        if jan_code:
                            self.category_manager.set_categories_by_jan(post_id, jan_code)
                            print(f"post_one: JANコードベースのカテゴリ設定完了: {jan_code}")
                    elif category_setting == "custom":
                        # カスタムカテゴリ設定
                        custom_categories = posting_settings.get("custom_categories", [])
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
        
        # 目標投稿数が設定されている場合の処理
        target_count = self.settings.target_new_posts
        if target_count > 0:
            print(f"run_once: 目標投稿数: {target_count}件")
            self.log_manager.info(LogType.SYSTEM, f"目標投稿数: {target_count}件")
        
        # SettingsManagerから投稿設定を取得
        try:
            post_settings = self.settings_manager.load_post_settings()
            if "post_settings" in post_settings and post_setting_num in post_settings["post_settings"]:
                setting = post_settings["post_settings"][post_setting_num]
                posting_settings = {
                    "title": setting.get("title", "[title]"),
                    "content": setting.get("content", "[title]の詳細情報です。"),
                    "eyecatch": setting.get("eyecatch", "sample"),
                    "movie_size": setting.get("movie_size", "auto"),
                    "poster": setting.get("poster", "package"),
                    "category": setting.get("category", "jan"),
                    "sort": setting.get("sort", "rank"),
                    "article": setting.get("article", ""),
                    "status": setting.get("status", "publish"),
                    "hour": setting.get("hour", "h09"),
                    "overwrite_existing": setting.get("overwrite_existing", False),
                    "target_new_posts": setting.get("target_new_posts", 10)
                }
                print(f"run_once: SettingsManagerから投稿設定{post_setting_num}を読み込みました")
                self.log_manager.info(LogType.SYSTEM, f"投稿設定{post_setting_num}読み込み完了")
            else:
                # 投稿設定が見つからない場合はデフォルト値を使用
                posting_settings = {
                    "title": "[title]",
                    "content": "[title]の詳細情報です。",
                    "eyecatch": "sample",
                    "movie_size": "auto",
                    "poster": "package",
                    "category": "jan",
                    "sort": "rank",
                    "article": "",
                    "status": "publish",
                    "hour": "h09",
                    "overwrite_existing": False,
                    "target_new_posts": 10
                }
                print(f"run_once: 投稿設定{post_setting_num}が見つからないため、デフォルト値を使用します")
                self.log_manager.warning(LogType.SYSTEM, f"投稿設定{post_setting_num}が見つからないため、デフォルト値を使用")
        except Exception as e:
            print(f"run_once: 投稿設定読み込みエラー: {e}")
            self.log_manager.error(LogType.SYSTEM, f"投稿設定読み込みエラー: {e}")
            # エラーが発生した場合はデフォルト値を使用
            posting_settings = {
                "title": "[title]",
                "content": "[title]の詳細情報です。",
                "eyecatch": "sample",
                "movie_size": "auto",
                "poster": "package",
                "category": "jan",
                "sort": "rank",
                "article": "",
                "status": "publish",
                "hour": "h09",
                "overwrite_existing": False,
                "target_new_posts": 10
            }
        
        print(f"run_once: 投稿設定{post_setting_num}を使用 - 上書き: {posting_settings['overwrite_existing']}, ステータス: {posting_settings['status']}")
        print(f"run_once: タイトル: {posting_settings['title']}")
        print(f"run_once: コンテンツ: {posting_settings['content'][:50]}...")
        
        while True:
            # アイテムを取得
            items, total = self.search_items_with_offset(offset, batch_size)
            if not items:
                print(f"run_once: これ以上のアイテムが見つかりません")
                self.log_manager.info(LogType.SYSTEM, "これ以上のアイテムが見つかりません")
                break
            
            print(f"run_once: バッチ {offset}: {len(items)}件のアイテムを処理開始")
            self.log_manager.info(LogType.SYSTEM, f"バッチ {offset}: {len(items)}件のアイテムを処理開始")
            
            for i, item in enumerate(items, 1):
                try:
                    print(f"run_once: アイテム{i}を処理中: {item.get('title', 'No title')}")
                    post_id = self.post_one(item, posting_settings)
                    if post_id:
                        created.append(post_id)
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
                    # continue on errors
                    continue
            
            # 次のバッチに進む
            offset += batch_size
            
            # 目標投稿数が設定されていない場合は、最初のバッチのみ処理
            if target_count == 0:
                break
        
        print(f"run_once: 完了。{len(created)}件の投稿を作成")
        self.log_manager.info(LogType.SYSTEM, f"run_once完了: {len(created)}件の投稿を作成")
        return created

    def search_items_with_offset(self, offset: int, batch_size: int) -> Tuple[List[Dict[str, Any]], int]:
        """指定されたオフセットからアイテムを検索する"""
        try:
            resp = self.dmm.item_list(
                site=self.settings.site,
                service=self.settings.service,
                floor=self.settings.floor,
                keyword=self.settings.keyword,
                sort=self.settings.sort,
                gte_date=(self.settings.from_date + "T00:00:00") if self.settings.from_date else None,
                lte_date=(self.settings.to_date + "T23:59:59") if self.settings.to_date else None,
                article=self.settings.article_type or None,
                article_id=self.settings.article_id or None,
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
                post_settings = self.settings_manager.load_post_settings()
                if "post_settings" in post_settings and post_setting_num in post_settings["post_settings"]:
                    setting = post_settings["post_settings"][post_setting_num]
                    posting_settings = {
                        "title": setting.get("title", "[title]"),
                        "content": setting.get("content", "[title]の詳細情報です。"),
                        "eyecatch": setting.get("eyecatch", "sample"),
                        "movie_size": setting.get("movie_size", "auto"),
                        "poster": setting.get("poster", "package"),
                        "category": setting.get("category", "jan"),
                        "sort": setting.get("sort", "rank"),
                        "article": setting.get("article", ""),
                        "status": setting.get("status", "publish"),
                        "hour": setting.get("hour", "h09"),
                        "overwrite_existing": setting.get("overwrite_existing", False)
                    }
                    print(f"run_test: SettingsManagerから投稿設定{post_setting_num}を読み込みました")
                    self.log_manager.info(LogType.SYSTEM, f"投稿設定{post_setting_num}読み込み完了")
                else:
                    # 投稿設定が見つからない場合はデフォルト値を使用
                    posting_settings = {
                        "title": "[title]",
                        "content": "[title]の詳細情報です。",
                        "eyecatch": "sample",
                        "movie_size": "auto",
                        "poster": "package",
                        "category": "jan",
                        "sort": "rank",
                        "article": "",
                        "status": "publish",
                        "hour": "h09",
                        "overwrite_existing": False
                    }
                    print(f"run_test: 投稿設定{post_setting_num}が見つからないため、デフォルト値を使用します")
                    self.log_manager.warning(LogType.SYSTEM, f"投稿設定{post_setting_num}が見つからないため、デフォルト値を使用")
            except Exception as e:
                print(f"run_test: 投稿設定読み込みエラー: {e}")
                self.log_manager.error(LogType.ERROR, f"投稿設定読み込みエラー: {e}")
                # エラーが発生した場合はデフォルト値を使用
                posting_settings = {
                    "title": "[title]",
                    "content": "[title]の詳細情報です。",
                    "eyecatch": "sample",
                    "movie_size": "auto",
                    "poster": "package",
                    "category": "jan",
                    "sort": "rank",
                    "article": "",
                    "status": "publish",
                    "hour": "h09",
                    "overwrite_existing": False
                }
            
            print(f"run_test: 投稿設定{post_setting_num}を使用: {posting_settings}")
            print(f"run_test: タイトル: {posting_settings['title']}")
            print(f"run_test: コンテンツ: {posting_settings['content'][:50]}...")
            print(f"run_test: 上書き: {posting_settings['overwrite_existing']}")
            
            # アイテムを検索
            items, total = self.search_items()
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
            result.append(f"Items to process: {min(len(items), self.settings.hits)}")
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
