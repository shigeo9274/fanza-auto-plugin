from __future__ import annotations
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import json
import sqlite3
from pathlib import Path

# ログレベル
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# ログタイプ
class LogType(Enum):
    SYSTEM = "system"           # システムログ
    SCRAPING = "scraping"       # スクレイピングログ
    POSTING = "posting"         # 投稿ログ
    ERROR = "error"             # エラーログ
    SCHEDULE = "schedule"       # スケジュールログ
    CATEGORY = "category"       # カテゴリ・タグログ

@dataclass
class LogEntry:
    """ログエントリ"""
    timestamp: datetime
    level: LogLevel
    type: LogType
    message: str
    details: Optional[Dict[str, Any]] = None
    error_traceback: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class DatabaseLogger:
    """データベースベースのログ記録"""
    
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベースを初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ログテーブルを作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    error_traceback TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # インデックスを作成
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs(level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON logs(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON logs(user_id)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
    
    def log(self, entry: LogEntry):
        """ログエントリを記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO logs (timestamp, level, type, message, details, error_traceback, user_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.timestamp.isoformat(),
                entry.level.value,
                entry.type.value,
                entry.message,
                json.dumps(entry.details) if entry.details else None,
                entry.error_traceback,
                entry.user_id,
                entry.session_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"ログ記録エラー: {e}")
    
    def get_logs(self, 
                 level: Optional[LogLevel] = None,
                 type: Optional[LogType] = None,
                 user_id: Optional[str] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 limit: int = 1000) -> List[LogEntry]:
        """ログを取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level.value)
            
            if type:
                query += " AND type = ?"
                params.append(type.value)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            logs = []
            for row in rows:
                log = LogEntry(
                    timestamp=datetime.fromisoformat(row[1]),
                    level=LogLevel(row[2]),
                    type=LogType(row[3]),
                    message=row[4],
                    details=json.loads(row[5]) if row[5] else None,
                    error_traceback=row[6],
                    user_id=row[7],
                    session_id=row[8]
                )
                logs.append(log)
            
            conn.close()
            return logs
            
        except Exception as e:
            print(f"ログ取得エラー: {e}")
            return []
    
    def cleanup_old_logs(self, days: int = 30):
        """古いログを削除"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM logs WHERE timestamp < ?', (cutoff_date.isoformat(),))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"ログクリーンアップエラー: {e}")
            return 0

class LogManager:
    """ログ管理クラス"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 db_logging: bool = True,
                 file_logging: bool = True,
                 console_logging: bool = True):
        
        self.log_dir = Path(log_dir)
        self.db_logging = db_logging
        self.file_logging = file_logging
        self.console_logging = console_logging
        
        # ログディレクトリを作成
        self.log_dir.mkdir(exist_ok=True)
        
        # データベースロガー
        if self.db_logging:
            self.db_logger = DatabaseLogger(self.log_dir / "logs.db")
        else:
            self.db_logger = None
        
        # ファイルロガー
        if self.file_logging:
            self._setup_file_logging()
        
        # コンソールロガー
        if self.console_logging:
            self._setup_console_logging()
        
        # セッションIDを生成
        self.session_id = self._generate_session_id()
        
        # ログレベル設定
        self.log_levels = {
            LogType.SYSTEM: LogLevel.INFO,
            LogType.SCRAPING: LogLevel.INFO,
            LogType.POSTING: LogLevel.INFO,
            LogType.ERROR: LogLevel.ERROR,
            LogType.SCHEDULE: LogLevel.INFO,
            LogType.CATEGORY: LogLevel.INFO
        }
    
    def _setup_file_logging(self):
        """ファイルログ設定"""
        try:
            # 日別ログファイル
            daily_handler = logging.handlers.TimedRotatingFileHandler(
                self.log_dir / "daily.log",
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8"
            )
            
            # エラーログファイル
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "error.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding="utf-8"
            )
            error_handler.setLevel(logging.ERROR)
            
            # フォーマッター
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            daily_handler.setFormatter(formatter)
            error_handler.setFormatter(formatter)
            
            # ルートロガーに追加
            root_logger = logging.getLogger()
            root_logger.addHandler(daily_handler)
            root_logger.addHandler(error_handler)
            root_logger.setLevel(logging.INFO)
            
        except Exception as e:
            print(f"ファイルログ設定エラー: {e}")
    
    def _setup_console_logging(self):
        """コンソールログ設定"""
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            root_logger = logging.getLogger()
            root_logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"コンソールログ設定エラー: {e}")
    
    def _generate_session_id(self) -> str:
        """セッションIDを生成"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def log(self, 
            level: LogLevel,
            type: LogType,
            message: str,
            details: Optional[Dict[str, Any]] = None,
            user_id: Optional[str] = None,
            exception: Optional[Exception] = None):
        """ログを記録"""
        try:
            # ログレベルチェック
            if level.value < self.log_levels[type].value:
                return
            
            # エラートレースバックを取得
            error_traceback = None
            if exception:
                error_traceback = traceback.format_exc()
            
            # ログエントリを作成
            entry = LogEntry(
                timestamp=datetime.now(),
                level=level,
                type=type,
                message=message,
                details=details,
                error_traceback=error_traceback,
                user_id=user_id,
                session_id=self.session_id
            )
            
            # データベースに記録
            if self.db_logger:
                self.db_logger.log(entry)
            
            # 標準ログにも記録
            logger = logging.getLogger(f"fanza_auto.{type.value}")
            
            if level == LogLevel.DEBUG:
                logger.debug(message, extra={"details": details})
            elif level == LogLevel.INFO:
                logger.info(message, extra={"details": details})
            elif level == LogLevel.WARNING:
                logger.warning(message, extra={"details": details})
            elif level == LogLevel.ERROR:
                logger.error(message, extra={"details": details, "exc_info": exception})
            elif level == LogLevel.CRITICAL:
                logger.critical(message, extra={"details": details, "exc_info": exception})
            
        except Exception as e:
            print(f"ログ記録エラー: {e}")
    
    def debug(self, type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """デバッグログ"""
        self.log(LogLevel.DEBUG, type, message, details, user_id)
    
    def info(self, type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """情報ログ"""
        self.log(LogLevel.INFO, type, message, details, user_id)
    
    def warning(self, type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """警告ログ"""
        self.log(LogLevel.WARNING, type, message, details, user_id)
    
    def error(self, type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None, exception: Optional[Exception] = None):
        """エラーログ"""
        self.log(LogLevel.ERROR, type, message, details, user_id, exception)
    
    def critical(self, type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None, exception: Optional[Exception] = None):
        """重大エラーログ"""
        self.log(LogLevel.CRITICAL, type, message, details, user_id, exception)
    
    def get_logs(self, 
                 level: Optional[LogLevel] = None,
                 type: Optional[LogType] = None,
                 user_id: Optional[str] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 limit: int = 1000) -> List[LogEntry]:
        """ログを取得"""
        if self.db_logger:
            return self.db_logger.get_logs(level, type, user_id, start_date, end_date, limit)
        return []
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """古いログを削除"""
        if self.db_logger:
            return self.db_logger.cleanup_old_logs(days)
        return 0
    
    def set_log_level(self, type: LogType, level: LogLevel):
        """ログレベルを設定"""
        self.log_levels[type] = level
    
    def get_log_level(self, type: LogType) -> LogLevel:
        """ログレベルを取得"""
        return self.log_levels.get(type, LogLevel.INFO)
    
    def export_logs(self, 
                    output_file: str,
                    level: Optional[LogLevel] = None,
                    type: Optional[LogType] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> bool:
        """ログをエクスポート"""
        try:
            logs = self.get_logs(level, type, None, start_date, end_date, 100000)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for log in logs:
                    log_data = {
                        'timestamp': log.timestamp.isoformat(),
                        'level': log.level.value,
                        'type': log.type.value,
                        'message': log.message,
                        'details': log.details,
                        'error_traceback': log.error_traceback,
                        'user_id': log.user_id,
                        'session_id': log.session_id
                    }
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            self.error(LogType.SYSTEM, f"ログエクスポートエラー: {e}", exception=e)
            return False
    
    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            error_logs = self.get_logs(
                level=LogLevel.ERROR,
                start_date=start_date,
                end_date=end_date
            )
            
            summary = {
                'total_errors': len(error_logs),
                'error_by_type': {},
                'error_by_user': {},
                'recent_errors': []
            }
            
            for log in error_logs:
                # タイプ別集計
                log_type = log.type.value
                summary['error_by_type'][log_type] = summary['error_by_type'].get(log_type, 0) + 1
                
                # ユーザー別集計
                if log.user_id:
                    summary['error_by_user'][log.user_id] = summary['error_by_user'].get(log.user_id, 0) + 1
                
                # 最近のエラー
                if len(summary['recent_errors']) < 10:
                    summary['recent_errors'].append({
                        'timestamp': log.timestamp.isoformat(),
                        'type': log_type,
                        'message': log.message
                    })
            
            return summary
            
        except Exception as e:
            self.error(LogType.SYSTEM, f"エラーサマリー取得エラー: {e}", exception=e)
            return {}
    
    def get_performance_stats(self, days: int = 7) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            all_logs = self.get_logs(start_date=start_date, end_date=end_date)
            
            stats = {
                'total_logs': len(all_logs),
                'logs_by_type': {},
                'logs_by_level': {},
                'logs_by_hour': {},
                'average_logs_per_day': len(all_logs) / days
            }
            
            for log in all_logs:
                # タイプ別集計
                log_type = log.type.value
                stats['logs_by_type'][log_type] = stats['logs_by_type'].get(log_type, 0) + 1
                
                # レベル別集計
                log_level = log.level.value
                stats['logs_by_level'][log_level] = stats['logs_by_level'].get(log_level, 0) + 1
                
                # 時間別集計
                hour = log.timestamp.hour
                stats['logs_by_hour'][hour] = stats['logs_by_hour'].get(hour, 0) + 1
            
            return stats
            
        except Exception as e:
            self.error(LogType.SYSTEM, f"パフォーマンス統計取得エラー: {e}", exception=e)
            return {}

# グローバルログマネージャーインスタンス
log_manager = LogManager()

# 便利な関数
def log_debug(type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
    """デバッグログ"""
    log_manager.debug(type, message, details, user_id)

def log_info(type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
    """情報ログ"""
    log_manager.info(type, message, details, user_id)

def log_warning(type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
    """警告ログ"""
    log_manager.warning(type, message, details, user_id)

def log_error(type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None, exception: Optional[Exception] = None):
    """エラーログ"""
    log_manager.error(type, message, details, user_id, exception)

def log_critical(type: LogType, message: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None, exception: Optional[Exception] = None):
    """重大エラーログ"""
    log_manager.critical(type, message, details, user_id, exception)
