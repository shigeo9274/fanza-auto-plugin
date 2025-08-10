import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
import os
import sys
from datetime import datetime
from typing import Optional
import traceback
import time

# 相対インポートを避けるため、パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Settings
from engine import Engine
from settings_manager import SettingsManager
from apscheduler.schedulers.background import BackgroundScheduler
import time

class FanzaAutoGUI:
    def __init__(self, root):
        print("GUI初期化開始")
        self.root = root
        self.root.title("FANZA Auto Plugin - Python版")
        self.root.geometry("1200x900")
        
        # 設定とエンジンの初期化
        try:
            print("設定ファイル読み込み開始")
            self.settings = Settings.load()
            print(f"設定読み込み成功: {self.settings}")
            self.engine = Engine.from_settings(self.settings)
            print("エンジン初期化成功")
            print("設定を.envファイルから読み込みました")
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            print(f"エラー詳細: {traceback.format_exc()}")
            # 環境変数が設定されていない場合はデフォルト値で初期化
            try:
                self.settings = Settings()
                self.engine = Engine.from_settings(self.settings)
                print("デフォルト値で初期化しました")
            except Exception as e2:
                print(f"デフォルト値初期化エラー: {e2}")
                print(f"エラー詳細: {traceback.format_exc()}")
                # エラーが発生してもGUIは起動する
                self.settings = None
                self.engine = None
        
        # SettingsManagerの初期化
        try:
            self.settings_manager = SettingsManager(os.path.dirname(os.path.abspath(__file__)))
            print("SettingsManager初期化完了")
        except Exception as e:
            print(f"SettingsManager初期化エラー: {e}")
            self.settings_manager = None
        
        self.scheduler: Optional[BackgroundScheduler] = None
        self.is_running = False
        self.monitoring_active = False  # 監視状態を管理
        
        # ログ用のキュー
        self.log_queue = queue.Queue()
        
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
        
        # 設定の読み込み
        try:
            self.load_settings_to_gui()
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
        
        # 設定のデフォルト値設定（設定が読み込まれていない場合のみ）
        try:
            if not hasattr(self, 'settings') or not self.settings:
                self.set_default_values()
        except Exception as e:
            print(f"デフォルト値設定エラー: {e}")
        
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
        # 基本設定タブ
        self.create_basic_settings_tab()
        
        # 検索設定タブ
        self.create_search_settings_tab()
        
        # スケジュール設定タブ
        self.create_schedule_settings_tab()
        
        # 投稿設定タブ
        self.create_post_settings_tab()
        
        # 実行・ログタブ
        self.create_execution_tab()
        
        # ボタンフレーム（全タブ共通）
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(0, 15))
        button_frame.columnconfigure(0, weight=1)
        
        # 保存ボタン
        save_button = ttk.Button(button_frame, text="設定を保存", 
                                command=self.save_settings, style="Accent.TButton")
        save_button.grid(row=0, column=0, padx=(0, 10))
        
        # ステータスバー
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, padding=(10, 5))
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        print("ウィジェット作成完了")
    
    def create_basic_settings_tab(self):
        """基本設定タブの作成"""
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="基本設定")
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(basic_frame)
        scrollbar = ttk.Scrollbar(basic_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # DMM API設定
        dmm_frame = ttk.LabelFrame(scrollable_frame, text="DMM API設定", padding="15")
        dmm_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        dmm_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(dmm_frame, text="DMM API ID:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.dmm_api_id_var = tk.StringVar()
        ttk.Entry(dmm_frame, textvariable=self.dmm_api_id_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(dmm_frame, text="※DMMアフィリエイトプログラムで取得", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(dmm_frame, text="DMM アフィリエイトID:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.dmm_affiliate_id_var = tk.StringVar()
        ttk.Entry(dmm_frame, textvariable=self.dmm_affiliate_id_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(dmm_frame, text="※アフィリエイトIDを入力", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # WordPress設定
        wp_frame = ttk.LabelFrame(scrollable_frame, text="WordPress設定", padding="15")
        wp_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        wp_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(wp_frame, text="WordPress URL:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.wp_url_var = tk.StringVar()
        ttk.Entry(wp_frame, textvariable=self.wp_url_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(wp_frame, text="※WordPressサイトのURL（例: https://example.com）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(wp_frame, text="ユーザー名:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.wp_username_var = tk.StringVar()
        ttk.Entry(wp_frame, textvariable=self.wp_username_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(wp_frame, text="※WordPressのユーザー名", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(wp_frame, text="アプリケーションパスワード:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.wp_app_password_var = tk.StringVar()
        ttk.Entry(wp_frame, textvariable=self.wp_app_password_var, width=40, show="*").grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(wp_frame, text="※WordPressのアプリケーションパスワード", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # ブラウザ設定
        browser_frame = ttk.LabelFrame(scrollable_frame, text="ブラウザ設定", padding="15")
        browser_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        browser_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(browser_frame, text="ページ待機時間（秒）:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.page_wait_sec_var = tk.StringVar()
        ttk.Entry(browser_frame, textvariable=self.page_wait_sec_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(browser_frame, text="※ページ読み込み後の待機時間", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        basic_frame.columnconfigure(0, weight=1)
        basic_frame.rowconfigure(0, weight=1)
    
    def create_search_settings_tab(self):
        """検索設定タブの作成"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="検索設定")
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(search_frame)
        scrollbar = ttk.Scrollbar(search_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 検索条件設定
        search_conditions_frame = ttk.LabelFrame(scrollable_frame, text="検索条件", padding="15")
        search_conditions_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        search_conditions_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(search_conditions_frame, text="サイト:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.site_var = tk.StringVar()
        site_combo = ttk.Combobox(search_conditions_frame, textvariable=self.site_var, 
                                 values=["FANZA", "FANZA通販", "FANZA動画"], state="readonly", width=15)
        site_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※対象サイトを選択", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="サービス:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.service_var = tk.StringVar()
        service_combo = ttk.Combobox(search_conditions_frame, textvariable=self.service_var, 
                                    values=["デジタル", "パッケージ", "両方"], state="readonly", width=15)
        service_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※デジタル/パッケージ/両方", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="フロア:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.floor_var = tk.StringVar()
        # フロア一覧を日本語で表示（実際の値は内部で管理）
        self.floor_combo = ttk.Combobox(search_conditions_frame, textvariable=self.floor_var, 
                                       values=["動画", "アニメ", "ゲーム", "電子書籍", "音楽", "ライブチャット", "写真集", "DVD", "Blu-ray", "CD", "書籍", "雑誌", "その他"], state="readonly", width=15)
        self.floor_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        # フロア一覧更新ボタン
        floor_update_button = ttk.Button(search_conditions_frame, text="更新", command=self.update_floor_list, width=8)
        floor_update_button.grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        ttk.Label(search_conditions_frame, text="※対象フロアを選択（更新ボタンで最新情報を取得）", font=("Arial", 8), foreground="gray").grid(row=row, column=3, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="キーワード:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.keyword_var = tk.StringVar()
        ttk.Entry(search_conditions_frame, textvariable=self.keyword_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※検索キーワード（空欄可）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="ソート:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.sort_var = tk.StringVar()
        sort_combo = ttk.Combobox(search_conditions_frame, textvariable=self.sort_var, 
                                 values=["発売日順", "名前順", "価格順", "レビュー順", "人気順"], state="readonly", width=15)
        sort_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※ソート順", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="取得件数:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.hits_var = tk.StringVar()
        ttk.Entry(search_conditions_frame, textvariable=self.hits_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※1回の検索で取得する件数（最大100）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="最大画像数:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.maximage_var = tk.StringVar()
        ttk.Entry(search_conditions_frame, textvariable=self.maximage_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※投稿に添付する最大画像数", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(search_conditions_frame, text="制限フラグ:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.limited_flag_var = tk.StringVar()
        limited_combo = ttk.Combobox(search_conditions_frame, textvariable=self.limited_flag_var, 
                                    values=["制限なし", "制限あり"], state="readonly", width=15)
        limited_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(search_conditions_frame, text="※0: 制限なし, 1: 制限あり", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 絞り込み設定
        filter_frame = ttk.LabelFrame(scrollable_frame, text="絞り込み設定", padding="15")
        filter_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        filter_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(filter_frame, text="記事タイプ:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.article_type_var = tk.StringVar()
        article_type_combo = ttk.Combobox(filter_frame, textvariable=self.article_type_var, 
                                         values=["指定なし", "女優", "ジャンル", "シリーズ"], state="readonly", width=15)
        article_type_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(filter_frame, text="※記事の種類で絞り込み", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(filter_frame, text="ID絞り込み:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.id_filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.id_filter_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(filter_frame, text="※特定のIDで絞り込み（空欄可）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 発売日絞り込み設定
        date_filter_frame = ttk.LabelFrame(scrollable_frame, text="発売日絞り込み設定", padding="15")
        date_filter_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        date_filter_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(date_filter_frame, text="発売日絞り込み:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.date_filter_enabled_var = tk.BooleanVar()
        date_filter_check = ttk.Checkbutton(date_filter_frame, text="発売日で絞り込みを有効にする", 
                                          variable=self.date_filter_enabled_var)
        date_filter_check.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(date_filter_frame, text="開始日:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.date_filter_start_var = tk.StringVar()
        ttk.Entry(date_filter_frame, textvariable=self.date_filter_start_var, width=12).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(date_filter_frame, text="※YYYY-MM-DD形式", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(date_filter_frame, text="終了日:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.date_filter_end_var = tk.StringVar()
        ttk.Entry(date_filter_frame, textvariable=self.date_filter_end_var, width=12).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(date_filter_frame, text="※YYYY-MM-DD形式", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        search_frame.columnconfigure(0, weight=1)
        search_frame.rowconfigure(0, weight=1)
    
    def create_schedule_settings_tab(self):
        """スケジュール設定タブの作成"""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="スケジュール設定")
        
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
        auto_execution_frame = ttk.LabelFrame(scrollable_frame, text="自動実行設定", padding="15")
        auto_execution_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        auto_execution_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(auto_execution_frame, text="自動実行:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.auto_on_var = tk.StringVar()
        auto_on_frame = ttk.Frame(auto_execution_frame)
        auto_on_frame.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Radiobutton(auto_on_frame, text="ON", variable=self.auto_on_var, value="on").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(auto_on_frame, text="OFF", variable=self.auto_on_var, value="off").pack(side=tk.LEFT)
        
        # 投稿対象（発売日絞り込み）
        row += 1
        ttk.Label(auto_execution_frame, text="投稿対象:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        target_frame = ttk.Frame(auto_execution_frame)
        target_frame.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        ttk.Label(target_frame, text="[直近分] 以下の期間に発売された作品を投稿対象とする", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        target_recent_frame = ttk.Frame(target_frame)
        target_recent_frame.pack(anchor=tk.W, pady=(5, 10))
        
        self.today_var = tk.BooleanVar()
        ttk.Checkbutton(target_recent_frame, text="本日", variable=self.today_var).pack(side=tk.LEFT, padx=(0, 20))
        self.threeday_var = tk.BooleanVar()
        ttk.Checkbutton(target_recent_frame, text="1日前～3日前", variable=self.threeday_var).pack(side=tk.LEFT)
        
        ttk.Label(target_frame, text="[過去分] 以下の期間に発売された作品を投稿対象とする", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
        target_past_frame = ttk.Frame(target_frame)
        target_past_frame.pack(anchor=tk.W)
        
        self.range_var = tk.BooleanVar()
        ttk.Checkbutton(target_past_frame, text="", variable=self.range_var).pack(side=tk.LEFT, padx=(0, 5))
        self.s_date_var = tk.StringVar()
        ttk.Entry(target_past_frame, textvariable=self.s_date_var, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(target_past_frame, text="～").pack(side=tk.LEFT, padx=(0, 5))
        self.e_date_var = tk.StringVar()
        ttk.Entry(target_past_frame, textvariable=self.e_date_var, width=12).pack(side=tk.LEFT)
        
        ttk.Label(target_frame, text="※DMM APIの検索結果上限は5万件", font=("Arial", 8), foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(target_frame, text="※検索結果が1万以上になると巡回の負荷が増えるため、絞り込んだ期間設定を推奨", font=("Arial", 8), foreground="gray").pack(anchor=tk.W)
        
        # 実行時刻設定
        row += 1
        ttk.Label(auto_execution_frame, text="実行時刻[時間]:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        hour_frame = ttk.Frame(auto_execution_frame)
        hour_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        # 時間選択フレームの列幅を調整
        hour_frame.columnconfigure(0, weight=1)
        hour_frame.columnconfigure(1, weight=1)
        hour_frame.columnconfigure(2, weight=1)
        hour_frame.columnconfigure(3, weight=1)
        
        # 時間選択フレームのスタイル設定
        style = ttk.Style()
        style.configure('Hour.TFrame', relief='solid', borderwidth=1)
        
        # 24時間分のチェックボックスと投稿設定選択
        self.hour_vars = {}
        self.hour_select_vars = {}
        
        # より見やすいレイアウト：4列×6行で配置
        for i in range(24):
            hour_key = f"h{i:02d}"
            hour_label = f"{i:02d}:00"
            
            # 行と列の計算（4列×6行）
            hour_row = i // 4
            hour_col = i % 4
            
            # 各時間のフレーム
            time_frame = ttk.Frame(hour_frame, style='Hour.TFrame')
            time_frame.grid(row=hour_row, column=hour_col, sticky=(tk.W, tk.E), padx=5, pady=2)
            
            # 時間のチェックボックス
            self.hour_vars[hour_key] = tk.BooleanVar()
            hour_check = ttk.Checkbutton(time_frame, text=hour_label, variable=self.hour_vars[hour_key])
            hour_check.pack(anchor=tk.W)
            
            # 投稿設定選択（1-4）
            self.hour_select_vars[hour_key] = tk.StringVar()
            select_frame = ttk.Frame(time_frame)
            select_frame.pack(fill=tk.X, pady=(2, 0))
            
            ttk.Label(select_frame, text="投稿設定:", font=("Arial", 7)).pack(side=tk.LEFT)
            for j in range(1, 5):
                ttk.Radiobutton(select_frame, text=str(j), variable=self.hour_select_vars[hour_key], 
                               value=str(j)).pack(side=tk.LEFT, padx=(0, 2))
        
        # 実行時刻[分]
        row += 1
        ttk.Label(auto_execution_frame, text="実行時刻[分]:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.exe_min_var = tk.StringVar()
        exe_min_entry = ttk.Entry(auto_execution_frame, textvariable=self.exe_min_var, width=10)
        exe_min_entry.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(auto_execution_frame, text="※0-59の範囲で指定", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 従来のスケジュール設定（互換性のため残す）
        schedule_settings_frame = ttk.LabelFrame(scrollable_frame, text="従来のスケジュール設定", padding="15")
        schedule_settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        schedule_settings_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(schedule_settings_frame, text="スケジュール有効:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.schedule_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(schedule_settings_frame, text="自動実行を有効にする", 
                       variable=self.schedule_enabled_var).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(schedule_settings_frame, text="実行間隔:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.schedule_interval_var = tk.StringVar()
        interval_combo = ttk.Combobox(schedule_settings_frame, textvariable=self.schedule_interval_var, 
                                     values=["毎分", "毎時", "毎日", "毎週", "毎月", "カスタム"], state="readonly", width=15)
        interval_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        interval_combo.bind('<<ComboboxSelected>>', self.on_interval_change)
        ttk.Label(schedule_settings_frame, text="※実行間隔を選択", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_settings_frame, text="実行時刻:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.schedule_time_var = tk.StringVar()
        time_combo = ttk.Combobox(schedule_settings_frame, textvariable=self.schedule_time_var, 
                                 values=["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"], state="readonly", width=15)
        time_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_settings_frame, text="※毎時/毎日/毎週/毎月の実行時刻", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_settings_frame, text="実行曜日:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.schedule_day_var = tk.StringVar()
        day_combo = ttk.Combobox(schedule_settings_frame, textvariable=self.schedule_day_var, 
                                values=["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"], state="readonly", width=15)
        day_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_settings_frame, text="※毎週の実行曜日", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_settings_frame, text="実行日:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.schedule_date_var = tk.StringVar()
        date_combo = ttk.Combobox(schedule_settings_frame, textvariable=self.schedule_date_var, 
                                 values=["1日", "2日", "3日", "4日", "5日", "6日", "7日", "8日", "9日", "10日", "11日", "12日", "13日", "14日", "15日", "16日", "17日", "18日", "19日", "20日", "21日", "22日", "23日", "24日", "25日", "26日", "27日", "28日", "29日", "30日", "31日"], state="readonly", width=15)
        date_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(schedule_settings_frame, text="※毎月の実行日", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(schedule_settings_frame, text="カスタムCron:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.custom_cron_var = tk.StringVar()
        ttk.Entry(schedule_settings_frame, textvariable=self.custom_cron_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(schedule_settings_frame, text="※例: */5 * * * * （5分毎）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # スクロール可能なフレームの幅を調整
        scrollable_frame.columnconfigure(0, weight=1)
        
        schedule_frame.columnconfigure(0, weight=1)
        schedule_frame.rowconfigure(0, weight=1)
    
    def create_post_settings_tab(self):
        """投稿設定タブの作成"""
        post_frame = ttk.Frame(self.notebook)
        self.notebook.add(post_frame, text="投稿設定")
        
        # 内部でタブに分ける
        post_notebook = ttk.Notebook(post_frame)
        post_notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 共通設定タブ
        self.create_common_settings_tab(post_notebook)
        
        # 投稿設定1タブ
        self.create_post_setting_tab(post_notebook, "投稿設定1", 1)
        
        # 投稿設定2タブ
        self.create_post_setting_tab(post_notebook, "投稿設定2", 2)
        
        # 投稿設定3タブ
        self.create_post_setting_tab(post_notebook, "投稿設定3", 3)
        
        # 投稿設定4タブ
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
        
        # 共通設定
        common_settings_frame = ttk.LabelFrame(scrollable_frame, text="共通設定", padding="15")
        common_settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        common_settings_frame.columnconfigure(1, weight=1)
        
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
        
        # 投稿設定フレーム
        post_settings_frame = ttk.LabelFrame(scrollable_frame, text=title, padding="15")
        post_settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        post_settings_frame.columnconfigure(1, weight=1)
        
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
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        post_frame.columnconfigure(0, weight=1)
        post_frame.rowconfigure(0, weight=1)
    
    def create_execution_tab(self):
        """実行・ログタブの作成"""
        execution_frame = ttk.Frame(self.notebook)
        self.notebook.add(execution_frame, text="実行・ログ")
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(execution_frame)
        scrollbar = ttk.Scrollbar(execution_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 監視制御フレーム
        monitoring_frame = ttk.LabelFrame(scrollable_frame, text="監視制御", padding="15")
        monitoring_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        monitoring_frame.columnconfigure(0, weight=1)
        
        row = 0
        # 監視状態表示
        self.monitoring_status_var = tk.StringVar(value="監視状態: 停止中")
        monitoring_status_label = ttk.Label(monitoring_frame, textvariable=self.monitoring_status_var, 
                                          font=("Arial", 10, "bold"), foreground="red")
        monitoring_status_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        row += 1
        # 監視制御ボタン
        start_monitoring_button = ttk.Button(monitoring_frame, text="監視開始", 
                                           command=self.start_monitoring, style="Accent.TButton")
        start_monitoring_button.grid(row=row, column=0, padx=(0, 10), pady=5)
        
        stop_monitoring_button = ttk.Button(monitoring_frame, text="監視停止", 
                                          command=self.stop_monitoring, style="Accent.TButton")
        stop_monitoring_button.grid(row=row, column=1, padx=(0, 10), pady=5)
        
        # 自動実行設定の表示
        auto_status_text = "自動実行: OFF"
        if hasattr(self, 'auto_on_var') and self.auto_on_var.get() == "on":
            auto_status_text = "自動実行: ON"
        
        auto_status_label = ttk.Label(monitoring_frame, text=auto_status_text, 
                                     font=("Arial", 9), foreground="blue")
        auto_status_label.grid(row=row, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        
        # 実行ボタンフレーム
        execution_buttons_frame = ttk.LabelFrame(scrollable_frame, text="実行制御", padding="15")
        execution_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        execution_buttons_frame.columnconfigure(0, weight=1)
        
        row = 0
        run_once_button = ttk.Button(execution_buttons_frame, text="1回実行", 
                                    command=self.run_once, style="Accent.TButton")
        run_once_button.grid(row=row, column=0, padx=(0, 10), pady=5)
        
        test_button = ttk.Button(execution_buttons_frame, text="テスト実行", 
                                command=self.run_test, style="Accent.TButton")
        test_button.grid(row=row, column=1, padx=(0, 10), pady=5)
        
        schedule_button = ttk.Button(execution_buttons_frame, text="スケジュール開始", 
                                    command=self.toggle_schedule, style="Accent.TButton")
        schedule_button.grid(row=row, column=2, padx=(0, 10), pady=5)
        
        self.schedule_status_var = tk.StringVar(value="停止中")
        ttk.Label(execution_buttons_frame, textvariable=self.schedule_status_var, 
                 font=("Arial", 10, "bold")).grid(row=row, column=3, padx=(20, 0), pady=5)
        
        # 投稿設定選択
        row += 1
        ttk.Label(execution_buttons_frame, text="投稿設定:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        # 確実に変数を作成
        if not hasattr(self, 'selected_post_setting_var'):
            self.selected_post_setting_var = tk.StringVar(value="1")
        post_setting_combo = ttk.Combobox(execution_buttons_frame, textvariable=self.selected_post_setting_var, 
                                         values=["1", "2", "3", "4"], state="readonly", width=5)
        post_setting_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(execution_buttons_frame, text="※1回実行・テスト実行で使用する投稿設定", 
                 font=("Arial", 8), foreground="gray").grid(row=row, column=2, columnspan=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # ログフレーム
        log_frame = ttk.LabelFrame(scrollable_frame, text="実行ログ", padding="15")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=15, pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # ログテキスト
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, 
                                                font=("Consolas", 8), wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # ログクリアボタン
        clear_button = ttk.Button(log_frame, text="ログをクリア", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=(0, 5))
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        execution_frame.columnconfigure(0, weight=1)
        execution_frame.rowconfigure(0, weight=1)
    
    def set_default_values(self):
        """GUI変数のデフォルト値を設定"""
        try:
            # 基本設定
            if hasattr(self, 'dmm_api_id_var') and not self.dmm_api_id_var.get():
                self.dmm_api_id_var.set("")
            if hasattr(self, 'dmm_affiliate_id_var') and not self.dmm_affiliate_id_var.get():
                self.dmm_affiliate_id_var.set("")
            if hasattr(self, 'wp_url_var') and not self.wp_url_var.get():
                self.wp_url_var.set("")
            if hasattr(self, 'wp_username_var') and not self.wp_username_var.get():
                self.wp_username_var.set("")
            if hasattr(self, 'wp_app_password_var') and not self.wp_app_password_var.get():
                self.wp_app_password_var.set("")
            if hasattr(self, 'page_wait_sec_var') and not self.page_wait_sec_var.get():
                self.page_wait_sec_var.set("5")
        
            # 検索設定
            if hasattr(self, 'site_var') and not self.site_var.get():
                self.site_var.set("FANZA")
            if hasattr(self, 'service_var') and not self.service_var.get():
                self.service_var.set("digital")
            if hasattr(self, 'floor_var') and not self.floor_var.get():
                self.floor_var.set("動画")
            if hasattr(self, 'hits_var') and not self.hits_var.get():
                self.hits_var.set("10")
            if hasattr(self, 'maximage_var') and not self.maximage_var.get():
                self.maximage_var.set("1")
            if hasattr(self, 'limited_flag_var') and not self.limited_flag_var.get():
                self.limited_flag_var.set("0")
            if hasattr(self, 'keyword_var') and not self.keyword_var.get():
                self.keyword_var.set("")
            if hasattr(self, 'sort_var') and not self.sort_var.get():
                self.sort_var.set("date")
        
            # スケジュール設定
            if hasattr(self, 'schedule_enabled_var') and not self.schedule_enabled_var.get():
                self.schedule_enabled_var.set(False)
            if hasattr(self, 'schedule_interval_var') and not self.schedule_interval_var.get():
                self.schedule_interval_var.set("毎日")
            if hasattr(self, 'schedule_time_var') and not self.schedule_time_var.get():
                self.schedule_time_var.set("00:00")
            if hasattr(self, 'schedule_day_var') and not self.schedule_day_var.get():
                self.schedule_day_var.set("月曜日")
            if hasattr(self, 'schedule_date_var') and not self.schedule_date_var.get():
                self.schedule_date_var.set("1日")
            if hasattr(self, 'custom_cron_var') and not self.custom_cron_var.get():
                self.custom_cron_var.set("")
        
            # 投稿設定1から4のデフォルト値は別メソッドで設定
            try:
                self.set_default_post_settings()
            except Exception as e:
                print(f"投稿設定デフォルト値設定エラー: {e}")
        
            # 共通設定のデフォルト値は別メソッドで設定
            try:
                self.set_default_common_settings()
            except Exception as e:
                print(f"共通設定デフォルト値設定エラー: {e}")
        
            # 自動実行設定のデフォルト値は別メソッドで設定
            try:
                self.set_default_auto_execution_settings()
            except Exception as e:
                print(f"自動実行設定デフォルト値設定エラー: {e}")
        
            # 絞り込み設定のデフォルト値は別メソッドで設定
            try:
                self.set_default_filter_settings()
            except Exception as e:
                print(f"絞り込み設定デフォルト値設定エラー: {e}")
            
            # 実行設定のデフォルト値
            if hasattr(self, 'selected_post_setting_var'):
                if not self.selected_post_setting_var.get():
                    self.selected_post_setting_var.set("1")
            else:
                # selected_post_setting_varが存在しない場合は作成
                self.selected_post_setting_var = tk.StringVar(value="1")
                
        except Exception as e:
            print(f"デフォルト値設定エラー: {e}")
            import traceback
            print(f"エラー詳細: {traceback.format_exc()}")
    
    def set_default_post_settings(self):
        """投稿設定1から4のデフォルト値を設定"""
        try:
            # 投稿設定1のデフォルト値
            self.post_title_1_var.set("[title]")
            self.post_content_text1.delete("1.0", tk.END)
            self.post_content_text1.insert("1.0", "[title]の詳細情報です。")
            self.post_eyecatch_1_var.set("sample")
            self.post_movie_size_1_var.set("auto")
            self.post_poster_1_var.set("package")
            self.post_category_1_var.set("jan")
            self.post_sort_1_var.set("rank")
            self.post_article_1_var.set("")
            self.post_status_1_var.set("publish")
            self.post_hour_1_var.set("h09")
            self.post_overwrite_existing_1_var.set(False)
            self.target_new_posts_1_var.set("10")
            
            # 投稿設定2のデフォルト値
            self.post_title_2_var.set("[title]")
            self.post_content_text2.delete("1.0", tk.END)
            self.post_content_text2.insert("1.0", "[title]の詳細情報です。設定2")
            self.post_eyecatch_2_var.set("sample")
            self.post_movie_size_2_var.set("auto")
            self.post_poster_2_var.set("package")
            self.post_category_2_var.set("jan")
            self.post_sort_2_var.set("rank")
            self.post_article_2_var.set("")
            self.post_status_2_var.set("publish")
            self.post_hour_2_var.set("h09")
            self.post_overwrite_existing_2_var.set(False)
            self.target_new_posts_2_var.set("10")
            
            # 投稿設定3のデフォルト値
            self.post_title_3_var.set("[title]")
            self.post_content_text3.delete("1.0", tk.END)
            self.post_content_text3.insert("1.0", "[title]の詳細情報です。設定3")
            self.post_eyecatch_3_var.set("sample")
            self.post_movie_size_3_var.set("auto")
            self.post_poster_3_var.set("package")
            self.post_category_3_var.set("jan")
            self.post_sort_3_var.set("rank")
            self.post_article_3_var.set("")
            self.post_status_3_var.set("publish")
            self.post_hour_3_var.set("h09")
            self.post_overwrite_existing_3_var.set(False)
            self.target_new_posts_3_var.set("10")
            
            # 投稿設定4のデフォルト値
            self.post_title_4_var.set("[title]")
            self.post_content_text4.delete("1.0", tk.END)
            self.post_content_text4.insert("1.0", "[title]の詳細情報です。設定4")
            self.post_eyecatch_4_var.set("sample")
            self.post_movie_size_4_var.set("auto")
            self.post_poster_4_var.set("package")
            self.post_category_4_var.set("jan")
            self.post_sort_4_var.set("rank")
            self.post_article_4_var.set("")
            self.post_status_4_var.set("publish")
            self.post_hour_4_var.set("h09")
            self.post_overwrite_existing_4_var.set(False)
            self.target_new_posts_4_var.set("10")
            
            self.log_message("投稿設定1から4のデフォルト値を設定しました")
            
        except Exception as e:
            self.log_message(f"投稿設定デフォルト値設定エラー: {e}")
    
    def set_default_common_settings(self):
        """共通設定のデフォルト値を設定"""
        try:
            # 共通設定のデフォルト値
            self.excerpt_template_var.set("[title]の詳細情報です。")
            self.max_sample_images_var.set("1")
            self.categories_var.set("")
            self.tags_var.set("")
            self.affiliate1_text_var.set("詳細を見る")
            self.affiliate1_color_var.set("#FFFFFF")
            self.affiliate1_bg_var.set("#FF6B6B")
            self.affiliate2_text_var.set("購入する")
            self.affiliate2_color_var.set("#FFFFFF")
            self.affiliate2_bg_var.set("#4ECDC4")
            self.post_date_setting_var.set("本日")
            self.random_text1_var.set("")
            self.random_text2_var.set("")
            self.random_text3_var.set("")
            
            self.log_message("共通設定のデフォルト値を設定しました")
            
        except Exception as e:
            self.log_message(f"共通設定デフォルト値設定エラー: {e}")
    
    def set_default_auto_execution_settings(self):
        """自動実行設定のデフォルト値を設定"""
        try:
            # 自動実行設定のデフォルト値
            self.auto_on_var.set("off")
            self.today_var.set(True)
            self.threeday_var.set(False)
            self.range_var.set(False)
            self.s_date_var.set("")
            self.e_date_var.set("")
            self.exe_min_var.set("0")
            
            # 24時間分のチェックボックスと投稿設定選択のデフォルト値
            for i in range(24):
                hour_key = f"h{i:02d}"
                self.hour_vars[hour_key].set(False)
                self.hour_select_vars[hour_key].set("1")
            
            self.log_message("自動実行設定のデフォルト値を設定しました")
            
        except Exception as e:
            self.log_message(f"自動実行設定デフォルト値設定エラー: {e}")
    
    def set_default_filter_settings(self):
        """絞り込み設定のデフォルト値を設定"""
        try:
            # 絞り込み設定のデフォルト値
            self.article_type_var.set("")
            self.id_filter_var.set("")
            self.date_filter_enabled_var.set(False)
            self.date_filter_start_var.set("")
            self.date_filter_end_var.set("")
            
            self.log_message("絞り込み設定のデフォルト値を設定しました")
            
        except Exception as e:
            self.log_message(f"絞り込み設定デフォルト値設定エラー: {e}")
    
    def on_interval_change(self, event=None):
        """実行間隔が変更された時の処理"""
        interval = self.schedule_interval_var.get()
        
        # 間隔に応じて関連する設定項目の有効/無効を制御
        if interval == "毎分":
            # 毎分の場合は時刻、曜日、日付は不要
            self.schedule_time_var.set("")
            self.schedule_day_var.set("")
            self.schedule_date_var.set("")
            # カスタムCronもクリア
            self.custom_cron_var.set("")
        elif interval == "毎時":
            # 毎時の場合は時刻のみ必要
            if not self.schedule_time_var.get() or ":" not in self.schedule_time_var.get():
                self.schedule_time_var.set("00:00")
            self.schedule_day_var.set("")
            self.schedule_date_var.set("")
            self.custom_cron_var.set("")
        elif interval == "毎日":
            # 毎日の場合は時刻のみ必要
            if not self.schedule_time_var.get() or ":" not in self.schedule_time_var.get():
                self.schedule_time_var.set("00:00")
            self.schedule_day_var.set("")
            self.schedule_date_var.set("")
            self.custom_cron_var.set("")
        elif interval == "毎週":
            # 毎週の場合は時刻と曜日が必要
            if not self.schedule_time_var.get() or ":" not in self.schedule_time_var.get():
                self.schedule_time_var.set("00:00")
            if not self.schedule_day_var.get() or self.schedule_day_var.get() == "毎日":
                self.schedule_day_var.set("月曜日")
            self.schedule_date_var.set("")
            self.custom_cron_var.set("")
        elif interval == "毎月":
            # 毎月の場合は時刻と日付が必要
            if not self.schedule_time_var.get() or ":" not in self.schedule_time_var.get():
                self.schedule_time_var.set("00:00")
            self.schedule_day_var.set("")
            if not self.schedule_date_var.get() or self.schedule_date_var.get() == "毎日":
                self.schedule_date_var.set("1日")
            self.custom_cron_var.set("")
        elif interval == "カスタム":
            # カスタムの場合は他の設定は無効化
            self.schedule_time_var.set("")
            self.schedule_day_var.set("")
            self.schedule_date_var.set("")
            if not self.custom_cron_var.get():
                self.custom_cron_var.set("*/30 * * * *")
        
        self.log_message(f"スケジュール間隔を {interval} に変更しました")
    
    def load_settings_to_gui(self):
        """設定をGUIに読み込む"""
        try:
            # 基本設定の読み込み
            self.dmm_api_id_var.set(self.settings.dmm_api_id or "")
            self.dmm_affiliate_id_var.set(self.settings.dmm_affiliate_id or "")
            self.wp_url_var.set(self.settings.wp_base_url or "")
            self.wp_username_var.set(self.settings.wp_username or "")
            self.wp_app_password_var.set(self.settings.wp_app_password or "")
            self.page_wait_sec_var.set(str(self.settings.page_wait_sec or "5"))
            
            # サイト設定を日本語表示に変換
            site_value = self.settings.site or "FANZA"
            if site_value == "FANZA":
                self.site_var.set("FANZA")
            elif site_value == "DMM":
                self.site_var.set("FANZA通販")
            else:
                self.site_var.set(site_value)
            
            # サービス設定を日本語表示に変換
            service_value = self.settings.service or "digital"
            if service_value == "digital":
                self.service_var.set("デジタル")
            elif service_value == "package":
                self.service_var.set("パッケージ")
            elif service_value == "both":
                self.service_var.set("両方")
            else:
                self.service_var.set(service_value)
            
            # フロア設定を日本語表示に変換
            floor_value = self.settings.floor or "videoc"
            if floor_value == "videoc":
                self.floor_var.set("動画")
            elif floor_value == "videoa":
                self.floor_var.set("アニメ")
            elif floor_value == "videob":
                self.floor_var.set("ゲーム")
            elif floor_value == "videod":
                self.floor_var.set("電子書籍")
            elif floor_value == "videoe":
                self.floor_var.set("音楽")
            elif floor_value == "videof":
                self.floor_var.set("ライブチャット")
            elif floor_value == "videog":
                self.floor_var.set("写真集")
            elif floor_value == "videoh":
                self.floor_var.set("DVD")
            elif floor_value == "videoi":
                self.floor_var.set("Blu-ray")
            elif floor_value == "videoj":
                self.floor_var.set("CD")
            elif floor_value == "videok":
                self.floor_var.set("書籍")
            elif floor_value == "videol":
                self.floor_var.set("雑誌")
            elif floor_value == "videom":
                self.floor_var.set("その他")  # その他の場合はvideomを使用
            else:
                self.floor_var.set("videoc")  # デフォルト値
            
            # 取得件数を日本語表示に変換
            hits_value = str(self.settings.hits or "10")
            self.hits_var.set(hits_value)
            
            # ソート設定を日本語表示に変換
            sort_value = self.settings.sort or "date"
            if sort_value == "date":
                self.sort_var.set("発売日順")
            elif sort_value == "name":
                self.sort_var.set("名前順")
            elif sort_value == "price":
                self.sort_var.set("価格順")
            elif sort_value == "review":
                self.sort_var.set("レビュー順")
            elif sort_value == "rank":
                self.sort_var.set("人気順")
            else:
                self.sort_var.set(sort_value)
            
            # 制限フラグ設定を日本語表示に変換
            limited_value = str(self.settings.limited_flag or "0")
            if limited_value == "0":
                self.limited_flag_var.set("制限なし")
            elif limited_value == "1":
                self.limited_flag_var.set("制限あり")
            else:
                self.limited_flag_var.set(limited_value)
            
            # 記事タイプ設定を日本語表示に変換
            article_type_value = self.settings.article_type or ""
            if article_type_value == "":
                self.article_type_var.set("指定なし")
            elif article_type_value == "actress":
                self.article_type_var.set("女優")
            elif article_type_value == "genre":
                self.article_type_var.set("ジャンル")
            elif article_type_value == "series":
                self.article_type_var.set("シリーズ")
            else:
                self.article_type_var.set(article_type_value)
            
            self.keyword_var.set(self.settings.keyword or "")
            self.maximage_var.set(str(self.settings.maximage or "1"))
            
            # スケジュール設定の読み込み（環境変数から、なければデフォルト値）
            self.schedule_enabled_var.set(os.getenv("SCHEDULE_ENABLED", "false").lower() == "true")
            self.schedule_interval_var.set(os.getenv("SCHEDULE_INTERVAL", "毎日"))
            self.schedule_time_var.set(os.getenv("SCHEDULE_TIME", "00:00"))
            self.schedule_day_var.set(os.getenv("SCHEDULE_DAY", "毎日"))
            self.schedule_date_var.set(os.getenv("SCHEDULE_DATE", ""))
            self.custom_cron_var.set(os.getenv("CUSTOM_CRON", ""))
            
            # 投稿設定1から4の読み込み（SettingsManagerから）
            try:
                post_settings = self.settings_manager.load_post_settings()
                
                # post_settingsキーから投稿設定を取得
                if "post_settings" in post_settings:
                    settings_data = post_settings["post_settings"]
                    
                    # 投稿設定1
                    if "1" in settings_data:
                        setting = settings_data["1"]
                        self.post_title_1_var.set(setting.get("title", "[title]"))
                        self.post_content_text1.delete("1.0", tk.END)
                        content = setting.get("content", "[title]の詳細情報です。設定1")
                        self.post_content_text1.insert("1.0", content)
                        
                        # アイキャッチ設定を日本語表示に変換
                        eyecatch_value = setting.get("eyecatch", "sample")
                        if eyecatch_value == "sample":
                            self.post_eyecatch_1_var.set("サンプル画像")
                        elif eyecatch_value == "package":
                            self.post_eyecatch_1_var.set("パッケージ画像")
                        elif eyecatch_value == "1":
                            self.post_eyecatch_1_var.set("画像1")
                        elif eyecatch_value == "99":
                            self.post_eyecatch_1_var.set("画像99")
                        else:
                            self.post_eyecatch_1_var.set(eyecatch_value)
                        
                        # 動画サイズ設定を日本語表示に変換
                        movie_size_value = setting.get("movie_size", "auto")
                        if movie_size_value == "auto":
                            self.post_movie_size_1_var.set("自動")
                        elif movie_size_value == "720":
                            self.post_movie_size_1_var.set("720p")
                        elif movie_size_value == "600":
                            self.post_movie_size_1_var.set("600p")
                        elif movie_size_value == "560":
                            self.post_movie_size_1_var.set("560p")
                        else:
                            self.post_movie_size_1_var.set(movie_size_value)
                        
                        # ポスター設定を日本語表示に変換
                        poster_value = setting.get("poster", "package")
                        if poster_value == "package":
                            self.post_poster_1_var.set("パッケージ画像")
                        elif poster_value == "sample":
                            self.post_poster_1_var.set("サンプル画像")
                        elif poster_value == "none":
                            self.post_poster_1_var.set("なし")
                        else:
                            self.post_poster_1_var.set(poster_value)
                        
                        # カテゴリ設定を日本語表示に変換
                        category_value = setting.get("category", "jan")
                        if category_value == "jan":
                            self.post_category_1_var.set("JAN")
                        elif category_value == "act":
                            self.post_category_1_var.set("女優")
                        elif category_value == "director":
                            self.post_category_1_var.set("監督")
                        elif category_value == "seri":
                            self.post_category_1_var.set("シリーズ")
                        else:
                            self.post_category_1_var.set(category_value)
                        
                        # ソート設定を日本語表示に変換
                        sort_value = setting.get("sort", "rank")
                        if sort_value == "rank":
                            self.post_sort_1_var.set("人気順")
                        elif sort_value == "date":
                            self.post_sort_1_var.set("発売日順")
                        elif sort_value == "review":
                            self.post_sort_1_var.set("レビュー順")
                        elif sort_value == "price":
                            self.post_sort_1_var.set("価格順")
                        else:
                            self.post_sort_1_var.set(sort_value)
                        
                        # 記事設定を日本語表示に変換
                        article_value = setting.get("article", "")
                        if article_value == "":
                            self.post_article_1_var.set("指定なし")
                        elif article_value == "actress":
                            self.post_article_1_var.set("女優")
                        elif article_value == "genre":
                            self.post_article_1_var.set("ジャンル")
                        elif article_value == "series":
                            self.post_article_1_var.set("シリーズ")
                        else:
                            self.post_article_1_var.set(article_value)
                        
                        # ステータス設定を日本語表示に変換
                        status_value = setting.get("status", "publish")
                        if status_value == "publish":
                            self.post_status_1_var.set("公開")
                        elif status_value == "draft":
                            self.post_status_1_var.set("下書き")
                        else:
                            self.post_status_1_var.set(status_value)
                        
                        # 時間設定を日本語表示に変換
                        hour_value = setting.get("hour", "h09")
                        if hour_value == "h09":
                            self.post_hour_1_var.set("09:00")
                        elif hour_value == "h12":
                            self.post_hour_1_var.set("12:00")
                        elif hour_value == "h18":
                            self.post_hour_1_var.set("18:00")
                        elif hour_value == "h21":
                            self.post_hour_1_var.set("21:00")
                        else:
                            self.post_hour_1_var.set(hour_value)
                        
                        self.post_overwrite_existing_1_var.set(setting.get("overwrite_existing", False))
                        self.target_new_posts_1_var.set(str(setting.get("target_new_posts", 10)))
                    
                    # 投稿設定2
                    if "2" in settings_data:
                        setting = settings_data["2"]
                        self.post_title_2_var.set(setting.get("title", "[title]"))
                        self.post_content_text2.delete("1.0", tk.END)
                        content = setting.get("content", "[title]の詳細情報です。設定2")
                        self.post_content_text2.insert("1.0", content)
                        
                        # アイキャッチ設定を日本語表示に変換
                        eyecatch_value = setting.get("eyecatch", "sample")
                        if eyecatch_value == "sample":
                            self.post_eyecatch_2_var.set("サンプル画像")
                        elif eyecatch_value == "package":
                            self.post_eyecatch_2_var.set("パッケージ画像")
                        elif eyecatch_value == "1":
                            self.post_eyecatch_2_var.set("画像1")
                        elif eyecatch_value == "99":
                            self.post_eyecatch_2_var.set("画像99")
                        else:
                            self.post_eyecatch_2_var.set(eyecatch_value)
                        
                        # 動画サイズ設定を日本語表示に変換
                        movie_size_value = setting.get("movie_size", "auto")
                        if movie_size_value == "auto":
                            self.post_movie_size_2_var.set("自動")
                        elif movie_size_value == "720":
                            self.post_movie_size_2_var.set("720p")
                        elif movie_size_value == "600":
                            self.post_movie_size_2_var.set("600p")
                        elif movie_size_value == "560":
                            self.post_movie_size_2_var.set("560p")
                        else:
                            self.post_movie_size_2_var.set(movie_size_value)
                        
                        # ポスター設定を日本語表示に変換
                        poster_value = setting.get("poster", "package")
                        if poster_value == "package":
                            self.post_poster_2_var.set("パッケージ画像")
                        elif poster_value == "sample":
                            self.post_poster_2_var.set("サンプル画像")
                        elif poster_value == "none":
                            self.post_poster_2_var.set("なし")
                        else:
                            self.post_poster_2_var.set(poster_value)
                        
                        # カテゴリ設定を日本語表示に変換
                        category_value = setting.get("category", "jan")
                        if category_value == "jan":
                            self.post_category_2_var.set("JAN")
                        elif category_value == "act":
                            self.post_category_2_var.set("女優")
                        elif category_value == "director":
                            self.post_category_2_var.set("監督")
                        elif category_value == "seri":
                            self.post_category_2_var.set("シリーズ")
                        else:
                            self.post_category_2_var.set(category_value)
                        
                        # ソート設定を日本語表示に変換
                        sort_value = setting.get("sort", "rank")
                        if sort_value == "rank":
                            self.post_sort_2_var.set("人気順")
                        elif sort_value == "date":
                            self.post_sort_2_var.set("発売日順")
                        elif sort_value == "review":
                            self.post_sort_2_var.set("レビュー順")
                        elif sort_value == "price":
                            self.post_sort_2_var.set("価格順")
                        else:
                            self.post_sort_2_var.set(sort_value)
                        
                        # 記事設定を日本語表示に変換
                        article_value = setting.get("article", "")
                        if article_value == "":
                            self.post_article_2_var.set("指定なし")
                        elif article_value == "actress":
                            self.post_article_2_var.set("女優")
                        elif article_value == "genre":
                            self.post_article_2_var.set("ジャンル")
                        elif article_value == "series":
                            self.post_article_2_var.set("シリーズ")
                        else:
                            self.post_article_2_var.set(article_value)
                        
                        # ステータス設定を日本語表示に変換
                        status_value = setting.get("status", "publish")
                        if status_value == "publish":
                            self.post_status_2_var.set("公開")
                        elif status_value == "draft":
                            self.post_status_2_var.set("下書き")
                        else:
                            self.post_status_2_var.set(status_value)
                        
                        # 時間設定を日本語表示に変換
                        hour_value = setting.get("hour", "h09")
                        if hour_value == "h09":
                            self.post_hour_2_var.set("09:00")
                        elif hour_value == "h12":
                            self.post_hour_2_var.set("12:00")
                        elif hour_value == "h18":
                            self.post_hour_2_var.set("18:00")
                        elif hour_value == "h21":
                            self.post_hour_2_var.set("21:00")
                        else:
                            self.post_hour_2_var.set(hour_value)
                        
                        self.post_overwrite_existing_2_var.set(setting.get("overwrite_existing", False))
                        self.target_new_posts_2_var.set(str(setting.get("target_new_posts", 10)))
                    
                    # 投稿設定3
                    if "3" in settings_data:
                        setting = settings_data["3"]
                        self.post_title_3_var.set(setting.get("title", "[title]"))
                        self.post_content_text3.delete("1.0", tk.END)
                        content = setting.get("content", "[title]の詳細情報です。設定3")
                        self.post_content_text3.insert("1.0", content)
                        
                        # アイキャッチ設定を日本語表示に変換
                        eyecatch_value = setting.get("eyecatch", "sample")
                        if eyecatch_value == "sample":
                            self.post_eyecatch_3_var.set("サンプル画像")
                        elif eyecatch_value == "package":
                            self.post_eyecatch_3_var.set("パッケージ画像")
                        elif eyecatch_value == "1":
                            self.post_eyecatch_3_var.set("画像1")
                        elif eyecatch_value == "99":
                            self.post_eyecatch_3_var.set("画像99")
                        else:
                            self.post_eyecatch_3_var.set(eyecatch_value)
                        
                        # 動画サイズ設定を日本語表示に変換
                        movie_size_value = setting.get("movie_size", "auto")
                        if movie_size_value == "auto":
                            self.post_movie_size_3_var.set("自動")
                        elif movie_size_value == "720":
                            self.post_movie_size_3_var.set("720p")
                        elif movie_size_value == "600":
                            self.post_movie_size_3_var.set("600p")
                        elif movie_size_value == "560":
                            self.post_movie_size_3_var.set("560p")
                        else:
                            self.post_movie_size_3_var.set(movie_size_value)
                        
                        # ポスター設定を日本語表示に変換
                        poster_value = setting.get("poster", "package")
                        if poster_value == "package":
                            self.post_poster_3_var.set("パッケージ画像")
                        elif poster_value == "sample":
                            self.post_poster_3_var.set("サンプル画像")
                        elif poster_value == "none":
                            self.post_poster_3_var.set("なし")
                        else:
                            self.post_poster_3_var.set(poster_value)
                        
                        # カテゴリ設定を日本語表示に変換
                        category_value = setting.get("category", "jan")
                        if category_value == "jan":
                            self.post_category_3_var.set("JAN")
                        elif category_value == "act":
                            self.post_category_3_var.set("女優")
                        elif category_value == "director":
                            self.post_category_3_var.set("監督")
                        elif category_value == "seri":
                            self.post_category_3_var.set("シリーズ")
                        else:
                            self.post_category_3_var.set(category_value)
                        
                        # ソート設定を日本語表示に変換
                        sort_value = setting.get("sort", "rank")
                        if sort_value == "rank":
                            self.post_sort_3_var.set("人気順")
                        elif sort_value == "date":
                            self.post_sort_3_var.set("発売日順")
                        elif sort_value == "review":
                            self.post_sort_3_var.set("レビュー順")
                        elif sort_value == "price":
                            self.post_sort_3_var.set("価格順")
                        else:
                            self.post_sort_3_var.set(sort_value)
                        
                        # 記事設定を日本語表示に変換
                        article_value = setting.get("article", "")
                        if article_value == "":
                            self.post_article_3_var.set("指定なし")
                        elif article_value == "actress":
                            self.post_article_3_var.set("女優")
                        elif article_value == "genre":
                            self.post_article_3_var.set("ジャンル")
                        elif article_value == "series":
                            self.post_article_3_var.set("シリーズ")
                        else:
                            self.post_article_3_var.set(article_value)
                        
                        # ステータス設定を日本語表示に変換
                        status_value = setting.get("status", "publish")
                        if status_value == "publish":
                            self.post_status_3_var.set("公開")
                        elif status_value == "draft":
                            self.post_status_3_var.set("下書き")
                        else:
                            self.post_status_3_var.set(status_value)
                        
                        # 時間設定を日本語表示に変換
                        hour_value = setting.get("hour", "h09")
                        if hour_value == "h09":
                            self.post_hour_3_var.set("09:00")
                        elif hour_value == "h12":
                            self.post_hour_3_var.set("12:00")
                        elif hour_value == "h18":
                            self.post_hour_3_var.set("18:00")
                        elif hour_value == "h21":
                            self.post_hour_3_var.set("21:00")
                        else:
                            self.post_hour_3_var.set(hour_value)
                        
                        self.post_overwrite_existing_3_var.set(setting.get("overwrite_existing", False))
                        self.target_new_posts_3_var.set(str(setting.get("target_new_posts", 10)))
                    
                    # 投稿設定4
                    if "4" in settings_data:
                        setting = settings_data["4"]
                        self.post_title_4_var.set(setting.get("title", "[title]"))
                        self.post_content_text4.delete("1.0", tk.END)
                        content = setting.get("content", "[title]の詳細情報です。設定4")
                        self.post_content_text4.insert("1.0", content)
                        
                        # アイキャッチ設定を日本語表示に変換
                        eyecatch_value = setting.get("eyecatch", "sample")
                        if eyecatch_value == "sample":
                            self.post_eyecatch_4_var.set("サンプル画像")
                        elif eyecatch_value == "package":
                            self.post_eyecatch_4_var.set("パッケージ画像")
                        elif eyecatch_value == "1":
                            self.post_eyecatch_4_var.set("画像1")
                        elif eyecatch_value == "99":
                            self.post_eyecatch_4_var.set("画像99")
                        else:
                            self.post_eyecatch_4_var.set(eyecatch_value)
                        
                        # 動画サイズ設定を日本語表示に変換
                        movie_size_value = setting.get("movie_size", "auto")
                        if movie_size_value == "auto":
                            self.post_movie_size_4_var.set("自動")
                        elif movie_size_value == "720":
                            self.post_movie_size_4_var.set("720p")
                        elif movie_size_value == "600":
                            self.post_movie_size_4_var.set("600p")
                        elif movie_size_value == "560":
                            self.post_movie_size_4_var.set("560p")
                        else:
                            self.post_movie_size_4_var.set(movie_size_value)
                        
                        # ポスター設定を日本語表示に変換
                        poster_value = setting.get("poster", "package")
                        if poster_value == "package":
                            self.post_poster_4_var.set("パッケージ画像")
                        elif poster_value == "sample":
                            self.post_poster_4_var.set("サンプル画像")
                        elif poster_value == "none":
                            self.post_poster_4_var.set("なし")
                        else:
                            self.post_poster_4_var.set(poster_value)
                        
                        # カテゴリ設定を日本語表示に変換
                        category_value = setting.get("category", "jan")
                        if category_value == "jan":
                            self.post_category_4_var.set("JAN")
                        elif category_value == "act":
                            self.post_category_4_var.set("女優")
                        elif category_value == "director":
                            self.post_category_4_var.set("監督")
                        elif category_value == "seri":
                            self.post_category_4_var.set("シリーズ")
                        else:
                            self.post_category_4_var.set(category_value)
                        
                        # ソート設定を日本語表示に変換
                        sort_value = setting.get("sort", "rank")
                        if sort_value == "rank":
                            self.post_sort_4_var.set("人気順")
                        elif sort_value == "date":
                            self.post_sort_4_var.set("発売日順")
                        elif sort_value == "review":
                            self.post_sort_4_var.set("レビュー順")
                        elif sort_value == "price":
                            self.post_sort_4_var.set("価格順")
                        else:
                            self.post_sort_4_var.set(sort_value)
                        
                        # 記事設定を日本語表示に変換
                        article_value = setting.get("article", "")
                        if article_value == "":
                            self.post_article_4_var.set("指定なし")
                        elif article_value == "actress":
                            self.post_article_4_var.set("女優")
                        elif article_value == "genre":
                            self.post_article_4_var.set("ジャンル")
                        elif article_value == "series":
                            self.post_article_4_var.set("シリーズ")
                        else:
                            self.post_article_4_var.set(article_value)
                        
                        # ステータス設定を日本語表示に変換
                        status_value = setting.get("status", "publish")
                        if status_value == "publish":
                            self.post_status_4_var.set("公開")
                        elif status_value == "draft":
                            self.post_status_4_var.set("下書き")
                        else:
                            self.post_status_4_var.set(status_value)
                        
                        # 時間設定を日本語表示に変換
                        hour_value = setting.get("hour", "h09")
                        if hour_value == "h09":
                            self.post_hour_4_var.set("09:00")
                        elif hour_value == "h12":
                            self.post_hour_4_var.set("12:00")
                        elif hour_value == "h18":
                            self.post_hour_4_var.set("18:00")
                        elif hour_value == "h21":
                            self.post_hour_4_var.set("21:00")
                        else:
                            self.post_hour_4_var.set(hour_value)
                        
                        self.post_overwrite_existing_4_var.set(setting.get("overwrite_existing", False))
                        self.target_new_posts_4_var.set(str(setting.get("target_new_posts", 10)))
                    
                    self.log_message("投稿設定1から4を読み込みました")
                else:
                    self.log_message("投稿設定が見つかりません。デフォルト値を設定します。")
                    self.set_default_post_settings()
                
            except Exception as e:
                self.log_message(f"投稿設定読み込みエラー: {e}")
                # エラーが発生した場合はデフォルト値を設定
                self.set_default_post_settings()
            
            # 共通設定の読み込み（環境変数から、なければデフォルト値）
            try:
                self.excerpt_template_var.set(os.getenv("EXCERPT_TEMPLATE", "[title]の詳細情報です。"))
                self.max_sample_images_var.set(os.getenv("MAX_SAMPLE_IMAGES", "1"))
                self.categories_var.set(os.getenv("CATEGORIES", ""))
                self.tags_var.set(os.getenv("TAGS", ""))
                self.affiliate1_text_var.set(os.getenv("AFFILIATE1_TEXT", "詳細を見る"))
                self.affiliate1_color_var.set(os.getenv("AFFILIATE1_COLOR", "#FFFFFF"))
                self.affiliate1_bg_var.set(os.getenv("AFFILIATE1_BG", "#FF6B6B"))
                self.affiliate2_text_var.set(os.getenv("AFFILIATE2_TEXT", "購入する"))
                self.affiliate2_color_var.set(os.getenv("AFFILIATE2_COLOR", "#FFFFFF"))
                self.affiliate2_bg_var.set(os.getenv("AFFILIATE2_BG", "#4ECDC4"))
                self.post_date_setting_var.set(os.getenv("POST_DATE_SETTING", "本日"))
                self.random_text1_var.set(os.getenv("RANDOM_TEXT1", ""))
                self.random_text2_var.set(os.getenv("RANDOM_TEXT2", ""))
                self.random_text3_var.set(os.getenv("RANDOM_TEXT3", ""))
                
                self.log_message("共通設定を読み込みました")
                
            except Exception as e:
                self.log_message(f"共通設定読み込みエラー: {e}")
                # エラーが発生した場合はデフォルト値を設定
                self.set_default_common_settings()
            
            # 自動実行設定の読み込み（環境変数から、なければデフォルト値）
            try:
                self.auto_on_var.set(os.getenv("AUTO_ON", "off"))
                self.today_var.set(os.getenv("TODAY", "true").lower() == "true")
                self.threeday_var.set(os.getenv("THREEDAY", "false").lower() == "true")
                self.range_var.set(os.getenv("RANGE", "false").lower() == "true")
                self.s_date_var.set(os.getenv("S_DATE", ""))
                self.e_date_var.set(os.getenv("E_DATE", ""))
                self.exe_min_var.set(os.getenv("EXE_MIN", "0"))
                
                # 24時間分のチェックボックスと投稿設定選択の読み込み
                for i in range(24):
                    hour_key = f"h{i:02d}"
                    hour_enabled = os.getenv(f"HOUR_{hour_key}", "false").lower() == "true"
                    hour_select = os.getenv(f"HOUR_{hour_key}_SELECT", "1")
                    self.hour_vars[hour_key].set(hour_enabled)
                    self.hour_select_vars[hour_key].set(hour_select)
                
                self.log_message("自動実行設定を読み込みました")
                
            except Exception as e:
                self.log_message(f"自動実行設定読み込みエラー: {e}")
                # エラーが発生した場合はデフォルト値を設定
                self.set_default_auto_execution_settings()
            
            # 絞り込み設定の読み込み（環境変数から、なければデフォルト値）
            try:
                self.article_type_var.set(os.getenv("ARTICLE_TYPE", ""))
                self.id_filter_var.set(os.getenv("ID_FILTER", ""))
                self.date_filter_enabled_var.set(os.getenv("DATE_FILTER_ENABLED", "false").lower() == "true")
                self.date_filter_start_var.set(os.getenv("DATE_FILTER_START", ""))
                self.date_filter_end_var.set(os.getenv("DATE_FILTER_END", ""))
                
                self.log_message("絞り込み設定を読み込みました")
                
            except Exception as e:
                self.log_message(f"絞り込み設定読み込みエラー: {e}")
                # エラーが発生した場合はデフォルト値を設定
                self.set_default_filter_settings()
            
            # 設定読み込み状況をログに記録
            env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            if os.path.exists(env_file_path):
                self.log_message(f"設定を.envファイルから読み込みました: {env_file_path}")
            else:
                self.log_message("設定をデフォルト値で初期化しました")
                
        except Exception as e:
            self.log_message(f"設定読み込みエラー: {e}")
            # エラーが発生した場合はデフォルト値を設定
            self.set_default_values()
    
    def save_settings(self):
        """設定を保存する"""
        try:
            # 設定値を取得（日本語表示から実際の値に変換）
            site_value = self.site_var.get()
            if "FANZA" in site_value:
                site_value = "FANZA"
            elif "DMM" in site_value:
                site_value = "DMM"
            
            service_value = self.service_var.get()
            if "digital" in service_value:
                service_value = "digital"
            elif "mono" in service_value:
                service_value = "mono"
            
            floor_value = self.floor_var.get()
            # フロアマッピングが利用可能な場合はそれを使用
            if hasattr(self, 'floor_mapping') and floor_value in self.floor_mapping:
                floor_value = self.floor_mapping[floor_value]
            else:
                # フロアマッピングがない場合は従来の変換処理を使用
                if floor_value == "動画":
                    floor_value = "videoc"
                elif floor_value == "アニメ":
                    floor_value = "videoa"
                elif floor_value == "ゲーム":
                    floor_value = "videob"
                elif floor_value == "電子書籍":
                    floor_value = "videod"
                elif floor_value == "音楽":
                    floor_value = "videoe"
                elif floor_value == "ライブチャット":
                    floor_value = "videof"
                elif floor_value == "写真集":
                    floor_value = "videog"
                elif floor_value == "DVD":
                    floor_value = "videoh"
                elif floor_value == "Blu-ray":
                    floor_value = "videoi"
                elif floor_value == "CD":
                    floor_value = "videoj"
                elif floor_value == "書籍":
                    floor_value = "videok"
                elif floor_value == "雑誌":
                    floor_value = "videol"
                elif floor_value == "その他":
                    floor_value = "videom"  # その他の場合はvideomを使用
                else:
                    floor_value = "videoc"  # デフォルト値
            
            hits_value = self.hits_var.get()
            if "1" in hits_value:
                hits_value = "1"
            elif "10" in hits_value:
                hits_value = "10"
            elif "20" in hits_value:
                hits_value = "20"
            elif "50" in hits_value:
                hits_value = "50"
            elif "100" in hits_value:
                hits_value = "100"
            
            sort_value = self.sort_var.get()
            if "date" in sort_value:
                sort_value = "date"
            elif "name" in sort_value:
                sort_value = "name"
            elif "price" in sort_value:
                sort_value = "price"
            elif "review" in sort_value:
                sort_value = "review"
            elif "rank" in sort_value:
                sort_value = "rank"
            
            # スケジュール設定の値を取得
            schedule_enabled = self.schedule_enabled_var.get()
            schedule_interval = self.schedule_interval_var.get()
            schedule_time = self.schedule_time_var.get()
            schedule_day = self.schedule_day_var.get()
            schedule_date = self.schedule_date_var.get()
            custom_cron = self.custom_cron_var.get()
            
            # 投稿設定1から4の値を取得
            post_settings_data = {}
            
            # 投稿設定1
            # アイキャッチ設定を実際の値に変換
            eyecatch_1_value = self.post_eyecatch_1_var.get()
            if eyecatch_1_value == "サンプル画像":
                eyecatch_1_value = "sample"
            elif eyecatch_1_value == "パッケージ画像":
                eyecatch_1_value = "package"
            elif eyecatch_1_value == "画像1":
                eyecatch_1_value = "1"
            elif eyecatch_1_value == "画像99":
                eyecatch_1_value = "99"
            
            # 動画サイズ設定を実際の値に変換
            movie_size_1_value = self.post_movie_size_1_var.get()
            if movie_size_1_value == "自動":
                movie_size_1_value = "auto"
            elif movie_size_1_value == "720p":
                movie_size_1_value = "720"
            elif movie_size_1_value == "600p":
                movie_size_1_value = "600"
            elif movie_size_1_value == "560p":
                movie_size_1_value = "560"
            
            # ポスター設定を実際の値に変換
            poster_1_value = self.post_poster_1_var.get()
            if poster_1_value == "パッケージ画像":
                poster_1_value = "package"
            elif poster_1_value == "サンプル画像":
                poster_1_value = "sample"
            elif poster_1_value == "なし":
                poster_1_value = "none"
            
            # カテゴリ設定を実際の値に変換
            category_1_value = self.post_category_1_var.get()
            if category_1_value == "JAN":
                category_1_value = "jan"
            elif category_1_value == "女優":
                category_1_value = "act"
            elif category_1_value == "監督":
                category_1_value = "director"
            elif category_1_value == "シリーズ":
                category_1_value = "seri"
            
            # ソート設定を実際の値に変換
            sort_1_value = self.post_sort_1_var.get()
            if sort_1_value == "人気順":
                sort_1_value = "rank"
            elif sort_1_value == "発売日順":
                sort_1_value = "date"
            elif sort_1_value == "レビュー順":
                sort_1_value = "review"
            elif sort_1_value == "価格順":
                sort_1_value = "price"
            
            # 記事設定を実際の値に変換
            article_1_value = self.post_article_1_var.get()
            if article_1_value == "指定なし":
                article_1_value = ""
            elif article_1_value == "女優":
                article_1_value = "actress"
            elif article_1_value == "ジャンル":
                article_1_value = "genre"
            elif article_1_value == "シリーズ":
                article_1_value = "series"
            
            # ステータス設定を実際の値に変換
            status_1_value = self.post_status_1_var.get()
            if status_1_value == "公開":
                status_1_value = "publish"
            elif status_1_value == "下書き":
                status_1_value = "draft"
            
            # 時間設定を実際の値に変換
            hour_1_value = self.post_hour_1_var.get()
            if hour_1_value == "09:00":
                hour_1_value = "h09"
            elif hour_1_value == "12:00":
                hour_1_value = "h12"
            elif hour_1_value == "18:00":
                hour_1_value = "h18"
            elif hour_1_value == "21:00":
                hour_1_value = "h21"
            
            post_settings_data["1"] = {
                "title": self.post_title_1_var.get(),
                "content": self.post_content_text1.get("1.0", tk.END).strip(),
                "eyecatch": eyecatch_1_value,
                "movie_size": movie_size_1_value,
                "poster": poster_1_value,
                "category": category_1_value,
                "sort": sort_1_value,
                "article": article_1_value,
                "status": status_1_value,
                "hour": hour_1_value,
                "overwrite_existing": self.post_overwrite_existing_1_var.get(),
                "target_new_posts": int(self.target_new_posts_1_var.get() or "10")
            }
            
            # 投稿設定2
            # アイキャッチ設定を実際の値に変換
            eyecatch_2_value = self.post_eyecatch_2_var.get()
            if eyecatch_2_value == "サンプル画像":
                eyecatch_2_value = "sample"
            elif eyecatch_2_value == "パッケージ画像":
                eyecatch_2_value = "package"
            elif eyecatch_2_value == "画像1":
                eyecatch_2_value = "1"
            elif eyecatch_2_value == "画像99":
                eyecatch_2_value = "99"
            
            # 動画サイズ設定を実際の値に変換
            movie_size_2_value = self.post_movie_size_2_var.get()
            if movie_size_2_value == "自動":
                movie_size_2_value = "auto"
            elif movie_size_2_value == "720p":
                movie_size_2_value = "720"
            elif movie_size_2_value == "600p":
                movie_size_2_value = "600"
            elif movie_size_2_value == "560p":
                movie_size_2_value = "560"
            
            # ポスター設定を実際の値に変換
            poster_2_value = self.post_poster_2_var.get()
            if poster_2_value == "パッケージ画像":
                poster_2_value = "package"
            elif poster_2_value == "サンプル画像":
                poster_2_value = "sample"
            elif poster_2_value == "なし":
                poster_2_value = "none"
            
            # カテゴリ設定を実際の値に変換
            category_2_value = self.post_category_2_var.get()
            if category_2_value == "JAN":
                category_2_value = "jan"
            elif category_2_value == "女優":
                category_2_value = "act"
            elif category_2_value == "監督":
                category_2_value = "director"
            elif category_2_value == "シリーズ":
                category_2_value = "seri"
            
            # ソート設定を実際の値に変換
            sort_2_value = self.post_sort_2_var.get()
            if sort_2_value == "人気順":
                sort_2_value = "rank"
            elif sort_2_value == "発売日順":
                sort_2_value = "date"
            elif sort_2_value == "レビュー順":
                sort_2_value = "review"
            elif sort_2_value == "価格順":
                sort_2_value = "price"
            
            # 記事設定を実際の値に変換
            article_2_value = self.post_article_2_var.get()
            if article_2_value == "指定なし":
                article_2_value = ""
            elif article_2_value == "女優":
                article_2_value = "actress"
            elif article_2_value == "ジャンル":
                article_2_value = "genre"
            elif article_2_value == "シリーズ":
                article_2_value = "series"
            
            # ステータス設定を実際の値に変換
            status_2_value = self.post_status_2_var.get()
            if status_2_value == "公開":
                status_2_value = "publish"
            elif status_2_value == "下書き":
                status_2_value = "draft"
            
            # 時間設定を実際の値に変換
            hour_2_value = self.post_hour_2_var.get()
            if hour_2_value == "09:00":
                hour_2_value = "h09"
            elif hour_2_value == "12:00":
                hour_2_value = "h12"
            elif hour_2_value == "18:00":
                hour_2_value = "h18"
            elif hour_2_value == "21:00":
                hour_2_value = "h21"
            
            post_settings_data["2"] = {
                "title": self.post_title_2_var.get(),
                "content": self.post_content_text2.get("1.0", tk.END).strip(),
                "eyecatch": eyecatch_2_value,
                "movie_size": movie_size_2_value,
                "poster": poster_2_value,
                "category": category_2_value,
                "sort": sort_2_value,
                "article": article_2_value,
                "status": status_2_value,
                "hour": hour_2_value,
                "overwrite_existing": self.post_overwrite_existing_2_var.get(),
                "target_new_posts": int(self.target_new_posts_2_var.get() or "10")
            }
            
            # 投稿設定3
            # アイキャッチ設定を実際の値に変換
            eyecatch_3_value = self.post_eyecatch_3_var.get()
            if eyecatch_3_value == "サンプル画像":
                eyecatch_3_value = "sample"
            elif eyecatch_3_value == "パッケージ画像":
                eyecatch_3_value = "package"
            elif eyecatch_3_value == "画像1":
                eyecatch_3_value = "1"
            elif eyecatch_3_value == "画像99":
                eyecatch_3_value = "99"
            
            # 動画サイズ設定を実際の値に変換
            movie_size_3_value = self.post_movie_size_3_var.get()
            if movie_size_3_value == "自動":
                movie_size_3_value = "auto"
            elif movie_size_3_value == "720p":
                movie_size_3_value = "720"
            elif movie_size_3_value == "600p":
                movie_size_3_value = "600"
            elif movie_size_3_value == "560p":
                movie_size_3_value = "560"
            
            # ポスター設定を実際の値に変換
            poster_3_value = self.post_poster_3_var.get()
            if poster_3_value == "パッケージ画像":
                poster_3_value = "package"
            elif poster_3_value == "サンプル画像":
                poster_3_value = "sample"
            elif poster_3_value == "なし":
                poster_3_value = "none"
            
            # カテゴリ設定を実際の値に変換
            category_3_value = self.post_category_3_var.get()
            if category_3_value == "JAN":
                category_3_value = "jan"
            elif category_3_value == "女優":
                category_3_value = "act"
            elif category_3_value == "監督":
                category_3_value = "director"
            elif category_3_value == "シリーズ":
                category_3_value = "seri"
            
            # ソート設定を実際の値に変換
            sort_3_value = self.post_sort_3_var.get()
            if sort_3_value == "人気順":
                sort_3_value = "rank"
            elif sort_3_value == "発売日順":
                sort_3_value = "date"
            elif sort_3_value == "レビュー順":
                sort_3_value = "review"
            elif sort_3_value == "価格順":
                sort_3_value = "price"
            
            # 記事設定を実際の値に変換
            article_3_value = self.post_article_3_var.get()
            if article_3_value == "指定なし":
                article_3_value = ""
            elif article_3_value == "女優":
                article_3_value = "actress"
            elif article_3_value == "ジャンル":
                article_3_value = "genre"
            elif article_3_value == "シリーズ":
                article_3_value = "series"
            
            # ステータス設定を実際の値に変換
            status_3_value = self.post_status_3_var.get()
            if status_3_value == "公開":
                status_3_value = "publish"
            elif status_3_value == "下書き":
                status_3_value = "draft"
            
            # 時間設定を実際の値に変換
            hour_3_value = self.post_hour_3_var.get()
            if hour_3_value == "09:00":
                hour_3_value = "h09"
            elif hour_3_value == "12:00":
                hour_3_value = "h12"
            elif hour_3_value == "18:00":
                hour_3_value = "h18"
            elif hour_3_value == "21:00":
                hour_3_value = "h21"
            
            post_settings_data["3"] = {
                "title": self.post_title_3_var.get(),
                "content": self.post_content_text3.get("1.0", tk.END).strip(),
                "eyecatch": eyecatch_3_value,
                "movie_size": movie_size_3_value,
                "poster": poster_3_value,
                "category": category_3_value,
                "sort": sort_3_value,
                "article": article_3_value,
                "status": status_3_value,
                "hour": hour_3_value,
                "overwrite_existing": self.post_overwrite_existing_3_var.get(),
                "target_new_posts": int(self.target_new_posts_3_var.get() or "10")
            }
            
            # 投稿設定4
            # アイキャッチ設定を実際の値に変換
            eyecatch_4_value = self.post_eyecatch_4_var.get()
            if eyecatch_4_value == "サンプル画像":
                eyecatch_4_value = "sample"
            elif eyecatch_4_value == "パッケージ画像":
                eyecatch_4_value = "package"
            elif eyecatch_4_value == "画像1":
                eyecatch_4_value = "1"
            elif eyecatch_4_value == "画像99":
                eyecatch_4_value = "99"
            
            # 動画サイズ設定を実際の値に変換
            movie_size_4_value = self.post_movie_size_4_var.get()
            if movie_size_4_value == "自動":
                movie_size_4_value = "auto"
            elif movie_size_4_value == "720p":
                movie_size_4_value = "720"
            elif movie_size_4_value == "600p":
                movie_size_4_value = "600"
            elif movie_size_4_value == "560p":
                movie_size_4_value = "560"
            
            # ポスター設定を実際の値に変換
            poster_4_value = self.post_poster_4_var.get()
            if poster_4_value == "パッケージ画像":
                poster_4_value = "package"
            elif poster_4_value == "サンプル画像":
                poster_4_value = "sample"
            elif poster_4_value == "なし":
                poster_4_value = "none"
            
            # カテゴリ設定を実際の値に変換
            category_4_value = self.post_category_4_var.get()
            if category_4_value == "JAN":
                category_4_value = "jan"
            elif category_4_value == "女優":
                category_4_value = "act"
            elif category_4_value == "監督":
                category_4_value = "director"
            elif category_4_value == "シリーズ":
                category_4_value = "seri"
            
            # ソート設定を実際の値に変換
            sort_4_value = self.post_sort_4_var.get()
            if sort_4_value == "人気順":
                sort_4_value = "rank"
            elif sort_4_value == "発売日順":
                sort_4_value = "date"
            elif sort_4_value == "レビュー順":
                sort_4_value = "review"
            elif sort_4_value == "価格順":
                sort_4_value = "price"
            
            # 記事設定を実際の値に変換
            article_4_value = self.post_article_4_var.get()
            if article_4_value == "指定なし":
                article_4_value = ""
            elif article_4_value == "女優":
                article_4_value = "actress"
            elif article_4_value == "ジャンル":
                article_4_value = "genre"
            elif article_4_value == "シリーズ":
                article_4_value = "series"
            
            # ステータス設定を実際の値に変換
            status_4_value = self.post_status_4_var.get()
            if status_4_value == "公開":
                status_4_value = "publish"
            elif status_4_value == "下書き":
                status_4_value = "draft"
            
            # 時間設定を実際の値に変換
            hour_4_value = self.post_hour_4_var.get()
            if hour_4_value == "09:00":
                hour_4_value = "h09"
            elif hour_4_value == "12:00":
                hour_4_value = "h12"
            elif hour_4_value == "18:00":
                hour_4_value = "h18"
            elif hour_4_value == "21:00":
                hour_4_value = "h21"
            
            post_settings_data["4"] = {
                "title": self.post_title_4_var.get(),
                "content": self.post_content_text4.get("1.0", tk.END).strip(),
                "eyecatch": eyecatch_4_value,
                "movie_size": movie_size_4_value,
                "poster": poster_4_value,
                "category": category_4_value,
                "sort": sort_4_value,
                "article": article_4_value,
                "status": status_4_value,
                "hour": hour_4_value,
                "overwrite_existing": self.post_overwrite_existing_4_var.get(),
                "target_new_posts": int(self.target_new_posts_4_var.get() or "10")
            }
            
            # 投稿設定をSettingsManagerに保存
            try:
                self.settings_manager.save_post_settings({"post_settings": post_settings_data})
                self.log_message("投稿設定を保存しました")
            except Exception as e:
                self.log_message(f"投稿設定保存エラー: {e}")
            
            # 数値フィールドのデフォルト値設定
            page_wait = self.page_wait_sec_var.get()
            if not page_wait or page_wait.strip() == "":
                page_wait = "5"
            
            # 共通設定の値を取得
            excerpt_template = self.excerpt_template_var.get() or "[title]の詳細情報です。"
            max_sample_images = self.max_sample_images_var.get() or "1"
            categories = self.categories_var.get() or ""
            tags = self.tags_var.get() or ""
            affiliate1_text = self.affiliate1_text_var.get() or "詳細を見る"
            affiliate1_color = self.affiliate1_color_var.get() or "#FFFFFF"
            affiliate1_bg = self.affiliate1_bg_var.get() or "#FF6B6B"
            affiliate2_text = self.affiliate2_text_var.get() or "購入する"
            affiliate2_color = self.affiliate2_color_var.get() or "#FFFFFF"
            affiliate2_bg = self.affiliate2_bg_var.get() or "#4ECDC4"
            post_date_setting = self.post_date_setting_var.get() or "本日"
            random_text1 = self.random_text1_var.get() or ""
            random_text2 = self.random_text2_var.get() or ""
            random_text3 = self.random_text3_var.get() or ""
            
            # 自動実行設定の値を取得
            auto_on = self.auto_on_var.get() or "off"
            today = str(self.today_var.get()).lower()
            threeday = str(self.threeday_var.get()).lower()
            range_enabled = str(self.range_var.get()).lower()
            s_date = self.s_date_var.get() or ""
            e_date = self.e_date_var.get() or ""
            exe_min = self.exe_min_var.get() or "0"
            
            # 絞り込み設定の値を取得
            article_type = self.article_type_var.get() or ""
            id_filter = self.id_filter_var.get() or ""
            date_filter_enabled = str(self.date_filter_enabled_var.get()).lower()
            date_filter_start = self.date_filter_start_var.get() or ""
            date_filter_end = self.date_filter_end_var.get() or ""
            
            settings_data = {
                "DMM_API_ID": self.dmm_api_id_var.get() or "",
                "DMM_AFFILIATE_ID": self.dmm_affiliate_id_var.get() or "",
                "WORDPRESS_BASE_URL": self.wp_url_var.get() or "",
                "WORDPRESS_USERNAME": self.wp_username_var.get() or "",
                "WORDPRESS_APPLICATION_PASSWORD": self.wp_app_password_var.get() or "",
                "SITE": site_value or "FANZA",
                "SERVICE": service_value or "digital",
                "FLOOR": floor_value or "videoc",
                "HITS": hits_value or "10",
                "SORT": sort_value or "date",
                "KEYWORD": self.keyword_var.get() or "",
                "MAXIMAGE": self.maximage_var.get() or "1",
                "LIMITED_FLAG": self.limited_flag_var.get() or "0",
                "PAGE_WAIT_SEC": page_wait,
                "SCHEDULE_ENABLED": str(schedule_enabled).lower(),
                "SCHEDULE_INTERVAL": schedule_interval,
                "SCHEDULE_TIME": schedule_time,
                "SCHEDULE_DAY": schedule_day,
                "SCHEDULE_DATE": schedule_date,
                "CUSTOM_CRON": custom_cron,
                # 共通設定
                "EXCERPT_TEMPLATE": excerpt_template,
                "MAX_SAMPLE_IMAGES": max_sample_images,
                "CATEGORIES": categories,
                "TAGS": tags,
                "AFFILIATE1_TEXT": affiliate1_text,
                "AFFILIATE1_COLOR": affiliate1_color,
                "AFFILIATE1_BG": affiliate1_bg,
                "AFFILIATE2_TEXT": affiliate2_text,
                "AFFILIATE2_COLOR": affiliate2_color,
                "AFFILIATE2_BG": affiliate2_bg,
                "POST_DATE_SETTING": post_date_setting,
                "RANDOM_TEXT1": random_text1,
                "RANDOM_TEXT2": random_text2,
                "RANDOM_TEXT3": random_text3,
                # 自動実行設定
                "AUTO_ON": auto_on,
                "TODAY": today,
                "THREEDAY": threeday,
                "RANGE": range_enabled,
                "S_DATE": s_date,
                "E_DATE": e_date,
                "EXE_MIN": exe_min,
                # 絞り込み設定
                "ARTICLE_TYPE": article_type,
                "ID_FILTER": id_filter,
                "DATE_FILTER_ENABLED": date_filter_enabled,
                "DATE_FILTER_START": date_filter_start,
                "DATE_FILTER_END": date_filter_end
            }
            
            # 投稿設定1から4の個別設定をsettings_dataに追加（基本設定のみ）
            for i in range(1, 5):
                post_setting = post_settings_data[str(i)]
                settings_data[f"POST_TITLE_{i}"] = post_setting["title"]
                settings_data[f"POST_EYECATCH_{i}"] = post_setting["eyecatch"]
                settings_data[f"POST_MOVIE_SIZE_{i}"] = post_setting["movie_size"]
                settings_data[f"POST_POSTER_{i}"] = post_setting["poster"]
                settings_data[f"POST_CATEGORY_{i}"] = post_setting["category"]
                settings_data[f"POST_SORT_{i}"] = post_setting["sort"]
                settings_data[f"POST_ARTICLE_{i}"] = post_setting["article"]
                settings_data[f"POST_STATUS_{i}"] = post_setting["status"]
                settings_data[f"POST_HOUR_{i}"] = post_setting["hour"]
                settings_data[f"POST_OVERWRITE_EXISTING_{i}"] = str(post_setting["overwrite_existing"]).lower()
                settings_data[f"POST_TARGET_NEW_POSTS_{i}"] = str(post_setting["target_new_posts"])
            
            # 24時間分のチェックボックスと投稿設定選択の値を追加
            for i in range(24):
                hour_key = f"h{i:02d}"
                hour_enabled = str(self.hour_vars[hour_key].get()).lower()
                hour_select = self.hour_select_vars[hour_key].get() or "1"
                settings_data[f"HOUR_{hour_key}"] = hour_enabled
                settings_data[f"HOUR_{hour_key}_SELECT"] = hour_select
            
            # .envファイルに保存（プロジェクトルートディレクトリに作成）
            env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            print(f"保存先パス: {env_file_path}")
            print(f"保存する設定数: {len(settings_data)}")
            with open(env_file_path, "w", encoding="utf-8") as f:
                for key, value in settings_data.items():
                    f.write(f"{key}={value}\n")
            print(f".envファイル保存完了: {env_file_path}")
            print(f"ファイルサイズ: {os.path.getsize(env_file_path)} bytes")
            
            # 環境変数として設定
            for key, value in settings_data.items():
                os.environ[key] = value
            
            # 投稿設定1から4をSettingsManagerを使って保存
            try:
                self.settings_manager.save_post_settings(post_settings_data)
                self.log_message("投稿設定1から4を保存しました")
            except Exception as e:
                self.log_message(f"投稿設定保存エラー: {e}")
                messagebox.showerror("エラー", f"投稿設定の保存に失敗しました: {e}")
            
            # 設定を再読み込み
            try:
                self.settings = Settings.load()
                self.engine = Engine.from_settings(self.settings)
                self.log_message("設定を正常に再読み込みしました")
            except Exception as e:
                self.log_message(f"設定再読み込みエラー: {e}")
                # エラーが発生しても設定は保存されているので続行
            
            self.log_message(f"設定を保存しました: {env_file_path}")
            self.status_var.set("設定保存完了")
            
            # 保存成功のメッセージ
            messagebox.showinfo("成功", "設定が正常に保存されました。")
            
        except Exception as e:
            self.log_message(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定保存に失敗しました: {e}")
    
    def load_settings_from_gui(self):
        """GUIから設定を読み込む"""
        self.load_settings_to_gui()
        self.log_message("設定を再読み込みしました")
    
    def run_once(self):
        """1回実行"""
        if self.is_running:
            return
        
        self.is_running = True
        self.status_var.set("実行中...")
        
        def run():
            try:
                self.log_message("通常実行を開始します...")
                
                # 選択された投稿設定を取得
                selected_setting = self.selected_post_setting_var.get()
                self.log_message(f"投稿設定{selected_setting}を使用して実行します")
                
                # 実行前の情報をログに表示
                items, total = self.engine.search_items()
                self.log_message(f"検索結果: {total}件のアイテムが見つかりました")
                self.log_message(f"処理対象: {len(items)}件のアイテム")
                
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
                self.status_var.set("実行完了")
            except Exception as e:
                self.log_message(f"実行エラー: {e}")
                self.status_var.set("実行エラー")
                import traceback
                self.log_message(f"エラー詳細: {traceback.format_exc()}")
            finally:
                self.is_running = False
        
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
    
    def run_test(self):
        """テスト実行"""
        if self.is_running:
            messagebox.showwarning("警告", "既に実行中です")
            return
        
        self.is_running = True
        self.status_var.set("テスト実行中...")
        
        def run():
            try:
                self.log_message("テスト実行を開始します...")
                
                # 選択された投稿設定を取得
                selected_setting = self.selected_post_setting_var.get()
                self.log_message(f"投稿設定{selected_setting}を使用してテスト実行します")
                
                result = self.engine.run_test(selected_setting)
                
                # 結果を解析して、HTMLプレビューを個別に表示
                lines = result.split('\n')
                for line in lines:
                    if line.strip():
                        if "--- HTML Preview" in line:
                            # HTMLプレビューの開始
                            self.log_message(line)
                        elif "--- End HTML Preview" in line:
                            # HTMLプレビューの終了
                            self.log_message(line)
                        elif line.startswith("--- Item") or line.startswith("Title:") or line.startswith("CID:") or line.startswith("URL:") or line.startswith("LargeImage:") or line.startswith("Desc(len):") or line.startswith("Large imgs:") or line.startswith("Small imgs:"):
                            # アイテム情報
                            self.log_message(line)
                        elif line.startswith("Total items found:") or line.startswith("Items to process:"):
                            # 基本情報
                            self.log_message(line)
                        else:
                            # HTMLの内容（改行なしで表示）
                            if line.strip():
                                self.log_message(f"HTML Content: {line}")
                
                self.log_message("テスト実行が完了しました")
                self.status_var.set("テスト完了")
            except Exception as e:
                self.log_message(f"テスト実行エラー: {e}")
                self.status_var.set("テストエラー")
                messagebox.showerror("エラー", f"テスト実行に失敗しました: {e}")
            finally:
                self.is_running = False
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def toggle_schedule(self):
        """スケジュールの開始/停止を切り替え"""
        if self.scheduler and self.scheduler.running:
            # スケジュールを停止
            self.scheduler.shutdown()
            self.scheduler = None
            self.status_var.set("スケジュール停止")
            self.log_message("スケジュールを停止しました")
        else:
            # スケジュールを開始
            if not self.schedule_enabled_var.get():
                messagebox.showwarning("警告", "スケジュールが無効になっています")
                return
            
            self.scheduler = BackgroundScheduler()
            
            # スケジュール設定に基づいてジョブを追加
            interval = self.schedule_interval_var.get()
            time_str = self.schedule_time_var.get()
            day = self.schedule_day_var.get()
            date = self.schedule_date_var.get()
            custom_cron = self.custom_cron_var.get()
            
            if interval == "毎分":
                self.scheduler.add_job(self.engine.run_once, 'interval', minutes=1)
                schedule_info = "毎分実行"
            elif interval == "毎時":
                hour = int(time_str.split(":")[0])
                self.scheduler.add_job(self.engine.run_once, 'cron', hour=hour)
                schedule_info = f"毎時{hour}時実行"
            elif interval == "毎日":
                hour, minute = map(int, time_str.split(":"))
                self.scheduler.add_job(self.engine.run_once, 'cron', hour=hour, minute=minute)
                schedule_info = f"毎日{time_str}実行"
            elif interval == "毎週":
                hour, minute = map(int, time_str.split(":"))
                day_map = {"月曜日": "mon", "火曜日": "tue", "水曜日": "wed", 
                          "木曜日": "thu", "金曜日": "fri", "土曜日": "sat", "日曜日": "sun"}
                day_of_week = day_map.get(day, "mon")
                self.scheduler.add_job(self.engine.run_once, 'cron', day_of_week=day_of_week, hour=hour, minute=minute)
                schedule_info = f"毎週{day}{time_str}実行"
            elif interval == "毎月":
                hour, minute = map(int, time_str.split(":"))
                date_num = int(date.replace("日", ""))
                self.scheduler.add_job(self.engine.run_once, 'cron', day=date_num, hour=hour, minute=minute)
                schedule_info = f"毎月{date}{time_str}実行"
            elif interval == "カスタム":
                if custom_cron:
                    self.scheduler.add_job(self.engine.run_once, 'cron', **self.parse_cron(custom_cron))
                    schedule_info = f"カスタム({custom_cron})"
                else:
                    messagebox.showwarning("警告", "カスタムCronが設定されていません")
                    return
            else:
                messagebox.showwarning("警告", "無効なスケジュール設定です")
                return
            
            self.scheduler.start()
            self.status_var.set(f"スケジュール実行中 ({schedule_info})")
            self.log_message(f"スケジュールを開始しました ({schedule_info})")
    
    def log_message(self, message):
        """ログメッセージを追加"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # HTMLプレビューの場合は特別な処理
            if "--- HTML Preview" in message or "--- End HTML Preview" in message:
                log_entry = f"[{timestamp}] {message}\n"
            else:
                log_entry = f"[{timestamp}] {message}\n"
            
            self.log_queue.put(log_entry)
            
            # ログテキストウィジェットに直接追加（存在する場合）
            if hasattr(self, 'log_text') and self.log_text:
                try:
                    self.log_text.insert(tk.END, log_entry)
                    self.log_text.see(tk.END)
                except Exception as e:
                    print(f"ログテキスト更新エラー: {e}")
        except Exception as e:
            print(f"ログメッセージ処理エラー: {e}")
    
    def update_log(self):
        """ログを更新"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # 100ms後に再度更新
        self.root.after(100, self.update_log)
    
    def clear_log(self):
        """ログをクリア"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("ログをクリアしました")
    
    def create_backup(self):
        """設定のバックアップを作成"""
        try:
            self.settings_manager._create_backup()
            messagebox.showinfo("バックアップ完了", "設定のバックアップが作成されました。")
            self.update_settings_status()
        except Exception as e:
            messagebox.showerror("バックアップエラー", f"バックアップの作成に失敗しました。\n{str(e)}")
    
    def show_restore_dialog(self):
        """設定復元ダイアログを表示"""
        try:
            backups = self.settings_manager.get_backup_list()
            if not backups:
                messagebox.showinfo("復元可能なバックアップなし", "復元可能なバックアップがありません。")
                return
            
            # 復元ダイアログを作成
            restore_dialog = tk.Toplevel(self.root)
            restore_dialog.title("設定を復元")
            restore_dialog.geometry("500x400")
            restore_dialog.transient(self.root)
            restore_dialog.grab_set()
            
            # ダイアログの内容
            ttk.Label(restore_dialog, text="復元するバックアップを選択してください:", 
                     font=("Arial", 12, "bold")).pack(pady=(20, 10))
            
            # バックアップリスト
            listbox_frame = ttk.Frame(restore_dialog)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            # バックアップファイルをリストに追加
            for backup in backups:
                listbox.insert(tk.END, backup)
            
            # 選択されたバックアップを表示
            if backups:
                listbox.selection_set(0)
            
            # ボタンフレーム
            button_frame = ttk.Frame(restore_dialog)
            button_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            def restore_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("選択なし", "復元するバックアップを選択してください。")
                    return
                
                backup_filename = backups[selection[0]]
                if messagebox.askyesno("確認", f"'{backup_filename}'から設定を復元しますか？\n現在の設定は失われます。"):
                    try:
                        if self.settings_manager.restore_from_backup(backup_filename):
                            messagebox.showinfo("復元完了", "設定の復元が完了しました。\nアプリケーションを再起動してください。")
                            restore_dialog.destroy()
                            self.update_settings_status()
                        else:
                            messagebox.showerror("復元エラー", "設定の復元に失敗しました。")
                    except Exception as e:
                        messagebox.showerror("復元エラー", f"設定の復元中にエラーが発生しました。\n{str(e)}")
            
            restore_button = ttk.Button(button_frame, text="復元", command=restore_selected, style="Accent.TButton")
            restore_button.pack(side=tk.RIGHT, padx=(10, 0))
            
            cancel_button = ttk.Button(button_frame, text="キャンセル", command=restore_dialog.destroy)
            cancel_button.pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("エラー", f"復元ダイアログの表示に失敗しました。\n{str(e)}")
    
    def toggle_settings_lock(self):
        """設定のロック状態を切り替え"""
        try:
            if self.settings_manager._is_locked():
                if messagebox.askyesno("ロック解除", "設定のロックを解除しますか？"):
                    self.settings_manager.unlock_settings()
                    messagebox.showinfo("ロック解除完了", "設定のロックが解除されました。")
            else:
                if messagebox.askyesno("ロック", "設定をロックしますか？\nロック中は設定の変更・保存ができなくなります。"):
                    self.settings_manager.lock_settings()
                    messagebox.showinfo("ロック完了", "設定がロックされました。")
            
            self.update_settings_status()
        except Exception as e:
            messagebox.showerror("エラー", f"設定のロック状態の変更に失敗しました。\n{str(e)}")
    
    def reset_settings(self):
        """設定をデフォルト値にリセット"""
        try:
            if messagebox.askyesno("確認", "設定をデフォルト値にリセットしますか？\n現在の設定は失われます。"):
                if self.settings_manager.reset_to_defaults():
                    messagebox.showinfo("リセット完了", "設定がデフォルト値にリセットされました。\nアプリケーションを再起動してください。")
                    self.update_settings_status()
                else:
                    messagebox.showerror("リセットエラー", "設定のリセットに失敗しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"設定のリセットに失敗しました。\n{str(e)}")
    
    def update_settings_status(self):
        """設定状態を更新"""
        try:
            if self.settings_manager._is_locked():
                self.settings_status_var.set("設定状態: ロック中 (変更不可)")
            else:
                self.settings_status_var.set("設定状態: 通常 (変更可能)")
        except Exception as e:
            self.settings_status_var.set(f"設定状態: エラー ({str(e)})")

    def preview_post_content(self):
        """投稿内容をプレビューする（投稿設定1から4）"""
        try:
            # プレビューウィンドウを作成
            preview_window = tk.Toplevel(self.root)
            preview_window.title("投稿内容プレビュー - 投稿設定1から4")
            preview_window.geometry("900x800")
            preview_window.transient(self.root)
            preview_window.grab_set()
            
            # プレビュー内容
            preview_frame = ttk.Frame(preview_window, padding="20")
            preview_frame.pack(fill=tk.BOTH, expand=True)
            
            # ノートブック（タブ）を作成
            notebook = ttk.Notebook(preview_frame)
            notebook.pack(fill=tk.BOTH, expand=True)
            
            # サンプルデータでテンプレートを置換
            sample_data = {
                "title": "サンプル動画タイトル",
                "comment": "これはサンプルの動画コメントです。実際の投稿時には実際の動画情報が表示されます。",
                "aff-link": "https://example.com/sample-affiliate-link",
                "image": "sample-image-url.jpg"
            }
            
            # 投稿設定1から4のタブを作成
            for i in range(1, 5):
                tab_frame = ttk.Frame(notebook, padding="15")
                notebook.add(tab_frame, text=f"投稿設定{i}")
                
                # 設定情報を取得
                title_var = getattr(self, f"post_title_{i}_var")
                content_text = getattr(self, f"post_content_text{i}")
                eyecatch_var = getattr(self, f"post_eyecatch_{i}_var")
                movie_size_var = getattr(self, f"post_movie_size_{i}_var")
                poster_var = getattr(self, f"post_poster_{i}_var")
                category_var = getattr(self, f"post_category_{i}_var")
                sort_var = getattr(self, f"post_sort_{i}_var")
                article_var = getattr(self, f"post_article_{i}_var")
                status_var = getattr(self, f"post_status_{i}_var")
                hour_var = getattr(self, f"post_hour_{i}_var")
                overwrite_var = getattr(self, f"post_overwrite_existing_{i}_var")
                target_var = getattr(self, f"target_new_posts_{i}_var")
                
                # タイトル
                ttk.Label(tab_frame, text="タイトル:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
                title_text_widget = tk.Text(tab_frame, height=2, wrap=tk.WORD, font=("Arial", 10))
                title_text_widget.pack(fill=tk.X, pady=(0, 15))
                title_preview = title_var.get() or "[title]"
                for key, value in sample_data.items():
                    title_preview = title_preview.replace(f"[{key}]", value)
                title_text_widget.insert(tk.END, title_preview)
                title_text_widget.config(state=tk.DISABLED)
                
                # 設定情報
                settings_frame = ttk.LabelFrame(tab_frame, text="設定情報", padding="10")
                settings_frame.pack(fill=tk.X, pady=(0, 15))
                
                # 1行目
                row1 = ttk.Frame(settings_frame)
                row1.pack(fill=tk.X, pady=(0, 5))
                ttk.Label(row1, text="アイキャッチ:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row1, text=eyecatch_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 20))
                ttk.Label(row1, text="動画サイズ:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row1, text=movie_size_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 20))
                ttk.Label(row1, text="ポスター:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row1, text=poster_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
                
                # 2行目
                row2 = ttk.Frame(settings_frame)
                row2.pack(fill=tk.X, pady=(0, 5))
                ttk.Label(row2, text="カテゴリ:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row2, text=category_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 20))
                ttk.Label(row2, text="ソート:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row2, text=sort_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 20))
                ttk.Label(row2, text="記事:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row2, text=article_var.get() or "なし", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
                
                # 3行目
                row3 = ttk.Frame(settings_frame)
                row3.pack(fill=tk.X, pady=(0, 5))
                ttk.Label(row3, text="ステータス:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row3, text=status_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 20))
                ttk.Label(row3, text="時間:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row3, text=hour_var.get(), font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 20))
                ttk.Label(row3, text="上書き:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row3, text="有効" if overwrite_var.get() else "無効", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
                
                # 4行目
                row4 = ttk.Frame(settings_frame)
                row4.pack(fill=tk.X, pady=(0, 15))
                ttk.Label(row4, text="目標投稿数:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                ttk.Label(row4, text=target_var.get() or "0", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
                
                # 本文
                ttk.Label(tab_frame, text="本文:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
                content_text_widget = tk.Text(tab_frame, height=8, wrap=tk.WORD, font=("Arial", 10))
                content_text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                content_preview = content_text.get("1.0", tk.END).strip() or "[title]の詳細情報です。"
                for key, value in sample_data.items():
                    content_preview = content_preview.replace(f"[{key}]", value)
                content_text_widget.insert(tk.END, content_preview)
                content_text_widget.config(state=tk.DISABLED)
            
            # テンプレート変数の説明
            help_frame = ttk.LabelFrame(preview_frame, text="利用可能なテンプレート変数", padding="10")
            help_frame.pack(fill=tk.X, pady=(15, 0))
            
            help_text = """[title] - 動画のタイトル
[comment] - 動画のコメント・説明
[aff-link] - アフィリエイトリンク
[image] - 動画の画像URL
[date] - 投稿日時
[category] - 動画のカテゴリ
[tags] - 動画のタグ"""
            
            help_label = ttk.Label(help_frame, text=help_text, font=("Consolas", 9), justify=tk.LEFT)
            help_label.pack(anchor=tk.W)
            
            # ボタンフレーム
            button_frame = ttk.Frame(preview_frame)
            button_frame.pack(fill=tk.X, pady=(15, 0))
            
            # 閉じるボタン
            ttk.Button(button_frame, text="閉じる", command=preview_window.destroy, style="Accent.TButton").pack(side=tk.RIGHT)
            
            self.log_message("投稿設定1から4のプレビューを表示しました")
            
        except Exception as e:
            self.log_message(f"プレビュー表示エラー: {e}")
            messagebox.showerror("エラー", f"プレビューの表示に失敗しました: {e}")
    
    def update_floor_list(self):
        """フロア一覧をAPIから取得して更新する"""
        try:
            # 基本設定からAPI情報を取得
            api_id = getattr(self, 'api_id_var', None)
            affiliate_id = getattr(self, 'affiliate_id_var', None)
            
            if not api_id or not affiliate_id:
                messagebox.showwarning("警告", "API IDまたはアフィリエイトIDが設定されていません。\n基本設定でAPI情報を設定してください。")
                return
            
            api_id_value = api_id.get()
            affiliate_id_value = affiliate_id.get()
            
            if not api_id_value or not affiliate_id_value:
                messagebox.showwarning("警告", "API IDまたはアフィリエイトIDが入力されていません。")
                return
            
            # DMMクライアントを作成してフロア一覧を取得
            from .dmm_client import DMMClient
            client = DMMClient(api_id=api_id_value, affiliate_id=affiliate_id_value)
            
            self.log_message("フロア一覧を取得中...")
            floor_data = client.floor_list()
            
            if 'result' in floor_data and 'site' in floor_data['result']:
                sites = floor_data['result']['site']
                floor_options = []
                floor_mapping = {}  # 日本語名とコードのマッピング
                
                for site in sites:
                    if 'service' in site:
                        for service in site['service']:
                            if 'floor' in service:
                                for floor in service['floor']:
                                    floor_name = floor.get('name', '')
                                    floor_code = floor.get('code', '')
                                    if floor_name and floor_code:
                                        floor_options.append(floor_name)
                                        floor_mapping[floor_name] = floor_code
                
                if floor_options:
                    # フロア一覧を更新
                    self.floor_combo['values'] = floor_options
                    
                    # 現在選択されている値を保持
                    current_value = self.floor_var.get()
                    if current_value in floor_mapping:
                        # 現在の値が新しい一覧に含まれている場合はそのまま
                        pass
                    else:
                        # 含まれていない場合は最初の値を選択
                        self.floor_var.set(floor_options[0] if floor_options else "動画")
                    
                    # フロアマッピングを保存（後で保存時に使用）
                    self.floor_mapping = floor_mapping
                    
                    self.log_message(f"フロア一覧を更新しました（{len(floor_options)}件）")
                    messagebox.showinfo("完了", f"フロア一覧を更新しました（{len(floor_options)}件）")
                else:
                    self.log_message("フロア情報が見つかりませんでした")
                    messagebox.showwarning("警告", "フロア情報が見つかりませんでした")
            else:
                self.log_message("フロア一覧の取得に失敗しました")
                messagebox.showerror("エラー", "フロア一覧の取得に失敗しました")
                
        except ImportError:
            messagebox.showerror("エラー", "DMMクライアントのインポートに失敗しました")
        except Exception as e:
            self.log_message(f"フロア一覧更新エラー: {e}")
            messagebox.showerror("エラー", f"フロア一覧の更新に失敗しました: {e}")

    def start_monitoring(self):
        """監視を開始する"""
        if self.monitoring_active:
            self.log_message("監視は既に開始されています")
            return
        
        self.monitoring_active = True
        self.log_message("監視を開始しました")
        
        # バックグラウンドで監視ループを開始
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # ステータスバーを更新
        self.status_var.set("監視中...")
        
        # 監視状態表示を更新
        self.update_monitoring_status()
    
    def stop_monitoring(self):
        """監視を停止する"""
        if not self.monitoring_active:
            self.log_message("監視は既に停止されています")
            return
        
        self.monitoring_active = False
        self.log_message("監視を停止しました")
        
        # ステータスバーを更新
        self.status_var.set("監視停止")
        
        # 監視状態表示を更新
        self.update_monitoring_status()
    
    def update_monitoring_status(self):
        """監視状態表示を更新する"""
        try:
            if hasattr(self, 'monitoring_status_var'):
                if self.monitoring_active:
                    self.monitoring_status_var.set("監視状態: 監視中")
                    # 色を緑に変更
                    for widget in self.root.winfo_children():
                        if isinstance(widget, ttk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Notebook):
                                    for tab in child.winfo_children():
                                        if hasattr(tab, 'winfo_children'):
                                            for tab_child in tab.winfo_children():
                                                if isinstance(tab_child, tk.Canvas):
                                                    for canvas_child in tab_child.winfo_children():
                                                        if isinstance(canvas_child, ttk.Frame):
                                                            for frame_child in canvas_child.winfo_children():
                                                                if isinstance(frame_child, ttk.LabelFrame) and "監視制御" in frame_child.cget("text"):
                                                                    for label_frame_child in frame_child.winfo_children():
                                                                        if isinstance(label_frame_child, ttk.Label) and hasattr(label_frame_child, 'cget'):
                                                                            if label_frame_child.cget("textvariable") == str(self.monitoring_status_var):
                                                                                label_frame_child.configure(foreground="green")
                                                                                break
                else:
                    self.monitoring_status_var.set("監視状態: 停止中")
                    # 色を赤に変更
                    for widget in self.root.winfo_children():
                        if isinstance(widget, ttk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Notebook):
                                    for tab in child.winfo_children():
                                        if hasattr(tab, 'winfo_children'):
                                            for tab_child in tab.winfo_children():
                                                if isinstance(tab_child, tk.Canvas):
                                                    for canvas_child in tab_child.winfo_children():
                                                        if isinstance(canvas_child, ttk.Frame):
                                                            for frame_child in canvas_child.winfo_children():
                                                                if isinstance(frame_child, ttk.LabelFrame) and "監視制御" in frame_child.cget("text"):
                                                                    for label_frame_child in frame_child.winfo_children():
                                                                        if isinstance(label_frame_child, ttk.Label) and hasattr(label_frame_child, 'cget'):
                                                                            if label_frame_child.cget("textvariable") == str(self.monitoring_status_var):
                                                                                label_frame_child.configure(foreground="red")
                                                                                break
        except Exception as e:
            print(f"監視状態更新エラー: {e}")
    
    def monitor_loop(self):
        """監視ループ（バックグラウンドで実行）"""
        while self.monitoring_active:
            try:
                # 現在時刻を取得
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                
                # 自動実行設定をチェック
                if self.auto_on_var.get() == "on":
                    # 24時間分のチェックボックスをチェック
                    hour_key = f"h{current_hour:02d}"
                    if hour_key in self.hour_vars and self.hour_vars[hour_key].get():
                        # 指定された分に実行
                        if str(current_minute) == self.exe_min_var.get():
                            # 投稿設定を取得
                            post_setting_num = self.hour_select_vars[hour_key].get()
                            self.log_message(f"自動実行: {current_hour:02d}:{current_minute:02d} - 投稿設定{post_setting_num}")
                            
                            # 非同期で実行
                            self.root.after(0, lambda: self.run_auto_execution(post_setting_num))
                
                # 1分待機
                time.sleep(60)
                
            except Exception as e:
                self.log_message(f"監視ループエラー: {e}")
                time.sleep(60)  # エラーが発生しても1分待機
    
    def run_auto_execution(self, post_setting_num):
        """自動実行を実行する"""
        try:
            self.log_message(f"投稿設定{post_setting_num}で自動実行を開始します")
            
            # 投稿設定を選択
            self.selected_post_setting_var.set(str(post_setting_num))
            
            # 1回実行を実行
            self.run_once()
            
        except Exception as e:
            self.log_message(f"自動実行エラー: {e}")
    
    def on_closing(self):
        """GUI終了時の処理"""
        try:
            print("GUI終了処理開始")
            
            # 監視を停止
            if hasattr(self, 'monitoring_active') and self.monitoring_active:
                self.stop_monitoring()
            
            # スケジューラーを停止
            if hasattr(self, 'scheduler') and self.scheduler:
                try:
                    self.scheduler.shutdown()
                except Exception as e:
                    print(f"スケジューラー停止エラー: {e}")
            
            print("GUI終了処理完了")
            self.root.destroy()
            
        except Exception as e:
            print(f"GUI終了処理エラー: {e}")
            # エラーが発生しても強制終了
            try:
                self.root.destroy()
            except:
                pass

def main():
    print("main関数開始")
    try:
        root = tk.Tk()
        print("Tkインスタンス作成完了")
        
        app = FanzaAutoGUI(root)
        print("FanzaAutoGUIインスタンス作成完了")
        
        # GUI終了時の処理を設定
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        print("プロトコルハンドラー設定完了")
        
        # ウィンドウの状態を確認
        print(f"ウィンドウサイズ: {root.winfo_width()}x{root.winfo_height()}")
        print(f"ウィンドウ位置: {root.winfo_x()}, {root.winfo_y()}")
        
        # ウィンドウを前面に表示
        root.lift()
        root.attributes('-topmost', True)
        root.attributes('-topmost', False)
        
        print("GUI開始 - mainloop開始")
        root.mainloop()
        print("GUI終了 - mainloop終了")
        
    except Exception as e:
        print(f"main関数エラー: {e}")
        import traceback
        print(f"エラー詳細: {traceback.format_exc()}")
        # エラーが発生しても少し待機
        import time
        time.sleep(5)

if __name__ == "__main__":
    main()
