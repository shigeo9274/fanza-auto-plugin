#!/usr/bin/env python3
"""Chrome設定タブ - ブラウザ設定とスクレイピングテスト機能"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional
import traceback

class ChromeSettingsTab:
    def __init__(self, notebook, parent):
        self.notebook = notebook
        self.parent = parent
        self.create_tab()
        # タブ作成後に設定を自動読み込み
        self.load_chrome_settings()
        
    def create_tab(self):
        """Chrome設定タブを作成"""
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Chrome設定・テスト")
        
        # メインフレーム（スクロール可能）
        main_canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # メインフレーム
        main_frame = ttk.Frame(scrollable_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="Chrome設定・スクレイピングテスト", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 設定フレーム
        self.create_settings_frame(main_frame)
        
        # テストフレーム
        self.create_test_frame(main_frame)
        
        # ログフレーム
        self.create_log_frame(main_frame)
        
        # スクロール設定
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_settings_frame(self, parent):
        """設定フレームを作成"""
        settings_frame = ttk.LabelFrame(parent, text="Chrome設定", padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 設定項目
        settings_grid = ttk.Frame(settings_frame)
        settings_grid.pack(fill=tk.X)
        
        # 1行目
        row1 = ttk.Frame(settings_grid)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        # ブラウザ使用
        ttk.Label(row1, text="ブラウザ使用:").pack(side=tk.LEFT, padx=(0, 10))
        self.use_browser_var = tk.BooleanVar(value=True)
        use_browser_check = ttk.Checkbutton(row1, text="Chromeを使用", 
                                          variable=self.use_browser_var)
        use_browser_check.pack(side=tk.LEFT, padx=(0, 20))
        
        # ヘッドレスモード
        ttk.Label(row1, text="ヘッドレスモード:").pack(side=tk.LEFT, padx=(0, 10))
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(row1, text="無画面実行", 
                                       variable=self.headless_var)
        headless_check.pack(side=tk.LEFT)
        
        # 2行目
        row2 = ttk.Frame(settings_grid)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        # 年齢認証ボタンのXPath
        ttk.Label(row2, text="年齢認証XPath:").pack(side=tk.LEFT, padx=(0, 10))
        self.click_xpath_var = tk.StringVar(
            value='//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a'
        )
        xpath_entry = ttk.Entry(row2, textvariable=self.click_xpath_var, width=60)
        xpath_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # ページ待機時間
        ttk.Label(row2, text="待機時間(秒):").pack(side=tk.LEFT, padx=(0, 10))
        self.page_wait_var = tk.StringVar(value="5")
        wait_entry = ttk.Entry(row2, textvariable=self.page_wait_var, width=5)
        wait_entry.pack(side=tk.LEFT)
        
        # 3行目
        row3 = ttk.Frame(settings_grid)
        row3.pack(fill=tk.X, pady=(0, 10))
        
        # 説明文セレクタ
        ttk.Label(row3, text="説明文セレクタ:").pack(side=tk.LEFT, padx=(0, 10))
        self.description_selectors_var = tk.StringVar(
            value='meta[name=description],p.tx-productComment,p.summary__txt,p.mg-b20,p.text-overflow,div[class*="description"],div[class*="detail"],div[class*="info"],div[class*="content"]'
        )
        description_entry = ttk.Entry(row3, textvariable=self.description_selectors_var, width=80)
        description_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 4行目
        row4 = ttk.Frame(settings_grid)
        row4.pack(fill=tk.X, pady=(0, 10))
        
        # レビュー文セレクタ
        ttk.Label(row4, text="レビュー文セレクタ:").pack(side=tk.LEFT, padx=(0, 10))
        self.review_selectors_var = tk.StringVar(
            value='#review,div[class*="review"],div[class*="comment"],div[class*="user"]'
        )
        review_entry = ttk.Entry(row4, textvariable=self.review_selectors_var, width=80)
        review_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # 5行目
        row5 = ttk.Frame(settings_grid)
        row5.pack(fill=tk.X, pady=(0, 10))
        
        # 設定保存ボタン
        save_button = ttk.Button(row5, text="設定を保存", 
                                command=self.save_chrome_settings,
                                style="Accent.TButton")
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 設定読み込みボタン
        load_button = ttk.Button(row5, text="設定を読み込み", 
                                command=self.load_chrome_settings)
        load_button.pack(side=tk.LEFT)
        
        # デバッグ用：フレームの境界を表示
        settings_frame.configure(relief="solid", borderwidth=2)
        
    def create_test_frame(self, parent):
        """テストフレームを作成"""
        test_frame = ttk.LabelFrame(parent, text="スクレイピングテスト", padding="15")
        test_frame.pack(fill=tk.X, pady=(0, 20))
        
        # テストURL入力
        url_frame = ttk.Frame(test_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_frame, text="テストURL:").pack(side=tk.LEFT, padx=(0, 10))
        self.test_url_var = tk.StringVar(
            value="https://video.dmm.co.jp/amateur/content/?id=mfcs176"
        )
        url_entry = ttk.Entry(url_frame, textvariable=self.test_url_var, width=80)
        url_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        # テスト実行ボタン（目立つようにスタイルを変更）
        test_button = ttk.Button(url_frame, text="🚀 テスト実行", 
                                command=self.run_scraping_test,
                                style="Accent.TButton")
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # テスト結果表示
        result_frame = ttk.Frame(test_frame)
        result_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(result_frame, text="テスト結果:").pack(anchor=tk.W)
        
        # 結果テキスト
        self.result_text = scrolledtext.ScrolledText(result_frame, height=8, width=100)
        self.result_text.pack(fill=tk.X, pady=(5, 0))
        
        # デバッグ用：フレームの境界を表示
        test_frame.configure(relief="solid", borderwidth=2)
        
    def create_log_frame(self, parent):
        """ログフレームを作成"""
        log_frame = ttk.LabelFrame(parent, text="実行ログ", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # ログテキスト
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ログクリアボタン
        clear_button = ttk.Button(log_frame, text="ログをクリア", 
                                 command=self.clear_log)
        clear_button.pack(pady=(10, 0))
        
        # デバッグ用：フレームの境界を表示
        log_frame.configure(relief="solid", borderwidth=2)
        
    def save_chrome_settings(self):
        """Chrome設定を保存"""
        try:
            # 現在の設定を取得
            current_settings = self.parent.settings_manager.load_settings()
            if not current_settings:
                current_settings = {}
            
            # Chrome設定のみを更新（他の設定は保持）
            chrome_settings = {
                "USE_BROWSER": bool(self.use_browser_var.get()),
                "HEADLESS": bool(self.headless_var.get()),
                "CLICK_XPATH": str(self.click_xpath_var.get()),
                "PAGE_WAIT_SEC": int(self.page_wait_var.get()),
                "DESCRIPTION_SELECTORS": str(self.description_selectors_var.get()),
                "REVIEW_SELECTORS": str(self.review_selectors_var.get())
            }
            
            # デバッグ情報をログに出力
            debug_msg = f"保存する設定: USE_BROWSER={chrome_settings['USE_BROWSER']}, HEADLESS={chrome_settings['HEADLESS']}, CLICK_XPATH={chrome_settings['CLICK_XPATH']}, PAGE_WAIT_SEC={chrome_settings['PAGE_WAIT_SEC']}"
            self.log_message(debug_msg)
            print(f"DEBUG: {debug_msg}")
            
            print(f"DEBUG: 保存前の既存設定 - HEADLESS: {current_settings.get('HEADLESS', 'NOT_FOUND')}")
            
            # 既存の設定とマージ
            current_settings.update(chrome_settings)
            
            print(f"DEBUG: 保存後の設定 - HEADLESS: {current_settings.get('HEADLESS', 'NOT_FOUND')}")
            
            # 設定を保存
            if self.parent.settings_manager.save_settings(current_settings):
                messagebox.showinfo("成功", "Chrome設定を保存しました")
                self.log_message("Chrome設定を保存しました")
            else:
                messagebox.showerror("エラー", "設定の保存に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存エラー: {e}")
            self.log_message(f"設定保存エラー: {e}")
            
    def load_chrome_settings(self):
        """Chrome設定を読み込み"""
        try:
            # 現在の設定を読み込み
            current_settings = self.parent.settings_manager.load_settings()
            if current_settings:
                # 設定値を設定（デフォルト値付き）
                use_browser = current_settings.get("USE_BROWSER", True)
                headless = current_settings.get("HEADLESS", True)
                click_xpath = current_settings.get("CLICK_XPATH", 
                    '//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a')
                page_wait = current_settings.get("PAGE_WAIT_SEC", 5)
                description_selectors = current_settings.get("DESCRIPTION_SELECTORS", 
                    'meta[name=description],p.tx-productComment,p.summary__txt,p.mg-b20,p.text-overflow,div[class*="description"],div[class*="detail"],div[class*="info"],div[class*="content"]')
                review_selectors = current_settings.get("REVIEW_SELECTORS", 
                    '#review,div[class*="review"],div[class*="comment"],div[class*="user"]')
                
                # 型変換の確実性を向上
                if isinstance(use_browser, str):
                    use_browser = use_browser.lower() in ('true', '1', 'yes', 'on')
                if isinstance(headless, str):
                    headless = headless.lower() in ('true', '1', 'yes', 'on')
                if isinstance(page_wait, str):
                    try:
                        page_wait = int(page_wait)
                    except ValueError:
                        page_wait = 5
                
                self.use_browser_var.set(use_browser)
                self.headless_var.set(headless)
                self.click_xpath_var.set(click_xpath)
                self.page_wait_var.set(str(page_wait))
                self.description_selectors_var.set(description_selectors)
                self.review_selectors_var.set(review_selectors)
                
                # デバッグ情報をログに出力
                debug_msg = f"設定読み込み完了: USE_BROWSER={use_browser}, HEADLESS={headless}, CLICK_XPATH={click_xpath}, PAGE_WAIT_SEC={page_wait}"
                self.log_message(debug_msg)
                print(f"DEBUG: {debug_msg}")
                
                print(f"DEBUG: 設定ファイルから読み込まれた値 - HEADLESS: {headless} (型: {type(headless)})")
                print(f"DEBUG: 設定ファイルから読み込まれた値 - USE_BROWSER: {use_browser} (型: {type(use_browser)})")
                
                messagebox.showinfo("成功", "Chrome設定を読み込みました")
                self.log_message("Chrome設定を読み込みました")
            else:
                messagebox.showwarning("警告", "設定ファイルが見つかりません")
                
        except Exception as e:
            error_msg = f"設定読み込みエラー: {e}"
            messagebox.showerror("エラー", error_msg)
            self.log_message(error_msg)
            
    def run_scraping_test(self):
        """スクレイピングテストを実行"""
        url = self.test_url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "テストURLを入力してください")
            return
            
        # テスト実行を別スレッドで実行
        test_thread = threading.Thread(target=self._run_test_thread, args=(url,))
        test_thread.daemon = True
        test_thread.start()
        
    def _run_test_thread(self, url):
        """テスト実行スレッド"""
        try:
            self.log_message(f"スクレイピングテスト開始: {url}")
            
            # 設定を取得
            use_browser = self.use_browser_var.get()
            headless = self.headless_var.get()
            click_xpath = self.click_xpath_var.get()
            page_wait = int(self.page_wait_var.get())
            description_selectors = self.description_selectors_var.get()
            review_selectors = self.review_selectors_var.get()
            
            # スクレイピングテスト実行
            from config import Settings
            from scrape import fetch_html, extract_specific_elements
            
            # テスト用設定
            test_settings = Settings(
                use_browser=use_browser,
                headless=headless,
                click_xpath=click_xpath,
                page_wait_sec=page_wait,
                description_selectors=description_selectors.split(','),
                review_selectors=review_selectors.split(',')
            )
            
            self.log_message("ChromeでHTML取得中...")
            html = fetch_html(url, settings=test_settings)
            
            if html:
                self.log_message("HTML取得成功")
                self.log_message(f"HTMLサイズ: {len(html)}文字")
                
                # 説明文とレビューを抽出
                description, review = extract_specific_elements(html, test_settings)
                
                # 結果を表示
                result = f"""=== スクレイピングテスト結果 ===
URL: {url}
HTMLサイズ: {len(html)}文字

説明文:
{description}

レビュー:
{review}

=== テスト完了 ===
"""
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, result)
                
                self.log_message("スクレイピングテスト完了")
                
            else:
                self.log_message("HTML取得失敗")
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, "HTML取得に失敗しました")
                
        except Exception as e:
            error_msg = f"テスト実行エラー: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, error_msg)
            
    def log_message(self, message):
        """ログメッセージを追加"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # GUIスレッドでログを更新
        self.parent.root.after(0, self._update_log, log_entry)
        
    def _update_log(self, log_entry):
        """ログを更新（GUIスレッド）"""
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """ログをクリア"""
        self.log_text.delete(1.0, tk.END)
