import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SettingsManager:
    """統一された設定管理クラス"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "config")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self.lock_file = os.path.join(self.config_dir, "settings.lock")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 初期設定ファイルが存在しない場合は作成
        if not os.path.exists(self.settings_file):
            logger.info("設定ファイルが存在しません。デフォルト設定を作成します")
            self._create_default_settings()
        else:
            # 既存の設定ファイルのバックアップを作成
            self._create_backup()
            # 設定ファイルの整合性をチェック
            try:
                logger.info("既存の設定ファイルの整合性をチェック中...")
                settings = self.load_settings()
                logger.info(f"設定ファイルの読み込みに成功しました: {len(settings)}件の設定")
                
                # 設定が空の場合はデフォルト設定を作成
                if not settings:
                    logger.info("設定が空のため、デフォルト設定を作成します")
                    self._create_default_settings()
                    settings = self.load_settings()
                    logger.info(f"デフォルト設定の作成が完了しました: {len(settings)}件の設定")
                    
            except Exception as e:
                logger.error(f"設定ファイルの整合性チェックエラー: {e}")
                logger.info("破損した設定ファイルをバックアップして、デフォルト設定を作成します")
                self._backup_corrupted_file()
                self._create_default_settings()
    
    def _create_default_settings(self) -> None:
        """デフォルト設定を作成"""
        default_settings = {
            # DMM API
            "DMM_API_ID": "",
            "DMM_AFFILIATE_ID": "",
            
            # WordPress REST API
            "WORDPRESS_BASE_URL": "",
            "WORDPRESS_USERNAME": "",
            "WORDPRESS_APPLICATION_PASSWORD": "",
            
            # 検索設定
            "SITE": "FANZA",
            "SERVICE": "digital",
            "FLOOR": "videoc",
            "HITS": 10,
            "SORT": "date",
            "KEYWORD": "",
            "MAXIMAGE": 1,
            "LIMITED_FLAG": 0,
            "ARTICLE_TYPE": "",
            "PAGE_WAIT_SEC": 3,
            
            # Chrome設定
            "USE_BROWSER": True,
            "HEADLESS": True,
            "CLICK_XPATH": '//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a',
            
            # スクレイピング設定
            "DESCRIPTION_SELECTORS": [
                "meta[name=description]",
                "p.tx-productComment",
                "p.summary__txt",
                "p.mg-b20",
                "p.text-overflow",
                "div[class*='description']",
                "div[class*='detail']",
                "div[class*='info']",
                "div[class*='content']"
            ],
            "REVIEW_SELECTORS": [
                "#review",
                "div[class*='review']",
                "div[class*='comment']",
                "div[class*='user']"
            ],
            
            # スケジュール設定
            "SCHEDULE_ENABLED": False,
            "SCHEDULE_INTERVAL": "毎日",
            "SCHEDULE_TIME": "09:00",
            "SCHEDULE_DAY": "月曜日",
            "SCHEDULE_DATE": "1日",
            "CUSTOM_CRON": "",
            
            # 投稿設定1-4
            "POST_TITLE_1": "[title]",
            "POST_EYECATCH_1": "sample",
            "POST_MOVIE_SIZE_1": "auto",
            "POST_POSTER_1": "package",
            "POST_CATEGORY_1": "jan",
            "POST_SORT_1": "rank",
            "POST_ARTICLE_1": "",
            "POST_STATUS_1": "publish",
            "POST_HOUR_1": "h09",
            "POST_OVERWRITE_EXISTING_1": False,
            "POST_TARGET_NEW_POSTS_1": 10,
            
            "POST_TITLE_2": "[title] - 設定2",
            "POST_EYECATCH_2": "package",
            "POST_MOVIE_SIZE_2": "720",
            "POST_POSTER_2": "sample",
            "POST_CATEGORY_2": "act",
            "POST_SORT_2": "date",
            "POST_ARTICLE_2": "actress",
            "POST_STATUS_2": "draft",
            "POST_HOUR_2": "h12",
            "POST_OVERWRITE_EXISTING_2": True,
            "POST_TARGET_NEW_POSTS_2": 20,
            
            "POST_TITLE_3": "[title] - 設定3",
            "POST_EYECATCH_3": "1",
            "POST_MOVIE_SIZE_3": "600",
            "POST_POSTER_3": "none",
            "POST_CATEGORY_3": "director",
            "POST_SORT_3": "review",
            "POST_ARTICLE_3": "genre",
            "POST_STATUS_3": "publish",
            "POST_HOUR_3": "h18",
            "POST_OVERWRITE_EXISTING_3": False,
            "POST_TARGET_NEW_POSTS_3": 15,
            
            "POST_TITLE_4": "[title] - 設定4",
            "POST_EYECATCH_4": "99",
            "POST_MOVIE_SIZE_4": "560",
            "POST_POSTER_4": "package",
            "POST_CATEGORY_4": "seri",
            "POST_SORT_4": "price",
            "POST_ARTICLE_4": "series",
            "POST_STATUS_4": "draft",
            "POST_HOUR_4": "h21",
            "POST_OVERWRITE_EXISTING_4": True,
            "POST_TARGET_NEW_POSTS_4": 25,
            
            # 共通設定
            "EXCERPT_TEMPLATE": "[title]の詳細情報です。",
            "MAX_SAMPLE_IMAGES": 5,
            "CATEGORIES": "",
            "TAGS": "",
            "AFFILIATE1_TEXT": "詳細を見る",
            "AFFILIATE1_COLOR": "#ffffff",
            "AFFILIATE1_BG": "#007cba",
            "AFFILIATE2_TEXT": "購入する",
            "AFFILIATE2_COLOR": "#ffffff",
            "AFFILIATE2_BG": "#d63638",
            "POST_DATE_SETTING": "now",
            "RANDOM_TEXT1": "",
            "RANDOM_TEXT2": "",
            "RANDOM_TEXT3": "",
            
            # 自動実行設定
            "AUTO_ON": False,
            "TODAY": False,
            "THREEDAY": False,
            "RANGE": False,
            "S_DATE": "",
            "E_DATE": "",
            "EXE_MIN": 0,
            
            # 絞り込み設定
            "ID_FILTER": "",
            "DATE_FILTER_ENABLED": False,
            "DATE_FILTER_START": "",
            "DATE_FILTER_END": "",
            
            # 24時間設定（正しい変数名で）
            "h00": False, "h00_number": "1",
            "h01": False, "h01_number": "1",
            "h02": False, "h02_number": "1",
            "h03": False, "h03_number": "1",
            "h04": False, "h04_number": "1",
            "h05": False, "h05_number": "1",
            "h06": False, "h06_number": "1",
            "h07": False, "h07_number": "1",
            "h08": False, "h08_number": "1",
            "h09": False, "h09_number": "1",
            "h10": False, "h10_number": "1",
            "h11": False, "h11_number": "1",
            "h12": False, "h12_number": "1",
            "h13": False, "h13_number": "1",
            "h14": False, "h14_number": "1",
            "h15": False, "h15_number": "1",
            "h16": False, "h16_number": "1",
            "h17": False, "h17_number": "1",
            "h18": False, "h18_number": "1",
            "h19": False, "h19_number": "1",
            "h20": False, "h20_number": "1",
            "h21": False, "h21_number": "1",
            "h22": False, "h22_number": "1",
            "h23": False, "h23_number": "1",
            
            # 投稿内容テンプレート
            "POST_CONTENT_1": "[title]の詳細情報です。",
            "POST_CONTENT_2": "[title]の詳細情報です。設定2",
            "POST_CONTENT_3": "[title]の詳細情報です。設定3",
            "POST_CONTENT_4": "[title]の詳細情報です。設定4",
            
            # メタデータ
            "last_updated": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        self.save_settings(default_settings)
        logger.info("デフォルト設定を作成しました")
    
    def _backup_corrupted_file(self) -> None:
        """破損した設定ファイルをバックアップ"""
        try:
            if os.path.exists(self.settings_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"corrupted_{timestamp}.json")
                shutil.copy2(self.settings_file, backup_path)
                logger.info(f"破損した設定ファイルをバックアップ: {backup_path}")
        except Exception as e:
            logger.error(f"破損ファイルのバックアップエラー: {e}")
    
    def _create_backup(self) -> None:
        """設定ファイルのバックアップを作成"""
        try:
            if os.path.exists(self.settings_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"settings_{timestamp}.json")
                shutil.copy2(self.settings_file, backup_path)
                logger.info(f"設定ファイルをバックアップ: {backup_path}")
        except Exception as e:
            logger.error(f"バックアップ作成エラー: {e}")
    
    def _is_locked(self) -> bool:
        """設定ファイルがロックされているかチェック"""
        return os.path.exists(self.lock_file)
    
    def _lock_settings(self) -> bool:
        """設定ファイルをロック"""
        try:
            with open(self.lock_file, "w") as f:
                f.write(datetime.now().isoformat())
            return True
        except Exception as e:
            logger.error(f"設定ロックエラー: {e}")
            return False
    
    def _unlock_settings(self) -> bool:
        """設定ファイルのロックを解除"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
            return True
        except Exception as e:
            logger.error(f"設定アンロックエラー: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """設定を読み込み"""
        try:
            if not os.path.exists(self.settings_file):
                logger.warning("設定ファイルが存在しません")
                return {}
            
            with open(self.settings_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    logger.warning("設定ファイルが空です")
                    return {}
                
                settings = json.loads(content)
                logger.info(f"設定を読み込みました: {len(settings)}件")
                return settings
                
        except json.JSONDecodeError as e:
            logger.error(f"JSONデコードエラー: {e}")
            self._backup_corrupted_file()
            return {}
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            return {}
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """設定を保存"""
        try:
            if self._is_locked():
                logger.warning("設定がロックされているため、保存できません")
                return False
            
            # ロックを取得
            if not self._lock_settings():
                logger.error("設定のロックを取得できませんでした")
                return False
            
            try:
                # 保存前にバックアップを作成
                self._create_backup()
                
                # 最終更新日時を更新
                settings["last_updated"] = datetime.now().isoformat()
                
                # tkinterオブジェクトを適切に処理
                serializable_settings = self._prepare_for_serialization(settings)
                
                # 一時ファイルに保存してから、本ファイルに移動（安全な保存）
                temp_file = self.settings_file + ".tmp"
                try:
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(serializable_settings, f, ensure_ascii=False, indent=2)
                    
                    # 一時ファイルを本ファイルに移動
                    if os.path.exists(self.settings_file):
                        os.remove(self.settings_file)
                    os.rename(temp_file, self.settings_file)
                    
                    logger.info("設定を保存しました")
                    return True
                    
                except Exception as e:
                    logger.error(f"一時ファイル保存エラー: {e}")
                    # 一時ファイルが残っている場合は削除
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    return False
                    
            finally:
                # ロックを解除
                self._unlock_settings()
                
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """指定されたキーの設定値を取得"""
        try:
            settings = self.load_settings()
            return settings.get(key, default)
        except Exception as e:
            logger.error(f"設定値取得エラー: {e}")
            return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """指定されたキーの設定値を設定"""
        try:
            settings = self.load_settings()
            settings[key] = value
            return self.save_settings(settings)
        except Exception as e:
            logger.error(f"設定値設定エラー: {e}")
            return False
    
    def get_post_settings(self, post_num: str = "1") -> Dict[str, Any]:
        """指定された投稿設定番号の設定を取得"""
        try:
            settings = self.load_settings()
            post_settings = {}
            
            # 投稿設定のプレフィックス
            prefix = f"POST_"
            
            for key, value in settings.items():
                if key.startswith(prefix) and key.endswith(f"_{post_num}"):
                    # プレフィックスと番号を除去してキー名を取得
                    setting_key = key[len(prefix):-len(f"_{post_num}")]
                    post_settings[setting_key] = value
            
            return post_settings
        except Exception as e:
            logger.error(f"投稿設定取得エラー: {e}")
            return {}
    
    def save_post_settings(self, post_num: str, post_settings: Dict[str, Any]) -> bool:
        """指定された投稿設定番号の設定を保存"""
        try:
            settings = self.load_settings()
            
            # 既存の投稿設定を削除
            keys_to_remove = [key for key in settings.keys() 
                             if key.startswith("POST_") and key.endswith(f"_{post_num}")]
            for key in keys_to_remove:
                del settings[key]
            
            # 新しい投稿設定を追加
            for key, value in post_settings.items():
                settings[f"POST_{key}_{post_num}"] = value
            
            return self.save_settings(settings)
        except Exception as e:
            logger.error(f"投稿設定保存エラー: {e}")
            return False
    
    def get_all_post_settings(self) -> Dict[str, Dict[str, Any]]:
        """全ての投稿設定を取得"""
        try:
            all_settings = {}
            for i in range(1, 5):
                post_num = str(i)
                post_settings = self.get_post_settings(post_num)
                if post_settings:
                    all_settings[post_num] = post_settings
            
            return all_settings
        except Exception as e:
            logger.error(f"全投稿設定取得エラー: {e}")
            return {}
    
    def export_settings(self, export_path: str) -> bool:
        """設定をエクスポート"""
        try:
            settings = self.load_settings()
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logger.info(f"設定をエクスポートしました: {export_path}")
            return True
        except Exception as e:
            logger.error(f"設定エクスポートエラー: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """設定をインポート"""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                imported_settings = json.load(f)
            
            # 現在の設定とマージ
            current_settings = self.load_settings()
            current_settings.update(imported_settings)
            
            # 最終更新日時を更新
            current_settings["last_updated"] = datetime.now().isoformat()
            
            if self.save_settings(current_settings):
                logger.info(f"設定をインポートしました: {import_path}")
                return True
            else:
                logger.error("設定の保存に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"設定インポートエラー: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """設定をデフォルトにリセット"""
        try:
            # 現在の設定をバックアップ
            self._create_backup()
            
            # デフォルト設定を作成
            self._create_default_settings()
            
            logger.info("設定をデフォルトにリセットしました")
            return True
        except Exception as e:
            logger.error(f"設定リセットエラー: {e}")
            return False
    
    def get_backup_files(self) -> List[str]:
        """バックアップファイルの一覧を取得"""
        try:
            if not os.path.exists(self.backup_dir):
                return []
            
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith(".json"):
                    backup_files.append(file)
            
            return sorted(backup_files, reverse=True)
        except Exception as e:
            logger.error(f"バックアップファイル一覧取得エラー: {e}")
            return []
    
    def restore_from_backup(self, backup_filename: str) -> bool:
        """指定されたバックアップから復元"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if not os.path.exists(backup_path):
                logger.error(f"バックアップファイルが存在しません: {backup_filename}")
                return False
            
            # 現在の設定をバックアップ
            self._create_backup()
            
            # バックアップファイルをコピー
            shutil.copy2(backup_path, self.settings_file)
            
            logger.info(f"バックアップから復元しました: {backup_filename}")
            return True
        except Exception as e:
            logger.error(f"バックアップ復元エラー: {e}")
            return False
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, List[str]]:
        """設定値の妥当性をチェック"""
        errors = {}
        
        try:
            # 必須項目のチェック
            required_fields = ["DMM_API_ID", "WORDPRESS_BASE_URL"]
            for field in required_fields:
                if not settings.get(field):
                    if "required" not in errors:
                        errors["required"] = []
                    errors["required"].append(f"必須項目 '{field}' が設定されていません")
            
            # 数値項目のチェック
            numeric_fields = ["HITS", "MAXIMAGE", "PAGE_WAIT_SEC"]
            for field in numeric_fields:
                if field in settings:
                    try:
                        int(settings[field])
                    except (ValueError, TypeError):
                        if "numeric" not in errors:
                            errors["numeric"] = []
                        errors["numeric"].append(f"'{field}' は数値である必要があります")
            
            # 真偽値項目のチェック
            boolean_fields = ["SCHEDULE_ENABLED", "AUTO_ON"]
            for field in boolean_fields:
                if field in settings:
                    value = settings[field]
                    if not isinstance(value, bool) and value not in ["true", "false", "0", "1"]:
                        if "boolean" not in errors:
                            errors["boolean"] = []
                        errors["boolean"].append(f"'{field}' は真偽値である必要があります")
            
        except Exception as e:
            logger.error(f"設定妥当性チェックエラー: {e}")
            errors["system"] = [f"システムエラー: {e}"]
        
        return errors

    def _prepare_for_serialization(self, data: Any) -> Any:
        """JSONシリアライズ可能な形式にデータを変換"""
        if isinstance(data, dict):
            return {key: self._prepare_for_serialization(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_serialization(item) for item in data]
        elif hasattr(data, 'get'):  # StringVar, IntVar, BooleanVarなどのtkinter変数
            try:
                return data.get()
            except:
                return str(data)
        else:
            return data

    def get_categories(self) -> List[str]:
        """カテゴリ一覧を取得"""
        try:
            # デフォルトのカテゴリ一覧
            default_categories = [
                "jan", "rank", "date", "price", "review", "popular"
            ]
            
            # 設定ファイルからカテゴリを読み込み
            settings = self.load_settings()
            custom_categories = settings.get("CUSTOM_CATEGORIES", [])
            
            # デフォルトとカスタムを結合
            all_categories = default_categories + custom_categories
            
            return all_categories
        except Exception as e:
            logger.error(f"カテゴリ取得エラー: {e}")
            return ["jan", "rank", "date", "price", "review", "popular"]
    
    def get_tags(self) -> List[str]:
        """タグ一覧を取得"""
        try:
            # デフォルトのタグ一覧
            default_tags = [
                "FANZA", "動画", "アダルト", "エンターテイメント"
            ]
            
            # 設定ファイルからタグを読み込み
            settings = self.load_settings()
            custom_tags = settings.get("CUSTOM_TAGS", [])
            
            # デフォルトとカスタムを結合
            all_tags = default_tags + custom_tags
            
            return all_tags
        except Exception as e:
            logger.error(f"タグ取得エラー: {e}")
            return ["FANZA", "動画", "アダルト", "エンターテイメント"]
