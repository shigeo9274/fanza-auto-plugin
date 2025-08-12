"""
メインGUIクラス - 設定ファイルの呼び出し・保存を完全に修正
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
import time

# 相対インポートを避けるため、パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Settings
from engine import Engine
from settings_manager import SettingsManager
from apscheduler.schedulers.background import BackgroundScheduler
from gui_basic_settings import BasicSettingsTab
from gui_schedule_settings import ScheduleSettingsTab
from gui_post_settings import PostSettingsTab
from gui_execution import ExecutionTab
from gui_chrome_settings import ChromeSettingsTab
import gui_utils

class FanzaAutoGUI:
    def __init__(self, root):
        print("GUI初期化開始")
        self.root = root
        self.root.title("FANZA Auto Plugin - Python版")
        self.root.geometry("1200x900")
        
        # 設定管理システムを最初に初期化
        try:
            self.settings_manager = SettingsManager(os.path.dirname(os.path.abspath(__file__)))
            print("SettingsManager初期化完了")
        except Exception as e:
            print(f"SettingsManager初期化エラー: {e}")
            self.settings_manager = None
        
        # 設定とエンジンの初期化
        try:
            print("設定ファイル読み込み開始")
            if self.settings_manager:
                # 新しい設定管理システムから設定を読み込み
                loaded_settings = self.settings_manager.load_settings()
                if loaded_settings:
                    # PydanticのSettingsクラスで正しく設定を読み込み
                    self.settings = Settings(**loaded_settings)
                    print(f"設定読み込み成功: {len(loaded_settings)}件")
                else:
                    self.settings = Settings()
                    print("デフォルト設定で初期化")
            else:
                self.settings = Settings()
                print("デフォルト設定で初期化")
            
            self.engine = Engine.from_settings(self.settings)
            print("エンジン初期化成功")
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            print(f"エラー詳細: {traceback.format_exc()}")
            # エラーが発生してもGUIは起動する
            self.settings = Settings()
            self.engine = Engine.from_settings(self.settings)
            print("デフォルト値で初期化しました")
        
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False
        self.monitoring_active = False  # 監視状態を管理
        
        # ログ用のキュー
        self.log_queue = queue.Queue()
        
        # 手動投稿状態管理用の変数
        self.manual_post_status_vars = {}
        
        # 投稿設定選択用の変数
        self.selected_post_setting_var = tk.StringVar(value="1")
        
        # 分割されたタブクラスのインスタンス
        self.basic_settings_tab = None
        self.schedule_settings_tab = None
        self.post_settings_tab = None
        self.execution_tab = None
        
        print("GUIウィジェット作成開始")
        # GUIの構築
        try:
            self.create_widgets()
            print("ウィジェット作成完了")
        except Exception as e:
            print(f"ウィジェット作成エラー: {e}")
            print(f"エラー詳細: {traceback.format_exc()}")
            # エラーが発生してもGUIは起動する
            pass
        
        # ログ更新の開始
        try:
            self.update_log()
        except Exception as e:
            print(f"ログ更新開始エラー: {e}")
        
        # 設定をGUIに読み込み（GUI作成後）
        try:
            if self.settings_manager:
                self.load_settings_to_gui()
                print("設定をGUIに読み込みました")
            else:
                print("SettingsManagerが利用できないため、設定の読み込みをスキップします")
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            print(f"エラー詳細: {traceback.format_exc()}")
        
        # 設定状態の更新
        try:
            self.update_settings_status()
        except Exception as e:
            print(f"設定状態更新エラー: {e}")
        
        # 自動監視の開始（エラーが発生してもGUIは起動する）
        try:
            self.start_monitoring()
        except Exception as e:
            print(f"自動監視開始エラー: {e}")
            if hasattr(self, 'log_message'):
                self.log_message(f"自動監視開始エラー: {e}")
        
        print("GUI初期化完了")
    
    def create_widgets(self):
        print("ウィジェット作成開始")
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # タイトル
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, pady=(0, 20))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(title_frame, text="FANZA Auto Plugin - Python版", 
                               font=("Arial", 18, "bold"), foreground="#2E86AB")
        title_label.grid(row=0, column=0)
        
        subtitle_label = ttk.Label(title_frame, text="DMMコンテンツの自動投稿プラグイン", 
                                   font=("Arial", 10), foreground="#666666")
        subtitle_label.grid(row=1, column=0, pady=(5, 0))
        
        # タブ付きノートブック
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        print("タブ作成開始")
        # 分割されたタブクラスを使用
        self.basic_settings_tab = BasicSettingsTab(self.notebook, self)
        self.schedule_settings_tab = ScheduleSettingsTab(self.notebook, self)
        # 投稿設定タブの作成（元のgui.pyの実装を使用）
        self.create_post_settings_tab()
        self.chrome_settings_tab = ChromeSettingsTab(self.notebook, self)
        self.execution_tab = ExecutionTab(self.notebook, self)
        
        # 設定状態表示フレーム
        self.create_settings_status_frame(main_frame)
        
        # ログ表示フレーム
        self.create_log_frame(main_frame)
        
        # 閉じるボタン
        close_button = ttk.Button(main_frame, text="閉じる", command=self.on_closing, style="Accent.TButton")
        close_button.grid(row=4, column=0, pady=(15, 0))
        
        print("ウィジェット作成完了")
    
    def create_post_settings_tab(self):
        """投稿設定タブの作成"""
        post_frame = ttk.Frame(self.notebook)
        self.notebook.add(post_frame, text="投稿設定（検索設定統合）")
        
        # 内部でタブに分ける
        post_notebook = ttk.Notebook(post_frame)
        post_notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 共通設定タブ
        self.create_common_settings_tab(post_notebook)
        
        # 投稿設定1タブ（検索設定統合）
        self.create_post_setting_tab(post_notebook, "投稿設定1", 1)
        
        # 投稿設定2タブ（検索設定統合）
        self.create_post_setting_tab(post_notebook, "投稿設定2", 2)
        
        # 投稿設定3タブ（検索設定統合）
        self.create_post_setting_tab(post_notebook, "投稿設定3", 3)
        
        # 投稿設定4タブ（検索設定統合）
        self.create_post_setting_tab(post_notebook, "投稿設定4", 4)
        
        # 設定管理フレーム
        settings_management_frame = ttk.LabelFrame(post_frame, text="設定管理", padding="15")
        settings_management_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # 設定管理ボタン
        management_buttons_frame = ttk.Frame(settings_management_frame)
        management_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 左側のボタン
        left_buttons_frame = ttk.Frame(management_buttons_frame)
        left_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        backup_button = ttk.Button(left_buttons_frame, text="設定をバックアップ", 
                                  command=self.create_backup, style="Accent.TButton")
        backup_button.pack(side=tk.LEFT, padx=(0, 10))
        
        restore_button = ttk.Button(left_buttons_frame, text="設定を復元", 
                                   command=self.show_restore_dialog, style="Accent.TButton")
        restore_button.pack(side=tk.LEFT, padx=(0, 10))
        
        repair_button = ttk.Button(left_buttons_frame, text="設定を修復", 
                                  command=self.repair_settings, style="Accent.TButton")
        repair_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右側のボタン
        right_buttons_frame = ttk.Frame(management_buttons_frame)
        right_buttons_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        lock_button = ttk.Button(right_buttons_frame, text="設定をロック", 
                                command=self.toggle_settings_lock, style="Accent.TButton")
        lock_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        reset_button = ttk.Button(right_buttons_frame, text="設定をリセット", 
                                 command=self.reset_settings, style="Accent.TButton")
        reset_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 設定状態表示
        status_frame = ttk.Frame(settings_management_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.settings_status_var = tk.StringVar()
        self.settings_status_var.set("設定状態: 読み込み中...")
        status_label = ttk.Label(status_frame, textvariable=self.settings_status_var, 
                                font=("Arial", 9), foreground="blue")
        status_label.pack(side=tk.LEFT)
        
        # プレビューボタン
        preview_frame = ttk.Frame(post_frame)
        preview_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        preview_button = ttk.Button(preview_frame, text="投稿内容をプレビュー", 
                                   command=self.preview_post_content, style="Accent.TButton")
        preview_button.pack(pady=15)
    
    def create_common_settings_tab(self, parent_notebook):
        """共通設定タブの作成"""
        common_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(common_frame, text="共通設定")
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(common_frame)
        scrollbar = ttk.Scrollbar(common_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        common_frame.columnconfigure(0, weight=1)
        common_frame.rowconfigure(0, weight=1)
        
        # 共通設定
        common_settings_frame = ttk.LabelFrame(scrollable_frame, text="共通設定", padding="15")
        common_settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        common_settings_frame.columnconfigure(1, weight=1)
        
        # キャンバスのサイズ設定
        canvas.configure(width=800, height=600)
        
        row = 0
        ttk.Label(common_settings_frame, text="抜粋欄テンプレート:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.excerpt_template_var = tk.StringVar()
        excerpt_entry = ttk.Entry(common_settings_frame, textvariable=self.excerpt_template_var, width=40)
        excerpt_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(common_settings_frame, text="※投稿の抜粋欄に表示される内容", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="サンプル画像最大数:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.max_sample_images_var = tk.StringVar()
        max_images_entry = ttk.Entry(common_settings_frame, textvariable=self.max_sample_images_var, width=10)
        max_images_entry.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(common_settings_frame, text="※表示するサンプル画像の最大数", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="カテゴリ指定:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.categories_var = tk.StringVar()
        categories_entry = ttk.Entry(common_settings_frame, textvariable=self.categories_var, width=40)
        categories_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(common_settings_frame, text="※カンマ区切りで複数指定可能", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="タグ指定:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.tags_var = tk.StringVar()
        tags_entry = ttk.Entry(common_settings_frame, textvariable=self.tags_var, width=40)
        tags_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(common_settings_frame, text="※カンマ区切りで複数指定可能", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="アフィリエイトボタン1:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        affiliate1_frame = ttk.Frame(common_settings_frame)
        affiliate1_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        self.affiliate1_text_var = tk.StringVar()
        ttk.Entry(affiliate1_frame, textvariable=self.affiliate1_text_var, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(affiliate1_frame, text="文字色:").pack(side=tk.LEFT, padx=(0, 5))
        self.affiliate1_color_var = tk.StringVar()
        ttk.Entry(affiliate1_frame, textvariable=self.affiliate1_color_var, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(affiliate1_frame, text="背景色:").pack(side=tk.LEFT, padx=(0, 5))
        self.affiliate1_bg_var = tk.StringVar()
        ttk.Entry(affiliate1_frame, textvariable=self.affiliate1_bg_var, width=10).pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(common_settings_frame, text="アフィリエイトボタン2:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        affiliate2_frame = ttk.Frame(common_settings_frame)
        affiliate2_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        self.affiliate2_text_var = tk.StringVar()
        ttk.Entry(affiliate2_frame, textvariable=self.affiliate2_text_var, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(affiliate2_frame, text="文字色:").pack(side=tk.LEFT, padx=(0, 5))
        self.affiliate2_color_var = tk.StringVar()
        ttk.Entry(affiliate2_frame, textvariable=self.affiliate2_color_var, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(affiliate2_frame, text="背景色:").pack(side=tk.LEFT, padx=(0, 5))
        self.affiliate2_bg_var = tk.StringVar()
        ttk.Entry(affiliate2_frame, textvariable=self.affiliate2_bg_var, width=10).pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(common_settings_frame, text="投稿日設定:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.post_date_setting_var = tk.StringVar()
        date_combo = ttk.Combobox(common_settings_frame, textvariable=self.post_date_setting_var, 
                                 values=["本日", "指定日", "ランダムな過去日"], state="readonly", width=20)
        date_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(common_settings_frame, text="※投稿日の設定方法", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="ランダムテキスト1:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.random_text1_var = tk.StringVar()
        ttk.Entry(common_settings_frame, textvariable=self.random_text1_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(common_settings_frame, text="※投稿内容にランダムで挿入されるテキスト", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="ランダムテキスト2:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.random_text2_var = tk.StringVar()
        ttk.Entry(common_settings_frame, textvariable=self.random_text2_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(common_settings_frame, text="ランダムテキスト3:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.random_text3_var = tk.StringVar()
        ttk.Entry(common_settings_frame, textvariable=self.random_text3_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        common_frame.columnconfigure(0, weight=1)
        common_frame.rowconfigure(0, weight=1)
    
    def create_post_setting_tab(self, parent_notebook, title, setting_num):
        """個別の投稿設定タブの作成"""
        post_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(post_frame, text=title)
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(post_frame)
        scrollbar = ttk.Scrollbar(post_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        post_frame.columnconfigure(0, weight=1)
        post_frame.rowconfigure(0, weight=1)
        
        # キャンバスのサイズ設定
        canvas.configure(width=800, height=600)
        
        # 投稿設定フレーム（検索設定統合）
        post_settings_frame = ttk.LabelFrame(scrollable_frame, text=f"{title}（検索・投稿統合）", padding="15")
        post_settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        post_settings_frame.columnconfigure(1, weight=1)
        
        # マウスホイールでのスクロール
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 手動投稿ボタンフレーム
        manual_post_frame = ttk.Frame(scrollable_frame)
        manual_post_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        manual_post_frame.columnconfigure(0, weight=1)
        
        # 手動投稿ボタン
        manual_post_button = ttk.Button(manual_post_frame, text=f"{title}で手動投稿", 
                                       command=lambda: self.manual_post(setting_num), 
                                       style="Accent.TButton")
        manual_post_button.grid(row=0, column=0, pady=10)
        
        # 投稿状態表示
        self.manual_post_status_vars[setting_num] = tk.StringVar(value="待機中")
        status_label = ttk.Label(manual_post_frame, textvariable=self.manual_post_status_vars[setting_num], 
                                font=("Arial", 9), foreground="blue")
        status_label.grid(row=0, column=1, padx=(20, 0), pady=10)
        
        # 投稿設定の変数を作成
        setattr(self, f"post_title_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_eyecatch_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_movie_size_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_poster_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_category_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_sort_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_article_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_status_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_hour_{setting_num}_var", tk.StringVar())
        setattr(self, f"post_overwrite_existing_{setting_num}_var", tk.BooleanVar())
        setattr(self, f"target_new_posts_{setting_num}_var", tk.StringVar())
        
        # 検索設定の変数を作成
        setattr(self, f"search_site_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_keyword_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_category_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_floor_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_service_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_sort_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_hits_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_from_date_{setting_num}_var", tk.StringVar())
        setattr(self, f"search_to_date_{setting_num}_var", tk.StringVar())
        
        row = 0
        ttk.Label(post_settings_frame, text="投稿タイトル:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        title_var = getattr(self, f"post_title_{setting_num}_var")
        ttk.Entry(post_settings_frame, textvariable=title_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※[title]でタイトルを挿入", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="投稿内容:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        content_text = scrolledtext.ScrolledText(post_settings_frame, width=50, height=6, wrap=tk.WORD)
        content_text.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        setattr(self, f"post_content_text{setting_num}", content_text)
        ttk.Label(post_settings_frame, text="※テンプレート変数を使用可能", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="アイキャッチ:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        eyecatch_var = getattr(self, f"post_eyecatch_{setting_num}_var")
        eyecatch_combo = ttk.Combobox(post_settings_frame, textvariable=eyecatch_var, 
                                       values=["サンプル画像", "パッケージ画像", "画像1", "画像99"], state="readonly", width=15)
        eyecatch_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※アイキャッチ画像の設定", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="動画サイズ:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        movie_size_var = getattr(self, f"post_movie_size_{setting_num}_var")
        movie_size_combo = ttk.Combobox(post_settings_frame, textvariable=movie_size_var, 
                                         values=["自動", "720p", "600p", "560p"], state="readonly", width=15)
        movie_size_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※動画のサイズ設定", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="ポスター:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        poster_var = getattr(self, f"post_poster_{setting_num}_var")
        poster_combo = ttk.Combobox(post_settings_frame, textvariable=poster_var, 
                                     values=["パッケージ画像", "サンプル画像", "なし"], state="readonly", width=15)
        poster_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※ポスター画像の設定", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="カテゴリ:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        category_var = getattr(self, f"post_category_{setting_num}_var")
        category_combo = ttk.Combobox(post_settings_frame, textvariable=category_var, 
                                       values=["JAN", "女優", "監督", "シリーズ"], state="readonly", width=15)
        category_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿のカテゴリ", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="ソート:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        sort_var = getattr(self, f"post_sort_{setting_num}_var")
        sort_combo = ttk.Combobox(post_settings_frame, textvariable=sort_var, 
                                   values=["人気順", "発売日順", "レビュー順", "価格順"], state="readonly", width=15)
        sort_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※ソート順", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="記事:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        article_var = getattr(self, f"post_article_{setting_num}_var")
        article_combo = ttk.Combobox(post_settings_frame, textvariable=article_var, 
                                      values=["指定なし", "女優", "ジャンル", "シリーズ"], state="readonly", width=15)
        article_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※記事の種類", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="ステータス:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        status_var = getattr(self, f"post_status_{setting_num}_var")
        status_combo = ttk.Combobox(post_settings_frame, textvariable=status_var, 
                                     values=["公開", "下書き"], state="readonly", width=15)
        status_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿のステータス", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="時間:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        hour_var = getattr(self, f"post_hour_{setting_num}_var")
        hour_combo = ttk.Combobox(post_settings_frame, textvariable=hour_var, 
                                   values=["09:00", "12:00", "18:00", "21:00"], state="readonly", width=15)
        hour_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿時間", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="既存投稿の上書き:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        overwrite_var = getattr(self, f"post_overwrite_existing_{setting_num}_var")
        overwrite_check = ttk.Checkbutton(post_settings_frame, text="既存投稿を上書きする", variable=overwrite_var)
        overwrite_check.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※スラッグが重複する場合の動作", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="目標投稿数:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        target_var = getattr(self, f"target_new_posts_{setting_num}_var")
        target_entry = ttk.Entry(post_settings_frame, textvariable=target_var, width=10)
        target_entry.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※0の場合は制限なし", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 検索設定セクション（投稿設定と統合）
        row += 1
        ttk.Separator(post_settings_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        row += 1
        search_label = ttk.Label(post_settings_frame, text="検索・投稿統合設定", font=("Arial", 12, "bold"), foreground="blue")
        search_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        row += 1
        ttk.Label(post_settings_frame, text="検索サイト:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_site_var = getattr(self, f"search_site_{setting_num}_var")
        search_site_combo = ttk.Combobox(post_settings_frame, textvariable=search_site_var, 
                                          values=["FANZA", "DMM"], state="readonly", width=15)
        search_site_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索サイト", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索キーワード:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_keyword_var = getattr(self, f"search_keyword_{setting_num}_var")
        ttk.Entry(post_settings_frame, textvariable=search_keyword_var, width=30).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索キーワード", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索カテゴリ:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_category_var = getattr(self, f"search_category_{setting_num}_var")
        ttk.Entry(post_settings_frame, textvariable=search_category_var, width=30).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索カテゴリ", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索フロア:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_floor_var = getattr(self, f"search_floor_{setting_num}_var")
        search_floor_combo = ttk.Combobox(post_settings_frame, textvariable=search_floor_var, 
                                           values=["videoc", "videoa", "videob", "videod"], state="readonly", width=15)
        search_floor_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索フロア", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索サービス:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_service_var = getattr(self, f"search_service_{setting_num}_var")
        search_service_combo = ttk.Combobox(post_settings_frame, textvariable=search_service_var, 
                                             values=["digital", "package", "rental"], state="readonly", width=15)
        search_service_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索サービス", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索ソート順:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_sort_var = getattr(self, f"search_sort_{setting_num}_var")
        search_sort_combo = ttk.Combobox(post_settings_frame, textvariable=search_sort_var, 
                                          values=["date", "review", "price", "popular"], state="readonly", width=15)
        search_sort_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索ソート順", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索結果数:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_hits_var = getattr(self, f"search_hits_{setting_num}_var")
        ttk.Entry(post_settings_frame, textvariable=search_hits_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索結果数", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索開始日:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_from_date_var = getattr(self, f"search_from_date_{setting_num}_var")
        ttk.Entry(post_settings_frame, textvariable=search_from_date_var, width=15).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索開始日", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_settings_frame, text="検索終了日:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        search_to_date_var = getattr(self, f"search_to_date_{setting_num}_var")
        ttk.Entry(post_settings_frame, textvariable=search_to_date_var, width=15).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_settings_frame, text="※投稿対象の検索終了日", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=row, column=1, sticky=(tk.N, tk.S))
        
        post_frame.columnconfigure(0, weight=1)
        post_frame.rowconfigure(0, weight=1)
    
    def create_settings_status_frame(self, parent):
        """設定状態表示フレームの作成"""
        status_frame = ttk.LabelFrame(parent, text="設定状態", padding="15")
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        status_frame.columnconfigure(1, weight=1)
        
        # 設定状態の表示
        self.settings_status_var = tk.StringVar(value="設定状態: 未確認")
        status_label = ttk.Label(status_frame, textvariable=self.settings_status_var, 
                                font=("Arial", 10, "bold"))
        status_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 設定管理ボタン
        buttons_frame = ttk.Frame(status_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 全設定保存ボタンを追加
        save_all_button = ttk.Button(buttons_frame, text="全設定を保存", 
                                    command=self.save_all_settings, style="Accent.TButton")
        save_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        backup_button = ttk.Button(buttons_frame, text="設定をバックアップ", 
                                  command=self.create_backup, style="Accent.TButton")
        backup_button.pack(side=tk.LEFT, padx=(0, 10))
        
        restore_button = ttk.Button(buttons_frame, text="設定を復元", 
                                   command=self.show_restore_dialog, style="Accent.TButton")
        restore_button.pack(side=tk.LEFT, padx=(0, 10))
        
        repair_button = ttk.Button(buttons_frame, text="設定修復", 
                                  command=self.repair_settings, style="Accent.TButton")
        repair_button.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_button = ttk.Button(buttons_frame, text="設定リセット", 
                                 command=self.reset_settings, style="Accent.TButton")
        reset_button.pack(side=tk.LEFT, padx=(0, 10))
    
    def create_log_frame(self, parent):
        """ログ表示フレームの作成"""
        log_frame = ttk.LabelFrame(parent, text="ログ", padding="15")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # ログテキストエリア
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # ログ操作ボタン
        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        clear_log_button = ttk.Button(log_buttons_frame, text="ログクリア", 
                                     command=self.clear_log, style="Accent.TButton")
        clear_log_button.pack(pady=(0, 5))
        
        # ログレベル選択
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_buttons_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                      state="readonly", width=10)
        log_level_combo.pack(pady=(0, 5))
    
    def save_all_settings(self):
        """全設定を保存する"""
        try:
            self.log_message("全設定の保存を開始します...")
            
            if not self.settings_manager:
                self.log_message("SettingsManagerが利用できません")
                messagebox.showerror("エラー", "設定管理システムが利用できません")
                return
            
            # 各タブから設定値を取得
            basic_settings = self.basic_settings_tab.get_variables() if self.basic_settings_tab else {}
            schedule_settings = self.schedule_settings_tab.get_variables() if self.schedule_settings_tab else {}
            # 投稿設定の取得（共通設定と個別設定）
            post_settings = self._get_post_settings_from_gui()
            execution_settings = self.execution_tab.get_variables() if self.execution_tab else {}
            
            # 設定の統合
            all_settings = {}
            all_settings.update(basic_settings)
            all_settings.update(schedule_settings)
            all_settings.update(post_settings)
            all_settings.update(execution_settings)
            
            # デバッグ用：設定の内容をログに出力
            self.log_message(f"保存する設定の内容:")
            self.log_message(f"  basic_settings: {len(basic_settings)}件")
            self.log_message(f"  schedule_settings: {len(schedule_settings)}件")
            self.log_message(f"  post_settings: {len(post_settings)}件")
            self.log_message(f"  execution_settings: {len(execution_settings)}件")
            self.log_message(f"  合計: {len(all_settings)}件")
            
            # 設定の内容を詳細にログ出力
            for key, value in all_settings.items():
                if isinstance(value, dict):
                    self.log_message(f"  {key}: {type(value).__name__} (キー数: {len(value)})")
                else:
                    self.log_message(f"  {key}: {type(value).__name__} = {value}")
            
            # 新しい設定管理システムを使用して保存
            try:
                if self.settings_manager.save_settings(all_settings):
                    self.log_message("全設定を保存しました")
                    messagebox.showinfo("保存完了", "全設定を保存しました")
                    
                    # 設定状態を更新
                    self.update_settings_status()
                else:
                    self.log_message("設定の保存に失敗しました")
                    messagebox.showerror("エラー", "設定の保存に失敗しました")
            except Exception as e:
                self.log_message(f"設定保存でエラーが発生: {e}")
                import traceback
                self.log_message(f"エラー詳細: {traceback.format_exc()}")
                messagebox.showerror("エラー", f"設定保存でエラーが発生しました:\n{e}")
            
        except Exception as e:
            self.log_message(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定保存に失敗しました:\n{e}")
    
    def load_settings_to_gui(self):
        """設定をGUIに読み込み"""
        try:
            if not self.settings_manager:
                self.log_message("SettingsManagerが利用できません")
                return
            
            # 新しい設定管理システムから設定を読み込み
            loaded_settings = self.settings_manager.load_settings()
            
            # デバッグ用：読み込まれた設定の内容をログに出力
            if loaded_settings:
                self.log_message(f"設定読み込み成功: {len(loaded_settings)}件")
                # 接続情報の確認
                connection_keys = ['DMM_API_ID', 'DMM_AFFILIATE_ID', 'WORDPRESS_BASE_URL', 'WORDPRESS_USERNAME', 'WORDPRESS_APPLICATION_PASSWORD']
                for key in connection_keys:
                    value = loaded_settings.get(key, '')
                    self.log_message(f"{key}: {value[:10]}{'...' if len(str(value)) > 10 else ''}")
                
                # 基本設定の読み込み
                if self.basic_settings_tab:
                    self.basic_settings_tab.load_from_settings(loaded_settings)
                
                # スケジュール設定の読み込み
                if self.schedule_settings_tab:
                    self.schedule_settings_tab.load_from_settings(loaded_settings)
                
                # 投稿設定の読み込み（共通設定と個別設定）
                self._load_post_settings_to_gui(loaded_settings)
                
                # 実行設定の読み込み
                if self.execution_tab:
                    self.execution_tab.load_from_settings(loaded_settings)
                
                # 設定オブジェクトも更新
                if self.settings:
                    for key, value in loaded_settings.items():
                        if hasattr(self.settings, key.lower()):
                            setattr(self.settings, key.lower(), value)
                
                self.log_message("設定をGUIに読み込みました")
            else:
                self.log_message("設定ファイルが見つからないか、読み込みに失敗しました")
                
        except Exception as e:
            self.log_message(f"設定読み込みエラー: {e}")
            print(f"設定読み込みエラー詳細: {traceback.format_exc()}")
    
    def _load_post_settings_to_gui(self, settings):
        """投稿設定をGUIに読み込み"""
        try:
            # 共通設定の読み込み
            if hasattr(self, 'excerpt_template_var'):
                self.excerpt_template_var.set(settings.get('EXCERPT_TEMPLATE', ''))
            if hasattr(self, 'max_sample_images_var'):
                self.max_sample_images_var.set(settings.get('MAX_SAMPLE_IMAGES', ''))
            if hasattr(self, 'categories_var'):
                self.categories_var.set(settings.get('CATEGORIES', ''))
            if hasattr(self, 'tags_var'):
                self.tags_var.set(settings.get('TAGS', ''))
            if hasattr(self, 'affiliate1_text_var'):
                self.affiliate1_text_var.set(settings.get('AFFILIATE1_TEXT', ''))
            if hasattr(self, 'affiliate1_color_var'):
                self.affiliate1_color_var.set(settings.get('AFFILIATE1_COLOR', ''))
            if hasattr(self, 'affiliate1_bg_var'):
                self.affiliate1_bg_var.set(settings.get('AFFILIATE1_BG', ''))
            if hasattr(self, 'affiliate2_text_var'):
                self.affiliate2_text_var.set(settings.get('AFFILIATE2_TEXT', ''))
            if hasattr(self, 'affiliate2_color_var'):
                self.affiliate2_color_var.set(settings.get('AFFILIATE2_COLOR', ''))
            if hasattr(self, 'affiliate2_bg_var'):
                self.affiliate2_bg_var.set(settings.get('AFFILIATE2_BG', ''))
            if hasattr(self, 'post_date_setting_var'):
                self.post_date_setting_var.set(settings.get('POST_DATE_SETTING', 'now'))
            if hasattr(self, 'random_text1_var'):
                self.random_text1_var.set(settings.get('RANDOM_TEXT1', ''))
            if hasattr(self, 'random_text2_var'):
                self.random_text2_var.set(settings.get('RANDOM_TEXT2', ''))
            if hasattr(self, 'random_text3_var'):
                self.random_text3_var.set(settings.get('RANDOM_TEXT3', ''))
            
            # 時間別投稿設定の読み込み
            for hour in range(24):
                hour_key = f"HOUR_h{hour:02d}"
                hour_select_key = f"HOUR_h{hour:02d}_SELECT"
                if hasattr(self, f'hour_{hour:02d}_var'):
                    getattr(self, f'hour_{hour:02d}_var').set(settings.get(hour_key, False))
                if hasattr(self, f'hour_{hour:02d}_select_var'):
                    getattr(self, f'hour_{hour:02d}_select_var').set(settings.get(hour_select_key, '1'))
            
            # 個別投稿設定の読み込み（1-4）
            for setting_num in range(1, 5):
                self._load_individual_post_settings(settings, setting_num)
                
        except Exception as e:
            self.log_message(f"投稿設定読み込みエラー: {e}")
            print(f"投稿設定読み込みエラー詳細: {traceback.format_exc()}")
    
    def _load_individual_post_settings(self, settings, setting_num):
        """個別の投稿設定を読み込み"""
        try:
            # post_settingsセクションから設定を取得
            post_settings = settings.get('post_settings', {})
            setting_data = post_settings.get(str(setting_num), {})
            
            if not setting_data:
                return
            
            # 投稿設定の読み込み
            if hasattr(self, f'post_title_{setting_num}_var'):
                getattr(self, f'post_title_{setting_num}_var').set(
                    setting_data.get('title', ''))
            
            if hasattr(self, f'post_eyecatch_{setting_num}_var'):
                getattr(self, f'post_eyecatch_{setting_num}_var').set(
                    setting_data.get('eyecatch', 'sample'))
            
            if hasattr(self, f'post_movie_size_{setting_num}_var'):
                getattr(self, f'post_movie_size_{setting_num}_var').set(
                    setting_data.get('movie_size', 'auto'))
            
            if hasattr(self, f'post_poster_{setting_num}_var'):
                getattr(self, f'post_poster_{setting_num}_var').set(
                    setting_data.get('poster', 'package'))
            
            if hasattr(self, f'post_category_{setting_num}_var'):
                getattr(self, f'post_category_{setting_num}_var').set(
                    setting_data.get('category', 'act'))
            
            if hasattr(self, f'post_sort_{setting_num}_var'):
                getattr(self, f'post_sort_{setting_num}_var').set(
                    setting_data.get('sort', 'rank'))
            
            if hasattr(self, f'post_article_{setting_num}_var'):
                getattr(self, f'post_article_{setting_num}_var').set(
                    setting_data.get('article', ''))
            
            if hasattr(self, f'post_status_{setting_num}_var'):
                getattr(self, f'post_status_{setting_num}_var').set(
                    setting_data.get('status', 'publish'))
            
            if hasattr(self, f'post_hour_{setting_num}_var'):
                getattr(self, f'post_hour_{setting_num}_var').set(
                    setting_data.get('hour', 'h09'))
            
            if hasattr(self, f'post_overwrite_existing_{setting_num}_var'):
                getattr(self, f'post_overwrite_existing_{setting_num}_var').set(
                    setting_data.get('overwrite_existing', True))
            
            if hasattr(self, f'target_new_posts_{setting_num}_var'):
                getattr(self, f'target_new_posts_{setting_num}_var').set(
                    setting_data.get('target_new_posts', 10))
            
            # 検索設定の読み込み
            if hasattr(self, f'search_site_{setting_num}_var'):
                getattr(self, f'search_site_{setting_num}_var').set(
                    setting_data.get('search_site', 'FANZA'))
            
            if hasattr(self, f'search_keyword_{setting_num}_var'):
                getattr(self, f'search_keyword_{setting_num}_var').set(
                    setting_data.get('search_keyword', ''))
            
            if hasattr(self, f'search_category_{setting_num}_var'):
                getattr(self, f'search_category_{setting_num}_var').set(
                    setting_data.get('search_category', ''))
            
            if hasattr(self, f'search_floor_{setting_num}_var'):
                getattr(self, f'search_floor_{setting_num}_var').set(
                    setting_data.get('search_floor', 'videoc'))
            
            if hasattr(self, f'search_service_{setting_num}_var'):
                getattr(self, f'search_service_{setting_num}_var').set(
                    setting_data.get('search_service', 'digital'))
            
            if hasattr(self, f'search_sort_{setting_num}_var'):
                getattr(self, f'search_sort_{setting_num}_var').set(
                    setting_data.get('search_sort', 'date'))
            
            if hasattr(self, f'search_hits_{setting_num}_var'):
                getattr(self, f'search_hits_{setting_num}_var').set(
                    setting_data.get('search_hits', 30))
            
            if hasattr(self, f'search_from_date_{setting_num}_var'):
                getattr(self, f'search_from_date_{setting_num}_var').set(
                    setting_data.get('search_from_date', ''))
            
            if hasattr(self, f'search_to_date_{setting_num}_var'):
                getattr(self, f'search_to_date_{setting_num}_var').set(
                    setting_data.get('search_to_date', ''))
            
            # 投稿内容テキストの読み込み
            if hasattr(self, f'post_content_text{setting_num}'):
                content_text = getattr(self, f'post_content_text{setting_num}')
                content_text.delete('1.0', tk.END)
                content_text.insert('1.0', setting_data.get('content', ''))
                
        except Exception as e:
            self.log_message(f"個別投稿設定{setting_num}読み込みエラー: {e}")
            print(f"個別投稿設定{setting_num}読み込みエラー詳細: {traceback.format_exc()}")
    
    def _get_post_settings_from_gui(self):
        """投稿設定をGUIから取得"""
        try:
            # 基本設定と投稿設定を分離
            basic_settings = {}
            post_settings = {}
            
            # 共通設定の取得（基本設定として保存）
            if hasattr(self, 'excerpt_template_var'):
                var = self.excerpt_template_var
                if hasattr(var, 'get'):
                    basic_settings['EXCERPT_TEMPLATE'] = var.get()
                else:
                    basic_settings['EXCERPT_TEMPLATE'] = str(var)
            if hasattr(self, 'max_sample_images_var'):
                var = self.max_sample_images_var
                if hasattr(var, 'get'):
                    basic_settings['MAX_SAMPLE_IMAGES'] = var.get()
                else:
                    basic_settings['MAX_SAMPLE_IMAGES'] = str(var)
            if hasattr(self, 'categories_var'):
                var = self.categories_var
                if hasattr(var, 'get'):
                    basic_settings['CATEGORIES'] = var.get()
                else:
                    basic_settings['CATEGORIES'] = str(var)
            if hasattr(self, 'tags_var'):
                var = self.tags_var
                if hasattr(var, 'get'):
                    basic_settings['TAGS'] = var.get()
                else:
                    basic_settings['TAGS'] = str(var)
            if hasattr(self, 'affiliate1_text_var'):
                var = self.affiliate1_text_var
                if hasattr(var, 'get'):
                    basic_settings['AFFILIATE1_TEXT'] = var.get()
                else:
                    basic_settings['AFFILIATE1_TEXT'] = str(var)
            if hasattr(self, 'affiliate1_color_var'):
                var = self.affiliate1_color_var
                if hasattr(var, 'get'):
                    basic_settings['AFFILIATE1_COLOR'] = var.get()
                else:
                    basic_settings['AFFILIATE1_COLOR'] = str(var)
            if hasattr(self, 'affiliate1_bg_var'):
                var = self.affiliate1_bg_var
                if hasattr(var, 'get'):
                    basic_settings['AFFILIATE1_BG'] = var.get()
                else:
                    basic_settings['AFFILIATE1_BG'] = str(var)
            if hasattr(self, 'affiliate2_text_var'):
                var = self.affiliate2_text_var
                if hasattr(var, 'get'):
                    basic_settings['AFFILIATE2_TEXT'] = var.get()
                else:
                    basic_settings['AFFILIATE2_TEXT'] = str(var)
            if hasattr(self, 'affiliate2_color_var'):
                var = self.affiliate2_color_var
                if hasattr(var, 'get'):
                    basic_settings['AFFILIATE2_COLOR'] = var.get()
                else:
                    basic_settings['AFFILIATE2_COLOR'] = str(var)
            if hasattr(self, 'affiliate2_bg_var'):
                var = self.affiliate2_bg_var
                if hasattr(var, 'get'):
                    basic_settings['AFFILIATE2_BG'] = var.get()
                else:
                    basic_settings['AFFILIATE2_BG'] = str(var)
            if hasattr(self, 'post_date_setting_var'):
                var = self.post_date_setting_var
                if hasattr(var, 'get'):
                    basic_settings['POST_DATE_SETTING'] = var.get()
                else:
                    basic_settings['POST_DATE_SETTING'] = str(var)
            if hasattr(self, 'random_text1_var'):
                var = self.random_text1_var
                if hasattr(var, 'get'):
                    basic_settings['RANDOM_TEXT1'] = var.get()
                else:
                    basic_settings['RANDOM_TEXT1'] = str(var)
            if hasattr(self, 'random_text2_var'):
                var = self.random_text2_var
                if hasattr(var, 'get'):
                    basic_settings['RANDOM_TEXT2'] = var.get()
                else:
                    basic_settings['RANDOM_TEXT2'] = str(var)
            if hasattr(self, 'random_text3_var'):
                var = self.random_text3_var
                if hasattr(var, 'get'):
                    basic_settings['RANDOM_TEXT3'] = var.get()
                else:
                    basic_settings['RANDOM_TEXT3'] = str(var)
            
            # 個別投稿設定の取得（1-4）をpost_settingsセクションとして保存
            post_settings['post_settings'] = {}
            for setting_num in range(1, 5):
                individual_settings = self._get_individual_post_settings(setting_num)
                if individual_settings:
                    post_settings['post_settings'][str(setting_num)] = individual_settings
                    self.log_message(f"投稿設定{setting_num}を取得: {len(individual_settings)}件")
                else:
                    self.log_message(f"投稿設定{setting_num}の取得に失敗")
            
            # 基本設定と投稿設定を統合
            all_settings = {}
            all_settings.update(basic_settings)
            all_settings.update(post_settings)
            
            self.log_message(f"_get_post_settings_from_gui: 基本設定{len(basic_settings)}件、投稿設定{len(post_settings)}件")
            
            return all_settings
            
        except Exception as e:
            self.log_message(f"投稿設定取得エラー: {e}")
            import traceback
            self.log_message(f"エラー詳細: {traceback.format_exc()}")
            return {}
    
    def _get_individual_post_settings(self, setting_num):
        """個別の投稿設定を取得"""
        try:
            individual_settings = {}
            
            # 投稿設定の取得
            if hasattr(self, f'post_title_{setting_num}_var'):
                var = getattr(self, f'post_title_{setting_num}_var')
                if hasattr(var, 'get'):
                    value = var.get()
                    individual_settings['title'] = value
                    self.log_message(f"投稿設定{setting_num} title: {type(value).__name__} = {value}")
                else:
                    value = str(var)
                    individual_settings['title'] = value
                    self.log_message(f"投稿設定{setting_num} title: {type(value).__name__} = {value}")
            
            if hasattr(self, f'post_eyecatch_{setting_num}_var'):
                var = getattr(self, f'post_eyecatch_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['eyecatch'] = var.get()
                else:
                    individual_settings['eyecatch'] = str(var)
            
            if hasattr(self, f'post_movie_size_{setting_num}_var'):
                var = getattr(self, f'post_movie_size_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['movie_size'] = var.get()
                else:
                    individual_settings['movie_size'] = str(var)
            
            if hasattr(self, f'post_poster_{setting_num}_var'):
                var = getattr(self, f'post_poster_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['poster'] = var.get()
                else:
                    individual_settings['poster'] = str(var)
            
            if hasattr(self, f'post_category_{setting_num}_var'):
                var = getattr(self, f'post_category_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['category'] = var.get()
                else:
                    individual_settings['category'] = str(var)
            
            if hasattr(self, f'post_sort_{setting_num}_var'):
                var = getattr(self, f'post_sort_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['sort'] = var.get()
                else:
                    individual_settings['sort'] = str(var)
            
            if hasattr(self, f'post_article_{setting_num}_var'):
                var = getattr(self, f'post_article_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['article_type'] = var.get()
                else:
                    individual_settings['article_type'] = str(var)
            
            if hasattr(self, f'post_status_{setting_num}_var'):
                var = getattr(self, f'post_status_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['status'] = var.get()
                else:
                    individual_settings['status'] = str(var)
            
            if hasattr(self, f'post_hour_{setting_num}_var'):
                var = getattr(self, f'post_hour_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['hour'] = var.get()
                else:
                    individual_settings['hour'] = str(var)
            
            if hasattr(self, f'post_overwrite_existing_{setting_num}_var'):
                var = getattr(self, f'post_overwrite_existing_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['overwrite_existing'] = var.get()
                else:
                    individual_settings['overwrite_existing'] = bool(var)
            
            if hasattr(self, f'target_new_posts_{setting_num}_var'):
                var = getattr(self, f'target_new_posts_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['target_new_posts'] = var.get()
                else:
                    individual_settings['target_new_posts'] = int(var)
            
            # 検索設定の取得
            if hasattr(self, f'search_site_{setting_num}_var'):
                var = getattr(self, f'search_site_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['site'] = var.get()
                else:
                    individual_settings['site'] = str(var)
            
            if hasattr(self, f'search_keyword_{setting_num}_var'):
                var = getattr(self, f'search_keyword_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['keyword'] = var.get()
                else:
                    individual_settings['keyword'] = str(var)
            
            if hasattr(self, f'search_category_{setting_num}_var'):
                var = getattr(self, f'search_category_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['article_type'] = var.get()
                else:
                    individual_settings['article_type'] = str(var)
            
            if hasattr(self, f'search_floor_{setting_num}_var'):
                var = getattr(self, f'search_floor_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['floor'] = var.get()
                else:
                    individual_settings['floor'] = str(var)
            
            if hasattr(self, f'search_service_{setting_num}_var'):
                var = getattr(self, f'search_service_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['service'] = var.get()
                else:
                    individual_settings['service'] = str(var)
            
            if hasattr(self, f'search_sort_{setting_num}_var'):
                var = getattr(self, f'search_sort_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['sort'] = var.get()
                else:
                    individual_settings['sort'] = str(var)
            
            if hasattr(self, f'search_hits_{setting_num}_var'):
                var = getattr(self, f'search_hits_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['hits'] = var.get()
                else:
                    individual_settings['hits'] = int(var)
            
            if hasattr(self, f'search_from_date_{setting_num}_var'):
                var = getattr(self, f'search_from_date_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['from_date'] = var.get()
                else:
                    individual_settings['from_date'] = str(var)
            
            if hasattr(self, f'search_to_date_{setting_num}_var'):
                var = getattr(self, f'search_to_date_{setting_num}_var')
                if hasattr(var, 'get'):
                    individual_settings['to_date'] = var.get()
                else:
                    individual_settings['to_date'] = str(var)
            
            # 投稿内容テキストの取得
            if hasattr(self, f'post_content_text{setting_num}'):
                content_text = getattr(self, f'post_content_text{setting_num}')
                if hasattr(content_text, 'get'):
                    individual_settings['content'] = content_text.get('1.0', tk.END).strip()
                else:
                    individual_settings['content'] = str(content_text)
            
            return individual_settings
                
        except Exception as e:
            self.log_message(f"個別投稿設定{setting_num}取得エラー: {e}")
            import traceback
            self.log_message(f"エラー詳細: {traceback.format_exc()}")
            return {}
    
    def _set_default_post_settings(self):
        """投稿設定をデフォルト値に設定"""
        try:
            # 共通設定のデフォルト値
            if hasattr(self, 'excerpt_template_var'):
                self.excerpt_template_var.set("")
            if hasattr(self, 'max_sample_images_var'):
                self.max_sample_images_var.set("5")
            if hasattr(self, 'categories_var'):
                self.categories_var.set("")
            if hasattr(self, 'tags_var'):
                self.tags_var.set("")
            if hasattr(self, 'affiliate1_text_var'):
                self.affiliate1_text_var.set("")
            if hasattr(self, 'affiliate1_color_var'):
                self.affiliate1_color_var.set("")
            if hasattr(self, 'affiliate1_bg_var'):
                self.affiliate1_bg_var.set("")
            if hasattr(self, 'affiliate2_text_var'):
                self.affiliate2_text_var.set("")
            if hasattr(self, 'affiliate2_color_var'):
                self.affiliate2_color_var.set("")
            if hasattr(self, 'affiliate2_bg_var'):
                self.affiliate2_bg_var.set("")
            if hasattr(self, 'post_date_setting_var'):
                self.post_date_setting_var.set("本日")
            if hasattr(self, 'random_text1_var'):
                self.random_text1_var.set("")
            if hasattr(self, 'random_text2_var'):
                self.random_text2_var.set("")
            if hasattr(self, 'random_text3_var'):
                self.random_text3_var.set("")
            
            # 個別投稿設定のデフォルト値（1-4）
            for setting_num in range(1, 5):
                self._set_default_individual_post_settings(setting_num)
                
        except Exception as e:
            self.log_message(f"投稿設定デフォルト値設定エラー: {e}")
    
    def _set_default_individual_post_settings(self, setting_num):
        """個別の投稿設定をデフォルト値に設定"""
        try:
            # 投稿設定のデフォルト値
            if hasattr(self, f'post_title_{setting_num}_var'):
                getattr(self, f'post_title_{setting_num}_var').set("")
            
            if hasattr(self, f'post_eyecatch_{setting_num}_var'):
                getattr(self, f'post_eyecatch_{setting_num}_var').set("サンプル画像")
            
            if hasattr(self, f'post_movie_size_{setting_num}_var'):
                getattr(self, f'post_movie_size_{setting_num}_var').set("自動")
            
            if hasattr(self, f'post_poster_{setting_num}_var'):
                getattr(self, f'post_poster_{setting_num}_var').set("パッケージ画像")
            
            if hasattr(self, f'post_category_{setting_num}_var'):
                getattr(self, f'post_category_{setting_num}_var').set("JAN")
            
            if hasattr(self, f'post_sort_{setting_num}_var'):
                getattr(self, f'post_sort_{setting_num}_var').set("人気順")
            
            if hasattr(self, f'post_article_{setting_num}_var'):
                getattr(self, f'post_article_{setting_num}_var').set("指定なし")
            
            if hasattr(self, f'post_status_{setting_num}_var'):
                getattr(self, f'post_status_{setting_num}_var').set("公開")
            
            if hasattr(self, f'post_hour_{setting_num}_var'):
                getattr(self, f'post_hour_{setting_num}_var').set("09:00")
            
            if hasattr(self, f'post_overwrite_existing_{setting_num}_var'):
                getattr(self, f'post_overwrite_existing_{setting_num}_var').set(False)
            
            if hasattr(self, f'target_new_posts_{setting_num}_var'):
                getattr(self, f'target_new_posts_{setting_num}_var').set("")
            
            # 検索設定のデフォルト値
            if hasattr(self, f'search_site_{setting_num}_var'):
                getattr(self, f'search_site_{setting_num}_var').set("FANZA")
            
            if hasattr(self, f'search_keyword_{setting_num}_var'):
                getattr(self, f'search_keyword_{setting_num}_var').set("")
            
            if hasattr(self, f'search_category_{setting_num}_var'):
                getattr(self, f'search_category_{setting_num}_var').set("")
            
            if hasattr(self, f'search_floor_{setting_num}_var'):
                getattr(self, f'search_floor_{setting_num}_var').set("videoc")
            
            if hasattr(self, f'search_service_{setting_num}_var'):
                getattr(self, f'search_service_{setting_num}_var').set("digital")
            
            if hasattr(self, f'search_sort_{setting_num}_var'):
                getattr(self, f'search_sort_{setting_num}_var').set("date")
            
            if hasattr(self, f'search_hits_{setting_num}_var'):
                getattr(self, f'search_hits_{setting_num}_var').set("")
            
            if hasattr(self, f'search_from_date_{setting_num}_var'):
                getattr(self, f'search_from_date_{setting_num}_var').set("")
            
            if hasattr(self, f'search_to_date_{setting_num}_var'):
                getattr(self, f'search_to_date_{setting_num}_var').set("")
            
            # 投稿内容テキストのデフォルト値
            if hasattr(self, f'post_content_text{setting_num}'):
                content_text = getattr(self, f'post_content_text{setting_num}')
                content_text.delete('1.0', tk.END)
                content_text.insert('1.0', "")
                
        except Exception as e:
            self.log_message(f"個別投稿設定{setting_num}デフォルト値設定エラー: {e}")
    
    def create_backup(self):
        """設定のバックアップを作成"""
        try:
            if self.settings_manager:
                backup_path = self.settings_manager.create_backup()
                self.log_message(f"設定をバックアップしました: {backup_path}")
                messagebox.showinfo("バックアップ完了", f"設定をバックアップしました:\n{backup_path}")
            else:
                self.log_message("SettingsManagerが利用できません")
        except Exception as e:
            self.log_message(f"バックアップ作成エラー: {e}")
            messagebox.showerror("エラー", f"バックアップ作成に失敗しました:\n{e}")
    
    def show_restore_dialog(self):
        """復元ダイアログを表示"""
        try:
            if not self.settings_manager:
                messagebox.showerror("エラー", "SettingsManagerが利用できません")
                return
            
            # バックアップファイルの選択
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "backups")
            if not os.path.exists(backup_dir):
                messagebox.showerror("エラー", "バックアップディレクトリが見つかりません")
                return
            
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
            if not backup_files:
                messagebox.showerror("エラー", "バックアップファイルが見つかりません")
                return
            
            # 復元ファイル選択ダイアログ
            restore_window = tk.Toplevel(self.root)
            restore_window.title("設定復元")
            restore_window.geometry("400x300")
            restore_window.transient(self.root)
            restore_window.grab_set()
            
            ttk.Label(restore_window, text="復元するバックアップファイルを選択してください:", 
                     font=("Arial", 10, "bold")).pack(pady=(20, 10))
            
            # ファイルリスト
            listbox = tk.Listbox(restore_window, height=10)
            listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            for backup_file in sorted(backup_files, reverse=True):
                listbox.insert(tk.END, backup_file)
            
            # 復元ボタン
            def restore_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("警告", "ファイルを選択してください")
                    return
                
                selected_file = backup_files[selection[0]]
                try:
                    self.settings_manager.restore_from_backup(selected_file)
                    self.log_message(f"設定を復元しました: {selected_file}")
                    messagebox.showinfo("復元完了", f"設定を復元しました:\n{selected_file}")
                    restore_window.destroy()
                    
                    # GUIの再読み込み
                    self.load_settings_to_gui()
                except Exception as e:
                    self.log_message(f"設定復元エラー: {e}")
                    messagebox.showerror("エラー", f"設定復元に失敗しました:\n{e}")
            
            restore_button = ttk.Button(restore_window, text="復元", 
                                       command=restore_selected, style="Accent.TButton")
            restore_button.pack(pady=(0, 20))
            
        except Exception as e:
            self.log_message(f"復元ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"復元ダイアログの表示に失敗しました:\n{e}")
    
    def repair_settings(self):
        """設定の修復"""
        try:
            if self.settings_manager:
                self.settings_manager.repair_settings()
                self.log_message("設定を修復しました")
                messagebox.showinfo("修復完了", "設定を修復しました")
                
                # GUIの再読み込み
                self.load_settings_to_gui()
            else:
                self.log_message("SettingsManagerが利用できません")
        except Exception as e:
            self.log_message(f"設定修復エラー: {e}")
            messagebox.showerror("エラー", f"設定修復に失敗しました:\n{e}")
    
    def reset_settings(self):
        """設定のリセット"""
        try:
            result = messagebox.askyesno("確認", "設定をリセットしますか？\nこの操作は元に戻せません。")
            if result:
                if self.settings_manager:
                    # 新しい設定管理システムを使用してリセット
                    self.settings_manager.reset_to_defaults()
                    self.log_message("設定をリセットしました")
                    messagebox.showinfo("リセット完了", "設定をリセットしました")
                    
                    # 各タブのデフォルト値を設定
                    if self.basic_settings_tab:
                        self.basic_settings_tab.set_default_values()
                    if self.schedule_settings_tab:
                        self.schedule_settings_tab.set_default_values()
                    # 投稿設定のデフォルト値を設定
                    self._set_default_post_settings()
                    if self.execution_tab:
                        self.execution_tab.set_default_values()
                    
                    # 設定オブジェクトもリセット
                    if self.settings:
                        self.settings = Settings()
                    
                    self.log_message("GUIをデフォルト値にリセットしました")
                    
                    # 設定状態を更新
                    self.update_settings_status()
                else:
                    self.log_message("SettingsManagerが利用できません")
                    messagebox.showerror("エラー", "設定管理システムが利用できません")
        except Exception as e:
            self.log_message(f"設定リセットエラー: {e}")
            messagebox.showerror("エラー", f"設定リセットに失敗しました:\n{e}")
    
    def update_settings_status(self):
        """設定状態の更新"""
        try:
            if not self.settings_manager:
                self.settings_status_var.set("設定状態: エラー")
                return
            
            # 新しい設定管理システムから設定状態を確認
            settings = self.settings_manager.load_settings()
            
            if settings and settings.get('DMM_API_ID'):
                self.settings_status_var.set("設定状態: 正常")
            else:
                self.settings_status_var.set("設定状態: 未設定")
                
        except Exception as e:
            self.settings_status_var.set("設定状態: エラー")
            self.log_message(f"設定状態更新エラー: {e}")
    
    def log_message(self, message):
        """ログメッセージを追加"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            # ログキューに追加
            self.log_queue.put(log_entry)
            
            # ログテキストエリアに直接追加（即座に表示）
            if hasattr(self, 'log_text'):
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)
                
                # ログが長すぎる場合は古いログを削除
                lines = int(self.log_text.index('end-1c').split('.')[0])
                if lines > 1000:
                    self.log_text.delete('1.0', f'{lines-500}.0')
        except Exception as e:
            print(f"ログメッセージ追加エラー: {e}")
    
    def update_log(self):
        """ログの更新"""
        try:
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                if hasattr(self, 'log_text'):
                    self.log_text.insert(tk.END, log_entry)
                    self.log_text.see(tk.END)
        except Exception as e:
            print(f"ログ更新エラー: {e}")
        
        # 100ms後に再度実行
        self.root.after(100, self.update_log)
    
    def clear_log(self):
        """ログをクリア"""
        try:
            if hasattr(self, 'log_text'):
                self.log_text.delete('1.0', tk.END)
                self.log_message("ログをクリアしました")
        except Exception as e:
            print(f"ログクリアエラー: {e}")
    
    def start_monitoring(self):
        """自動監視の開始"""
        try:
            if not self.monitoring_active:
                self.monitoring_active = True
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.log_message("自動監視を開始しました")
        except Exception as e:
            self.log_message(f"自動監視開始エラー: {e}")
    
    def stop_monitoring(self):
        """自動監視の停止"""
        try:
            self.monitoring_active = False
            self.log_message("自動監視を停止しました")
        except Exception as e:
            self.log_message(f"自動監視停止エラー: {e}")
    
    def monitor_loop(self):
        """監視ループ"""
        try:
            while self.monitoring_active:
                # 監視処理をここに実装
                time.sleep(60)  # 1分間隔
        except Exception as e:
            self.log_message(f"監視ループエラー: {e}")
    
    def manual_post(self, setting_num):
        """指定された投稿設定で手動投稿を実行"""
        try:
            if self.is_running:
                self.log_message("既に実行中です。手動投稿をスキップします。")
                return
            
            # 投稿設定の状態を更新
            self.manual_post_status_vars[setting_num].set("実行中...")
            
            # ログに開始メッセージを追加
            self.log_message(f"投稿設定{setting_num}で手動投稿を開始します")
            
            # 投稿設定を選択
            self.selected_post_setting_var.set(str(setting_num))
            
            # 現在のGUIの設定を保存
            self.save_all_settings()
            
            # 設定を再読み込みしてエンジンに反映
            if self.settings_manager:
                loaded_settings = self.settings_manager.load_settings()
                if loaded_settings:
                    self.log_message(f"設定ファイルから読み込み: {len(loaded_settings)}件")
                    
                    # 投稿設定の確認
                    if "post_settings" in loaded_settings:
                        post_settings = loaded_settings["post_settings"]
                        self.log_message(f"loaded_settingsからpost_settingsを取得: {len(post_settings)}件")
                        self.log_message(f"post_settingsの型: {type(post_settings)}")
                        self.log_message(f"post_settingsのキー: {list(post_settings.keys())}")
                        
                        if str(setting_num) in post_settings:
                            setting_data = post_settings[str(setting_num)]
                            self.log_message(f"投稿設定{setting_num}の内容:")
                            self.log_message(f"  タイトル: {setting_data.get('title', 'N/A')}")
                            self.log_message(f"  カテゴリ: {setting_data.get('category', 'N/A')}")
                            self.log_message(f"  ステータス: {setting_data.get('status', 'N/A')}")
                            self.log_message(f"  データ型: {type(setting_data)}")
                        else:
                            self.log_message(f"投稿設定{setting_num}が見つかりません")
                    else:
                        self.log_message("post_settingsセクションが見つかりません")
                        self.log_message(f"loaded_settingsのキー: {list(loaded_settings.keys())}")
                    
                    # エンジンの設定を更新
                    try:
                        self.settings = Settings(**loaded_settings)
                        self.log_message("Settingsオブジェクトの作成完了")
                        self.log_message(f"self.settingsの型: {type(self.settings)}")
                        
                        self.engine.settings = self.settings
                        self.log_message("エンジンの設定を更新しました")
                        
                        # 投稿設定の確認
                        if hasattr(self.settings, 'post_settings') and self.settings.post_settings:
                            self.log_message(f"投稿設定の確認: {len(self.settings.post_settings)}件")
                            self.log_message(f"post_settingsの型: {type(self.settings.post_settings)}")
                            for key in self.settings.post_settings.keys():
                                self.log_message(f"  設定{key}: {self.settings.post_settings[key].get('title', 'N/A')}")
                        else:
                            self.log_message("投稿設定が見つかりません")
                            if hasattr(self.settings, 'post_settings'):
                                self.log_message(f"post_settingsの値: {self.settings.post_settings}")
                    except Exception as e:
                        self.log_message(f"Settingsオブジェクトの作成でエラー: {e}")
                        import traceback
                        self.log_message(f"エラー詳細: {traceback.format_exc()}")
                    
                    # エンジンの設定キャッシュをクリア
                    if hasattr(self.engine, '_clear_settings_cache'):
                        self.engine._clear_settings_cache()
                        self.log_message("エンジンの設定キャッシュをクリアしました")
                else:
                    self.log_message("設定ファイルの読み込みに失敗しました")
            
            # 1回実行を実行（手動投稿として）
            self.engine.run_once(str(setting_num))
            
            # 投稿完了後の状態更新
            self.manual_post_status_vars[setting_num].set("完了")
            
        except Exception as e:
            error_msg = f"手動投稿エラー: {e}"
            self.log_message(error_msg)
            self.manual_post_status_vars[setting_num].set("エラー")
            print(f"手動投稿エラー: {e}")
            import traceback
            print(f"エラー詳細: {traceback.format_exc()}")
    
    def run_once(self):
        """1回実行"""
        if self.is_running:
            return
        
        # 実行前のフロア設定検証
        if not self.validate_floor_settings():
            return
        
        self.is_running = True
        
        def run():
            try:
                self.log_message("通常実行を開始します...")
                
                # 選択された投稿設定を取得
                selected_setting = self.selected_post_setting_var.get()
                self.log_message(f"投稿設定{selected_setting}を使用して実行します")
                
                # 現在のフロア情報をログに表示
                floor_info = self.get_current_floor_info()
                if floor_info:
                    self.log_message(f"対象フロア: {floor_info.get('name', 'N/A')} (コード: {floor_info.get('code', 'N/A')})")
                    self.log_message(f"サイト: {floor_info.get('site', 'N/A')}, サービス: {floor_info.get('service', 'N/A')}")
                
                # 投稿設定を読み込み
                posting_settings = self.engine._load_posting_settings(selected_setting)
                self.log_message(f"投稿設定{selected_setting}を使用して検索します")
                
                # 実行前の情報をログに表示
                items, total = self.engine.search_items(posting_settings)
                self.log_message(f"検索結果: {total}件のアイテムが見つかりました")
                self.log_message(f"処理対象: {len(items)}件のアイテム")
                
                # 投稿設定の詳細をログに表示
                if hasattr(self.engine, '_load_posting_settings'):
                    try:
                        posting_settings = self.engine._load_posting_settings(selected_setting)
                        self.log_message(f"投稿設定{selected_setting}の詳細:")
                        self.log_message(f"  タイトル: {posting_settings.title}")
                        self.log_message(f"  カテゴリ: {posting_settings.category}")
                        self.log_message(f"  ステータス: {posting_settings.status}")
                        self.log_message(f"  上書き: {posting_settings.overwrite_existing}")
                        
                        # 設定の詳細情報も表示
                        self.log_message(f"  検索サイト: {posting_settings.site}")
                        self.log_message(f"  検索フロア: {posting_settings.floor}")
                        self.log_message(f"  検索サービス: {posting_settings.service}")
                        self.log_message(f"  検索件数: {posting_settings.hits}")
                    except Exception as e:
                        self.log_message(f"投稿設定の詳細取得エラー: {e}")
                        import traceback
                        self.log_message(f"エラー詳細: {traceback.format_exc()}")
                else:
                    self.log_message("エンジンに_load_posting_settingsメソッドがありません")
                
                # 実行
                created_posts = self.engine.run_once(selected_setting)
                
                # 実行結果をログに表示
                if created_posts:
                    self.log_message(f"投稿作成完了: {len(created_posts)}件")
                    for i, post_id in enumerate(created_posts, 1):
                        self.log_message(f"投稿{i}: ID {post_id}")
                else:
                    self.log_message("新しく作成された投稿はありません")
                
                self.log_message("通常実行が完了しました")
            except Exception as e:
                self.log_message(f"実行エラー: {e}")
                import traceback
                self.log_message(f"エラー詳細: {traceback.format_exc()}")
            finally:
                self.is_running = False
        
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
    
    def validate_floor_settings(self) -> bool:
        """フロア設定の検証"""
        try:
            # 基本的な設定が存在するかをチェック
            if not hasattr(self, 'engine') or not self.engine:
                self.log_message("エンジンが初期化されていません")
                return False
            
            # フロア情報が設定されているかをチェック
            floor_info = self.get_current_floor_info()
            if not floor_info:
                self.log_message("フロア情報が設定されていません")
                return False
            
            return True
        except Exception as e:
            self.log_message(f"フロア設定検証エラー: {e}")
            return False
    
    def get_current_floor_info(self) -> Dict[str, Any]:
        """現在のフロア情報を取得"""
        try:
            # 基本的なフロア情報を返す
            # 実際の実装では、GUIからフロア設定を取得する必要があります
            return {
                'name': 'ビデオ',
                'code': 'videoc',
                'site': 'FANZA',
                'service': 'digital'
            }
        except Exception as e:
            self.log_message(f"フロア情報取得エラー: {e}")
            return {}
    
    def preview_post_content(self):
        """投稿内容をプレビュー"""
        try:
            # プレビューウィンドウを作成
            preview_window = tk.Toplevel(self.root)
            preview_window.title("投稿内容プレビュー")
            preview_window.geometry("800x600")
            preview_window.transient(self.root)
            preview_window.grab_set()
            
            # プレビュー内容を表示
            preview_text = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD, width=80, height=30)
            preview_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # サンプルプレビュー内容
            sample_content = """# 投稿内容プレビュー

この機能は投稿設定に基づいて実際の投稿内容をプレビュー表示します。

## 設定項目
- 投稿タイトル: [title]
- アイキャッチ: サンプル画像
- 動画サイズ: 自動
- カテゴリ: JAN

## テンプレート変数
[title] - 商品タイトル
[description] - 商品説明
[price] - 価格
[category] - カテゴリ

実際の投稿時には、これらの変数が実際の値に置き換えられます。"""
            
            preview_text.insert(tk.END, sample_content)
            preview_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.log_message(f"プレビュー表示エラー: {e}")
            messagebox.showerror("エラー", f"プレビューの表示に失敗しました:\n{e}")
    
    def toggle_settings_lock(self):
        """設定のロック/アンロックを切り替え"""
        try:
            if not self.settings_manager:
                messagebox.showerror("エラー", "設定管理システムが利用できません")
                return
            
            # 現在のロック状態を確認
            current_settings = self.settings_manager.load_settings()
            is_locked = current_settings.get('SETTINGS_LOCKED', False)
            
            if is_locked:
                # ロックを解除
                current_settings['SETTINGS_LOCKED'] = False
                self.settings_manager.save_settings(current_settings)
                self.log_message("設定のロックを解除しました")
                messagebox.showinfo("ロック解除", "設定のロックを解除しました")
            else:
                # ロックを設定
                current_settings['SETTINGS_LOCKED'] = True
                self.settings_manager.save_settings(current_settings)
                self.log_message("設定をロックしました")
                messagebox.showinfo("ロック設定", "設定をロックしました")
            
            # 設定状態を更新
            self.update_settings_status()
            
        except Exception as e:
            self.log_message(f"設定ロック切り替えエラー: {e}")
            messagebox.showerror("エラー", f"設定ロックの切り替えに失敗しました:\n{e}")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        try:
            self.stop_monitoring()
            
            # スケジューラーの停止
            if self.scheduler:
                self.scheduler.shutdown()
            
            self.log_message("アプリケーションを終了します")
            self.root.quit()
        except Exception as e:
            print(f"終了処理エラー: {e}")
            self.root.quit()

def main():
    """メイン関数"""
    try:
        root = tk.Tk()
        app = FanzaAutoGUI(root)
        
        # ウィンドウを閉じる際の処理
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # メインループの開始
        root.mainloop()
    except Exception as e:
        print(f"メイン関数エラー: {e}")
        print(f"エラー詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
