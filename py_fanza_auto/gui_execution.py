import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Any
import os
import threading
import queue
import time
from datetime import datetime

class ExecutionTab:
    """実行タブの管理クラス"""
    
    def __init__(self, parent_notebook, parent_gui=None):
        self.parent_notebook = parent_notebook
        self.parent_gui = parent_gui
        self.vars = {}
        self.log_queue = queue.Queue()
        self.is_running = False
        self.create_tab()
        self.start_log_monitor()
    
    def create_tab(self):
        """実行タブの作成"""
        execution_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(execution_frame, text="実行")
        
        # 実行制御フレーム
        control_frame = ttk.LabelFrame(execution_frame, text="実行制御", padding="15")
        control_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        # 実行ボタンフレーム
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 左側のボタン
        left_buttons_frame = ttk.Frame(button_frame)
        left_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.start_button = ttk.Button(left_buttons_frame, text="実行開始", 
                                      command=self.start_execution, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(left_buttons_frame, text="実行停止", 
                                     command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pause_button = ttk.Button(left_buttons_frame, text="一時停止", 
                                      command=self.pause_execution, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右側のボタン
        right_buttons_frame = ttk.Frame(button_frame)
        right_buttons_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        clear_log_button = ttk.Button(right_buttons_frame, text="ログクリア", 
                                     command=self.clear_log)
        clear_log_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        export_log_button = ttk.Button(right_buttons_frame, text="ログエクスポート", 
                                      command=self.export_log)
        export_log_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 実行設定フレーム
        settings_frame = ttk.Frame(control_frame)
        settings_frame.pack(fill=tk.X)
        
        # 左側の設定
        left_settings_frame = ttk.Frame(settings_frame)
        left_settings_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        row = 0
        ttk.Label(left_settings_frame, text="実行モード:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['execution_mode'] = tk.StringVar()
        mode_combo = ttk.Combobox(left_settings_frame, textvariable=self.vars['execution_mode'], 
                                  values=["通常実行", "テスト実行", "デバッグ実行"], state="readonly", width=20)
        mode_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(left_settings_frame, text="実行回数:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['execution_count'] = tk.StringVar()
        ttk.Entry(left_settings_frame, textvariable=self.vars['execution_count'], width=20).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(left_settings_frame, text="※0で無制限", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 右側の設定
        right_settings_frame = ttk.Frame(settings_frame)
        right_settings_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        row = 0
        ttk.Label(right_settings_frame, text="タイムアウト（分）:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['execution_timeout'] = tk.StringVar()
        ttk.Entry(right_settings_frame, textvariable=self.vars['execution_timeout'], width=20).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(right_settings_frame, text="※分単位で指定", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(right_settings_frame, text="エラー時再試行:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['retry_on_error'] = tk.BooleanVar()
        ttk.Checkbutton(right_settings_frame, text="エラー時に再試行する", 
                       variable=self.vars['retry_on_error']).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        # 実行状況フレーム
        status_frame = ttk.LabelFrame(execution_frame, text="実行状況", padding="15")
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # 状況表示フレーム
        status_display_frame = ttk.Frame(status_frame)
        status_display_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 左側の状況
        left_status_frame = ttk.Frame(status_display_frame)
        left_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        row = 0
        ttk.Label(left_status_frame, text="実行状態:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['execution_status'] = tk.StringVar()
        self.vars['execution_status'].set("待機中")
        status_label = ttk.Label(left_status_frame, textvariable=self.vars['execution_status'], 
                                font=("Arial", 10), foreground="blue")
        status_label.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(left_status_frame, text="開始時刻:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['start_time'] = tk.StringVar()
        self.vars['start_time'].set("未開始")
        ttk.Label(left_status_frame, textvariable=self.vars['start_time'], 
                 font=("Arial", 10)).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        # 右側の状況
        right_status_frame = ttk.Frame(status_display_frame)
        right_status_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        row = 0
        ttk.Label(right_status_frame, text="実行回数:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['current_count'] = tk.StringVar()
        self.vars['current_count'].set("0")
        ttk.Label(right_status_frame, textvariable=self.vars['current_count'], 
                 font=("Arial", 10)).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(right_status_frame, text="経過時間:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['elapsed_time'] = tk.StringVar()
        self.vars['elapsed_time'].set("00:00:00")
        ttk.Label(right_status_frame, textvariable=self.vars['elapsed_time'], 
                 font=("Arial", 10)).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        # プログレスバー
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(progress_frame, text="進捗:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=300)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.progress_label = ttk.Label(progress_frame, text="0%", font=("Arial", 10))
        self.progress_label.pack(side=tk.LEFT)
        
        # ログ表示フレーム
        log_frame = ttk.LabelFrame(execution_frame, text="実行ログ", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # ログテキスト
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ログレベル選択
        log_level_frame = ttk.Frame(log_frame)
        log_level_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(log_level_frame, text="ログレベル:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        self.vars['log_level'] = tk.StringVar()
        self.vars['log_level'].set("INFO")
        log_level_combo = ttk.Combobox(log_level_frame, textvariable=self.vars['log_level'], 
                                       values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly", width=15)
        log_level_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # ログフィルタ
        ttk.Label(log_level_frame, text="フィルタ:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(20, 15))
        self.vars['log_filter'] = tk.StringVar()
        log_filter_entry = ttk.Entry(log_level_frame, textvariable=self.vars['log_filter'], width=30)
        log_filter_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(log_level_frame, text="※キーワードでログをフィルタ", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)
        
        # デフォルト値を設定
        self.set_default_values()
    
    def set_default_values(self):
        """デフォルト値を設定"""
        self.vars['execution_mode'].set("通常実行")
        self.vars['execution_count'].set("0")
        self.vars['execution_timeout'].set("60")
        self.vars['retry_on_error'].set(True)
    
    def start_execution(self):
        """実行開始"""
        try:
            if self.is_running:
                messagebox.showwarning("警告", "既に実行中です")
                return
            
            # 実行設定の検証
            if not self.validate_execution_settings():
                return
            
            # 実行状態を更新
            self.is_running = True
            self.vars['execution_status'].set("実行中")
            self.vars['start_time'].set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.vars['current_count'].set("0")
            
            # ボタン状態を更新
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
            
            # プログレスバーをリセット
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0%")
            
            # ログに開始メッセージを追加
            self.add_log("INFO", "実行を開始しました")
            
            # 実行処理を別スレッドで開始
            execution_thread = threading.Thread(target=self.execution_worker, daemon=True)
            execution_thread.start()
            
        except Exception as e:
            messagebox.showerror("エラー", f"実行開始に失敗しました:\n{e}")
            self.stop_execution()
    
    def stop_execution(self):
        """実行停止"""
        try:
            self.is_running = False
            self.vars['execution_status'].set("停止中")
            
            # ボタン状態を更新
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.DISABLED)
            
            # ログに停止メッセージを追加
            self.add_log("INFO", "実行を停止しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"実行停止に失敗しました:\n{e}")
    
    def pause_execution(self):
        """実行一時停止"""
        try:
            if self.vars['execution_status'].get() == "実行中":
                self.vars['execution_status'].set("一時停止中")
                self.pause_button.config(text="再開")
                self.add_log("INFO", "実行を一時停止しました")
            else:
                self.vars['execution_status'].set("実行中")
                self.pause_button.config(text="一時停止")
                self.add_log("INFO", "実行を再開しました")
        except Exception as e:
            messagebox.showerror("エラー", f"一時停止/再開に失敗しました:\n{e}")
    
    def execution_worker(self):
        """実行処理のワーカースレッド"""
        try:
            start_time = time.time()
            count = 0
            
            while self.is_running:
                # 実行状態をチェック
                if self.vars['execution_status'].get() == "一時停止中":
                    time.sleep(1)
                    continue
                
                # タイムアウトチェック
                timeout_minutes = int(self.vars['execution_timeout'].get())
                if timeout_minutes > 0 and (time.time() - start_time) > (timeout_minutes * 60):
                    self.add_log("WARNING", f"タイムアウト（{timeout_minutes}分）により実行を停止しました")
                    break
                
                # 実行回数チェック
                max_count = int(self.vars['execution_count'].get())
                if max_count > 0 and count >= max_count:
                    self.add_log("INFO", f"指定された実行回数（{max_count}回）に達しました")
                    break
                
                # 実行処理をシミュレート
                count += 1
                self.vars['current_count'].set(str(count))
                
                # 進捗を更新
                if max_count > 0:
                    progress = (count / max_count) * 100
                else:
                    progress = min(count * 10, 100)  # 無限実行の場合は10回ごとに10%ずつ
                
                self.progress_bar['value'] = progress
                self.progress_label.config(text=f"{progress:.0f}%")
                
                # ログに実行状況を記録
                self.add_log("INFO", f"実行 {count} 回目完了")
                
                # 実行間隔（実際の処理では適切な間隔を設定）
                time.sleep(2)
            
            # 実行完了
            elapsed_time = time.time() - start_time
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            self.vars['elapsed_time'].set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            self.add_log("INFO", f"実行完了 - 総実行回数: {count}, 経過時間: {self.vars['elapsed_time'].get()}")
            
        except Exception as e:
            self.add_log("ERROR", f"実行中にエラーが発生しました: {e}")
        finally:
            # 実行状態をリセット
            self.is_running = False
            self.vars['execution_status'].set("完了")
            
            # ボタン状態を更新
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.DISABLED)
    
    def validate_execution_settings(self):
        """実行設定の検証"""
        try:
            # 実行回数の検証
            count = self.vars['execution_count'].get()
            if count and count != "0":
                try:
                    count_int = int(count)
                    if count_int < 0:
                        messagebox.showerror("エラー", "実行回数は0以上の値を指定してください")
                        return False
                except ValueError:
                    messagebox.showerror("エラー", "実行回数は数値で指定してください")
                    return False
            
            # タイムアウトの検証
            timeout = self.vars['execution_timeout'].get()
            if timeout:
                try:
                    timeout_int = int(timeout)
                    if timeout_int <= 0:
                        messagebox.showerror("エラー", "タイムアウトは1分以上の値を指定してください")
                        return False
                except ValueError:
                    messagebox.showerror("エラー", "タイムアウトは数値で指定してください")
                    return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定の検証に失敗しました:\n{e}")
            return False
    
    def add_log(self, level, message):
        """ログを追加"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            
            # ログレベルフィルタをチェック
            log_levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            current_level = log_levels.get(self.vars['log_level'].get(), 1)
            message_level = log_levels.get(level, 1)
            
            if message_level >= current_level:
                # ログフィルタをチェック
                filter_text = self.vars['log_filter'].get().strip()
                if not filter_text or filter_text.lower() in message.lower():
                    # ログキューに追加
                    self.log_queue.put(log_entry)
        except Exception as e:
            print(f"ログ追加エラー: {e}")
    
    def start_log_monitor(self):
        """ログモニターを開始"""
        def monitor_log():
            while True:
                try:
                    # ログキューからログを取得
                    log_entry = self.log_queue.get(timeout=0.1)
                    
                    # ログテキストに追加
                    self.log_text.insert(tk.END, log_entry)
                    self.log_text.see(tk.END)
                    
                    # ログテキストの最大行数を制限（パフォーマンス向上のため）
                    lines = self.log_text.get('1.0', tk.END).split('\n')
                    if len(lines) > 1000:
                        self.log_text.delete('1.0', f'{len(lines) - 1000}.0')
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"ログモニターエラー: {e}")
        
        # ログモニタースレッドを開始
        log_monitor_thread = threading.Thread(target=monitor_log, daemon=True)
        log_monitor_thread.start()
    
    def clear_log(self):
        """ログをクリア"""
        try:
            self.log_text.delete('1.0', tk.END)
            self.add_log("INFO", "ログをクリアしました")
        except Exception as e:
            messagebox.showerror("エラー", f"ログのクリアに失敗しました:\n{e}")
    
    def export_log(self):
        """ログをエクスポート"""
        try:
            from tkinter import filedialog
            
            # ファイル保存ダイアログ
            filename = filedialog.asksaveasfilename(
                title="ログを保存",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                # ログ内容を取得
                log_content = self.log_text.get('1.0', tk.END)
                
                # ファイルに保存
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                messagebox.showinfo("完了", f"ログを {filename} に保存しました")
                self.add_log("INFO", f"ログをエクスポートしました: {filename}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"ログのエクスポートに失敗しました:\n{e}")
    
    def get_variables(self) -> Dict[str, Any]:
        """設定変数の辞書を取得"""
        return self.vars
    
    def load_from_settings(self, settings):
        """設定オブジェクトまたは辞書から値を読み込み"""
        try:
            # 辞書形式の設定に対応
            if isinstance(settings, dict):
                if 'execution_mode' in settings:
                    self.vars['execution_mode'].set(settings['execution_mode'] or "通常実行")
                if 'execution_count' in settings:
                    self.vars['execution_count'].set(str(settings['execution_count'] or "0"))
                if 'execution_timeout' in settings:
                    self.vars['execution_timeout'].set(str(settings['execution_timeout'] or "60"))
                if 'retry_on_error' in settings:
                    self.vars['retry_on_error'].set(settings['retry_on_error'] or True)
                if 'log_level' in settings:
                    self.vars['log_level'].set(settings['log_level'] or "INFO")
                if 'log_filter' in settings:
                    self.vars['log_filter'].set(settings['log_filter'] or "")
            else:
                # 従来のオブジェクト形式の設定に対応
                if hasattr(settings, 'execution_mode'):
                    self.vars['execution_mode'].set(settings.execution_mode or "通常実行")
                if hasattr(settings, 'execution_count'):
                    self.vars['execution_count'].set(str(settings.execution_count or "0"))
                if hasattr(settings, 'execution_timeout'):
                    self.vars['execution_timeout'].set(str(settings.execution_timeout or "60"))
                if hasattr(settings, 'retry_on_error'):
                    self.vars['retry_on_error'].set(settings.retry_on_error or True)
                if hasattr(settings, 'log_level'):
                    self.vars['log_level'].set(settings.log_level or "INFO")
        except Exception as e:
            print(f"実行設定読み込みエラー: {e}")
