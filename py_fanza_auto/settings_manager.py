import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List


class SettingsManager:
    """投稿設定を管理するクラス"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "config")
        self.templates_dir = os.path.join(base_dir, "templates")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        self.post_settings_file = os.path.join(self.config_dir, "post_settings.json")
        self.lock_file = os.path.join(self.config_dir, "settings.lock")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 初期設定ファイルが存在しない場合は作成
        if not os.path.exists(self.post_settings_file):
            self._create_default_post_settings()
        else:
            # 既存の設定ファイルのバックアップを作成
            self._create_backup()
    
    def _create_backup(self):
        """設定ファイルのバックアップを作成"""
        try:
            if os.path.exists(self.post_settings_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"post_settings_{timestamp}.json")
                shutil.copy2(self.post_settings_file, backup_file)
                print(f"設定のバックアップを作成しました: {backup_file}")
        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
    
    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """設定値の妥当性をチェック"""
        try:
            if "post_settings" not in settings:
                return False
            
            for setting_id, setting in settings["post_settings"].items():
                # 必須フィールドのチェック
                required_fields = ["title", "content", "eyecatch", "status"]
                for field in required_fields:
                    if field not in setting:
                        print(f"設定{setting_id}に必須フィールド'{field}'がありません")
                        return False
                
                # 値の妥当性チェック
                if setting.get("status") not in ["publish", "draft", "private"]:
                    print(f"設定{setting_id}のstatus値が無効です: {setting.get('status')}")
                    return False
                
                if setting.get("eyecatch") not in ["sample", "package", "1", "99"]:
                    print(f"設定{setting_id}のeyecatch値が無効です: {setting.get('eyecatch')}")
                    return False
            
            return True
        except Exception as e:
            print(f"設定検証エラー: {e}")
            return False
    
    def _is_locked(self) -> bool:
        """設定がロックされているかチェック"""
        return os.path.exists(self.lock_file)
    
    def lock_settings(self):
        """設定をロックする"""
        try:
            with open(self.lock_file, "w") as f:
                f.write(f"Locked at {datetime.now().isoformat()}")
            print("設定をロックしました")
        except Exception as e:
            print(f"設定ロックエラー: {e}")
    
    def unlock_settings(self):
        """設定のロックを解除する"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                print("設定のロックを解除しました")
        except Exception as e:
            print(f"設定ロック解除エラー: {e}")
    
    def get_backup_list(self) -> List[str]:
        """利用可能なバックアップファイルのリストを取得"""
        try:
            if not os.path.exists(self.backup_dir):
                return []
            
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("post_settings_") and filename.endswith(".json"):
                    backups.append(filename)
            
            return sorted(backups, reverse=True)
        except Exception as e:
            print(f"バックアップリスト取得エラー: {e}")
            return []
    
    def restore_from_backup(self, backup_filename: str) -> bool:
        """指定されたバックアップから設定を復元"""
        try:
            if self._is_locked():
                print("設定がロックされているため、復元できません")
                return False
            
            backup_file = os.path.join(self.backup_dir, backup_filename)
            if not os.path.exists(backup_file):
                print(f"バックアップファイルが見つかりません: {backup_filename}")
                return False
            
            # 現在の設定をバックアップ
            self._create_backup()
            
            # バックアップから復元
            with open(backup_file, "r", encoding="utf-8") as f:
                restored_settings = json.load(f)
            
            # 復元された設定を検証
            if not self._validate_settings(restored_settings):
                print("復元された設定が無効です")
                return False
            
            # 設定を復元
            self.save_post_settings(restored_settings)
            print(f"設定を復元しました: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"設定復元エラー: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """設定をデフォルト値にリセット"""
        try:
            if self._is_locked():
                print("設定がロックされているため、リセットできません")
                return False
            
            # 現在の設定をバックアップ
            self._create_backup()
            
            # デフォルト設定を作成
            self._create_default_post_settings()
            print("設定をデフォルト値にリセットしました")
            return True
            
        except Exception as e:
            print(f"設定リセットエラー: {e}")
            return False

    def _create_default_post_settings(self):
        """デフォルトの投稿設定を作成"""
        default_settings = {
            "post_settings": {
                "1": {
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
                },
                "2": {
                    "title": "[title] - 設定2",
                    "content": "[title]の詳細情報です。設定2",
                    "eyecatch": "package",
                    "movie_size": "720",
                    "poster": "sample",
                    "category": "act",
                    "sort": "date",
                    "article": "actress",
                    "status": "draft",
                    "hour": "h12",
                    "overwrite_existing": True,
                    "target_new_posts": 20
                },
                "3": {
                    "title": "[title] - 設定3",
                    "content": "[title]の詳細情報です。設定3",
                    "eyecatch": "1",
                    "movie_size": "600",
                    "poster": "none",
                    "category": "director",
                    "sort": "review",
                    "article": "genre",
                    "status": "publish",
                    "hour": "h18",
                    "overwrite_existing": False,
                    "target_new_posts": 15
                },
                "4": {
                    "title": "[title] - 設定4",
                    "content": "[title]の詳細情報です。設定4",
                    "eyecatch": "99",
                    "movie_size": "560",
                    "poster": "package",
                    "category": "seri",
                    "sort": "price",
                    "article": "series",
                    "status": "draft",
                    "hour": "h21",
                    "overwrite_existing": True,
                    "target_new_posts": 25
                }
            }
        }
        
        # デフォルトのHTMLテンプレートファイルも作成
        self._create_default_templates()
        
        # 設定ファイルを保存
        self.save_post_settings(default_settings)
    
    def _create_default_templates(self):
        """デフォルトのHTMLテンプレートファイルを作成"""
        templates = {
            "post_content_1.html": "[title]の詳細情報です。",
            "post_content_2.html": "[title]の詳細情報です。設定2",
            "post_content_3.html": "[title]の詳細情報です。設定3",
            "post_content_4.html": "[title]の詳細情報です。設定4"
        }
        
        for filename, content in templates.items():
            filepath = os.path.join(self.templates_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
    
    def load_post_settings(self) -> Dict[str, Any]:
        """投稿設定を読み込む"""
        try:
            if os.path.exists(self.post_settings_file):
                with open(self.post_settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                    # 設定の妥当性をチェック
                    if not self._validate_settings(settings):
                        print("設定ファイルが破損しているため、デフォルト設定を使用します")
                        # 破損した設定をバックアップ
                        corrupted_backup = os.path.join(self.backup_dir, f"corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                        shutil.copy2(self.post_settings_file, corrupted_backup)
                        # デフォルト設定を作成
                        self._create_default_post_settings()
                        return self.load_post_settings()
                    
                    return settings
            else:
                return {"post_settings": {}}
        except Exception as e:
            print(f"投稿設定読み込みエラー: {e}")
            # エラーが発生した場合は、デフォルト設定を作成
            self._create_default_post_settings()
            return self.load_post_settings()
    
    def save_post_settings(self, settings: Dict[str, Any]):
        """投稿設定を保存する"""
        try:
            if self._is_locked():
                print("設定がロックされているため、保存できません")
                return False
            
            # 設定の妥当性をチェック
            if not self._validate_settings(settings):
                print("設定値が無効なため、保存できません")
                return False
            
            # 保存前にバックアップを作成
            self._create_backup()
            
            # 設定を保存
            with open(self.post_settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            print("設定を保存しました")
            return True
            
        except Exception as e:
            print(f"投稿設定保存エラー: {e}")
            return False
    
    def get_post_content(self, setting_id: str) -> str:
        """指定された設定IDの投稿内容を取得"""
        try:
            settings = self.load_post_settings()
            post_setting = settings.get("post_settings", {}).get(setting_id, {})
            # content_fileではなく、直接contentを使用
            content = post_setting.get("content", "")
            
            if content:
                return content
            
            return ""
        except Exception as e:
            print(f"投稿内容取得エラー: {e}")
            return ""
    
    def save_post_content(self, setting_id: str, content: str):
        """指定された設定IDの投稿内容を保存"""
        try:
            if self._is_locked():
                print("設定がロックされているため、保存できません")
                return False
            
            settings = self.load_post_settings()
            post_setting = settings.get("post_settings", {}).get(setting_id, {})
            content_file = post_setting.get("content_file", "")
            
            if content_file:
                filepath = os.path.join(self.base_dir, content_file)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                return True
            
            return False
        except Exception as e:
            print(f"投稿内容保存エラー: {e}")
            return False
    
    def update_post_setting(self, setting_id: str, key: str, value: Any):
        """指定された設定IDの特定の設定値を更新"""
        try:
            if self._is_locked():
                print("設定がロックされているため、更新できません")
                return False
            
            settings = self.load_post_settings()
            if "post_settings" not in settings:
                settings["post_settings"] = {}
            if setting_id not in settings["post_settings"]:
                settings["post_settings"][setting_id] = {}
            
            # 更新前の値を保存
            old_value = settings["post_settings"][setting_id].get(key)
            
            # 値を更新
            settings["post_settings"][setting_id][key] = value
            
            # 設定を保存
            if self.save_post_settings(settings):
                print(f"設定{setting_id}の{key}を{old_value}から{value}に更新しました")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"設定更新エラー: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """利用可能なカテゴリのリストを取得"""
        try:
            # 設定ファイルからカテゴリを読み込み
            if hasattr(self, 'settings') and hasattr(self.settings, 'post_settings'):
                categories = set()
                for setting_num in ['1', '2', '3', '4']:
                    if hasattr(self.settings, f'post_category_{setting_num}'):
                        category = getattr(self.settings, f'post_category_{setting_num}')
                        if category:
                            categories.add(category)
                
                # デフォルトのカテゴリも追加
                default_categories = ["jan", "act", "director", "seri"]
                categories.update(default_categories)
                
                return list(categories)
            else:
                # デフォルトのカテゴリリストを返す
                return ["jan", "act", "director", "seri"]
        except Exception as e:
            print(f"カテゴリ取得エラー: {e}")
            return ["jan", "act", "director", "seri"]
    
    def get_tags(self) -> List[str]:
        """利用可能なタグのリストを取得"""
        try:
            # 設定ファイルからタグを読み込み
            if hasattr(self, 'settings') and hasattr(self.settings, 'tags'):
                tags_str = getattr(self.settings, 'tags', '')
                if tags_str:
                    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            # デフォルトのタグリストを返す
            return []
        except Exception as e:
            print(f"タグ取得エラー: {e}")
            return []
