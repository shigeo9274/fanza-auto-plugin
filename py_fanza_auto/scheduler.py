from __future__ import annotations
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import logging
import os
from dataclasses import dataclass
from enum import Enum

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    DAILY = "毎日"
    WEEKLY = "毎週"
    MONTHLY = "毎月"
    CUSTOM = "カスタム"


@dataclass
class ScheduleConfig:
    """スケジュール設定"""
    enabled: bool = False
    schedule_type: ScheduleType = ScheduleType.DAILY
    time: str = "00:00"
    day: str = "月曜日"  # 週次・月次用
    date: str = "1日"    # 月次用
    custom_cron: str = ""  # カスタムcron式
    post_setting_num: str = "1"
    target_posts: int = 10


class Scheduler:
    """投稿スケジュール管理クラス"""
    
    def __init__(self, config: ScheduleConfig, engine=None):
        self.engine = engine
        self.config = config
        self.running = False
        self.thread = None
        self._setup_schedule()
    
    def _setup_schedule(self):
        """スケジュールを設定"""
        if not self.config.enabled:
            return
        
        try:
            if self.config.schedule_type == ScheduleType.DAILY:
                schedule.every().day.at(self.config.time).do(
                    self._run_scheduled_task, 
                    self.config.post_setting_num, 
                    self.config.target_posts
                )
                logger.info(f"日次スケジュールを設定: {self.config.time}")
                
            elif self.config.schedule_type == ScheduleType.WEEKLY:
                day_map = {
                    "月曜日": schedule.every().monday,
                    "火曜日": schedule.every().tuesday,
                    "水曜日": schedule.every().wednesday,
                    "木曜日": schedule.every().thursday,
                    "金曜日": schedule.every().friday,
                    "土曜日": schedule.every().saturday,
                    "日曜日": schedule.every().sunday
                }
                
                if self.config.day in day_map:
                    day_map[self.config.day].at(self.config.time).do(
                        self._run_scheduled_task,
                        self.config.post_setting_num,
                        self.config.target_posts
                    )
                    logger.info(f"週次スケジュールを設定: {self.config.day} {self.config.time}")
                
            elif self.config.schedule_type == ScheduleType.MONTHLY:
                # 月次スケジュール（毎月指定日の指定時間）
                try:
                    day = int(self.config.date.replace("日", ""))
                    schedule.every().month.at(self.config.time).do(
                        self._run_scheduled_task,
                        self.config.post_setting_num,
                        self.config.target_posts
                    )
                    logger.info(f"月次スケジュールを設定: 毎月{day}日 {self.config.time}")
                except ValueError:
                    logger.error(f"無効な日付形式: {self.config.date}")
                
            elif self.config.schedule_type == ScheduleType.CUSTOM and self.config.custom_cron:
                # カスタムcron式の解析と設定
                self._setup_custom_cron()
                
        except Exception as e:
            logger.error(f"スケジュール設定エラー: {e}")
    
    def _setup_custom_cron(self):
        """カスタムcron式を設定"""
        try:
            # 簡単なcron式パーサー（分 時 日 月 曜日）
            parts = self.config.custom_cron.split()
            if len(parts) >= 5:
                minute, hour, day, month, weekday = parts[:5]
                
                # 分と時の設定
                if minute != "*" and hour != "*":
                    schedule.every().day.at(f"{hour.zfill(2)}:{minute.zfill(2)}").do(
                        self._run_scheduled_task,
                        self.config.post_setting_num,
                        self.config.target_posts
                    )
                    logger.info(f"カスタムcronスケジュールを設定: {hour}:{minute}")
                else:
                    logger.warning("カスタムcron式の分・時は具体的な値を指定してください")
            else:
                logger.error(f"無効なcron式: {self.config.custom_cron}")
                
        except Exception as e:
            logger.error(f"カスタムcron設定エラー: {e}")
    
    def _run_scheduled_task(self, post_setting_num: str, target_posts: int):
        """スケジュールされたタスクを実行"""
        try:
            logger.info(f"スケジュールタスク開始: 設定{post_setting_num}, 目標{target_posts}件")
            
            # エンジンの設定を一時的に更新
            original_target = self.engine.settings.target_new_posts
            self.engine.settings.target_new_posts = target_posts
            
            # 投稿実行
            created_posts = self.engine.run_once(post_setting_num)
            
            # 設定を元に戻す
            self.engine.settings.target_new_posts = original_target
            
            logger.info(f"スケジュールタスク完了: {len(created_posts)}件の投稿を作成")
            
        except Exception as e:
            logger.error(f"スケジュールタスクエラー: {e}")
    
    def start(self):
        """スケジューラーを開始"""
        if self.running:
            logger.warning("スケジューラーは既に実行中です")
            return
        
        if not self.config.enabled:
            logger.info("スケジュールが無効のため、スケジューラーを開始しません")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("スケジューラーを開始しました")
    
    def stop(self):
        """スケジューラーを停止"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("スケジューラーを停止しました")
    
    def _run_scheduler(self):
        """スケジューラーのメインループ"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
            except Exception as e:
                logger.error(f"スケジューラーエラー: {e}")
                time.sleep(60)
    
    def get_next_run(self) -> Optional[datetime]:
        """次の実行時刻を取得"""
        try:
            next_run = schedule.next_run()
            if next_run:
                return next_run
        except Exception as e:
            logger.error(f"次回実行時刻取得エラー: {e}")
        return None
    
    def get_all_jobs(self) -> list:
        """全てのジョブを取得"""
        try:
            return schedule.get_jobs()
        except Exception as e:
            logger.error(f"ジョブ取得エラー: {e}")
            return []
    
    def clear_all_jobs(self):
        """全てのジョブをクリア"""
        try:
            schedule.clear()
            logger.info("全てのスケジュールをクリアしました")
        except Exception as e:
            logger.error(f"ジョブクリアエラー: {e}")
    
    def update_config(self, new_config: ScheduleConfig):
        """設定を更新"""
        try:
            self.stop()
            self.config = new_config
            self._setup_schedule()
            if self.config.enabled:
                self.start()
            logger.info("スケジュール設定を更新しました")
        except Exception as e:
            logger.error(f"設定更新エラー: {e}")


