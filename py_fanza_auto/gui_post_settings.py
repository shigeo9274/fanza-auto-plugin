import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Any
import os

class PostSettingsTab:
    """投稿設定タブの管理クラス"""
    
    def __init__(self, parent_notebook, main_gui):
        self.parent_notebook = parent_notebook
        self.main_gui = main_gui
        self.vars = {}
        self.create_tab()
    
    def create_tab(self):
        """投稿設定タブの作成"""
        post_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(post_frame, text="投稿設定")
        
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
        
        # 投稿設定
        self._create_post_settings(scrollable_frame)
        
        # テンプレート設定
        self._create_template_settings(scrollable_frame)
        
        # 画像設定
        self._create_image_settings(scrollable_frame)
        
        # 保存ボタンを追加
        self._create_save_button(scrollable_frame)
        
        # レイアウト設定
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        post_frame.columnconfigure(0, weight=1)
        post_frame.rowconfigure(0, weight=1)
    
    def _create_save_button(self, parent):
        """保存ボタンの作成"""
        save_frame = ttk.Frame(parent)
        save_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        save_frame.columnconfigure(0, weight=1)
        
        # 保存ボタン
        save_button = ttk.Button(save_frame, text="投稿設定を保存", 
                                command=self.save_post_settings, style="Accent.TButton")
        save_button.grid(row=0, column=0, pady=10)
        
        # デフォルト値設定ボタン
        default_button = ttk.Button(save_frame, text="デフォルト値に設定", 
                                   command=self.set_default_values, style="Accent.TButton")
        default_button.grid(row=0, column=1, padx=(10, 0), pady=10)
    
    def _create_post_settings(self, parent):
        """投稿設定フレームの作成"""
        post_frame = ttk.LabelFrame(parent, text="投稿設定", padding="15")
        post_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        post_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(post_frame, text="投稿タイトル:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['POST_TITLE'] = tk.StringVar()
        ttk.Entry(post_frame, textvariable=self.vars['POST_TITLE'], width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(post_frame, text="※投稿のタイトル", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_frame, text="投稿ステータス:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['POST_STATUS'] = tk.StringVar()
        status_combo = ttk.Combobox(post_frame, textvariable=self.vars['POST_STATUS'], 
                                   values=["draft", "publish", "private"], state="readonly", width=15)
        status_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_frame, text="※投稿の公開状態", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_frame, text="投稿タイプ:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['POST_TYPE'] = tk.StringVar()
        type_combo = ttk.Combobox(post_frame, textvariable=self.vars['POST_TYPE'], 
                                 values=["post", "page"], state="readonly", width=15)
        type_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_frame, text="※投稿の種類", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_frame, text="カテゴリ:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['POST_CATEGORY'] = tk.StringVar()
        ttk.Entry(post_frame, textvariable=self.vars['POST_CATEGORY'], width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_frame, text="※投稿のカテゴリ", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_frame, text="タグ:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['POST_TAGS'] = tk.StringVar()
        ttk.Entry(post_frame, textvariable=self.vars['POST_TAGS'], width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(post_frame, text="※投稿のタグ（カンマ区切り）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(post_frame, text="著者:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['POST_AUTHOR'] = tk.StringVar()
        ttk.Entry(post_frame, textvariable=self.vars['POST_AUTHOR'], width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(post_frame, text="※投稿の著者", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_template_settings(self, parent):
        """テンプレート設定フレームの作成"""
        template_frame = ttk.LabelFrame(parent, text="テンプレート設定", padding="15")
        template_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        template_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(template_frame, text="テンプレートファイル:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['TEMPLATE_FILE'] = tk.StringVar()
        ttk.Entry(template_frame, textvariable=self.vars['TEMPLATE_FILE'], width=40).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(template_frame, text="※使用するテンプレートファイル", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(template_frame, text="テンプレートエンジン:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['TEMPLATE_ENGINE'] = tk.StringVar()
        engine_combo = ttk.Combobox(template_frame, textvariable=self.vars['TEMPLATE_ENGINE'], 
                                   values=["jinja2", "string"], state="readonly", width=15)
        engine_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(template_frame, text="※使用するテンプレートエンジン", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(template_frame, text="カスタム変数:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['CUSTOM_VARIABLES'] = tk.StringVar()
        ttk.Entry(template_frame, textvariable=self.vars['CUSTOM_VARIABLES'], width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(template_frame, text="※カスタム変数の設定（JSON形式）", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
    
    def _create_image_settings(self, parent):
        """画像設定フレームの作成"""
        image_frame = ttk.LabelFrame(parent, text="画像設定", padding="15")
        image_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        image_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(image_frame, text="画像の自動挿入:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['AUTO_INSERT_IMAGES'] = tk.BooleanVar()
        ttk.Checkbutton(image_frame, text="画像を自動的に挿入する", 
                       variable=self.vars['AUTO_INSERT_IMAGES']).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        
        row += 1
        ttk.Label(image_frame, text="画像サイズ:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['IMAGE_SIZE'] = tk.StringVar()
        size_combo = ttk.Combobox(image_frame, textvariable=self.vars['IMAGE_SIZE'], 
                                 values=["thumbnail", "medium", "large", "full"], state="readonly", width=15)
        size_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(image_frame, text="※挿入する画像のサイズ", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(image_frame, text="画像の説明:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['IMAGE_CAPTION'] = tk.StringVar()
        ttk.Entry(image_frame, textvariable=self.vars['IMAGE_CAPTION'], width=50).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(image_frame, text="※画像の説明文", 
                 font=("Arial", 8), foreground="gray").grid(
            row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(image_frame, text="画像の配置:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        self.vars['IMAGE_ALIGNMENT'] = tk.StringVar()
        align_combo = ttk.Combobox(image_frame, textvariable=self.vars['IMAGE_ALIGNMENT'], 
                                  values=["left", "center", "right", "none"], state="readonly", width=15)
        align_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(image_frame, text="※画像の配置位置", 
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
    
    def save_post_settings(self):
        """投稿設定を保存"""
        try:
            if not self.main_gui or not self.main_gui.settings_manager:
                messagebox.showerror("エラー", "設定管理システムが利用できません")
                return
            
            # 設定値を取得
            settings = self.get_variables()
            
            # 現在の設定を読み込み
            current_settings = self.main_gui.settings_manager.load_settings()
            
            # 投稿設定を更新
            current_settings.update(settings)
            
            # 保存
            if self.main_gui.settings_manager.save_settings(current_settings):
                messagebox.showinfo("保存完了", "投稿設定を保存しました")
                if hasattr(self.main_gui, 'log_message'):
                    self.main_gui.log_message("投稿設定を保存しました")
                # 設定状態を更新
                if hasattr(self.main_gui, 'update_settings_status'):
                    self.main_gui.update_settings_status()
            else:
                messagebox.showerror("エラー", "設定の保存に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存に失敗しました:\n{e}")
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(f"投稿設定保存エラー: {e}")
    
    def set_default_values(self):
        """デフォルト値を設定"""
        self.vars['POST_TITLE'].set("")
        self.vars['POST_STATUS'].set("draft")
        self.vars['POST_TYPE'].set("post")
        self.vars['POST_CATEGORY'].set("")
        self.vars['POST_TAGS'].set("")
        self.vars['POST_AUTHOR'].set("")
        self.vars['TEMPLATE_FILE'].set("default.html")
        self.vars['TEMPLATE_ENGINE'].set("jinja2")
        self.vars['CUSTOM_VARIABLES'].set("{}")
        self.vars['AUTO_INSERT_IMAGES'].set(True)
        self.vars['IMAGE_SIZE'].set("medium")
        self.vars['IMAGE_CAPTION'].set("")
        self.vars['IMAGE_ALIGNMENT'].set("center")
        
        if hasattr(self.main_gui, 'log_message'):
            self.main_gui.log_message("投稿設定をデフォルト値に設定しました")
    
    def load_from_settings(self, settings):
        """設定オブジェクトまたは辞書から値を読み込み"""
        try:
            # 辞書形式の設定に対応
            if isinstance(settings, dict):
                # 辞書から直接値を取得
                if 'POST_TITLE' in settings:
                    self.vars['POST_TITLE'].set(settings['POST_TITLE'] or "")
                if 'POST_STATUS' in settings:
                    self.vars['POST_STATUS'].set(settings['POST_STATUS'] or "draft")
                if 'POST_TYPE' in settings:
                    self.vars['POST_TYPE'].set(settings['POST_TYPE'] or "post")
                if 'POST_CATEGORY' in settings:
                    self.vars['POST_CATEGORY'].set(settings['POST_CATEGORY'] or "")
                if 'POST_TAGS' in settings:
                    self.vars['POST_TAGS'].set(settings['POST_TAGS'] or "")
                if 'POST_AUTHOR' in settings:
                    self.vars['POST_AUTHOR'].set(settings['POST_AUTHOR'] or "")
                if 'TEMPLATE_FILE' in settings:
                    self.vars['TEMPLATE_FILE'].set(settings['TEMPLATE_FILE'] or "default.html")
                if 'TEMPLATE_ENGINE' in settings:
                    self.vars['TEMPLATE_ENGINE'].set(settings['TEMPLATE_ENGINE'] or "jinja2")
                if 'CUSTOM_VARIABLES' in settings:
                    self.vars['CUSTOM_VARIABLES'].set(settings['CUSTOM_VARIABLES'] or "{}")
                if 'AUTO_INSERT_IMAGES' in settings:
                    self.vars['AUTO_INSERT_IMAGES'].set(settings['AUTO_INSERT_IMAGES'] or True)
                if 'IMAGE_SIZE' in settings:
                    self.vars['IMAGE_SIZE'].set(settings['IMAGE_SIZE'] or "medium")
                if 'IMAGE_CAPTION' in settings:
                    self.vars['IMAGE_CAPTION'].set(settings['IMAGE_CAPTION'] or "")
                if 'IMAGE_ALIGNMENT' in settings:
                    self.vars['IMAGE_ALIGNMENT'].set(settings['IMAGE_ALIGNMENT'] or "center")
            else:
                # 従来のオブジェクト形式の設定に対応
                if hasattr(settings, 'post_title'):
                    self.vars['POST_TITLE'].set(settings.post_title or "")
                if hasattr(settings, 'post_status'):
                    self.vars['POST_STATUS'].set(settings.post_status or "draft")
                # 他の設定も同様に読み込み
                
        except Exception as e:
            if hasattr(self.main_gui, 'log_message'):
                self.main_gui.log_message(f"投稿設定読み込みエラー: {e}")
            print(f"投稿設定読み込みエラー: {e}")
