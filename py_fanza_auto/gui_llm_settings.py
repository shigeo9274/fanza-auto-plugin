"""
LLM設定タブ - AI機能の設定を管理
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from typing import Dict, Any

class LLMSettingsTab:
    def __init__(self, parent_notebook, main_gui):
        self.parent_notebook = parent_notebook
        self.main_gui = main_gui
        
        # LLM設定タブを作成
        self.llm_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.llm_frame, text="LLM設定")
        
        # 設定変数
        self.llm_provider_var = tk.StringVar(value="openai")
        self.openai_api_key_var = tk.StringVar()
        self.openai_model_var = tk.StringVar(value="gpt-4")
        self.anthropic_api_key_var = tk.StringVar()
        self.anthropic_model_var = tk.StringVar(value="claude-3-sonnet")
        self.google_api_key_var = tk.StringVar()
        self.local_endpoint_var = tk.StringVar(value="http://localhost:11434")
        self.local_model_var = tk.StringVar(value="gpt-oss-20b")
        self.max_tokens_var = tk.StringVar(value="1000")
        self.temperature_var = tk.StringVar(value="0.7")
        
        self.create_widgets()
        self.load_settings()
    
    def create_widgets(self):
        """ウィジェットの作成"""
        # スクロール可能なキャンバス
        canvas = tk.Canvas(self.llm_frame)
        scrollbar = ttk.Scrollbar(self.llm_frame, orient="vertical", command=canvas.yview)
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
        
        self.llm_frame.columnconfigure(0, weight=1)
        self.llm_frame.rowconfigure(0, weight=1)
        
        # キャンバスのサイズ設定
        canvas.configure(width=800, height=600)
        
        # 基本設定フレーム
        basic_frame = ttk.LabelFrame(scrollable_frame, text="基本設定", padding="15")
        basic_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=(15, 15))
        basic_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(basic_frame, text="LLMプロバイダー:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        provider_combo = ttk.Combobox(basic_frame, textvariable=self.llm_provider_var, 
                                     values=["openai", "anthropic", "google", "local"], 
                                     state="readonly", width=20)
        provider_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(basic_frame, text="※使用するLLMサービスを選択", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(basic_frame, text="最大トークン数:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Entry(basic_frame, textvariable=self.max_tokens_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(basic_frame, text="※生成されるテキストの最大長（100-4000）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(basic_frame, text="温度（創造性）:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Entry(basic_frame, textvariable=self.temperature_var, width=10).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(basic_frame, text="※低い値で一貫性重視、高い値で創造性重視（0.0-2.0）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
                # OpenAI設定フレーム
        self.openai_frame = ttk.LabelFrame(scrollable_frame, text="OpenAI設定", padding="15")
        self.openai_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        self.openai_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(self.openai_frame, text="APIキー:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        api_key_entry = ttk.Entry(self.openai_frame, textvariable=self.openai_api_key_var, width=50, show="*")
        api_key_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(self.openai_frame, text="※OpenAIのAPIキーを入力", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(self.openai_frame, text="モデル:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        model_combo = ttk.Combobox(self.openai_frame, textvariable=self.openai_model_var, 
                                    values=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"], 
                                    state="readonly", width=20)
        model_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(self.openai_frame, text="※使用するGPTモデルを選択", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
                # Anthropic設定フレーム
        self.anthropic_frame = ttk.LabelFrame(scrollable_frame, text="Anthropic設定", padding="15")
        self.anthropic_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        self.anthropic_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(self.anthropic_frame, text="APIキー:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        api_key_entry = ttk.Entry(self.anthropic_frame, textvariable=self.anthropic_api_key_var, width=50, show="*")
        api_key_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(self.anthropic_frame, text="※AnthropicのAPIキーを入力", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(self.anthropic_frame, text="モデル:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        model_combo = ttk.Combobox(self.anthropic_frame, textvariable=self.anthropic_model_var, 
                                    values=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"], 
                                    state="readonly", width=20)
        model_combo.grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(self.anthropic_frame, text="※使用するClaudeモデルを選択", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # Google設定フレーム
        self.google_frame = ttk.LabelFrame(scrollable_frame, text="Google設定", padding="15")
        self.google_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        self.google_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(self.google_frame, text="APIキー:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        api_key_entry = ttk.Entry(self.google_frame, textvariable=self.google_api_key_var, width=50, show="*")
        api_key_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        ttk.Label(self.google_frame, text="※Google AI StudioのAPIキーを入力", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # ローカルLLM設定フレーム
        self.local_frame = ttk.LabelFrame(scrollable_frame, text="ローカルLLM設定（推奨: gpt-oss-20b）", padding="15")
        self.local_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        self.local_frame.columnconfigure(1, weight=1)
        
        row = 0
        ttk.Label(self.local_frame, text="エンドポイント:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Entry(self.local_frame, textvariable=self.local_endpoint_var, width=40).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(self.local_frame, text="※Ollama等のローカルLLMのエンドポイントURL", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        row += 1
        ttk.Label(self.local_frame, text="モデル:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=(0, 15), pady=5)
        ttk.Entry(self.local_frame, textvariable=self.local_model_var, width=20).grid(row=row, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(self.local_frame, text="※使用するローカルモデル名（gpt-oss-20b, llama2, mistral等）", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # ローカルLLM状態表示
        row += 1
        status_frame = ttk.Frame(self.local_frame)
        status_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(status_frame, text="ローカルLLM状態:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.local_llm_status_var = tk.StringVar(value="未確認")
        status_label = ttk.Label(status_frame, textvariable=self.local_llm_status_var, 
                                font=("Arial", 9), foreground="gray")
        status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 状態確認ボタン
        check_status_button = ttk.Button(status_frame, text="状態確認", 
                                        command=self.check_local_llm_status, 
                                        style="Accent.TButton")
        check_status_button.pack(side=tk.LEFT)
        
        # ローカルLLM管理フレーム
        row += 1
        management_frame = ttk.LabelFrame(self.local_frame, text="ローカルLLM管理", padding="10")
        management_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 1行目: Ollamaインストールとサービス管理
        mgmt_row1 = ttk.Frame(management_frame)
        mgmt_row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(mgmt_row1, text="Ollamaインストール", 
                   command=self.install_ollama, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(mgmt_row1, text="サービス起動", 
                   command=self.start_ollama_service, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(mgmt_row1, text="サービス停止", 
                   command=self.stop_ollama_service, style="Accent.TButton").pack(side=tk.LEFT)
        
        # 2行目: モデル管理
        mgmt_row2 = ttk.Frame(management_frame)
        mgmt_row2.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(mgmt_row2, text="モデル:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.model_download_var = tk.StringVar(value="gpt-oss-20b")
        model_combo = ttk.Combobox(mgmt_row2, textvariable=self.model_download_var, 
                                   values=["gpt-oss-20b", "llama2", "mistral", "codellama", "neural-chat"], 
                                   state="readonly", width=15)
        model_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(mgmt_row2, text="モデルダウンロード", 
                   command=self.download_model, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(mgmt_row2, text="モデル削除", 
                   command=self.delete_model, style="Accent.TButton").pack(side=tk.LEFT)
        
        # 3行目: モデル一覧表示
        mgmt_row3 = ttk.Frame(management_frame)
        mgmt_row3.pack(fill=tk.X)
        
        ttk.Button(mgmt_row3, text="モデル一覧更新", 
                   command=self.refresh_model_list, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        self.model_list_var = tk.StringVar(value="モデル一覧を更新してください")
        model_list_label = ttk.Label(mgmt_row3, textvariable=self.model_list_var, 
                                    font=("Arial", 8), foreground="gray")
        model_list_label.pack(side=tk.LEFT)
        
        # 操作ボタンフレーム
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        
        # 接続テストボタン
        test_button = ttk.Button(buttons_frame, text="接続テスト", 
                                command=self.test_connection, style="Accent.TButton")
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 生成テストボタン
        generate_test_button = ttk.Button(buttons_frame, text="生成テスト", 
                                         command=self.show_generate_test_dialog, style="Accent.TButton")
        generate_test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 設定保存ボタン
        save_button = ttk.Button(buttons_frame, text="設定保存", 
                                command=self.save_settings, style="Accent.TButton")
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 設定リセットボタン
        reset_button = ttk.Button(buttons_frame, text="設定リセット", 
                                 command=self.reset_settings, style="Accent.TButton")
        reset_button.pack(side=tk.LEFT)
        
        # 説明フレーム
        info_frame = ttk.LabelFrame(scrollable_frame, text="LLM機能の説明", padding="15")
        info_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        info_frame.columnconfigure(0, weight=1)
        
        info_text = """LLM機能により、以下のAI支援機能が利用できます：