class ScheduleManager:
    """複数のスケジュールを管理するクラス"""
    
    def __init__(self, engine):
        self.engine = engine
        self.schedulers: Dict[str, Scheduler] = {}
        self.config_file = "schedule_config.json"
        self._load_configs()
    
    def _load_configs(self):
        """設定ファイルからスケジュール設定を読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    import json
                    configs = json.load(f)
                    
                    for name, config_data in configs.items():
                        config = ScheduleConfig(**config_data)
                        self.schedulers[name] = Scheduler(self.engine, config)
                        
                        if config.enabled:
                            self.schedulers[name].start()
                            
                logger.info(f"{len(self.schedulers)}個のスケジュール設定を読み込みました")
        except Exception as e:
            logger.error(f"スケジュール設定読み込みエラー: {e}")
    
    def save_configs(self):
        """スケジュール設定をファイルに保存"""
        try:
            configs = {}
            for name, scheduler in self.schedulers.items():
                configs[name] = {
                    'enabled': scheduler.config.enabled,
                    'schedule_type': scheduler.config.schedule_type.value,
                    'time': scheduler.config.time,
                    'day': scheduler.config.day,
                    'date': scheduler.config.date,
                    'custom_cron': scheduler.config.custom_cron,
                    'post_setting_num': scheduler.config.post_setting_num,
                    'target_posts': scheduler.config.target_posts
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(configs, f, ensure_ascii=False, indent=2)
                
            logger.info("スケジュール設定を保存しました")
        except Exception as e:
            logger.error(f"スケジュール設定保存エラー: {e}")
    
    def add_scheduler(self, name: str, config: ScheduleConfig) -> bool:
        """新しいスケジューラーを追加"""
        try:
            scheduler = Scheduler(self.engine, config)
            self.schedulers[name] = scheduler
            
            if config.enabled:
                scheduler.start()
            
            self.save_configs()
            logger.info(f"スケジューラー'{name}'を追加しました")
            return True
        except Exception as e:
            logger.error(f"スケジューラー追加エラー: {e}")
            return False
    
    def remove_scheduler(self, name: str) -> bool:
        """スケジューラーを削除"""
        try:
            if name in self.schedulers:
                self.schedulers[name].stop()
                del self.schedulers[name]
                self.save_configs()
                logger.info(f"スケジューラー'{name}'を削除しました")
                return True
            return False
        except Exception as e:
            logger.error(f"スケジューラー削除エラー: {e}")
            return False
    
    def update_scheduler(self, name: str, config: ScheduleConfig) -> bool:
        """スケジューラーを更新"""
        try:
            if name in self.schedulers:
                self.schedulers[name].update_config(config)
                self.save_configs()
                return True
            return False
        except Exception as e:
            logger.error(f"スケジューラー更新エラー: {e}")
            return False
    
    def start_all(self):
        """全てのスケジューラーを開始"""
        for name, scheduler in self.schedulers.items():
            if scheduler.config.enabled:
                scheduler.start()
        logger.info("全てのスケジューラーを開始しました")
    
    def stop_all(self):
        """全てのスケジューラーを停止"""
        for name, scheduler in self.schedulers.items():
            scheduler.stop()
        logger.info("全てのスケジューラーを停止しました")
    
    def get_status(self) -> Dict[str, Any]:
        """全スケジューラーの状態を取得"""
        status = {}
        for name, scheduler in self.schedulers.items():
            status[name] = {
                'enabled': scheduler.config.enabled,
                'running': scheduler.running,
                'next_run': scheduler.get_next_run(),
                'config': {
                    'schedule_type': scheduler.config.schedule_type.value,
                    'time': scheduler.config.time,
                    'day': scheduler.config.day,
                    'date': scheduler.config.date,
                    'custom_cron': scheduler.config.custom_cron,
                    'post_setting_num': scheduler.config.post_setting_num,
                    'target_posts': scheduler.config.target_posts
                }
            }
        return status
