from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from settings_manager import SettingsManager


class Settings(BaseModel):
    # DMM API
    dmm_api_id: str = Field(default="", alias="DMM_API_ID")
    dmm_affiliate_id: str = Field(default="", alias="DMM_AFFILIATE_ID")

    # WordPress REST API
    wp_base_url: str = Field(default="", alias="WORDPRESS_BASE_URL")
    wp_username: str = Field(default="", alias="WORDPRESS_USERNAME")
    wp_app_password: str = Field(default="", alias="WORDPRESS_APPLICATION_PASSWORD")

    # Search defaults
    site: str = Field("FANZA", alias="SITE")
    service: str = Field("digital", alias="SERVICE")
    floor: str = Field("videoc", alias="FLOOR")
    hits: int = Field(10, alias="HITS")
    sort: str = Field("date", alias="SORT")
    keyword: str = Field("", alias="KEYWORD")
    from_date: str = Field("", alias="FROM_DATE")
    to_date: str = Field("", alias="TO_DATE")
    article_type: str = Field("", alias="ARTICLE_TYPE")
    article_id: str = Field("", alias="ARTICLE_ID")

    # Post settings (simplified)
    post_status: str = Field("publish", alias="POST_STATUS")
    eye: str = Field("sample", alias="EYE")
    poster: str = Field("package", alias="POSTER")
    maximage: int = Field(10, alias="MAXIMAGE")
    movie_size: str = Field("auto", alias="MOVIE_SIZE")
    random_text1: str = Field("", alias="RANDOM_TEXT1")
    random_text2: str = Field("", alias="RANDOM_TEXT2")
    random_text3: str = Field("", alias="RANDOM_TEXT3")
    limited_flag: int = Field(0, alias="LIMITED_FLAG")
    rand_start_date: str = Field("", alias="RAND_START_DATE")
    rand_end_date: str = Field("", alias="RAND_END_DATE")

    # Selenium options
    use_browser: bool = Field(default=True, alias="USE_BROWSER")
    headless: bool = Field(default=True, alias="HEADLESS")
    click_xpath: str = Field(default='//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a', alias="CLICK_XPATH")
    page_wait_sec: int = Field(default=5, alias="PAGE_WAIT_SEC")
    
    # スクレイピング設定
    description_selectors: List[str] = Field(default=[
        "meta[name=description]",
        "p.tx-productComment",
        "p.summary__txt",
        "p.mg-b20",
        "p.text-overflow",
        "div[class*='description']",
        "div[class*='detail']",
        "div[class*='info']",
        "div[class*='content']"
    ], alias="DESCRIPTION_SELECTORS")
    
    review_selectors: List[str] = Field(default=[
        "#review",
        "div[class*='review']",
        "div[class*='comment']",
        "div[class*='user']"
    ], alias="REVIEW_SELECTORS")

    # GUI用の追加設定項目
    schedule_enabled: bool = Field(default=False, alias="SCHEDULE_ENABLED")
    schedule_interval: str = Field(default="毎日", alias="SCHEDULE_INTERVAL")
    schedule_time: str = Field(default="00:00", alias="SCHEDULE_TIME")
    schedule_day: str = Field(default="月曜日", alias="SCHEDULE_DAY")
    schedule_date: str = Field(default="1日", alias="SCHEDULE_DATE")
    custom_cron: str = Field(default="", alias="CUSTOM_CRON")
    
    # 投稿設定1
    post_title_1: str = Field(default="[title]", alias="POST_TITLE_1")
    post_content_1: str = Field(default="[title]の詳細情報です。", alias="POST_CONTENT_1")
    post_eyecatch_1: str = Field(default="sample", alias="POST_EYECATCH_1")
    post_movie_size_1: str = Field(default="auto", alias="POST_MOVIE_SIZE_1")
    post_poster_1: str = Field(default="package", alias="POST_POSTER_1")
    post_category_1: str = Field(default="jan", alias="POST_CATEGORY_1")
    post_sort_1: str = Field(default="rank", alias="POST_SORT_1")
    post_article_1: str = Field(default="", alias="POST_ARTICLE_1")
    post_status_1: str = Field(default="publish", alias="POST_STATUS_1")
    post_hour_1: str = Field(default="h09", alias="POST_HOUR_1")
    post_overwrite_existing_1: bool = Field(default=False, alias="POST_OVERWRITE_EXISTING_1")
    post_target_new_posts_1: int = Field(default=10, alias="POST_TARGET_NEW_POSTS_1")
    
    # 投稿設定2
    post_title_2: str = Field(default="[title] - 設定2", alias="POST_TITLE_2")
    post_content_2: str = Field(default="[title]の詳細情報です。設定2", alias="POST_CONTENT_2")
    post_eyecatch_2: str = Field(default="package", alias="POST_EYECATCH_2")
    post_movie_size_2: str = Field(default="720", alias="POST_MOVIE_SIZE_2")
    post_poster_2: str = Field(default="sample", alias="POST_POSTER_2")
    post_category_2: str = Field(default="act", alias="POST_CATEGORY_2")
    post_sort_2: str = Field(default="date", alias="POST_SORT_2")
    post_article_2: str = Field(default="actress", alias="POST_ARTICLE_2")
    post_status_2: str = Field(default="draft", alias="POST_STATUS_2")
    post_hour_2: str = Field(default="h12", alias="POST_HOUR_2")
    post_overwrite_existing_2: bool = Field(default=True, alias="POST_OVERWRITE_EXISTING_2")
    post_target_new_posts_2: int = Field(default=20, alias="POST_TARGET_NEW_POSTS_2")
    
    # 投稿設定3
    post_title_3: str = Field(default="[title] - 設定3", alias="POST_TITLE_3")
    post_content_3: str = Field(default="[title]の詳細情報です。設定3", alias="POST_CONTENT_3")
    post_eyecatch_3: str = Field(default="1", alias="POST_EYECATCH_3")
    post_movie_size_3: str = Field(default="600", alias="POST_MOVIE_SIZE_3")
    post_poster_3: str = Field(default="none", alias="POST_POSTER_3")
    post_category_3: str = Field(default="director", alias="POST_CATEGORY_3")
    post_sort_3: str = Field(default="review", alias="POST_SORT_3")
    post_article_3: str = Field(default="genre", alias="POST_ARTICLE_3")
    post_status_3: str = Field(default="publish", alias="POST_STATUS_3")
    post_hour_3: str = Field(default="h18", alias="POST_HOUR_3")
    post_overwrite_existing_3: bool = Field(default=False, alias="POST_OVERWRITE_EXISTING_3")
    post_target_new_posts_3: int = Field(default=15, alias="POST_TARGET_NEW_POSTS_3")
    
    # 投稿設定4
    post_title_4: str = Field(default="[title] - 設定4", alias="POST_TITLE_4")
    post_content_4: str = Field(default="[title]の詳細情報です。設定4", alias="POST_CONTENT_4")
    post_eyecatch_4: str = Field(default="99", alias="POST_EYECATCH_4")
    post_movie_size_4: str = Field(default="560", alias="POST_MOVIE_SIZE_4")
    post_poster_4: str = Field(default="package", alias="POST_POSTER_4")
    post_category_4: str = Field(default="seri", alias="POST_CATEGORY_4")
    post_sort_4: str = Field(default="price", alias="POST_SORT_4")
    post_article_4: str = Field(default="series", alias="POST_ARTICLE_4")
    post_status_4: str = Field(default="draft", alias="POST_STATUS_4")
    post_hour_4: str = Field(default="h21", alias="POST_HOUR_4")
    post_overwrite_existing_4: bool = Field(default=True, alias="POST_OVERWRITE_EXISTING_4")
    post_target_new_posts_4: int = Field(default=25, alias="POST_TARGET_NEW_POSTS_4")
    
    # 投稿作成の動作設定（後方互換性のため残す）
    overwrite_existing: bool = Field(default=False, alias="OVERWRITE_EXISTING")
    target_new_posts: int = Field(default=0, alias="TARGET_NEW_POSTS")
    
    # 投稿設定の管理（settings.jsonのpost_settingsセクション用）
    post_settings: Optional[Dict[str, Any]] = Field(default=None, alias="post_settings")

    @classmethod
    def load(cls) -> "Settings":
        """設定を読み込み"""
        try:
            # 設定マネージャーを使用して設定を読み込み
            base_dir = os.path.dirname(os.path.abspath(__file__))
            settings_manager = SettingsManager(base_dir)
            settings_data = settings_manager.load_settings()
            
            if not settings_data:
                # 設定が空の場合はデフォルト値で初期化
                return cls()
            
            # 設定データを環境変数として設定（後方互換性のため）
            for key, value in settings_data.items():
                if key not in ["last_updated", "version"]:  # メタデータは除外
                    os.environ[key] = str(value)
            
            # 重要な設定値を明示的に設定
            if "USE_BROWSER" in settings_data:
                settings_data["use_browser"] = settings_data["USE_BROWSER"]
            if "HEADLESS" in settings_data:
                settings_data["headless"] = settings_data["HEADLESS"]
            if "CLICK_XPATH" in settings_data:
                settings_data["click_xpath"] = settings_data["CLICK_XPATH"]
            if "PAGE_WAIT_SEC" in settings_data:
                settings_data["page_wait_sec"] = settings_data["PAGE_WAIT_SEC"]
            
            # Pydanticモデルとして検証
            return cls.model_validate(settings_data, from_attributes=True)
            
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            # エラーが発生した場合はデフォルト値で初期化
            return cls()
    
    @classmethod
    def save(cls, settings_data: dict) -> bool:
        """設定を保存"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            settings_manager = SettingsManager(base_dir)
            return settings_manager.save_settings(settings_data)
        except Exception as e:
            print(f"設定保存エラー: {e}")
            return False
