import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
import os
from datetime import datetime, time
import json

class ScheduleSettingsTab:
    """スケジュール設定タブの管理クラス（PHPプラグインと統一）"""
    
    def __init__(self, parent_notebook, main_gui):
        self.parent_notebook = parent_notebook
        self.main_gui = main_gui
        self.vars = {}
        self.hour_vars = {}  # 時間選択用
        self.hour_number_vars = {}  # 各時間の投稿設定用
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
        
        # 自動実行設定
        self._create_auto_execution_settings(scrollable_frame)
        
        # 投稿対象設定
        self._create_post_target_settings(scrollable_frame)
        
        # 実行時刻設定
        self._create_execution_time_settings(scrollable_frame)
        
        # 保存ボタンを追加
        self._create_save_button(scrollable_frame)
        
        # OSスケジューラー登録セクションを追加
        os_scheduler_frame = ttk.LabelFrame(schedule_frame, text="OSスケジューラー登録", padding="10")
        os_scheduler_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        os_scheduler_frame.columnconfigure(1, weight=1)
        
        # スケジューラー情報表示
        self.scheduler_info_label = ttk.Label(os_scheduler_frame, text="")
        self.scheduler_info_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(os_scheduler_frame)
        button_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        # OSスケジューラーに登録ボタン
        self.register_os_scheduler_btn = ttk.Button(
            button_frame, 
            text="OSスケジューラーに登録", 
            command=self.register_to_os_scheduler
        )
        self.register_os_scheduler_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # OSスケジューラーから削除ボタン
        self.remove_os_scheduler_btn = ttk.Button(
            button_frame, 
            text="OSスケジューラーから削除", 
            command=self.remove_from_os_scheduler
        )
        self.remove_os_scheduler_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # テスト実行ボタン
        self.test_os_scheduler_btn = ttk.Button(
            button_frame, 
            text="テスト実行", 
            command=self.test_os_scheduler
        )
        self.test_os_scheduler_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # スケジュール一覧表示ボタン
        self.list_os_scheduler_btn = ttk.Button(
            button_frame, 
            text="スケジュール一覧", 
            command=self.list_os_scheduler
        )
        self.list_os_scheduler_btn.pack(side=tk.LEFT)
        
        # 初期化時にスケジューラー情報を表示
        self.update_scheduler_info()
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        schedule_frame.columnconfigure(0, weight=1)
        schedule_frame.rowconfigure(0, weight=1)
    
    def _create_auto_execution_settings(self, parent):
        """自動実行設定フレームの作成"""
        auto_frame = ttk.LabelFrame(parent, text="自動実行設定", padding="15")
        auto_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        auto_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(auto_frame, text="自動実行ON/OFF:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        
        self.vars['AUTO_ON'] = tk.StringVar(value="off")
        auto_on_frame = ttk.Frame(auto_frame)
        auto_on_frame.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        ttk.Radiobutton(auto_on_frame, text="ON", variable=self.vars['AUTO_ON'], 
                       value="on").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(auto_on_frame, text="OFF", variable=self.vars['AUTO_ON'], 
                       value="off").pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(auto_frame, text="※自動実行の有効/無効を設定", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=2)
    
    def _create_post_target_settings(self, parent):
        """投稿対象設定フレームの作成"""
        target_frame = ttk.LabelFrame(parent, text="投稿対象設定", padding="15")
        target_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        target_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(target_frame, text="投稿対象:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Label(target_frame, text="※「発売日絞り込み」※ [直近分]を投稿し切ってから[過去分]を実行", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=2)
        
        row += 1
        ttk.Label(target_frame, text="[直近分]:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Label(target_frame, text="以下の期間に発売された作品を投稿対象とする", 
                 font=("Arial", 8)).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=2)
        
        row += 1
        recent_frame = ttk.Frame(target_frame)
        recent_frame.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        self.vars['TODAY'] = tk.BooleanVar()
        self.vars['THREEDAY'] = tk.BooleanVar()
        
        ttk.Checkbutton(recent_frame, text="本日", variable=self.vars['TODAY']).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Checkbutton(recent_frame, text="1日前～3日前", variable=self.vars['THREEDAY']).pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(target_frame, text="[過去分]:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Label(target_frame, text="以下の期間に発売された作品を投稿対象とする", 
                 font=("Arial", 8)).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=2)
        
        row += 1
        past_frame = ttk.Frame(target_frame)
        past_frame.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        self.vars['RANGE'] = tk.BooleanVar()
        self.vars['START_DATE'] = tk.StringVar()
        self.vars['END_DATE'] = tk.StringVar()
        
        ttk.Checkbutton(past_frame, text="期間指定", variable=self.vars['RANGE']).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(past_frame, textvariable=self.vars['START_DATE'], width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(past_frame, text="～").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(past_frame, textvariable=self.vars['END_DATE'], width=12).pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(target_frame, text="※DMM APIの検索結果上限は5万件 ※検索結果が1万以上になると巡回の負荷が増えるため、絞り込んだ期間設定を推奨", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=2)
    
    def _create_execution_time_settings(self, parent):
        """実行時刻設定フレームの作成"""
        time_frame = ttk.LabelFrame(parent, text="実行時刻設定", padding="15")
        time_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        time_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(time_frame, text="実行時刻[時間]:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        
        # 時間選択フレーム
        hour_frame = ttk.Frame(time_frame)
        hour_frame.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        # 24時間のチェックボックスと投稿設定を生成
        self._create_hour_checkboxes(hour_frame)
        
        row += 1
        ttk.Label(time_frame, text="実行時刻[分]:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        
        self.vars['EXE_MIN'] = tk.StringVar(value="0")
        ttk.Entry(time_frame, textvariable=self.vars['EXE_MIN'], width=10).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(time_frame, text="※0-59の値を入力", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_hour_checkboxes(self, parent):
        """24時間のチェックボックスと投稿設定を生成"""
        # 時間配列（PHPプラグインと同様）
        hour_ary = {
            'h00': '00時台', 'h01': '01時台', 'h02': '02時台', 'h03': '03時台',
            'h04': '04時台', 'h05': '05時台', 'h06': '06時台', 'h07': '07時台',
            'h08': '08時台', 'h09': '09時台', 'h10': '10時台', 'h11': '11時台',
            'h12': '12時台', 'h13': '13時台', 'h14': '14時台', 'h15': '15時台',
            'h16': '16時台', 'h17': '17時台', 'h18': '18時台', 'h19': '19時台',
            'h20': '20時台', 'h21': '21時台', 'h22': '22時台', 'h23': '23時台'
        }
        
        # 各時間の設定を生成
        for i, (hour_key, hour_label) in enumerate(hour_ary.items()):
            row = i // 3  # 3列で表示
            col = i % 3
            
            # 時間選択用のフレーム
            hour_item_frame = ttk.Frame(parent)
            hour_item_frame.grid(row=row, column=col, sticky=tk.W, padx=(0, 20), pady=2)
            
            # 時間選択チェックボックス
            self.hour_vars[hour_key] = tk.BooleanVar()
            ttk.Checkbutton(hour_item_frame, text=hour_label, 
                           variable=self.hour_vars[hour_key]).pack(side=tk.LEFT)
            
            # 投稿設定ラジオボタン
            ttk.Label(hour_item_frame, text="（投稿設定：").pack(side=tk.LEFT, padx=(5, 0))
            
            self.hour_number_vars[hour_key] = tk.StringVar(value="1")
            for num in range(1, 5):
                ttk.Radiobutton(hour_item_frame, text=str(num), 
                               variable=self.hour_number_vars[hour_key], 
                               value=str(num)).pack(side=tk.LEFT, padx=(0, 2))
            
            ttk.Label(hour_item_frame, text="）").pack(side=tk.LEFT)
    
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
    
    def save_schedule_settings(self):
        """スケジュール設定を保存"""
        try:
            # 設定値を取得
            settings = self.get_variables()
            
            # 設定ファイルに保存
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, 'schedule_settings.json')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message("スケジュール設定を保存しました。")
            
            messagebox.showinfo("保存完了", "スケジュール設定を保存しました。")
            
        except Exception as e:
            error_msg = f"スケジュール設定の保存中にエラーが発生しました: {str(e)}"
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(error_msg)
            
            messagebox.showerror("保存エラー", error_msg)
    
    def load_schedule_settings(self, settings):
        """設定を読み込み"""
        try:
            if isinstance(settings, dict):
                # 辞書から直接値を取得
                if 'AUTO_ON' in settings:
                    self.vars['AUTO_ON'].set(settings['AUTO_ON'] or "off")
                if 'TODAY' in settings:
                    self.vars['TODAY'].set(settings['TODAY'] or False)
                if 'THREEDAY' in settings:
                    self.vars['THREEDAY'].set(settings['THREEDAY'] or False)
                if 'RANGE' in settings:
                    self.vars['RANGE'].set(settings['RANGE'] or False)
                if 'START_DATE' in settings:
                    self.vars['START_DATE'].set(settings['START_DATE'] or "")
                if 'END_DATE' in settings:
                    self.vars['END_DATE'].set(settings['END_DATE'] or "")
                if 'EXE_MIN' in settings:
                    self.vars['EXE_MIN'].set(settings['EXE_MIN'] or "0")
                
                # 時間選択チェックボックスと投稿設定を読み込み（正しい変数名で）
                for hour_key in self.hour_vars:
                    if hour_key in settings:
                        self.hour_vars[hour_key].set(settings[hour_key] or False)
                    else:
                        self.hour_vars[hour_key].set(False)
                    
                    # 投稿設定番号を読み込み
                    number_key = f"{hour_key}_number"
                    if number_key in settings:
                        self.hour_number_vars[hour_key].set(settings[number_key] or "1")
                    else:
                        self.hour_number_vars[hour_key].set("1")
            else:
                # 従来のオブジェクト形式の設定に対応
                if hasattr(settings, 'auto_on'):
                    self.vars['AUTO_ON'].set(settings.auto_on or "off")
                if hasattr(settings, 'today'):
                    self.vars['TODAY'].set(settings.today or False)
                if hasattr(settings, 'threeday'):
                    self.vars['THREEDAY'].set(settings.threeday or False)
                if hasattr(settings, 'range'):
                    self.vars['RANGE'].set(settings.range or False)
                if hasattr(settings, 'start_date'):
                    self.vars['START_DATE'].set(settings.start_date or "")
                if hasattr(settings, 'end_date'):
                    self.vars['END_DATE'].set(settings.end_date or "")
                if hasattr(settings, 'exe_min'):
                    self.vars['EXE_MIN'].set(settings.exe_min or "0")
                
                # 時間選択チェックボックスと投稿設定を読み込み（正しい変数名で）
                for hour_key in self.hour_vars:
                    if hasattr(settings, hour_key):
                        self.hour_vars[hour_key].set(getattr(settings, hour_key) or False)
                    else:
                        self.hour_vars[hour_key].set(False)
                    
                    # 投稿設定番号を読み込み
                    number_key = f"{hour_key}_number"
                    if hasattr(settings, number_key):
                        self.hour_number_vars[hour_key].set(getattr(settings, number_key) or "1")
                    else:
                        self.hour_number_vars[hour_key].set("1")
                
        except Exception as e:
            error_msg = f"スケジュール設定の読み込み中にエラーが発生しました: {str(e)}"
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(error_msg)
            print(error_msg)
    
    def set_default_values(self):
        """デフォルト値を設定"""
        self.vars['AUTO_ON'].set("off")
        self.vars['TODAY'].set(False)
        self.vars['THREEDAY'].set(False)
        self.vars['RANGE'].set(False)
        self.vars['START_DATE'].set("")
        self.vars['END_DATE'].set("")
        self.vars['EXE_MIN'].set("0")
        
        # 時間選択チェックボックスと投稿設定をデフォルトに設定
        for hour_key in self.hour_vars:
            self.hour_vars[hour_key].set(False)
            self.hour_number_vars[hour_key].set("1")
        
        if hasattr(self.main_gui, 'log_message'):
            self.main_gui.log_message("スケジュール設定をデフォルト値に設定しました。")
        
        messagebox.showinfo("設定完了", "スケジュール設定をデフォルト値に設定しました。")
    
    def load_from_settings(self, settings: Dict[str, Any]):
        """設定辞書から値を読み込み"""
        try:
            # 自動実行設定
            if 'AUTO_ON' in self.vars:
                self.vars['AUTO_ON'].set(settings.get('AUTO_ON', 'off'))
            
            # 投稿対象設定
            if 'POST_TARGET' in self.vars:
                self.vars['POST_TARGET'].set(settings.get('POST_TARGET', 'recent'))
            
            # 時間設定（正しい変数名で読み込み）
            for hour_key in self.hour_vars:
                if hour_key in settings:
                    self.hour_vars[hour_key].set(settings.get(hour_key, False))
                else:
                    self.hour_vars[hour_key].set(False)
                
                # 投稿設定番号を読み込み
                number_key = f"{hour_key}_number"
                if number_key in settings:
                    self.hour_number_vars[hour_key].set(settings.get(number_key, '1'))
                else:
                    self.hour_number_vars[hour_key].set('1')
            
            # その他の設定
            for key in self.vars:
                if key in settings:
                    self.vars[key].set(settings[key])
                    
        except Exception as e:
            print(f"スケジュール設定読み込みエラー: {e}")
    
    def get_variables(self) -> Dict[str, Any]:
        """設定変数を辞書形式で取得"""
        result = {}
        
        # 基本設定
        for key, var in self.vars.items():
            result[key] = var.get()
        
        # 時間設定（正しい変数名で保存）
        for hour_key in self.hour_vars:
            result[hour_key] = self.hour_vars[hour_key].get()
            # 投稿設定番号も保存
            if hour_key in self.hour_number_vars:
                result[f"{hour_key}_number"] = self.hour_number_vars[hour_key].get()
        
        return result

    def update_scheduler_info(self):
        """スケジューラー情報を更新"""
        try:
            from platform_scheduler import PlatformSchedulerManager
            manager = PlatformSchedulerManager()
            info = manager.get_scheduler_info()
            
            scheduler_text = f"スケジューラー: {info['name']}\nプラットフォーム: {info['platform']}"
            self.scheduler_info_label.config(text=scheduler_text)
            
        except Exception as e:
            self.scheduler_info_label.config(text=f"スケジューラー情報取得エラー: {e}")
    
    def register_to_os_scheduler(self):
        """OSスケジューラーに登録"""
        try:
            from platform_scheduler import PlatformSchedulerManager
            
            # 現在のスケジュール設定を取得
            schedule_config = self.get_current_schedule_config()
            
            if not schedule_config:
                messagebox.showerror("エラー", "スケジュール設定を先に保存してください")
                return
            
            # スケジューラーマネージャーを作成
            manager = PlatformSchedulerManager()
            
            # OSスケジューラーに登録
            if manager.setup_schedule(schedule_config):
                messagebox.showinfo("成功", "OSスケジューラーに登録しました")
                self.update_scheduler_info()
            else:
                messagebox.showerror("エラー", "OSスケジューラーへの登録に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"OSスケジューラー登録エラー: {e}")
    
    def remove_from_os_scheduler(self):
        """OSスケジューラーから削除"""
        try:
            from platform_scheduler import PlatformSchedulerManager
            
            # スケジューラーマネージャーを作成
            manager = PlatformSchedulerManager()
            
            # OSスケジューラーから削除
            if manager.remove_schedule("FanzaAutoPlugin"):
                messagebox.showinfo("成功", "OSスケジューラーから削除しました")
                self.update_scheduler_info()
            else:
                messagebox.showerror("エラー", "OSスケジューラーからの削除に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"OSスケジューラー削除エラー: {e}")
    
    def test_os_scheduler(self):
        """OSスケジューラーをテスト実行"""
        try:
            from platform_scheduler import PlatformSchedulerManager
            
            # スケジューラーマネージャーを作成
            manager = PlatformSchedulerManager()
            
            # テスト実行
            if manager.test_schedule("FanzaAutoPlugin"):
                messagebox.showinfo("成功", "OSスケジューラーのテスト実行が完了しました")
            else:
                messagebox.showerror("エラー", "OSスケジューラーのテスト実行に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"OSスケジューラーテスト実行エラー: {e}")
    
    def list_os_scheduler(self):
        """OSスケジューラーの一覧を表示"""
        try:
            from platform_scheduler import PlatformSchedulerManager
            
            # スケジューラーマネージャーを作成
            manager = PlatformSchedulerManager()
            
            # スケジュール一覧を取得
            schedules = manager.list_schedules()
            
            if schedules:
                schedule_text = "\n".join(schedules)
                messagebox.showinfo("スケジュール一覧", f"登録済みスケジュール:\n\n{schedule_text}")
            else:
                messagebox.showinfo("スケジュール一覧", "登録済みのスケジュールはありません")
                
        except Exception as e:
            messagebox.showerror("エラー", f"スケジュール一覧取得エラー: {e}")
    
    def get_current_schedule_config(self):
        """現在のスケジュール設定を取得"""
        try:
            config = {}
            
            # AUTO_ON
            config["AUTO_ON"] = self.vars['AUTO_ON'].get()
            
            # EXE_MIN
            config["EXE_MIN"] = self.vars['EXE_MIN'].get()
            
            # 時間設定（h00-h23）
            for hour_key in self.hour_vars:
                config[hour_key] = self.hour_vars[hour_key].get()
                
                # 投稿設定番号も含める
                if hour_key in self.hour_number_vars:
                    config[f"{hour_key}_number"] = self.hour_number_vars[hour_key].get()
            
            return config
            
        except Exception as e:
            print(f"スケジュール設定取得エラー: {e}")
            return None
