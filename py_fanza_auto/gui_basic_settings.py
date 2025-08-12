import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

class BasicSettingsTab:
    """基本設定タブの管理クラス"""
    
    def __init__(self, parent_notebook, main_gui):
        self.parent_notebook = parent_notebook
        self.main_gui = main_gui
        self.vars = {}
        self.create_tab()
    
    def create_tab(self):
        """基本設定タブの作成"""
        basic_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(basic_frame, text="基本設定")
        
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
        self._create_dmm_settings(scrollable_frame)
        
        # WordPress設定
        self._create_wordpress_settings(scrollable_frame)
        
        # ブラウザ設定
        self._create_browser_settings(scrollable_frame)
        
        # 日付フィルター設定
        self._create_date_filter_settings(scrollable_frame)
        
        # 保存ボタンを追加
        self._create_save_button(scrollable_frame)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        basic_frame.columnconfigure(0, weight=1)
        basic_frame.rowconfigure(0, weight=1)
    
    def _create_save_button(self, parent):
        """保存ボタンの作成"""
        save_frame = ttk.Frame(parent)
        save_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        save_frame.columnconfigure(0, weight=1)
        
        # 保存ボタン
        save_button = ttk.Button(save_frame, text="基本設定を保存", 
                                command=self.save_basic_settings, style="Accent.TButton")
        save_button.grid(row=0, column=0, pady=10)
        
        # デフォルト値設定ボタン
        default_button = ttk.Button(save_frame, text="デフォルト値に設定", 
                                   command=self.set_default_values, style="Accent.TButton")
        default_button.grid(row=0, column=1, padx=(10, 0), pady=10)
    
    def _create_dmm_settings(self, parent):
        """DMM API設定フレームの作成"""
        dmm_frame = ttk.LabelFrame(parent, text="DMM API設定", padding="15")
        dmm_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        dmm_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(dmm_frame, text="DMM API ID:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['DMM_API_ID'] = tk.StringVar()
        ttk.Entry(dmm_frame, textvariable=self.vars['DMM_API_ID'], width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(dmm_frame, text="※DMMアフィリエイトプログラムで取得", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(dmm_frame, text="DMM アフィリエイトID:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['DMM_AFFILIATE_ID'] = tk.StringVar()
        ttk.Entry(dmm_frame, textvariable=self.vars['DMM_AFFILIATE_ID'], width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(dmm_frame, text="※アフィリエイトIDを入力", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_wordpress_settings(self, parent):
        """WordPress設定フレームの作成"""
        wp_frame = ttk.LabelFrame(parent, text="WordPress設定", padding="15")
        wp_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        wp_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(wp_frame, text="WordPress URL:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['WORDPRESS_BASE_URL'] = tk.StringVar()
        ttk.Entry(wp_frame, textvariable=self.vars['WORDPRESS_BASE_URL'], width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(wp_frame, text="※WordPressサイトのURL（例: https://example.com）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(wp_frame, text="ユーザー名:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['WORDPRESS_USERNAME'] = tk.StringVar()
        ttk.Entry(wp_frame, textvariable=self.vars['WORDPRESS_USERNAME'], width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(wp_frame, text="※WordPressのユーザー名", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(wp_frame, text="アプリケーションパスワード:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['WORDPRESS_APPLICATION_PASSWORD'] = tk.StringVar()
        ttk.Entry(wp_frame, textvariable=self.vars['WORDPRESS_APPLICATION_PASSWORD'], width=40, show="*").grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(wp_frame, text="※WordPressのアプリケーションパスワード", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_browser_settings(self, parent):
        """ブラウザ設定フレームの作成"""
        browser_frame = ttk.LabelFrame(parent, text="ブラウザ設定", padding="15")
        browser_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        browser_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(browser_frame, text="ページ待機時間（秒）:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['PAGE_WAIT_SEC'] = tk.StringVar()
        ttk.Entry(browser_frame, textvariable=self.vars['PAGE_WAIT_SEC'], width=10).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(browser_frame, text="※ページ読み込み後の待機時間", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_date_filter_settings(self, parent):
        """日付フィルター設定フレームの作成"""
        date_filter_frame = ttk.LabelFrame(parent, text="日付フィルター設定", padding="15")
        date_filter_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        date_filter_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(date_filter_frame, text="日付フィルター:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['DATE_FILTER_ENABLED'] = tk.BooleanVar()
        ttk.Checkbutton(date_filter_frame, text="日付フィルターを有効にする", 
                       variable=self.vars['DATE_FILTER_ENABLED']).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(date_filter_frame, text="開始日:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['DATE_FILTER_START'] = tk.StringVar()
        ttk.Entry(date_filter_frame, textvariable=self.vars['DATE_FILTER_START'], width=15).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(date_filter_frame, text="※YYYY-MM-DD形式", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(date_filter_frame, text="終了日:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['DATE_FILTER_END'] = tk.StringVar()
        ttk.Entry(date_filter_frame, textvariable=self.vars['DATE_FILTER_END'], width=15).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(date_filter_frame, text="※YYYY-MM-DD形式", 
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
    
    def save_basic_settings(self):
        """基本設定を保存"""
        try:
            if not self.main_gui or not self.main_gui.settings_manager:
                messagebox.showerror("エラー", "設定管理システムが利用できません")
                return
            
            # 設定値を取得
            settings = self.get_variables()
            
            # 現在の設定を読み込み
            current_settings = self.main_gui.settings_manager.load_settings()
            
            # 基本設定を更新
            current_settings.update(settings)
            
            # 保存
            if self.main_gui.settings_manager.save_settings(current_settings):
                messagebox.showinfo("保存完了", "基本設定を保存しました")
                if hasattr(self.main_gui, 'log_message'):
                    self.main_gui.log_message("基本設定を保存しました")
                # 設定状態を更新
                if hasattr(self.main_gui, 'update_settings_status'):
                    self.main_gui.update_settings_status()
            else:
                messagebox.showerror("エラー", "設定の保存に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存に失敗しました:\n{e}")
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(f"基本設定保存エラー: {e}")
    
    def set_default_values(self):
        """デフォルト値を設定"""
        self.vars['DMM_API_ID'].set("")
        self.vars['DMM_AFFILIATE_ID'].set("")
        self.vars['WORDPRESS_BASE_URL'].set("")
        self.vars['WORDPRESS_USERNAME'].set("")
        self.vars['WORDPRESS_APPLICATION_PASSWORD'].set("")
        self.vars['PAGE_WAIT_SEC'].set("3")
        self.vars['DATE_FILTER_ENABLED'].set(False)
        self.vars['DATE_FILTER_START'].set("")
        self.vars['DATE_FILTER_END'].set("")
        
        if hasattr(self.main_gui, 'log_message'):
            self.main_gui.log_message("基本設定をデフォルト値に設定しました")
    
    def load_from_settings(self, settings):
        """設定オブジェクトまたは辞書から値を読み込み"""
        try:
            # 辞書形式の設定に対応
            if isinstance(settings, dict):
                # デバッグ用：読み込まれる設定の内容を確認
                if hasattr(self.main_gui, 'log_message'):
                    self.main_gui.log_message(f"基本設定読み込み開始: {len(settings)}件の設定")
                
                # 辞書から直接値を取得
                if 'DMM_API_ID' in settings:
                    value = settings['DMM_API_ID'] or ""
                    self.vars['DMM_API_ID'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"DMM_API_ID設定: {value[:10]}{'...' if len(str(value)) > 10 else ''}")
                if 'DMM_AFFILIATE_ID' in settings:
                    value = settings['DMM_AFFILIATE_ID'] or ""
                    self.vars['DMM_AFFILIATE_ID'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"DMM_AFFILIATE_ID設定: {value[:10]}{'...' if len(str(value)) > 10 else ''}")
                if 'WORDPRESS_BASE_URL' in settings:
                    value = settings['WORDPRESS_BASE_URL'] or ""
                    self.vars['WORDPRESS_BASE_URL'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"WORDPRESS_BASE_URL設定: {value[:10]}{'...' if len(str(value)) > 10 else ''}")
                if 'WORDPRESS_USERNAME' in settings:
                    value = settings['WORDPRESS_USERNAME'] or ""
                    self.vars['WORDPRESS_USERNAME'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"WORDPRESS_USERNAME設定: {value[:10]}{'...' if len(str(value)) > 10 else ''}")
                if 'WORDPRESS_APPLICATION_PASSWORD' in settings:
                    value = settings['WORDPRESS_APPLICATION_PASSWORD'] or ""
                    self.vars['WORDPRESS_APPLICATION_PASSWORD'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"WORDPRESS_APPLICATION_PASSWORD設定: {value[:10]}{'...' if len(str(value)) > 10 else ''}")
                if 'PAGE_WAIT_SEC' in settings:
                    value = settings['PAGE_WAIT_SEC'] or "3"
                    self.vars['PAGE_WAIT_SEC'].set(str(value))
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"PAGE_WAIT_SEC設定: {value}")
                if 'DATE_FILTER_ENABLED' in settings:
                    value = settings['DATE_FILTER_ENABLED'] or False
                    self.vars['DATE_FILTER_ENABLED'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"DATE_FILTER_ENABLED設定: {value}")
                if 'DATE_FILTER_START' in settings:
                    value = settings['DATE_FILTER_START'] or ""
                    self.vars['DATE_FILTER_START'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"DATE_FILTER_START設定: {value}")
                if 'DATE_FILTER_END' in settings:
                    value = settings['DATE_FILTER_END'] or ""
                    self.vars['DATE_FILTER_END'].set(value)
                    if hasattr(self.main_gui, 'log_message'):
                        self.main_gui.log_message(f"DATE_FILTER_END設定: {value}")
                
                if hasattr(self.main_gui, 'log_message'):
                    self.main_gui.log_message("基本設定の読み込みが完了しました")
            else:
                # 従来のオブジェクト形式の設定に対応
                if hasattr(settings, 'dmm_api_id'):
                    self.vars['DMM_API_ID'].set(settings.dmm_api_id or "")
                if hasattr(settings, 'dmm_affiliate_id'):
                    self.vars['DMM_AFFILIATE_ID'].set(settings.dmm_affiliate_id or "")
                if hasattr(settings, 'wp_base_url'):
                    self.vars['WORDPRESS_BASE_URL'].set(settings.wp_base_url or "")
                if hasattr(settings, 'wp_username'):
                    self.vars['WORDPRESS_USERNAME'].set(settings.wp_username or "")
                if hasattr(settings, 'wp_app_password'):
                    self.vars['WORDPRESS_APPLICATION_PASSWORD'].set(settings.wp_app_password or "")
                if hasattr(settings, 'page_wait_sec'):
                    self.vars['PAGE_WAIT_SEC'].set(str(settings.page_wait_sec or "3"))
                # 他の設定も同様に読み込み
                
        except Exception as e:
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(f"基本設定読み込みエラー: {e}")
            print(f"基本設定読み込みエラー: {e}")
