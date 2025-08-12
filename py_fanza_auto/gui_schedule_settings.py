import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
import os
from datetime import datetime, time

class ScheduleSettingsTab:
    """スケジュール設定タブの管理クラス"""
    
    def __init__(self, parent_notebook, main_gui):
        self.parent_notebook = parent_notebook
        self.main_gui = main_gui
        self.vars = {}
        self.create_tab()
    
    def create_tab(self):
        """スケジュール設定タブの作成"""
        schedule_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(schedule_frame, text="スケジュール設定")
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(schedule_frame)
        scrollbar = ttk.Scrollbar(schedule_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # スケジュール設定
        self._create_schedule_settings(scrollable_frame)
        
        # 実行設定
        self._create_execution_settings(scrollable_frame)
        
        # 保存ボタンを追加
        self._create_save_button(scrollable_frame)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        schedule_frame.columnconfigure(0, weight=1)
        schedule_frame.rowconfigure(0, weight=1)
    
    def _create_save_button(self, parent):
        """保存ボタンの作成"""
        save_frame = ttk.Frame(parent)
        save_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        save_frame.columnconfigure(0, weight=1)
        
        # 保存ボタン
        save_button = ttk.Button(save_frame, text="スケジュール設定を保存", 
                                command=self.save_schedule_settings, style="Accent.TButton")
        save_button.grid(row=0, column=0, pady=10)
        
        # デフォルト値設定ボタン
        default_button = ttk.Button(save_frame, text="デフォルト値に設定", 
                                   command=self.set_default_values, style="Accent.TButton")
        default_button.grid(row=0, column=1, padx=(10, 0), pady=10)
    
    def _create_schedule_settings(self, parent):
        """スケジュール設定フレームの作成"""
        schedule_frame = ttk.LabelFrame(parent, text="スケジュール設定", padding="15")
        schedule_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        schedule_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(schedule_frame, text="スケジュール有効化:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['SCHEDULE_ENABLED'] = tk.BooleanVar()
        ttk.Checkbutton(schedule_frame, text="スケジュール実行を有効にする", 
                       variable=self.vars['SCHEDULE_ENABLED']).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(schedule_frame, text="実行頻度:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['EXECUTION_FREQUENCY'] = tk.StringVar()
        frequency_combo = ttk.Combobox(schedule_frame, textvariable=self.vars['EXECUTION_FREQUENCY'], 
                                      values=["daily", "weekly", "monthly", "custom"], state="readonly", width=15)
        frequency_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_frame, text="※実行の頻度", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_frame, text="実行時刻:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['EXECUTION_TIME'] = tk.StringVar()
        time_combo = ttk.Combobox(schedule_frame, textvariable=self.vars['EXECUTION_TIME'], 
                                 values=[f"{i:02d}:{j:02d}" for i in range(24) for j in [0, 30]], state="readonly", width=15)
        time_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_frame, text="※実行する時刻（HH:MM形式）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_frame, text="曜日指定:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['EXECUTION_DAYS'] = tk.StringVar()
        days_combo = ttk.Combobox(schedule_frame, textvariable=self.vars['EXECUTION_DAYS'], 
                                 values=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "all"], state="readonly", width=15)
        days_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_frame, text="※実行する曜日（週次実行時）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_frame, text="日付指定:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['EXECUTION_DATE'] = tk.StringVar()
        ttk.Entry(schedule_frame, textvariable=self.vars['EXECUTION_DATE'], width=15).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_frame, text="※実行する日付（月次実行時、1-31）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_frame, text="カスタム間隔:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['CUSTOM_INTERVAL'] = tk.StringVar()
        ttk.Entry(schedule_frame, textvariable=self.vars['CUSTOM_INTERVAL'], width=15).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_frame, text="※カスタム実行時の間隔（分）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_execution_settings(self, parent):
        """実行設定フレームの作成"""
        execution_frame = ttk.LabelFrame(parent, text="実行設定", padding="15")
        execution_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        execution_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(execution_frame, text="最大実行時間:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['MAX_EXECUTION_TIME'] = tk.StringVar()
        ttk.Entry(execution_frame, textvariable=self.vars['MAX_EXECUTION_TIME'], width=15).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(execution_frame, text="※最大実行時間（分）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(execution_frame, text="再試行回数:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['MAX_RETRY_COUNT'] = tk.StringVar()
        retry_combo = ttk.Combobox(execution_frame, textvariable=self.vars['MAX_RETRY_COUNT'], 
                                   values=["0", "1", "2", "3", "5"], state="readonly", width=15)
        retry_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(execution_frame, text="※エラー時の再試行回数", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(execution_frame, text="再試行間隔:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['RETRY_INTERVAL'] = tk.StringVar()
        interval_combo = ttk.Combobox(execution_frame, textvariable=self.vars['RETRY_INTERVAL'], 
                                     values=["1", "5", "10", "30", "60"], state="readonly", width=15)
        interval_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(execution_frame, text="※再試行の間隔（分）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(execution_frame, text="並行実行:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['PARALLEL_EXECUTION'] = tk.BooleanVar()
        ttk.Checkbutton(execution_frame, text="並行実行を許可する", 
                       variable=self.vars['PARALLEL_EXECUTION']).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(execution_frame, text="最大並行数:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['MAX_PARALLEL_JOBS'] = tk.StringVar()
        parallel_combo = ttk.Combobox(execution_frame, textvariable=self.vars['MAX_PARALLEL_JOBS'], 
                                     values=["1", "2", "3", "5", "10"], state="readonly", width=15)
        parallel_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(execution_frame, text="※最大並行実行数", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(execution_frame, text="ログ保持期間:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['LOG_RETENTION_DAYS'] = tk.StringVar()
        log_combo = ttk.Combobox(execution_frame, textvariable=self.vars['LOG_RETENTION_DAYS'], 
                                 values=["7", "30", "90", "180", "365"], state="readonly", width=15)
        log_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(execution_frame, text="※ログファイルの保持期間（日）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def get_variables(self) -> Dict[str, Any]:
        """設定変数の辞書を取得"""
        variables = {}
        for key, var in self.vars.items():
            if isinstance(var, tk.BooleanVar):
                variables[key] = var.get()
            else:
                variables[key] = var.get()
        return variables
    
    def save_schedule_settings(self):
        """スケジュール設定を保存"""
        try:
            if not self.main_gui or not self.main_gui.settings_manager:
                messagebox.showerror("エラー", "設定管理システムが利用できません")
                return
            
            # 設定値を取得
            settings = self.get_variables()
            
            # 現在の設定を読み込み
            current_settings = self.main_gui.settings_manager.load_settings()
            
            # スケジュール設定を更新
            current_settings.update(settings)
            
            # 保存
            if self.main_gui.settings_manager.save_settings(current_settings):
                messagebox.showinfo("保存完了", "スケジュール設定を保存しました")
                if hasattr(self.main_gui, 'log_message'):
                    self.main_gui.log_message("スケジュール設定を保存しました")
                # 設定状態を更新
                if hasattr(self.main_gui, 'update_settings_status'):
                    self.main_gui.update_settings_status()
            else:
                messagebox.showerror("エラー", "設定の保存に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存に失敗しました:\n{e}")
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(f"スケジュール設定保存エラー: {e}")
    
    def set_default_values(self):
        """デフォルト値を設定"""
        self.vars['SCHEDULE_ENABLED'].set(False)
        self.vars['EXECUTION_FREQUENCY'].set("daily")
        self.vars['EXECUTION_TIME'].set("09:00")
        self.vars['EXECUTION_DAYS'].set("all")
        self.vars['EXECUTION_DATE'].set("1")
        self.vars['CUSTOM_INTERVAL'].set("60")
        self.vars['MAX_EXECUTION_TIME'].set("120")
        self.vars['MAX_RETRY_COUNT'].set("3")
        self.vars['RETRY_INTERVAL'].set("5")
        self.vars['PARALLEL_EXECUTION'].set(False)
        self.vars['MAX_PARALLEL_JOBS'].set("1")
        self.vars['LOG_RETENTION_DAYS'].set("30")
        
        if hasattr(self.main_gui, 'log_message'):
            self.main_gui.log_message("スケジュール設定をデフォルト値に設定しました")
    
    def load_from_settings(self, settings):
        """設定オブジェクトまたは辞書から値を読み込み"""
        try:
            # 辞書形式の設定に対応
            if isinstance(settings, dict):
                # 辞書から直接値を取得
                if 'SCHEDULE_ENABLED' in settings:
                    self.vars['SCHEDULE_ENABLED'].set(settings['SCHEDULE_ENABLED'] or False)
                if 'EXECUTION_FREQUENCY' in settings:
                    self.vars['EXECUTION_FREQUENCY'].set(settings['EXECUTION_FREQUENCY'] or "daily")
                if 'EXECUTION_TIME' in settings:
                    self.vars['EXECUTION_TIME'].set(settings['EXECUTION_TIME'] or "09:00")
                if 'EXECUTION_DAYS' in settings:
                    self.vars['EXECUTION_DAYS'].set(settings['EXECUTION_DAYS'] or "all")
                if 'EXECUTION_DATE' in settings:
                    self.vars['EXECUTION_DATE'].set(settings['EXECUTION_DATE'] or "1")
                if 'CUSTOM_INTERVAL' in settings:
                    self.vars['CUSTOM_INTERVAL'].set(settings['CUSTOM_INTERVAL'] or "60")
                if 'MAX_EXECUTION_TIME' in settings:
                    self.vars['MAX_EXECUTION_TIME'].set(settings['MAX_EXECUTION_TIME'] or "120")
                if 'MAX_RETRY_COUNT' in settings:
                    self.vars['MAX_RETRY_COUNT'].set(settings['MAX_RETRY_COUNT'] or "3")
                if 'RETRY_INTERVAL' in settings:
                    self.vars['RETRY_INTERVAL'].set(settings['RETRY_INTERVAL'] or "5")
                if 'PARALLEL_EXECUTION' in settings:
                    self.vars['PARALLEL_EXECUTION'].set(settings['PARALLEL_EXECUTION'] or False)
                if 'MAX_PARALLEL_JOBS' in settings:
                    self.vars['MAX_PARALLEL_JOBS'].set(settings['MAX_PARALLEL_JOBS'] or "1")
                if 'LOG_RETENTION_DAYS' in settings:
                    self.vars['LOG_RETENTION_DAYS'].set(settings['LOG_RETENTION_DAYS'] or "30")
            else:
                # 従来のオブジェクト形式の設定に対応
                if hasattr(settings, 'schedule_enabled'):
                    self.vars['SCHEDULE_ENABLED'].set(settings.schedule_enabled or False)
                if hasattr(settings, 'execution_frequency'):
                    self.vars['EXECUTION_FREQUENCY'].set(settings.execution_frequency or "daily")
                # 他の設定も同様に読み込み
                
        except Exception as e:
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(f"スケジュール設定読み込みエラー: {e}")
            print(f"スケジュール設定読み込みエラー: {e}")