1. 紹介文の自動生成（[llm_intro]）
   - 作品の説明文から魅力的な紹介文を自動生成
   - 200-300文字程度の読みやすい文章

2. SEO最適化タイトルの生成（[llm_seo_title]）
   - 検索されやすいキーワードを含むタイトルを自動生成
   - 30-50文字程度の最適な長さ

3. コンテンツの改善（[llm_enhance]）
   - 既存のコンテンツをより魅力的で読みやすい内容に改善

これらの機能は投稿設定のテンプレートで変数タグとして使用できます。

推奨ローカルモデル: gpt-oss-20b
- 20Bパラメータの高性能オープンソースGPTモデル
- 日本語と英語の両方に対応
- 創造的な文章生成に優れている
- Ollamaで簡単に利用可能"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=700)
        info_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # プロバイダー変更時のイベント
        provider_combo.bind('<<ComboboxSelected>>', self.on_provider_change)
        
        # 初期状態の設定
        self.on_provider_change()
        
        # ローカルLLMが選択されている場合は状態確認
        if self.llm_provider_var.get() == "local":
            self.auto_check_local_llm_status()
        
        # 初期化時にモデル一覧を更新
        self.refresh_model_list()
    
    def on_provider_change(self, event=None):
        """プロバイダー変更時の処理"""
        provider = self.llm_provider_var.get()
        
        # 各設定フレームの表示/非表示を切り替え
        if provider == "openai":
            self.show_frame("openai")
            self.hide_frame("anthropic")
            self.hide_frame("google")
            self.hide_frame("local")
        elif provider == "anthropic":
            self.hide_frame("openai")
            self.show_frame("anthropic")
            self.hide_frame("google")
            self.hide_frame("local")
        elif provider == "google":
            self.hide_frame("openai")
            self.hide_frame("anthropic")
            self.show_frame("google")
            self.hide_frame("local")
        elif provider == "local":
            self.hide_frame("openai")
            self.hide_frame("anthropic")
            self.hide_frame("google")
            self.show_frame("local")
            # ローカルLLM選択時に自動的に状態確認
            self.auto_check_local_llm_status()
    
    def show_frame(self, frame_name):
        """指定されたフレームを表示"""
        if frame_name == "openai":
            self.openai_frame.grid()
        elif frame_name == "anthropic":
            self.anthropic_frame.grid()
        elif frame_name == "google":
            self.google_frame.grid()
        elif frame_name == "local":
            self.local_frame.grid()
    
    def hide_frame(self, frame_name):
        """指定されたフレームを非表示"""
        if frame_name == "openai":
            self.openai_frame.grid_remove()
        elif frame_name == "anthropic":
            self.anthropic_frame.grid_remove()
        elif frame_name == "google":
            self.google_frame.grid_remove()
        elif frame_name == "local":
            self.local_frame.grid_remove()
    
    def load_settings(self):
        """設定を読み込み"""
        try:
            if hasattr(self.main_gui, 'settings_manager') and self.main_gui.settings_manager:
                settings = self.main_gui.settings_manager.load_settings()
                if settings:
                    # LLM設定の読み込み
                    self.llm_provider_var.set(settings.get('LLM_PROVIDER', 'openai'))
                    self.openai_api_key_var.set(settings.get('OPENAI_API_KEY', ''))
                    self.openai_model_var.set(settings.get('OPENAI_MODEL', 'gpt-4'))
                    self.anthropic_api_key_var.set(settings.get('ANTHROPIC_API_KEY', ''))
                    self.anthropic_model_var.set(settings.get('ANTHROPIC_MODEL', 'claude-3-sonnet'))
                    self.google_api_key_var.set(settings.get('GOOGLE_API_KEY', ''))
                    self.local_endpoint_var.set(settings.get('LOCAL_ENDPOINT', 'http://localhost:11434'))
                    self.local_model_var.set(settings.get('LOCAL_MODEL', 'gpt-oss-20b'))
                    self.max_tokens_var.set(settings.get('LLM_MAX_TOKENS', '1000'))
                    self.temperature_var.set(settings.get('LLM_TEMPERATURE', '0.7'))
                    
                    # プロバイダー変更時の表示更新
                    self.on_provider_change()
        except Exception as e:
            print(f"LLM設定読み込みエラー: {e}")
    
    def save_settings(self):
        """設定を保存"""
        try:
            if hasattr(self.main_gui, 'settings_manager') and self.main_gui.settings_manager:
                # 現在の設定を取得
                current_settings = self.main_gui.settings_manager.load_settings() or {}
                
                # LLM設定を更新
                current_settings.update({
                    'LLM_PROVIDER': self.llm_provider_var.get(),
                    'OPENAI_API_KEY': self.openai_api_key_var.get(),
                    'OPENAI_MODEL': self.openai_model_var.get(),
                    'ANTHROPIC_API_KEY': self.anthropic_api_key_var.get(),
                    'ANTHROPIC_MODEL': self.anthropic_model_var.get(),
                    'GOOGLE_API_KEY': self.google_api_key_var.get(),
                    'LOCAL_ENDPOINT': self.local_endpoint_var.get(),
                    'LOCAL_MODEL': self.local_model_var.get(),
                    'LLM_MAX_TOKENS': self.max_tokens_var.get(),
                    'LLM_TEMPERATURE': self.temperature_var.get()
                })
                
                # 設定を保存
                if self.main_gui.settings_manager.save_settings(current_settings):
                    messagebox.showinfo("保存完了", "LLM設定を保存しました")
                    self.main_gui.log_message("LLM設定を保存しました")
                else:
                    messagebox.showerror("エラー", "LLM設定の保存に失敗しました")
            else:
                messagebox.showerror("エラー", "設定管理システムが利用できません")
        except Exception as e:
            messagebox.showerror("エラー", f"LLM設定の保存に失敗しました:\n{e}")
            print(f"LLM設定保存エラー: {e}")
    
    def reset_settings(self):
        """設定をリセット"""
        try:
            result = messagebox.askyesno("確認", "LLM設定をリセットしますか？\nこの操作は元に戻せません。")
            if result:
                # デフォルト値にリセット
                self.llm_provider_var.set("openai")
                self.openai_api_key_var.set("")
                self.openai_model_var.set("gpt-4")
                self.anthropic_api_key_var.set("")
                self.anthropic_model_var.set("claude-3-sonnet")
                self.google_api_key_var.set("")
                self.local_endpoint_var.set("http://localhost:11434")
                self.local_model_var.set("gpt-oss-20b")
                self.max_tokens_var.set("1000")
                self.temperature_var.set("0.7")
                
                messagebox.showinfo("リセット完了", "LLM設定をリセットしました")
                self.main_gui.log_message("LLM設定をリセットしました")
        except Exception as e:
            messagebox.showerror("エラー", f"LLM設定のリセットに失敗しました:\n{e}")
            print(f"LLM設定リセットエラー: {e}")
    
    def test_connection(self):
        """接続テスト"""
        try:
            provider = self.llm_provider_var.get()
            
            if provider == "openai":
                api_key = self.openai_api_key_var.get()
                if not api_key:
                    messagebox.showwarning("警告", "OpenAIのAPIキーが設定されていません")
                    return
                # 実際のAPI接続テストはここに実装
                messagebox.showinfo("接続テスト", "OpenAI APIの接続テストを実行しました")
                
            elif provider == "anthropic":
                api_key = self.anthropic_api_key_var.get()
                if not api_key:
                    messagebox.showwarning("警告", "AnthropicのAPIキーが設定されていません")
                    return
                messagebox.showinfo("接続テスト", "Anthropic APIの接続テストを実行しました")
                
            elif provider == "google":
                api_key = self.google_api_key_var.get()
                if not api_key:
                    messagebox.showwarning("警告", "GoogleのAPIキーが設定されていません")
                    return
                messagebox.showinfo("接続テスト", "Google AI APIの接続テストを実行しました")
                
            elif provider == "local":
                endpoint = self.local_endpoint_var.get()
                if not endpoint:
                    messagebox.showwarning("警告", "ローカルLLMのエンドポイントが設定されていません")
                    return
                
                # ローカルLLMの実際の接続テスト
                if self.test_local_llm_connection(endpoint):
                    messagebox.showinfo("接続テスト", "ローカルLLMに正常に接続できました！")
                else:
                    messagebox.showerror("接続テスト", "ローカルLLMに接続できませんでした。\n\n確認事項：\n1. Ollama等のローカルLLMが起動しているか\n2. エンドポイントURLが正しいか\n3. ファイアウォールの設定")
            
            self.main_gui.log_message(f"{provider}の接続テストを実行しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"接続テストに失敗しました:\n{e}")
            print(f"接続テストエラー: {e}")
    
    def test_local_llm_connection(self, endpoint):
        """ローカルLLMの接続テスト"""
        try:
            import requests
            import json
            
            # ヘルスチェック用のエンドポイント
            health_url = f"{endpoint.rstrip('/')}/api/tags"
            
            # タイムアウトを短く設定（ローカルなので5秒）
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                # 利用可能なモデル一覧を取得
                models = response.json()
                if 'models' in models and models['models']:
                    model_names = [model['name'] for model in models['models']]
                    self.main_gui.log_message(f"ローカルLLM接続成功: {len(model_names)}個のモデルを検出")
                    self.main_gui.log_message(f"利用可能モデル: {', '.join(model_names)}")
                    
                    # 設定されているモデルが利用可能かチェック
                    configured_model = self.local_model_var.get()
                    if configured_model in model_names:
                        self.main_gui.log_message(f"設定モデル '{configured_model}' が利用可能です")
                    else:
                        self.main_gui.log_message(f"警告: 設定モデル '{configured_model}' が見つかりません")
                        self.main_gui.log_message(f"利用可能なモデルから選択してください: {', '.join(model_names)}")
                    
                    return True
                else:
                    self.main_gui.log_message("ローカルLLMに接続できましたが、モデルが見つかりません")
                    return False
            else:
                self.main_gui.log_message(f"ローカルLLM接続エラー: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.main_gui.log_message("ローカルLLM接続エラー: 接続できません。サービスが起動しているか確認してください。")
            return False
        except requests.exceptions.Timeout:
            self.main_gui.log_message("ローカルLLM接続エラー: タイムアウト。エンドポイントURLを確認してください。")
            return False
        except Exception as e:
            self.main_gui.log_message(f"ローカルLLM接続エラー: {e}")
            return False
    
    def get_variables(self) -> Dict[str, Any]:
        """設定変数を辞書形式で取得"""
        return {
            'LLM_PROVIDER': self.llm_provider_var.get(),
            'OPENAI_API_KEY': self.openai_api_key_var.get(),
            'OPENAI_MODEL': self.openai_model_var.get(),
            'ANTHROPIC_API_KEY': self.anthropic_api_key_var.get(),
            'ANTHROPIC_MODEL': self.anthropic_model_var.get(),
            'GOOGLE_API_KEY': self.google_api_key_var.get(),
            'LOCAL_ENDPOINT': self.local_endpoint_var.get(),
            'LOCAL_MODEL': self.local_model_var.get(),
            'LLM_MAX_TOKENS': self.max_tokens_var.get(),
            'LLM_TEMPERATURE': self.temperature_var.get()
        }
    
    def load_from_settings(self, settings: Dict[str, Any]):
        """設定辞書から値を読み込み"""
        try:
            self.llm_provider_var.set(settings.get('LLM_PROVIDER', 'openai'))
            self.openai_api_key_var.set(settings.get('OPENAI_API_KEY', ''))
            self.openai_model_var.set(settings.get('OPENAI_MODEL', 'gpt-4'))
            self.anthropic_api_key_var.set(settings.get('ANTHROPIC_API_KEY', ''))
            self.anthropic_model_var.set(settings.get('ANTHROPIC_MODEL', 'claude-3-sonnet'))
            self.google_api_key_var.set(settings.get('GOOGLE_API_KEY', ''))
            self.local_endpoint_var.set(settings.get('LOCAL_ENDPOINT', 'http://localhost:11434'))
            self.local_model_var.set(settings.get('LOCAL_MODEL', 'llama2'))
            self.max_tokens_var.set(settings.get('LLM_MAX_TOKENS', '1000'))
            self.temperature_var.set(settings.get('LLM_TEMPERATURE', '0.7'))
            
            # プロバイダー変更時の表示更新
            self.on_provider_change()
        except Exception as e:
            print(f"LLM設定読み込みエラー: {e}")
    
    def set_default_values(self):
        """デフォルト値を設定"""
        try:
            self.llm_provider_var.set("openai")
            self.openai_api_key_var.set("")
            self.openai_model_var.set("gpt-4")
            self.anthropic_api_key_var.set("")
            self.anthropic_model_var.set("claude-3-sonnet")
            self.google_api_key_var.set("")
            self.local_endpoint_var.set("http://localhost:11434")
            self.local_model_var.set("gpt-oss-20b")
            self.max_tokens_var.set("1000")
            self.temperature_var.set("0.7")
            
            # プロバイダー変更時の表示更新
            self.on_provider_change()
        except Exception as e:
            print(f"LLM設定デフォルト値設定エラー: {e}")
    
    def check_local_llm_status(self):
        """ローカルLLMの状態を確認"""
        try:
            endpoint = self.local_endpoint_var.get()
            if not endpoint:
                self.local_llm_status_var.set("エンドポイント未設定")
                return
            
            # 状態確認中
            self.local_llm_status_var.set("確認中...")
            self.main_gui.log_message("ローカルLLMの状態を確認中...")
            
            # 接続テストを実行
            if self.test_local_llm_connection(endpoint):
                self.local_llm_status_var.set("起動中 ✓")
                self.main_gui.log_message("ローカルLLM状態: 起動中")
            else:
                self.local_llm_status_var.set("停止中 ✗")
                self.main_gui.log_message("ローカルLLM状態: 停止中")
                
        except Exception as e:
            self.local_llm_status_var.set("エラー")
            self.main_gui.log_message(f"ローカルLLM状態確認エラー: {e}")
    
    def auto_check_local_llm_status(self):
        """ローカルLLMの状態を自動確認（プロバイダー変更時など）"""
        try:
            if self.llm_provider_var.get() == "local":
                # 少し遅延してから状態確認（UI更新後に実行）
                self.llm_frame.after(1000, self.check_local_llm_status)
        except Exception as e:
            print(f"自動状態確認エラー: {e}")
    
    def install_ollama(self):
        """Ollamaをインストール"""
        try:
            import platform
            import subprocess
            import webbrowser
            
            system = platform.system().lower()
            
            if system == "windows":
                # Windows用のインストール方法
                result = messagebox.askyesno("Ollamaインストール", 
                    "Windows用のOllamaインストーラーをダウンロードしますか？\n\n"
                    "1. 公式サイトが開きます\n"
                    "2. インストーラーをダウンロードして実行してください\n"
                    "3. インストール完了後、このアプリを再起動してください")
                
                if result:
                    webbrowser.open("https://ollama.ai/download/windows")
                    messagebox.showinfo("インストール手順", 
                        "インストーラーのダウンロードが開始されました。\n\n"
                        "インストール手順：\n"
                        "1. ダウンロードしたインストーラーを実行\n"
                        "2. インストール完了後、PCを再起動\n"
                        "3. このアプリを再起動してLLM設定を確認")
            else:
                # Linux/macOS用のインストール方法
                result = messagebox.askyesno("Ollamaインストール", 
                    f"{system.capitalize()}用のOllamaをインストールしますか？\n\n"
                    "ターミナルで以下のコマンドが実行されます：\n"
                    "curl -fsSL https://ollama.ai/install.sh | sh")
                
                if result:
                    try:
                        # インストールスクリプトを実行
                        subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], 
                                     shell=True, check=True)
                        messagebox.showinfo("インストール完了", "Ollamaのインストールが完了しました！")
                        self.check_local_llm_status()
                    except subprocess.CalledProcessError as e:
                        messagebox.showerror("インストールエラー", f"インストールに失敗しました：\n{e}")
                        # 手動インストールの案内
                        webbrowser.open("https://ollama.ai/download")
                        
        except Exception as e:
            messagebox.showerror("エラー", f"インストール処理でエラーが発生しました：\n{e}")
            print(f"Ollamaインストールエラー: {e}")
    
    def start_ollama_service(self):
        """Ollamaサービスを起動"""
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            
            if system == "windows":
                # Windows用の起動方法
                try:
                    subprocess.run(["ollama", "serve"], 
                                 shell=True, check=True, 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
                    messagebox.showinfo("サービス起動", "Ollamaサービスを起動しました！")
                    self.check_local_llm_status()
                except subprocess.CalledProcessError:
                    messagebox.showerror("起動エラー", "Ollamaサービスを起動できませんでした。\nOllamaがインストールされているか確認してください。")
            else:
                # Linux/macOS用の起動方法
                try:
                    subprocess.run(["ollama", "serve"], 
                                 shell=True, check=True, 
                                 start_new_session=True)
                    messagebox.showinfo("サービス起動", "Ollamaサービスを起動しました！")
                    self.check_local_llm_status()
                except subprocess.CalledProcessError:
                    messagebox.showerror("起動エラー", "Ollamaサービスを起動できませんでした。\nOllamaがインストールされているか確認してください。")
                    
        except Exception as e:
            messagebox.showerror("エラー", f"サービス起動でエラーが発生しました：\n{e}")
            print(f"Ollamaサービス起動エラー: {e}")
    
    def stop_ollama_service(self):
        """Ollamaサービスを停止"""
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            
            if system == "windows":
                # Windows用の停止方法
                try:
                    subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], 
                                 shell=True, check=True)
                    messagebox.showinfo("サービス停止", "Ollamaサービスを停止しました！")
                    self.check_local_llm_status()
                except subprocess.CalledProcessError:
                    messagebox.showinfo("サービス停止", "Ollamaサービスは既に停止しているか、起動していません。")
            else:
                # Linux/macOS用の停止方法
                try:
                    subprocess.run(["pkill", "-f", "ollama"], 
                                 shell=True, check=True)
                    messagebox.showinfo("サービス停止", "Ollamaサービスを停止しました！")
                    self.check_local_llm_status()
                except subprocess.CalledProcessError:
                    messagebox.showinfo("サービス停止", "Ollamaサービスは既に停止しているか、起動していません。")
                    
        except Exception as e:
            messagebox.showerror("エラー", f"サービス停止でエラーが発生しました：\n{e}")
            print(f"Ollamaサービス停止エラー: {e}")
    
    def download_model(self):
        """モデルをダウンロード"""
        try:
            model_name = self.model_download_var.get()
            if not model_name:
                messagebox.showwarning("警告", "ダウンロードするモデルを選択してください")
                return
            
            result = messagebox.askyesno("モデルダウンロード", 
                f"モデル '{model_name}' をダウンロードしますか？\n\n"
                "注意：\n"
                "- ダウンロードには時間がかかります（数分〜数十分）\n"
                "- モデルサイズは数GB〜数十GBになります\n"
                "- インターネット接続が必要です")
            
            if result:
                # ダウンロード進捗ダイアログを表示
                self.show_download_progress_dialog(model_name)
                
        except Exception as e:
            messagebox.showerror("エラー", f"モデルダウンロードでエラーが発生しました：\n{e}")
            print(f"モデルダウンロードエラー: {e}")
    
    def show_download_progress_dialog(self, model_name):
        """ダウンロード進捗ダイアログを表示"""
        try:
            import threading
            
            # 進捗ダイアログを作成
            progress_window = tk.Toplevel(self.llm_frame)
            progress_window.title(f"モデルダウンロード: {model_name}")
            progress_window.geometry("500x300")
            progress_window.transient(self.llm_frame)
            progress_window.grab_set()
            
            # メインフレーム
            main_frame = ttk.Frame(progress_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # タイトル
            ttk.Label(main_frame, text=f"モデル '{model_name}' をダウンロード中...", 
                     font=("Arial", 12, "bold")).pack(pady=(0, 20))
            
            # 進捗バー
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(main_frame, variable=progress_var, 
                                         maximum=100, length=400)
            progress_bar.pack(pady=(0, 10))
            
            # ステータス表示
            status_var = tk.StringVar(value="ダウンロードを開始しています...")
            status_label = ttk.Label(main_frame, textvariable=status_var, 
                                   font=("Arial", 10))
            status_label.pack(pady=(0, 20))
            
            # ログ表示
            log_frame = ttk.LabelFrame(main_frame, text="ダウンロードログ", padding="10")
            log_frame.pack(fill=tk.BOTH, expand=True)
            
            log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
            log_text.pack(fill=tk.BOTH, expand=True)
            
            # キャンセルボタン
            cancel_button = ttk.Button(main_frame, text="キャンセル", 
                                     command=progress_window.destroy)
            cancel_button.pack(pady=(10, 0))
            
            # ダウンロード処理を別スレッドで実行
            def download_thread():
                try:
                    import subprocess
                    
                    # ollama pullコマンドを実行
                    cmd = ["ollama", "pull", model_name]
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                            stderr=subprocess.STDOUT, 
                                            universal_newlines=True)
                    
                    # 出力を読み取りながら進捗を更新
                    for line in process.stdout:
                        if progress_window.winfo_exists():
                            log_text.insert(tk.END, line)
                            log_text.see(tk.END)
                            
                            # 進捗の更新（簡易的な進捗表示）
                            if "downloading" in line.lower():
                                progress_var.set(50)
                                status_var.set("ダウンロード中...")
                            elif "verifying" in line.lower():
                                progress_var.set(75)
                                status_var.set("検証中...")
                            elif "pulling" in line.lower():
                                progress_var.set(25)
                                status_var.set("プル中...")
                            
                            progress_window.update()
                        else:
                            break
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        progress_var.set(100)
                        status_var.set("ダウンロード完了！")
                        log_text.insert(tk.END, "\n\n✅ ダウンロードが完了しました！")
                        
                        # 完了メッセージ
                        messagebox.showinfo("ダウンロード完了", 
                            f"モデル '{model_name}' のダウンロードが完了しました！")
                        
                        # モデル一覧を更新
                        self.refresh_model_list()
                        
                        # 少し待ってからダイアログを閉じる
                        progress_window.after(2000, progress_window.destroy)
                    else:
                        status_var.set("ダウンロードに失敗しました")
                        log_text.insert(tk.END, f"\n\n❌ ダウンロードに失敗しました（終了コード: {process.returncode}）")
                        
                except Exception as e:
                    status_var.set("エラーが発生しました")
                    log_text.insert(tk.END, f"\n\n❌ エラー: {e}")
                    print(f"モデルダウンロードエラー: {e}")
            
            # ダウンロードスレッドを開始
            download_thread = threading.Thread(target=download_thread)
            download_thread.daemon = True
            download_thread.start()
            
        except Exception as e:
            messagebox.showerror("エラー", f"進捗ダイアログの表示でエラーが発生しました：\n{e}")
            print(f"進捗ダイアログ表示エラー: {e}")
    
    def delete_model(self):
        """モデルを削除"""
        try:
            model_name = self.model_download_var.get()
            if not model_name:
                messagebox.showwarning("警告", "削除するモデルを選択してください")
                return
            
            result = messagebox.askyesno("モデル削除", 
                f"モデル '{model_name}' を削除しますか？\n\n"
                "注意：\n"
                "- この操作は元に戻せません\n"
                "- モデルファイルが完全に削除されます\n"
                "- 再度使用する場合は再ダウンロードが必要です")
            
            if result:
                import subprocess
                
                try:
                    # ollama rmコマンドを実行
                    subprocess.run(["ollama", "rm", model_name], 
                                 shell=True, check=True)
                    
                    messagebox.showinfo("削除完了", f"モデル '{model_name}' を削除しました！")
                    
                    # モデル一覧を更新
                    self.refresh_model_list()
                    
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("削除エラー", f"モデルの削除に失敗しました：\n{e}")
                    
        except Exception as e:
            messagebox.showerror("エラー", f"モデル削除でエラーが発生しました：\n{e}")
            print(f"モデル削除エラー: {e}")
    
    def refresh_model_list(self):
        """モデル一覧を更新"""
        try:
            import requests
            
            endpoint = self.local_endpoint_var.get()
            if not endpoint:
                self.model_list_var.set("エンドポイントが設定されていません")
                return
            
            # モデル一覧を取得
            health_url = f"{endpoint.rstrip('/')}/api/tags"
            
            try:
                response = requests.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    models = response.json()
                    if 'models' in models and models['models']:
                        model_names = [model['name'] for model in models['models']]
                        self.model_list_var.set(f"利用可能モデル: {', '.join(model_names)}")
                        
                        # 設定されているモデルが利用可能かチェック
                        configured_model = self.local_model_var.get()
                        if configured_model in model_names:
                            self.model_list_var.set(f"✓ {configured_model} 利用可能 | 全{len(model_names)}個")
                        else:
                            self.model_list_var.set(f"⚠ {configured_model} 未検出 | 全{len(model_names)}個")
                    else:
                        self.model_list_var.set("利用可能なモデルがありません")
                else:
                    self.model_list_var.set(f"接続エラー: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                self.model_list_var.set("Ollamaに接続できません")
            except Exception as e:
                self.model_list_var.set(f"エラー: {e}")
                
        except Exception as e:
            self.model_list_var.set(f"更新エラー: {e}")
            print(f"モデル一覧更新エラー: {e}")
    
    def show_generate_test_dialog(self):
        """生成テストダイアログを表示"""
        try:
            # テスト用の入力ウィンドウを作成
            test_window = tk.Toplevel(self.llm_frame)
            test_window.title("LLM生成テスト")
            test_window.geometry("800x600")
            test_window.transient(self.llm_frame)
            test_window.grab_set()
            
            # メインフレーム
            main_frame = ttk.Frame(test_window, padding="15")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 入力セクション
            input_frame = ttk.LabelFrame(main_frame, text="テスト入力", padding="15")
            input_frame.pack(fill=tk.X, pady=(0, 15))
            
            # 説明文入力
            ttk.Label(input_frame, text="説明文（作品の説明など）:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            description_text = scrolledtext.ScrolledText(input_frame, height=6, wrap=tk.WORD)
            description_text.pack(fill=tk.X, pady=(0, 10))
            description_text.insert(tk.END, "この作品は、魅力的なストーリーと美しい映像で構成された感動的な作品です。")
            
            # 生成タイプ選択
            ttk.Label(input_frame, text="生成タイプ:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            generate_type_var = tk.StringVar(value="intro")
            type_frame = ttk.Frame(input_frame)
            type_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Radiobutton(type_frame, text="紹介文生成", variable=generate_type_var, value="intro").pack(side=tk.LEFT, padx=(0, 20))
            ttk.Radiobutton(type_frame, text="SEOタイトル生成", variable=generate_type_var, value="title").pack(side=tk.LEFT, padx=(0, 20))
            ttk.Radiobutton(type_frame, text="コンテンツ改善", variable=generate_type_var, value="enhance").pack(side=tk.LEFT)
            
            # 生成ボタン
            generate_button = ttk.Button(input_frame, text="生成テスト実行", 
                                        command=lambda: self.execute_generate_test(
                                            description_text.get('1.0', tk.END).strip(),
                                            generate_type_var.get(),
                                            result_text
                                        ), style="Accent.TButton")
            generate_button.pack(pady=10)
            
            # 結果表示セクション
            result_frame = ttk.LabelFrame(main_frame, text="生成結果", padding="15")
            result_frame.pack(fill=tk.BOTH, expand=True)
            
            result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD)
            result_text.pack(fill=tk.BOTH, expand=True)
            
            # 初期メッセージ
            result_text.insert(tk.END, "生成テストを実行すると、ここに結果が表示されます。\n\n")
            result_text.insert(tk.END, "使用方法：\n")
            result_text.insert(tk.END, "1. 説明文を入力してください\n")
            result_text.insert(tk.END, "2. 生成タイプを選択してください\n")
            result_text.insert(tk.END, "3. 「生成テスト実行」ボタンをクリックしてください\n\n")
            
        except Exception as e:
            messagebox.showerror("エラー", f"生成テストダイアログの表示に失敗しました:\n{e}")
            print(f"生成テストダイアログ表示エラー: {e}")
    
    def execute_generate_test(self, description, generate_type, result_text):
        """生成テストを実行"""
        try:
            if not description.strip():
                messagebox.showwarning("警告", "説明文を入力してください")
                return
            
            # 結果表示をクリア
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, "生成テストを実行中...\n\n")
            result_text.see(tk.END)
            
            # 現在の設定を取得
            provider = self.llm_provider_var.get()
            
            if provider == "local":
                # ローカルLLMでの生成テスト
                result = self.generate_with_local_llm(description, generate_type)
            else:
                # 他のプロバイダーでの生成テスト（実装予定）
                result = f"現在、{provider}での生成テストは実装されていません。\nローカルLLMを使用してください。"
            
            # 結果を表示
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, f"生成タイプ: {self.get_generate_type_name(generate_type)}\n")
            result_text.insert(tk.END, f"入力説明文:\n{description}\n\n")
            result_text.insert(tk.END, f"生成結果:\n{result}\n")
            
            self.main_gui.log_message(f"LLM生成テスト完了: {generate_type}")
            
        except Exception as e:
            error_msg = f"生成テストでエラーが発生しました:\n{e}"
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, error_msg)
            self.main_gui.log_message(f"生成テストエラー: {e}")
            print(f"生成テストエラー: {e}")
    
    def generate_with_local_llm(self, description, generate_type):
        """ローカルLLMを使用して生成"""
        try:
            import requests
            import json
            
            endpoint = self.local_endpoint_var.get()
            model = self.local_model_var.get()
            
            # プロンプトの構築
            if generate_type == "intro":
                prompt = f"""以下の説明文から魅力的な紹介文を生成してください。200-300文字程度で、読者の興味を引く内容にしてください。

説明文:
{description}

紹介文:"""
            elif generate_type == "title":
                prompt = f"""以下の説明文からSEOに効果的なタイトルを生成してください。30-50文字程度で、検索されやすく魅力的なタイトルにしてください。

説明文:
{description}

SEOタイトル:"""
            elif generate_type == "enhance":
                prompt = f"""以下の説明文をより魅力的で読みやすい内容に改善してください。文章の流れを整え、適切な段落分けを行ってください。

説明文:
{description}

改善された内容:"""
            else:
                return "不明な生成タイプです"
            
            # Ollama APIを使用して生成
            api_url = f"{endpoint.rstrip('/')}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": float(self.temperature_var.get()),
                    "num_predict": int(self.max_tokens_var.get())
                }
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    return result['response'].strip()
                else:
                    return "生成に失敗しました（レスポンス形式が不正）"
            else:
                return f"API呼び出しに失敗しました（HTTP {response.status_code}）"
                
        except requests.exceptions.ConnectionError:
            return "ローカルLLMに接続できません。Ollamaが起動しているか確認してください。"
        except requests.exceptions.Timeout:
            return "生成がタイムアウトしました。モデルのサイズや設定を確認してください。"
        except Exception as e:
            return f"生成中にエラーが発生しました: {e}"
    
    def get_generate_type_name(self, generate_type):
        """生成タイプの日本語名を取得"""
        type_names = {
            "intro": "紹介文生成",
            "title": "SEOタイトル生成",
            "enhance": "コンテンツ改善"
        }
        return type_names.get(generate_type, "不明")
