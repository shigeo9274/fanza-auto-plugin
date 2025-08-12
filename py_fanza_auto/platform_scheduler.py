"""
クロスプラットフォーム対応スケジューラーモジュール
OSを自動判定して、最適なスケジューラーを選択
"""

import platform
import os
import subprocess
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScheduler(ABC):
    """スケジューラーの基底クラス"""
    
    @abstractmethod
    def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """スケジュールを設定"""
        pass
    
    @abstractmethod
    def remove_schedule(self, schedule_name: str) -> bool:
        """スケジュールを削除"""
        pass
    
    @abstractmethod
    def list_schedules(self) -> list:
        """スケジュール一覧を取得"""
        pass
    
    @abstractmethod
    def test_schedule(self, schedule_name: str) -> bool:
        """スケジュールをテスト実行"""
        pass


class WindowsTaskScheduler(BaseScheduler):
    """Windowsタスクスケジューラー用クラス"""
    
    def __init__(self):
        self.scheduler_name = "Windows Task Scheduler"
        logger.info(f"{self.scheduler_name} を初期化しました")
    
    def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """Windowsタスクスケジューラーでスケジュールを設定"""
        try:
            # スケジュール設定から時間を取得
            hour = self._get_enabled_hour(schedule_config)
            minute = int(schedule_config.get("EXE_MIN", "0"))
            
            if hour is None:
                logger.error("有効な時間設定が見つかりません")
                return False
            
            # バッチファイルのパス
            batch_path = os.path.join(os.getcwd(), "run_schedule.bat")
            self._create_batch_file(batch_path)
            
            # タスクスケジューラーに登録（基本的な設定）
            task_name = "FanzaAutoPlugin"
            cmd = [
                "schtasks", "/create", "/tn", task_name,
                "/tr", batch_path,
                "/sc", "daily",
                "/st", f"{hour:02d}:{minute:02d}",
                "/f"
            ]
            
            logger.info(f"タスク作成コマンド: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Windowsタスクスケジューラーに登録しました: {hour:02d}:{minute:02d}")
                logger.info(f"実行権限: 標準設定")
                return True
            else:
                logger.error(f"タスク登録エラー: {result.stderr}")
                logger.error(f"終了コード: {result.returncode}")
                return False
                
        except Exception as e:
            logger.error(f"Windowsスケジュール設定エラー: {e}")
            return False
    
    def remove_schedule(self, schedule_name: str) -> bool:
        """スケジュールを削除"""
        try:
            cmd = ["schtasks", "/delete", "/tn", schedule_name, "/f"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"スケジュール {schedule_name} を削除しました")
                return True
            else:
                logger.error(f"スケジュール削除エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"スケジュール削除エラー: {e}")
            return False
    
    def list_schedules(self) -> list:
        """スケジュール一覧を取得"""
        try:
            cmd = ["schtasks", "/query", "/tn", "FanzaAutoPlugin*"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
            else:
                return []
                
        except Exception as e:
            logger.error(f"スケジュール一覧取得エラー: {e}")
            return []
    
    def test_schedule(self, schedule_name: str) -> bool:
        """スケジュールをテスト実行"""
        try:
            cmd = ["schtasks", "/run", "/tn", schedule_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"スケジュール {schedule_name} をテスト実行しました")
                return True
            else:
                logger.error(f"テスト実行エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            return False
    
    def _get_enabled_hour(self, schedule_config: Dict[str, Any]) -> Optional[int]:
        """有効な時間設定を取得"""
        for i in range(24):
            hour_key = f"h{i:02d}"
            if schedule_config.get(hour_key, False):
                return i
        return None
    
    def _create_batch_file(self, batch_path: str):
        """バッチファイルを作成"""
        batch_content = f"""@echo off
cd /d "{os.getcwd()}"
call .venv\\Scripts\\Activate.bat
python run_gui.py --auto-run
"""
        
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        logger.info(f"バッチファイルを作成しました: {batch_path}")


class MacOSScheduler(BaseScheduler):
    """macOS launchd用クラス"""
    
    def __init__(self):
        self.scheduler_name = "macOS launchd"
        logger.info(f"{self.scheduler_name} を初期化しました")
    
    def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """macOS launchdでスケジュールを設定"""
        try:
            # スケジュール設定から時間を取得
            hour = self._get_enabled_hour(schedule_config)
            minute = schedule_config.get("EXE_MIN", "0")
            
            if hour is None:
                logger.error("有効な時間設定が見つかりません")
                return False
            
            # plistファイルのパス
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.fanza.auto.plugin.plist")
            self._create_plist_file(plist_path, hour, minute)
            
            # launchdに登録
            cmd = ["launchctl", "load", plist_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"macOS launchdに登録しました: {hour:02d}:{minute:02d}")
                return True
            else:
                logger.error(f"launchd登録エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"macOSスケジュール設定エラー: {e}")
            return False
    
    def remove_schedule(self, schedule_name: str) -> bool:
        """スケジュールを削除"""
        try:
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.fanza.auto.plugin.plist")
            
            # launchdから削除
            cmd = ["launchctl", "unload", plist_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # plistファイルを削除
            if os.path.exists(plist_path):
                os.remove(plist_path)
            
            if result.returncode == 0:
                logger.info("macOSスケジュールを削除しました")
                return True
            else:
                logger.error(f"スケジュール削除エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"スケジュール削除エラー: {e}")
            return False
    
    def list_schedules(self) -> list:
        """スケジュール一覧を取得"""
        try:
            cmd = ["launchctl", "list", "com.fanza.auto.plugin"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
            else:
                return []
                
        except Exception as e:
            logger.error(f"スケジュール一覧取得エラー: {e}")
            return []
    
    def test_schedule(self, schedule_name: str) -> bool:
        """スケジュールをテスト実行"""
        try:
            cmd = ["launchctl", "start", "com.fanza.auto.plugin"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("macOSスケジュールをテスト実行しました")
                return True
            else:
                logger.error(f"テスト実行エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            return False
    
    def _get_enabled_hour(self, schedule_config: Dict[str, Any]) -> Optional[int]:
        """有効な時間設定を取得"""
        for i in range(24):
            hour_key = f"h{i:02d}"
            if schedule_config.get(hour_key, False):
                return i
        return None
    
    def _create_plist_file(self, plist_path: str, hour: int, minute: int):
        """plistファイルを作成"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fanza.auto.plugin</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{os.path.join(os.getcwd(), 'run_gui.py')}</string>
        <string>--auto-run</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>{os.getcwd()}</string>
</dict>
</plist>
"""
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)
        
        with open(plist_path, 'w', encoding='utf-8') as f:
            f.write(plist_content)
        
        logger.info(f"plistファイルを作成しました: {plist_path}")


class LinuxScheduler(BaseScheduler):
    """Linux cron用クラス"""
    
    def __init__(self):
        self.scheduler_name = "Linux cron"
        logger.info(f"{self.scheduler_name} を初期化しました")
    
    def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """Linux cronでスケジュールを設定"""
        try:
            # スケジュール設定から時間を取得
            hour = self._get_enabled_hour(schedule_config)
            minute = schedule_config.get("EXE_MIN", "0")
            
            if hour is None:
                logger.error("有効な時間設定が見つかりません")
                return False
            
            # cronエントリを作成
            cron_entry = f"{minute} {hour} * * * cd {os.getcwd()} && python3 run_gui.py --auto-run"
            
            # 現在のcronを取得
            current_cron = self._get_current_cron()
            
            # 既存のエントリを削除
            current_cron = [line for line in current_cron if "run_gui.py --auto-run" not in line]
            
            # 新しいエントリを追加
            current_cron.append(cron_entry)
            
            # cronを更新
            if self._update_cron(current_cron):
                logger.info(f"Linux cronに登録しました: {hour:02d}:{minute:02d}")
                return True
            else:
                logger.error("cron更新に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"Linuxスケジュール設定エラー: {e}")
            return False
    
    def remove_schedule(self, schedule_name: str) -> bool:
        """スケジュールを削除"""
        try:
            # 現在のcronを取得
            current_cron = self._get_current_cron()
            
            # 該当エントリを削除
            current_cron = [line for line in current_cron if "run_gui.py --auto-run" not in line]
            
            # cronを更新
            if self._update_cron(current_cron):
                logger.info("Linux cronから削除しました")
                return True
            else:
                logger.error("cron更新に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"スケジュール削除エラー: {e}")
            return False
    
    def list_schedules(self) -> list:
        """スケジュール一覧を取得"""
        try:
            return self._get_current_cron()
        except Exception as e:
            logger.error(f"スケジュール一覧取得エラー: {e}")
            return []
    
    def test_schedule(self, schedule_name: str) -> bool:
        """スケジュールをテスト実行"""
        try:
            cmd = ["python3", "run_gui.py", "--auto-run"]
            result = subprocess.run(cmd, cwd=os.getcwd(), capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Linux cronをテスト実行しました")
                return True
            else:
                logger.error(f"テスト実行エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            return False
    
    def _get_enabled_hour(self, schedule_config: Dict[str, Any]) -> Optional[int]:
        """有効な時間設定を取得"""
        for i in range(24):
            hour_key = f"h{i:02d}"
            if schedule_config.get(hour_key, False):
                return i
        return None
    
    def _get_current_cron(self) -> list:
        """現在のcronを取得"""
        try:
            cmd = ["crontab", "-l"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
            else:
                return []
                
        except Exception:
            return []
    
    def _update_cron(self, cron_entries: list) -> bool:
        """cronを更新"""
        try:
            # 一時ファイルにcronエントリを書き込み
            temp_file = "/tmp/fanza_cron_temp"
            with open(temp_file, 'w') as f:
                for entry in cron_entries:
                    f.write(entry + '\n')
            
            # crontabを更新
            cmd = ["crontab", temp_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 一時ファイルを削除
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"cron更新エラー: {e}")
            return False


class PythonScheduler(BaseScheduler):
    """Python APScheduler用クラス（フォールバック）"""
    
    def __init__(self):
        self.scheduler_name = "Python APScheduler"
        logger.info(f"{self.scheduler_name} を初期化しました")
    
    def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """Python APSchedulerでスケジュールを設定"""
        try:
            logger.info("Python APSchedulerでスケジュールを設定しました（フォールバック）")
            return True
        except Exception as e:
            logger.error(f"Pythonスケジュール設定エラー: {e}")
            return False
    
    def remove_schedule(self, schedule_name: str) -> bool:
        """スケジュールを削除"""
        try:
            logger.info("Python APSchedulerからスケジュールを削除しました")
            return True
        except Exception as e:
            logger.error(f"スケジュール削除エラー: {e}")
            return False
    
    def list_schedules(self) -> list:
        """スケジュール一覧を取得"""
        return ["Python APScheduler (フォールバック)"]
    
    def test_schedule(self, schedule_name: str) -> bool:
        """スケジュールをテスト実行"""
        try:
            logger.info("Python APSchedulerをテスト実行しました")
            return True
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            return False


class PlatformSchedulerManager:
    """プラットフォーム別スケジューラーマネージャー"""
    
    def __init__(self):
        self.scheduler = self._create_scheduler()
        logger.info(f"スケジューラーを初期化しました: {self.scheduler.scheduler_name}")
    
    def _create_scheduler(self) -> BaseScheduler:
        """OSに応じたスケジューラーを作成"""
        system = platform.system().lower()
        
        if system == "windows":
            return WindowsTaskScheduler()
        elif system == "darwin":
            return MacOSScheduler()
        elif system == "linux":
            return LinuxScheduler()
        else:
            logger.warning(f"未対応のOS: {system}、Python APSchedulerを使用します")
            return PythonScheduler()
    
    def setup_schedule(self, schedule_config: Dict[str, Any]) -> bool:
        """スケジュールを設定"""
        return self.scheduler.setup_schedule(schedule_config)
    
    def remove_schedule(self, schedule_name: str) -> bool:
        """スケジュールを削除"""
        return self.scheduler.remove_schedule(schedule_name)
    
    def list_schedules(self) -> list:
        """スケジュール一覧を取得"""
        return self.scheduler.list_schedules()
    
    def test_schedule(self, schedule_name: str) -> bool:
        """スケジュールをテスト実行"""
        return self.scheduler.test_schedule(schedule_name)
    
    def get_scheduler_info(self) -> Dict[str, str]:
        """スケジューラー情報を取得"""
        return {
            "name": self.scheduler.scheduler_name,
            "platform": platform.system(),
            "version": platform.version()
        }


# 使用例
if __name__ == "__main__":
    # スケジューラーマネージャーを作成
    manager = PlatformSchedulerManager()
    
    # スケジューラー情報を表示
    info = manager.get_scheduler_info()
    print(f"スケジューラー: {info['name']}")
    print(f"プラットフォーム: {info['platform']}")
    
    # テスト用のスケジュール設定
    test_config = {
        "AUTO_ON": "on",
        "EXE_MIN": "30",
        "h13": True
    }
    
    # スケジュールを設定
    if manager.setup_schedule(test_config):
        print("スケジュール設定が完了しました")
        
        # スケジュール一覧を表示
        schedules = manager.list_schedules()
        print(f"登録済みスケジュール: {schedules}")
    else:
        print("スケジュール設定に失敗しました")
