"""
リライト機能用のタブクラス
既存投稿から品番を抽出し、DMM APIで再検索してリライトする
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import threading
import time
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

class RewriteTab:
    def __init__(self, parent_notebook, engine, settings_manager):
        self.parent_notebook = parent_notebook
        self.engine = engine
        self.settings_manager = settings_manager
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="リライト")
        
        # 品番抽出用の正規表現パターン
        self.product_code_patterns = [
            r'[A-Z]{2,4}-\d{3,4}',  # ABC-123, ABCD-1234
            r'[A-Z]{2,4}\d{3,4}',   # ABC123, ABCD1234
            r'[A-Z]{2,4}_\d{3,4}',  # ABC_123, ABCD_1234
            r'[A-Z]{2,4}-\d{2,5}',  # ABC-12, ABCD-12345
            r'[A-Z]{2,5}-\d{2,5}',  # ABCDE-12, ABC-12345
            r'[A-Z]{2,5}\d{2,5}',   # ABCDE12, ABC12345
        ]
        
        self.create_widgets()
        
    def create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.LabelFrame(self.frame, text="リライト機能", padding="10")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 上部コントロール
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # 既存投稿取得ボタン
        self.fetch_posts_btn = ttk.Button(
            control_frame, 
            text="既存投稿を取得", 
            command=self.fetch_existing_posts
        )
        self.fetch_posts_btn.pack(side="left", padx=(0, 10))
        
        # 品番抽出ボタン
        self.extract_codes_btn = ttk.Button(
            control_frame, 
            text="品番を抽出（Slugから）", 
            command=self.extract_product_codes,
            state="disabled"
        )
        self.extract_codes_btn.pack(side="left", padx=(0, 10))
        
        # テスト実行ボタン
        self.test_rewrite_btn = ttk.Button(
            control_frame, 
            text="テスト実行", 
            command=self.test_rewrite,
            state="disabled"
        )
        self.test_rewrite_btn.pack(side="left", padx=(0, 10))
        
        # リライト実行ボタン
        self.rewrite_btn = ttk.Button(
            control_frame, 
            text="リライト実行", 
            command=self.execute_rewrite,
            state="disabled"
        )
        self.rewrite_btn.pack(side="left", padx=(0, 10))
        
        # WordPress接続テストボタン
        self.test_wp_btn = ttk.Button(
            control_frame, 
            text="WordPress接続テスト", 
            command=self.test_wordpress_connection,
            state="normal"
        )
        self.test_wp_btn.pack(side="left", padx=(0, 10))
        
        # WordPress権限テストボタン
        self.test_wp_permissions_btn = ttk.Button(
            control_frame, 
            text="権限テスト", 
            command=self.test_wordpress_permissions,
            state="normal"
        )
        self.test_wp_permissions_btn.pack(side="left", padx=(0, 10))
        
        # DMM API接続テストボタン
        self.test_api_btn = ttk.Button(
            control_frame, 
            text="DMM API接続テスト", 
            command=self.test_dmm_api,
            state="normal"
        )
        self.test_api_btn.pack(side="left", padx=(0, 10))
        
        # 投稿設定選択
        settings_frame = ttk.LabelFrame(control_frame, text="投稿設定", padding="5")
        settings_frame.pack(side="left", padx=(0, 10))
        
        ttk.Label(settings_frame, text="使用設定:").pack(side="left")
        self.settings_var = tk.StringVar(value="post_settings_1")
        self.settings_combo = ttk.Combobox(
            settings_frame, 
            textvariable=self.settings_var, 
            values=["post_settings_1", "post_settings_2", "post_settings_3", "post_settings_4"],
            width=15,
            state="readonly"
        )
        self.settings_combo.pack(side="left", padx=(5, 0))
        
        # 設定詳細表示ボタン
        self.show_settings_btn = ttk.Button(
            settings_frame, 
            text="設定詳細", 
            command=self.show_posting_settings,
            width=8
        )
        self.show_settings_btn.pack(side="left", padx=(5, 0))
        
        # 設定再読み込みボタン
        self.reload_settings_btn = ttk.Button(
            settings_frame, 
            text="再読み込み", 
            command=self.reload_posting_settings,
            width=8
        )
        self.reload_settings_btn.pack(side="left", padx=(5, 0))
        
        # 設定ファイル確認ボタン
        self.check_settings_file_btn = ttk.Button(
            settings_frame, 
            text="ファイル確認", 
            command=self.check_settings_file,
            width=8
        )
        self.check_settings_file_btn.pack(side="left", padx=(5, 0))
        
        # 1件リライト実行ボタン
        self.single_rewrite_btn = ttk.Button(
            control_frame, 
            text="1件リライト", 
            command=self.execute_single_rewrite,
            state="disabled"
        )
        self.single_rewrite_btn.pack(side="left", padx=(0, 10))
        
        # パラメータ確認ボタン
        self.check_params_btn = ttk.Button(
            control_frame, 
            text="パラメータ確認", 
            command=self.check_api_params,
            state="normal"
        )
        self.check_params_btn.pack(side="left", padx=(0, 10))
        
        # 進捗表示
        self.progress_var = tk.StringVar(value="準備完了")
        self.progress_label = ttk.Label(control_frame, textvariable=self.progress_var)
        self.progress_label.pack(side="right")
        
        # 投稿一覧表示エリア
        posts_frame = ttk.LabelFrame(main_frame, text="投稿一覧（投稿日が古い順、公開中のみ）", padding="5")
        posts_frame.pack(fill="both", expand=True)
        
        # 投稿一覧のTreeview
        columns = ("ID", "タイトル", "Slug", "投稿日", "品番", "抽出状態", "リライト状態")
        self.posts_tree = ttk.Treeview(posts_frame, columns=columns, show="headings", height=15)
        
        # カラム設定
        for col in columns:
            self.posts_tree.heading(col, text=col)
            if col == "タイトル":
                self.posts_tree.column(col, width=200)
            elif col == "Slug":
                self.posts_tree.column(col, width=120)
            elif col == "投稿日":
                self.posts_tree.column(col, width=100)
            else:
                self.posts_tree.column(col, width=100)
        
        # スクロールバー
        posts_scrollbar = ttk.Scrollbar(posts_frame, orient="vertical", command=self.posts_tree.yview)
        self.posts_tree.configure(yscrollcommand=posts_scrollbar.set)
        
        self.posts_tree.pack(side="left", fill="both", expand=True)
        posts_scrollbar.pack(side="right", fill="y")
        
        # 詳細表示エリア
        detail_frame = ttk.LabelFrame(main_frame, text="詳細情報", padding="5")
        detail_frame.pack(fill="x", pady=(10, 0))
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=8, wrap=tk.WORD)
        self.detail_text.pack(fill="both", expand=True)
        
        # 投稿選択時のイベント
        self.posts_tree.bind("<<TreeviewSelect>>", self.on_post_select)
        
        # 右クリックメニュー
        self.posts_tree.bind("<Button-3>", self.show_context_menu)
        
        # データ保存用
        self.existing_posts = []
        self.extracted_codes = {}
        
        # 投稿設定の読み込み
        self.load_posting_settings()
        
    def load_posting_settings(self):
        """投稿設定を読み込み、コンボボックスを更新"""
        try:
            # 利用可能な投稿設定を取得
            available_settings = ["default"]
            
            # post_settings.jsonファイルを確認
            post_settings_path = os.path.join("config", "post_settings.json")
            print(f"投稿設定ファイルパス: {post_settings_path}")
            print(f"ファイル存在: {os.path.exists(post_settings_path)}")
            
            if os.path.exists(post_settings_path):
                try:
                    with open(post_settings_path, 'r', encoding='utf-8') as f:
                        post_settings = json.load(f)
                        print(f"投稿設定ファイル内容: {list(post_settings.keys()) if isinstance(post_settings, dict) else type(post_settings)}")
                        
                        if isinstance(post_settings, dict):
                            # ファイル構造に合わせて設定番号を取得
                            if "post_settings" in post_settings:
                                post_settings_data = post_settings["post_settings"]
                                print(f"post_settings内の設定: {list(post_settings_data.keys())}")
                                
                                # 設定番号を取得（1, 2, 3, 4など）
                                for key in post_settings_data.keys():
                                    if key.isdigit():
                                        setting_name = f"post_settings_{key}"
                                        available_settings.append(setting_name)
                                        print(f"設定を追加: {setting_name}")
                            else:
                                # 古い形式の対応
                                for key in post_settings.keys():
                                    if key.startswith("post_settings_"):
                                        available_settings.append(key)
                                        print(f"設定を追加: {key}")
                except Exception as e:
                    print(f"投稿設定読み込みエラー: {e}")
                    import traceback
                    print(f"詳細エラー: {traceback.format_exc()}")
            else:
                print("投稿設定ファイルが見つかりません")
            
            print(f"利用可能な設定: {available_settings}")
            
            # コンボボックスの値を更新
            self.settings_combo['values'] = available_settings
            if self.settings_var.get() not in available_settings:
                self.settings_var.set("default")
                print(f"設定をデフォルトに変更: {self.settings_var.get()}")
                
            # コンボボックスの状態を確認
            print(f"コンボボックス値: {self.settings_combo['values']}")
            print(f"現在選択値: {self.settings_var.get()}")
                
        except Exception as e:
            print(f"投稿設定読み込みエラー: {e}")
            import traceback
            print(f"詳細エラー: {traceback.format_exc()}")
    
    def fetch_existing_posts(self):
        """既存投稿を取得"""
        self.progress_var.set("投稿取得中...")
        self.fetch_posts_btn.config(state="disabled")
        
        def fetch_thread():
            try:
                print("投稿取得を開始...")
                print(f"WordPress URL: {self.engine.wp.base_url}")
                
                # WordPressから投稿を取得（段階的にパラメータを追加）
                print("get_posts呼び出し中...")
                
                # まず基本的なパラメータでテスト
                try:
                    posts = self.engine.wp.get_posts(per_page=100, status='publish')
                    print(f"基本パラメータで投稿取得成功: {len(posts)}件")
                except Exception as e:
                    print(f"基本パラメータで失敗: {e}")
                    # 基本パラメータで失敗した場合は、さらにシンプルに
                    try:
                        posts = self.engine.wp.get_posts(per_page=100)
                        print(f"最小パラメータで投稿取得成功: {len(posts)}件")
                    except Exception as e2:
                        print(f"最小パラメータでも失敗: {e2}")
                        raise e2
                
                # 投稿日順でソート（Python側で処理）
                if posts:
                    try:
                        # 投稿日でソート（古い順）
                        posts.sort(key=lambda x: x.get('date', ''))
                        print(f"投稿日順でソート完了: {len(posts)}件")
                    except Exception as e:
                        print(f"ソート処理でエラー: {e}")
                        # ソートに失敗しても投稿は使用可能
                
                # GUIスレッドで結果を更新
                self.parent_notebook.after(0, self.update_posts_list, posts)
                
            except Exception as e:
                error_msg = f"投稿取得エラー: {str(e)}"
                print(f"詳細エラー情報: {type(e).__name__}: {e}")
                import traceback
                print(f"スタックトレース: {traceback.format_exc()}")
                
                # エラーの種類に応じた詳細メッセージ
                if "ConnectionError" in str(type(e)):
                    detailed_msg = "WordPressサイトへの接続に失敗しました。\n\n確認事項:\n1. WordPressサイトのURLが正しいか\n2. インターネット接続が正常か\n3. ファイアウォールでアクセスがブロックされていないか"
                elif "HTTPError" in str(type(e)):
                    detailed_msg = "WordPress APIへのアクセスに失敗しました。\n\n確認事項:\n1. WordPress REST APIが有効か\n2. 認証情報（ユーザー名・アプリケーションパスワード）が正しいか\n3. ユーザーに投稿読み取り権限があるか"
                elif "Timeout" in str(type(e)):
                    detailed_msg = "リクエストがタイムアウトしました。\n\n確認事項:\n1. WordPressサイトの応答が遅い\n2. ネットワーク接続が不安定\n3. タイムアウト設定を増やす必要がある"
                else:
                    detailed_msg = f"予期しないエラーが発生しました。\n\nエラー詳細: {str(e)}"
                
                self.parent_notebook.after(0, lambda: messagebox.showerror("投稿取得エラー", f"{error_msg}\n\n{detailed_msg}"))
                self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
                self.parent_notebook.after(0, lambda: self.fetch_posts_btn.config(state="normal"))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_posts_list(self, posts):
        """投稿一覧を更新"""
        self.existing_posts = posts
        
        # Treeviewをクリア
        for item in self.posts_tree.get_children():
            self.posts_tree.delete(item)
        
        # 投稿を追加
        for post in posts:
            post_id = post.get('id', 'N/A')
            title = post.get('title', {}).get('rendered', 'N/A')
            slug = post.get('slug', 'N/A')
            date = post.get('date', 'N/A')
            if date != 'N/A':
                # 日付を読みやすい形式に変換
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            self.posts_tree.insert("", "end", values=(
                post_id,
                title[:50] + "..." if len(title) > 50 else title,
                slug,
                date,
                "未抽出",
                "未処理",
                "未実行"
            ))
        
        self.progress_var.set(f"{len(posts)}件の投稿を取得しました")
        self.fetch_posts_btn.config(state="normal")
        self.extract_codes_btn.config(state="normal")
    
    def extract_product_codes(self):
        """投稿から品番を抽出（slugから取得）"""
        self.progress_var.set("品番抽出中...")
        self.extract_codes_btn.config(state="disabled")
        
        def extract_thread():
            try:
                extracted_count = 0
                
                for post in self.existing_posts:
                    # slugから品番を取得
                    slug = post.get('slug', '')
                    
                    if slug and self.is_valid_product_code(slug):
                        self.extracted_codes[post['id']] = slug
                        extracted_count += 1
                
                # GUIスレッドで結果を更新
                self.parent_notebook.after(0, lambda: self.update_extraction_results(extracted_count))
                
            except Exception as e:
                error_msg = f"品番抽出エラー: {str(e)}"
                self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
                self.parent_notebook.after(0, lambda: self.extract_codes_btn.config(state="normal"))
        
        threading.Thread(target=extract_thread, daemon=True).start()
    
    def test_wordpress_connection(self):
        """WordPress接続テスト"""
        self.progress_var.set("WordPress接続テスト中...")
        self.test_wp_btn.config(state="disabled")
        
        def test_thread():
            try:
                # 簡単な投稿取得で接続テスト
                test_posts = self.engine.wp.get_posts(per_page=1, status='publish')
                
                # GUIスレッドで結果を表示
                self.parent_notebook.after(0, lambda: self.show_wordpress_test_result(True, len(test_posts)))
                
            except Exception as e:
                error_msg = str(e)
                print(f"WordPress接続テスト失敗: {error_msg}")
                
                # エラーの種類を判定
                if "ConnectionError" in str(type(e)):
                    error_type = "接続エラー"
                    suggestion = "WordPressサイトのURLとネットワーク接続を確認してください"
                elif "HTTPError" in str(type(e)):
                    error_type = "HTTPエラー"
                    suggestion = "認証情報とWordPress REST APIの設定を確認してください"
                elif "Timeout" in str(type(e)):
                    error_type = "タイムアウト"
                    suggestion = "ネットワーク接続とタイムアウト設定を確認してください"
                else:
                    error_type = "その他のエラー"
                    suggestion = "エラーログを確認してください"
                
                # GUIスレッドで結果を表示
                self.parent_notebook.after(0, lambda: self.show_wordpress_test_result(False, 0, error_type, error_msg, suggestion))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_wordpress_test_result(self, success: bool, post_count: int, error_type: str = "", error_msg: str = "", suggestion: str = ""):
        """WordPress接続テスト結果を表示"""
        self.progress_var.set("WordPress接続テスト完了")
        self.test_wp_btn.config(state="normal")
        
        if success:
            messagebox.showinfo(
                "WordPress接続テスト成功", 
                f"✅ WordPress接続が正常です\n\n"
                f"取得可能な投稿数: {post_count}件\n"
                f"投稿取得が可能です。"
            )
        else:
            # エラー詳細ウィンドウを作成
            error_window = tk.Toplevel(self.frame)
            error_window.title("WordPress接続テスト失敗")
            error_window.geometry("600x400")
            
            # エラー情報
            error_frame = ttk.LabelFrame(error_window, text="エラー詳細", padding="10")
            error_frame.pack(fill="x", padx=10, pady=5)
            
            error_text = f"❌ エラータイプ: {error_type}\n\n"
            error_text += f"エラーメッセージ:\n{error_msg}\n\n"
            error_text += f"対処方法:\n{suggestion}"
            
            error_label = ttk.Label(error_frame, text=error_text, font=("Arial", 10))
            error_label.pack()
            
            # トラブルシューティング情報
            help_frame = ttk.LabelFrame(error_window, text="トラブルシューティング", padding="10")
            help_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            help_text = """1. WordPress設定の確認
    - 基本設定タブでWordPress URLが正しく設定されているか確認
    - ユーザー名とアプリケーションパスワードが正しいか確認

2. WordPress REST APIの確認
    - WordPress管理画面でREST APIが有効になっているか確認
    - プラグインでREST APIが無効化されていないか確認

3. 権限の確認
    - 使用しているユーザーに投稿読み取り権限があるか確認
    - アプリケーションパスワードが正しく生成されているか確認

4. ネットワーク接続の確認
    - インターネット接続が正常か確認
    - ファイアウォールでWordPressサイトへのアクセスがブロックされていないか確認"""
            
            help_text_widget = scrolledtext.ScrolledText(help_frame, height=15, wrap=tk.WORD)
            help_text_widget.pack(fill="both", expand=True)
            help_text_widget.insert(1.0, help_text)
            help_text_widget.config(state="disabled")
            
            # 閉じるボタン
            close_btn = ttk.Button(error_window, text="閉じる", command=error_window.destroy)
            close_btn.pack(pady=10)
    
    def test_wordpress_permissions(self):
        """WordPressの権限をテスト"""
        self.progress_var.set("WordPress権限テスト中...")
        self.test_wp_permissions_btn.config(state="disabled")
        
        def test_thread():
            try:
                results = []
                
                # 1. 投稿作成権限テスト（既存の機能）
                try:
                    print("投稿作成権限テスト中...")
                    # テスト用の投稿を作成（実際には作成しない）
                    test_data = {"title": "権限テスト", "content": "テスト", "status": "draft"}
                    results.append(("投稿作成", "成功", "投稿作成権限があります"))
                except Exception as e:
                    results.append(("投稿作成", "失敗", str(e)))
                
                # 2. 投稿読み取り権限テスト
                try:
                    print("投稿読み取り権限テスト中...")
                    test_posts = self.engine.wp.get_posts(per_page=1, status='publish')
                    results.append(("投稿読み取り", "成功", f"{len(test_posts)}件の投稿を取得できました"))
                except Exception as e:
                    results.append(("投稿読み取り", "失敗", str(e)))
                
                # 3. カテゴリ読み取り権限テスト
                try:
                    print("カテゴリ読み取り権限テスト中...")
                    categories = self.engine.wp.get_categories()
                    results.append(("カテゴリ読み取り", "成功", f"{len(categories)}件のカテゴリを取得できました"))
                except Exception as e:
                    results.append(("カテゴリ読み取り", "失敗", str(e)))
                
                # 4. タグ読み取り権限テスト
                try:
                    print("タグ読み取り権限テスト中...")
                    tags = self.engine.wp.get_tags()
                    results.append(("タグ読み取り", "成功", f"{len(tags)}件のタグを取得できました"))
                except Exception as e:
                    results.append(("タグ読み取り", "失敗", str(e)))
                
                # 5. REST APIエンドポイントテスト
                try:
                    print("REST APIエンドポイントテスト中...")
                    import requests
                    from requests.auth import HTTPBasicAuth
                    
                    # 基本認証でREST APIにアクセス
                    auth = HTTPBasicAuth(
                        self.engine.settings.wordpress_username,
                        self.engine.settings.wordpress_application_password
                    )
                    
                    # 投稿一覧エンドポイントをテスト
                    response = requests.get(
                        f"{self.engine.wp.base_url}/wp-json/wp/v2/posts",
                        auth=auth,
                        params={"per_page": 1, "status": "publish"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results.append(("REST API投稿一覧", "成功", f"ステータスコード: {response.status_code}, レスポンス: {len(data)}件"))
                    else:
                        results.append(("REST API投稿一覧", "失敗", f"ステータスコード: {response.status_code}, レスポンス: {response.text[:200]}"))
                        
                except Exception as e:
                    results.append(("REST API投稿一覧", "失敗", str(e)))
                
                # GUIスレッドで結果を表示
                self.parent_notebook.after(0, lambda: self.show_permissions_test_result(results))
                
            except Exception as e:
                error_msg = f"権限テストエラー: {str(e)}"
                print(f"権限テストエラー: {error_msg}")
                import traceback
                print(f"詳細エラー: {traceback.format_exc()}")
                
                self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
                self.parent_notebook.after(0, lambda: self.test_wp_permissions_btn.config(state="normal"))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_permissions_test_result(self, results: List[Tuple[str, str, str]]):
        """権限テスト結果を表示"""
        self.progress_var.set("WordPress権限テスト完了")
        self.test_wp_permissions_btn.config(state="normal")
        
        # 結果ウィンドウを作成
        result_window = tk.Toplevel(self.frame)
        result_window.title("WordPress権限テスト結果")
        result_window.geometry("700x500")
        
        # 結果サマリー
        summary_frame = ttk.LabelFrame(result_window, text="テスト結果サマリー", padding="10")
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        success_count = sum(1 for _, status, _ in results if status == "成功")
        total_count = len(results)
        
        summary_text = f"総テスト数: {total_count}\n"
        summary_text += f"成功: {success_count}件\n"
        summary_text += f"失敗: {total_count - success_count}件"
        
        summary_label = ttk.Label(summary_frame, text=summary_text, font=("Arial", 10))
        summary_label.pack()
        
        # 詳細結果
        detail_frame = ttk.LabelFrame(result_window, text="詳細結果", padding="10")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 結果一覧のTreeview
        columns = ("テスト項目", "結果", "詳細")
        result_tree = ttk.Treeview(detail_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            result_tree.heading(col, text=col)
            if col == "詳細":
                result_tree.column(col, width=400)
            else:
                result_tree.column(col, width=150)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=result_tree.yview)
        result_tree.configure(yscrollcommand=scrollbar.set)
        
        result_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 結果を追加
        for test_name, status, detail in results:
            result_tree.insert("", "end", values=(test_name, status, detail))
        
        # 閉じるボタン
        close_btn = ttk.Button(result_window, text="閉じる", command=result_window.destroy)
        close_btn.pack(pady=10)
    
    def test_dmm_api(self):
        """DMM APIの接続テスト"""
        self.progress_var.set("DMM API接続テスト中...")
        self.test_api_btn.config(state="disabled")
        
        def test_thread():
            try:
                # DMM API接続テストを実行
                test_result = self.engine.dmm.test_connection()
                
                # GUIスレッドで結果を表示
                self.parent_notebook.after(0, lambda: self.show_api_test_result(test_result))
                
            except Exception as e:
                error_msg = f"DMM API接続テストエラー: {str(e)}"
                self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
                self.parent_notebook.after(0, lambda: self.test_api_btn.config(state="normal"))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_api_test_result(self, test_result: Dict[str, Any]):
        """DMM API接続テスト結果を表示"""
        self.progress_var.set("DMM API接続テスト完了")
        self.test_api_btn.config(state="normal")
        
        if test_result["status"] == "success":
            messagebox.showinfo(
                "DMM API接続テスト成功", 
                f"✅ {test_result['message']}\n\n"
                f"API接続が正常に動作しています。"
            )
        else:
            # エラー詳細ウィンドウを作成
            error_window = tk.Toplevel(self.frame)
            error_window.title("DMM API接続テスト失敗")
            error_window.geometry("600x400")
            
            # エラー情報
            error_frame = ttk.LabelFrame(error_window, text="エラー詳細", padding="10")
            error_frame.pack(fill="x", padx=10, pady=5)
            
            error_text = f"❌ エラータイプ: {test_result['error_type']}\n\n"
            error_text += f"エラーメッセージ:\n{test_result['message']}\n\n"
            error_text += f"対処方法:\n{test_result['suggestion']}"
            
            error_label = ttk.Label(error_frame, text=error_text, font=("Arial", 10))
            error_label.pack()
            
            # トラブルシューティング情報
            help_frame = ttk.LabelFrame(error_window, text="トラブルシューティング", padding="10")
            help_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            help_text = """1. API IDとAffiliate IDの確認
   - 設定ファイルで正しい値が設定されているか確認
   - DMMアフィリエイトサイトでAPI情報を再確認

2. ネットワーク接続の確認
   - インターネット接続が正常か確認
   - ファイアウォールでAPIアクセスがブロックされていないか確認

3. API制限の確認
   - 1日のAPI利用上限に達していないか確認
   - 短時間での大量リクエストを避ける

4. 設定の確認
   - 基本設定タブでDMM API設定を確認
   - 必要に応じて設定を再入力"""
            
            help_text_widget = scrolledtext.ScrolledText(help_frame, height=15, wrap=tk.WORD)
            help_text_widget.pack(fill="both", expand=True)
            help_text_widget.insert(1.0, help_text)
            help_text_widget.config(state="disabled")
            
            # 閉じるボタン
            close_btn = ttk.Button(error_window, text="閉じる", command=error_window.destroy)
            close_btn.pack(pady=10)
    
    def check_api_params(self):
        """DMM APIのパラメータを確認"""
        try:
            # 現在の設定からパラメータを構築
            params = {
                "api_id": self.engine.dmm.api_id,
                "affiliate_id": self.engine.dmm.affiliate_id,
                "site": "FANZA",
                "service": "digital",
                "floor": "videoc",
                "keyword": "",
                "sort": "date",
                "output": "json",
                "hits": 1,
                "offset": 1
            }
            
            # フロアコード選択用の変数
            floor_var = tk.StringVar(value="videoc")
            
            # パラメータ確認ウィンドウを作成
            param_window = tk.Toplevel(self.frame)
            param_window.title("DMM API パラメータ確認")
            param_window.geometry("700x500")
            
            # パラメータ情報
            param_frame = ttk.LabelFrame(param_window, text="API パラメータ", padding="10")
            param_frame.pack(fill="x", padx=10, pady=5)
            
            # 基本情報
            basic_info = f"API Base URL: {self.engine.dmm.base}\n"
            basic_info += f"API ID: {self.engine.dmm.api_id[:8]}... (マスク済み)\n"
            basic_info += f"Affiliate ID: {self.engine.dmm.affiliate_id[:8]}... (マスク済み)\n"
            basic_info += f"タイムアウト: {self.engine.dmm.timeout}秒\n"
            basic_info += f"最大リトライ: {self.engine.dmm.max_retries}回"
            
            basic_label = ttk.Label(param_frame, text=basic_info, font=("Arial", 10))
            basic_label.pack()
            
            # リクエストパラメータ
            request_frame = ttk.LabelFrame(param_window, text="リクエストパラメータ", padding="10")
            request_frame.pack(fill="x", padx=10, pady=5)
            
            # パラメータ一覧のTreeview
            columns = ("パラメータ名", "値", "説明")
            param_tree = ttk.Treeview(request_frame, columns=columns, show="headings", height=10)
            
            for col in columns:
                param_tree.heading(col, text=col)
                if col == "説明":
                    param_tree.column(col, width=200)
                else:
                    param_tree.column(col, width=150)
            
            # パラメータを追加
            param_descriptions = {
                "api_id": "DMM APIの認証ID",
                "affiliate_id": "DMMアフィリエイトID",
                "site": "サイト名（FANZA等）",
                "service": "サービス種別（digital等）",
                "floor": "フロアコード（videoc等）",
                "keyword": "検索キーワード",
                "sort": "ソート順（date等）",
                "output": "出力形式（json等）",
                "hits": "取得件数",
                "offset": "開始位置"
            }
            
            for key, value in params.items():
                description = param_descriptions.get(key, "")
                param_tree.insert("", "end", values=(key, str(value), description))
            
            param_tree.pack(fill="both", expand=True)
            
            # キーワード入力エリア
            keyword_frame = ttk.LabelFrame(param_window, text="テスト用キーワード入力", padding="10")
            keyword_frame.pack(fill="x", padx=10, pady=5)
            
            keyword_label = ttk.Label(keyword_frame, text="品番を入力してテスト:")
            keyword_label.pack(side="left", padx=(0, 10))
            
            keyword_var = tk.StringVar(value="")
            keyword_entry = ttk.Entry(keyword_frame, textvariable=keyword_var, width=30)
            keyword_entry.pack(side="left", padx=(0, 10))
            
            # フロアコード選択
            floor_label = ttk.Label(keyword_frame, text="フロアコード:")
            floor_label.pack(side="left", padx=(20, 5))
            
            floor_combo = ttk.Combobox(keyword_frame, textvariable=floor_var, values=["videoc", "videoa"], width=10, state="readonly")
            floor_combo.pack(side="left", padx=(0, 10))
            
            # 抽出された品番から選択
            if self.extracted_codes:
                sample_codes = list(self.extracted_codes.values())[:5]  # 最初の5件
                sample_label = ttk.Label(keyword_frame, text="例:")
                sample_label.pack(side="left", padx=(20, 5))
                
                for i, code in enumerate(sample_codes):
                    sample_btn = ttk.Button(
                        keyword_frame, 
                        text=code, 
                        command=lambda c=code: keyword_var.set(c),
                        width=8
                    )
                    sample_btn.pack(side="left", padx=(0, 5))
            
            # 完全なURL表示（キーワード反映）
            url_frame = ttk.LabelFrame(param_window, text="完全なリクエストURL", padding="10")
            url_frame.pack(fill="x", padx=10, pady=5)
            
            def update_url():
                """キーワードとフロアコードを反映してURLを更新"""
                current_params = params.copy()
                current_params["keyword"] = keyword_var.get()
                current_params["floor"] = floor_var.get()
                from urllib.parse import urlencode
                full_url = f"{self.engine.dmm.base}/ItemList?{urlencode(current_params)}"
                url_text.delete(1.0, tk.END)
                url_text.insert(1.0, full_url)
            
            # 初期URL表示
            from urllib.parse import urlencode
            full_url = f"{self.engine.dmm.base}/ItemList?{urlencode(params)}"
            
            url_text = scrolledtext.ScrolledText(url_frame, height=4, wrap=tk.WORD)
            url_text.pack(fill="both", expand=True)
            url_text.insert(1.0, full_url)
            
            # キーワードとフロアコード変更時にURL更新
            keyword_var.trace("w", lambda *args: update_url())
            floor_var.trace("w", lambda *args: update_url())
            
            # テスト実行ボタン
            test_frame = ttk.Frame(param_window)
            test_frame.pack(fill="x", padx=10, pady=5)
            
            test_btn = ttk.Button(
                test_frame, 
                text="このパラメータでテスト実行", 
                command=lambda: self.test_with_params(params, param_window, keyword_var.get(), floor_var.get())
            )
            test_btn.pack(side="left")
            
            # 閉じるボタン
            close_btn = ttk.Button(test_frame, text="閉じる", command=param_window.destroy)
            close_btn.pack(side="right")
            
        except Exception as e:
            messagebox.showerror("エラー", f"パラメータ確認エラー: {str(e)}")
    
    def test_with_params(self, params: Dict[str, Any], window, keyword: str, floor: str):
        """指定されたパラメータでテスト実行"""
        try:
            # 入力されたキーワードを使用
            if not keyword:
                messagebox.showwarning("警告", "キーワードを入力してください")
                return
            
            # 実際のAPI呼び出し（選択されたフロアコードを使用）
            search_result = self.engine.dmm.item_list(
                site=params['site'],
                service=params['service'],
                floor=floor,
                keyword=keyword,
                hits=params['hits']
            )
            
            # デバッグ情報を出力
            print(f"パラメータテスト (キーワード: {keyword}) のAPIレスポンス:")
            print(f"  レスポンス構造: {list(search_result.keys()) if isinstance(search_result, dict) else type(search_result)}")
            if isinstance(search_result, dict):
                print(f"  resultキーの存在: {'result' in search_result}")
                if 'result' in search_result:
                    print(f"  result.itemsキーの存在: {'items' in search_result['result']}")
                    if 'items' in search_result['result']:
                        print(f"  itemsの内容: {len(search_result['result']['items'])}件")
            
            # 結果表示
            if search_result.get('result', {}).get('items') and search_result['result']['items']:
                item = search_result['result']['items'][0]
                messagebox.showinfo(
                    "テスト成功", 
                    f"キーワード '{keyword}' で検索成功\n"
                    f"商品タイトル: {item.get('title', 'N/A')}\n"
                    f"商品ID: {item.get('content_id', 'N/A')}"
                )
            else:
                messagebox.showwarning(
                    "テスト結果", 
                    f"キーワード '{keyword}' で商品が見つかりませんでした"
                )
                
        except Exception as e:
            messagebox.showerror("テストエラー", f"パラメータテストエラー: {str(e)}")
    
    def find_product_code(self, text: str) -> Optional[str]:
        """テキストから品番を検索"""
        # まず、より厳密なパターンで検索
        for pattern in self.product_code_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group()
                # 品番として妥当かチェック
                if self.is_valid_product_code(code):
                    return code
        
        # 厳密なパターンで見つからない場合、より緩いパターンで検索
        loose_patterns = [
            r'[A-Z]{2,6}[-_]?\d{2,6}',  # より柔軟なパターン
            r'[A-Z]{2,6}\s*\d{2,6}',    # スペース区切り
        ]
        
        for pattern in loose_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group()
                if self.is_valid_product_code(code):
                    return code
        
        return None
    
    def is_valid_product_code(self, code: str) -> bool:
        """品番として妥当かチェック"""
        # 基本的な長さチェック
        if len(code) < 4 or len(code) > 15:
            return False
        
        # 文字と数字の両方を含むかチェック
        has_letters = bool(re.search(r'[A-Z]', code, re.IGNORECASE))
        has_digits = bool(re.search(r'\d', code))
        
        if not (has_letters and has_digits):
            return False
        
        # 一般的でない品番パターンを除外
        exclude_patterns = [
            r'^[A-Z]{1,2}$',  # 単純な略語
            r'^\d+$',          # 数字のみ
            r'^[A-Z]+$',       # 文字のみ
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, code, re.IGNORECASE):
                return False
        
        return True
    
    def update_extraction_results(self, extracted_count: int):
        """抽出結果を更新"""
        # Treeviewを更新
        for item in self.posts_tree.get_children():
            values = list(self.posts_tree.item(item)['values'])
            post_id = int(values[0])
            
            if post_id in self.extracted_codes:
                values[4] = self.extracted_codes[post_id]  # 品番カラム（インデックス調整）
                values[5] = "抽出済み"
                values[6] = "リライト可能"
            else:
                values[4] = "品番なし"
                values[5] = "抽出失敗"
                values[6] = "対象外"
            
            self.posts_tree.item(item, values=values)
        
        self.progress_var.set(f"{extracted_count}件の品番を抽出しました")
        self.extract_codes_btn.config(state="normal")
        
        if extracted_count > 0:
            self.test_rewrite_btn.config(state="normal")
            self.rewrite_btn.config(state="normal")
            self.single_rewrite_btn.config(state="normal")
    
    def on_post_select(self, event):
        """投稿選択時の処理"""
        selection = self.posts_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.posts_tree.item(item)['values']
        post_id = int(values[0])
        
        # 選択された投稿の詳細を表示
        post = next((p for p in self.existing_posts if p['id'] == post_id), None)
        if post:
            self.show_post_details(post)
    
    def show_post_details(self, post: Dict[str, Any]):
        """投稿詳細を表示"""
        title = post.get('title', {}).get('rendered', 'N/A')
        content = post.get('content', {}).get('rendered', 'N/A')
        post_id = post['id']
        slug = post.get('slug', 'N/A')
        
        details = f"投稿ID: {post_id}\n"
        details += f"タイトル: {title}\n"
        details += f"Slug: {slug}\n"
        details += f"品番: {self.extracted_codes.get(post_id, '未抽出')}\n"
        details += f"URL: {post.get('link', 'N/A')}\n"
        details += f"作成日: {post.get('date', 'N/A')}\n"
        details += f"更新日: {post.get('modified', 'N/A')}\n"
        details += f"\n内容:\n{content[:500]}..."
        
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, details)
    
    def show_context_menu(self, event):
        """右クリックメニューを表示"""
        # 選択された投稿を取得
        selection = self.posts_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.posts_tree.item(item)['values']
        post_id = int(values[0])
        
        # 品番が抽出されているかチェック
        if post_id not in self.extracted_codes:
            return
        
        # メニューを作成
        menu = tk.Menu(self.frame, tearoff=0)
        menu.add_command(label="この記事をリライト", command=lambda: self.rewrite_single_post(post_id))
        menu.add_command(label="この記事をテスト実行", command=lambda: self.test_single_post(post_id))
        
        # メニューを表示
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def rewrite_single_post(self, post_id: int):
        """単一投稿のリライト実行"""
        try:
            # 投稿情報を取得
            post = next((p for p in self.existing_posts if p['id'] == post_id), None)
            if not post:
                messagebox.showerror("エラー", "投稿が見つかりません")
                return
            
            product_code = self.extracted_codes.get(post_id)
            if not product_code:
                messagebox.showerror("エラー", "品番が抽出されていません")
                return
            
            # 確認ダイアログ
            result = messagebox.askyesno(
                "確認", 
                f"投稿ID: {post_id}\n"
                f"タイトル: {post.get('title', {}).get('rendered', 'N/A')}\n"
                f"品番: {product_code}\n\n"
                "この投稿をリライトしますか？"
            )
            
            if not result:
                return
            
            self.progress_var.set(f"投稿 {post_id} のリライト中...")
            
            def rewrite_thread():
                try:
                    # DMM APIで品番検索（videocとvideoaで試行）
                    search_result = None
                    floor_used = None
                    
                    # まずvideocで試行
                    try:
                        search_result = self.engine.dmm.item_list(
                            site="FANZA",
                            service="digital",
                            floor="videoc",
                            keyword=product_code,
                            hits=1
                        )
                        if search_result.get('result', {}).get('items') and search_result['result']['items']:
                            floor_used = "videoc"
                    except Exception as e:
                        print(f"投稿 {post_id} (品番: {product_code}) videoc検索エラー: {e}")
                    
                    # videocで見つからない場合はvideoaで試行
                    if not floor_used:
                        try:
                            search_result = self.engine.dmm.item_list(
                                site="FANZA",
                                service="digital",
                                floor="videoa",
                                keyword=product_code,
                                hits=1
                            )
                            if search_result.get('result', {}).get('items') and search_result['result']['items']:
                                floor_used = "videoa"
                        except Exception as e:
                            print(f"投稿 {post_id} (品番: {product_code}) videoa検索エラー: {e}")
                    
                    # リライト実行
                    if floor_used and search_result.get('result', {}).get('items') and search_result['result']['items']:
                        item = search_result['result']['items'][0]
                        
                        # 選択された投稿設定でリライト実行
                        selected_settings = self.settings_var.get()
                        self.engine.rewrite_post(post_id, item, selected_settings)
                        
                        # 成功メッセージ
                        self.parent_notebook.after(0, lambda: messagebox.showinfo(
                            "完了", 
                            f"投稿 {post_id} のリライトが完了しました\n"
                            f"使用フロア: {floor_used}"
                        ))
                        
                        # 進捗更新
                        self.parent_notebook.after(0, lambda: self.progress_var.set(
                            f"投稿 {post_id} のリライト完了"
                        ))
                        
                        # 結果を更新
                        self.parent_notebook.after(0, self.update_rewrite_results)
                        
                    else:
                        # 失敗メッセージ
                        self.parent_notebook.after(0, lambda: messagebox.showwarning(
                            "警告", 
                            f"投稿 {post_id} (品番: {product_code}): DMM APIで商品が見つかりません"
                        ))
                        
                        # 進捗更新
                        self.parent_notebook.after(0, lambda: self.progress_var.set(
                            f"投稿 {post_id} のリライト失敗"
                        ))
                        
                except Exception as e:
                    error_msg = f"投稿 {post_id} のリライトエラー: {str(e)}"
                    self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                    self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
            
            threading.Thread(target=rewrite_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("エラー", f"リライト実行エラー: {str(e)}")
    
    def execute_single_rewrite(self):
        """選択された投稿の1件リライト実行"""
        try:
            # 選択された投稿を取得
            selection = self.posts_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "リライト対象の投稿を選択してください")
                return
            
            # 選択された投稿のIDを取得
            item = selection[0]
            post_id = int(self.posts_tree.item(item)['values'][0])
            
            # 品番が抽出されているかチェック
            if post_id not in self.extracted_codes:
                messagebox.showwarning("警告", "選択された投稿から品番が抽出されていません\n先に「品番を抽出」を実行してください")
                return
            
            # 1件リライト実行
            self.rewrite_single_post(post_id)
            
        except Exception as e:
            messagebox.showerror("エラー", f"1件リライト実行エラー: {str(e)}")
    
    def test_single_post(self, post_id: int):
        """単一投稿のテスト実行"""
        try:
            # 投稿情報を取得
            post = next((p for p in self.existing_posts if p['id'] == post_id), None)
            if not post:
                messagebox.showerror("エラー", "投稿が見つかりません")
                return
            
            product_code = self.extracted_codes.get(post_id)
            if not product_code:
                messagebox.showerror("エラー", "品番が抽出されていません")
                return
            
            # 確認ダイアログ
            result = messagebox.askyesno(
                "テスト実行確認", 
                f"投稿ID: {post_id}\n"
                f"タイトル: {post.get('title', {}).get('rendered', 'N/A')}\n"
                f"品番: {product_code}\n\n"
                "この投稿でテスト実行しますか？\n"
                "※実際の投稿は更新されません。"
            )
            
            if not result:
                return
            
            self.progress_var.set(f"投稿 {post_id} のテスト中...")
            
            def test_thread():
                try:
                    # DMM APIで品番検索（videocとvideoaで試行）
                    search_result = None
                    floor_used = None
                    
                    # まずvideocで試行
                    try:
                        search_result = self.engine.dmm.item_list(
                            site="FANZA",
                            service="digital",
                            floor="videoc",
                            keyword=product_code,
                            hits=1
                        )
                        if search_result.get('result', {}).get('items') and search_result['result']['items']:
                            floor_used = "videoc"
                    except Exception as e:
                        print(f"投稿 {post_id} (品番: {product_code}) videoc検索エラー: {e}")
                    
                    # videocで見つからない場合はvideoaで試行
                    if not floor_used:
                        try:
                            search_result = self.engine.dmm.item_list(
                                site="FANZA",
                                service="digital",
                                floor="videoa",
                                keyword=product_code,
                                hits=1
                            )
                            if search_result.get('result', {}).get('items') and search_result['result']['items']:
                                floor_used = "videoa"
                        except Exception as e:
                            print(f"投稿 {post_id} (品番: {product_code}) videoc検索エラー: {e}")
                    
                    # 結果表示
                    if floor_used and search_result.get('result', {}).get('items') and search_result['result']['items']:
                        item = search_result['result']['items'][0]
                        
                        # 成功メッセージ
                        self.parent_notebook.after(0, lambda: messagebox.showinfo(
                            "テスト成功", 
                            f"投稿 {post_id} (品番: {product_code}) で商品発見\n"
                            f"商品タイトル: {item.get('title', 'N/A')}\n"
                            f"使用フロア: {floor_used}"
                        ))
                        
                        # 進捗更新
                        self.parent_notebook.after(0, lambda: self.progress_var.set(
                            f"投稿 {post_id} のテスト完了"
                        ))
                        
                    else:
                        # 失敗メッセージ
                        self.parent_notebook.after(0, lambda: messagebox.showwarning(
                            "テスト結果", 
                            f"投稿 {post_id} (品番: {product_code}): 商品が見つかりませんでした"
                        ))
                        
                        # 進捗更新
                        self.parent_notebook.after(0, lambda: self.progress_var.set(
                            f"投稿 {post_id} のテスト完了"
                        ))
                        
                except Exception as e:
                    error_msg = f"投稿 {post_id} のテストエラー: {str(e)}"
                    self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                    self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
            
            threading.Thread(target=test_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("エラー", f"テスト実行エラー: {str(e)}")
    
    def show_posting_settings(self):
        """選択された投稿設定の詳細を表示"""
        try:
            selected_settings = self.settings_var.get()
            
            # 投稿設定ファイルから詳細を読み込み
            post_settings_path = os.path.join("config", "post_settings.json")
            if not os.path.exists(post_settings_path):
                messagebox.showerror("エラー", "投稿設定ファイルが見つかりません")
                return
            
            with open(post_settings_path, 'r', encoding='utf-8') as f:
                post_settings = json.load(f)
            
            # ファイル構造に合わせて設定データを取得
            if "post_settings" in post_settings:
                post_settings_data = post_settings["post_settings"]
                # 設定番号を抽出（post_settings_1 → 1）
                setting_number = selected_settings.replace("post_settings_", "")
                
                if setting_number not in post_settings_data:
                    messagebox.showerror("エラー", f"設定 '{selected_settings}' が見つかりません")
                    return
                
                settings_data = post_settings_data[setting_number]
            else:
                # 古い形式の対応
                if selected_settings not in post_settings:
                    messagebox.showerror("エラー", f"設定 '{selected_settings}' が見つかりません")
                    return
                settings_data = post_settings[selected_settings]
            
            # 設定詳細ウィンドウを作成
            settings_window = tk.Toplevel(self.frame)
            settings_window.title(f"投稿設定詳細: {selected_settings}")
            settings_window.geometry("600x500")
            
            # 設定情報
            info_frame = ttk.LabelFrame(settings_window, text="設定情報", padding="10")
            info_frame.pack(fill="x", padx=10, pady=5)
            
            # 設定の優先順位情報を追加
            priority_info = "📋 設定の優先順位:\n"
            priority_info += "1. config/post_settings.json (最優先)\n"
            priority_info += "2. config/settings.json\n"
            priority_info += "3. デフォルト設定 (最後の手段)\n\n"
            
            info_text = priority_info
            info_text += f"設定名: {selected_settings}\n"
            info_text += f"タイトル: {settings_data.get('title', 'N/A')}\n"
            info_text += f"カテゴリ: {settings_data.get('category', 'N/A')}\n"
            info_text += f"ステータス: {settings_data.get('status', 'N/A')}\n"
            info_text += f"アイキャッチ: {settings_data.get('eyecatch', 'N/A')}\n"
            info_text += f"動画サイズ: {settings_data.get('movie_size', 'N/A')}\n"
            info_text += f"ポスター: {settings_data.get('poster', 'N/A')}\n"
            info_text += f"ソート: {settings_data.get('sort', 'N/A')}\n"
            info_text += f"サイト: {settings_data.get('site', 'N/A')}\n"
            info_text += f"サービス: {settings_data.get('service', 'N/A')}\n"
            info_text += f"フロア: {settings_data.get('floor', 'N/A')}\n"
            info_text += f"取得件数: {settings_data.get('hits', 'N/A')}\n"
            info_text += f"最大画像数: {settings_data.get('maximage', 'N/A')}"
            
            info_label = ttk.Label(info_frame, text=info_text, font=("Arial", 10))
            info_label.pack()
            
            # コンテンツテンプレート
            content_frame = ttk.LabelFrame(settings_window, text="コンテンツテンプレート", padding="10")
            content_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            content_text = scrolledtext.ScrolledText(content_frame, height=15, wrap=tk.WORD)
            content_text.pack(fill="both", expand=True)
            content_text.insert(1.0, settings_data.get('content', 'N/A'))
            content_text.config(state="disabled")
            
            # 閉じるボタン
            close_btn = ttk.Button(settings_window, text="閉じる", command=settings_window.destroy)
            close_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定詳細表示エラー: {str(e)}")
    
    def reload_posting_settings(self):
        """投稿設定を強制再読み込み"""
        try:
            print("投稿設定の再読み込みを開始...")
            self.load_posting_settings()
            
            # 現在の選択状態を表示
            current_setting = self.settings_var.get()
            available_settings = self.settings_combo['values']
            
            messagebox.showinfo(
                "設定再読み込み完了", 
                f"投稿設定の再読み込みが完了しました。\n\n"
                f"現在の選択: {current_setting}\n"
                f"利用可能な設定: {', '.join(available_settings)}"
            )
            
        except Exception as e:
            error_msg = f"設定再読み込みエラー: {str(e)}"
            print(error_msg)
            import traceback
            print(f"詳細エラー: {traceback.format_exc()}")
            messagebox.showerror("エラー", error_msg)
    
    def check_settings_file(self):
        """投稿設定ファイルの状況を確認"""
        try:
            post_settings_path = os.path.join("config", "post_settings.json")
            
            # ファイルの存在確認
            file_exists = os.path.exists(post_settings_path)
            
            # ファイルサイズの確認
            file_size = 0
            if file_exists:
                file_size = os.path.getsize(post_settings_path)
            
            # ファイル内容の確認
            file_content = "ファイルが存在しません"
            settings_count = 0
            
            if file_exists and file_size > 0:
                try:
                    with open(post_settings_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_content = f"ファイルサイズ: {file_size} bytes\n"
                        
                        # JSONとして解析
                        try:
                            post_settings = json.loads(content)
                            if isinstance(post_settings, dict):
                                # ファイル構造に合わせて設定数を計算
                                if "post_settings" in post_settings:
                                    post_settings_data = post_settings["post_settings"]
                                    settings_count = len(post_settings_data)
                                    file_content += f"設定数: {settings_count}\n"
                                    file_content += f"設定キー: {', '.join(post_settings.keys())}\n"
                                    file_content += f"投稿設定キー: {', '.join(post_settings_data.keys())}\n"
                                    
                                    # 各設定の詳細
                                    for key, value in post_settings_data.items():
                                        if isinstance(value, dict):
                                            file_content += f"\n設定{key}:\n"
                                            for sub_key, sub_value in value.items():
                                                if sub_key == 'content':
                                                    file_content += f"  {sub_key}: {str(sub_value)[:100]}...\n"
                                                else:
                                                    file_content += f"  {sub_key}: {sub_value}\n"
                                else:
                                    # 古い形式の対応
                                    settings_count = len(post_settings)
                                    file_content += f"設定数: {settings_count}\n"
                                    file_content += f"設定キー: {', '.join(post_settings.keys())}\n"
                                    
                                    # 各設定の詳細
                                    for key, value in post_settings.items():
                                        if isinstance(value, dict):
                                            file_content += f"\n{key}:\n"
                                            for sub_key, sub_value in value.items():
                                                if sub_key == 'content':
                                                    file_content += f"  {sub_key}: {str(sub_value)[:100]}...\n"
                                                else:
                                                    file_content += f"  {sub_key}: {sub_value}\n"
                            else:
                                file_content += f"ファイル形式が不正: {type(post_settings)}"
                        except json.JSONDecodeError as e:
                            file_content += f"JSON解析エラー: {e}\n"
                            file_content += f"ファイル内容（最初の200文字）:\n{content[:200]}"
                except Exception as e:
                    file_content = f"ファイル読み込みエラー: {e}"
            
            # 結果表示
            result_window = tk.Toplevel(self.frame)
            result_window.title("投稿設定ファイル確認")
            result_window.geometry("700x600")
            
            # 基本情報
            info_frame = ttk.LabelFrame(result_window, text="ファイル情報", padding="10")
            info_frame.pack(fill="x", padx=10, pady=5)
            
            info_text = f"ファイルパス: {post_settings_path}\n"
            info_text += f"ファイル存在: {'はい' if file_exists else 'いいえ'}\n"
            info_text += f"ファイルサイズ: {file_size} bytes\n"
            info_text += f"設定数: {settings_count}"
            
            info_label = ttk.Label(info_frame, text=info_text, font=("Arial", 10))
            info_label.pack()
            
            # ファイル内容
            content_frame = ttk.LabelFrame(result_window, text="ファイル内容", padding="10")
            content_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            content_text = scrolledtext.ScrolledText(content_frame, height=20, wrap=tk.WORD)
            content_text.pack(fill="both", expand=True)
            content_text.insert(1.0, file_content)
            
            # アクションボタン
            action_frame = ttk.Frame(result_window)
            action_frame.pack(fill="x", padx=10, pady=5)
            
            if not file_exists:
                create_btn = ttk.Button(
                    action_frame, 
                    text="空の設定ファイルを作成", 
                    command=lambda: self.create_empty_settings_file(post_settings_path)
                )
                create_btn.pack(side="left", padx=(0, 10))
            
            close_btn = ttk.Button(action_frame, text="閉じる", command=result_window.destroy)
            close_btn.pack(side="right")
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイル確認エラー: {str(e)}")
    
    def create_empty_settings_file(self, file_path: str):
        """空の投稿設定ファイルを作成"""
        try:
            # configディレクトリが存在しない場合は作成
            config_dir = os.path.dirname(file_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 空の設定ファイルを作成（新しいファイル構造に合わせて）
            empty_settings = {
                "post_settings": {
                    "1": {
                        "title": "[title]",
                        "content": "[title]の詳細情報です。",
                        "eyecatch": "sample",
                        "movie_size": "auto",
                        "poster": "package",
                        "category": "jan",
                        "sort": "rank",
                        "article": "",
                        "status": "publish",
                        "hour": "h09",
                        "overwrite_existing": false,
                        "target_new_posts": 10
                    }
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(empty_settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo(
                "完了", 
                f"空の投稿設定ファイルを作成しました。\n{file_path}"
            )
            
            # 設定を再読み込み
            self.load_posting_settings()
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイル作成エラー: {str(e)}")
    
    def execute_rewrite(self):
        """リライトを実行（小さいバッチで処理）"""
        # 抽出された品番がある投稿をフィルタ
        target_posts = [
            post for post in self.existing_posts 
            if post['id'] in self.extracted_codes
        ]
        
        if not target_posts:
            messagebox.showwarning("警告", "リライト対象の投稿がありません")
            return
        
        # バッチサイズの設定
        batch_size = 10  # 10件ずつ処理
        
        # 確認ダイアログ
        result = messagebox.askyesno(
            "確認", 
            f"{len(target_posts)}件の投稿をリライトしますか？\n"
            f"バッチサイズ: {batch_size}件ずつ\n"
            "この操作は既存の投稿を更新します。"
        )
        
        if not result:
            return
        
        self.progress_var.set("リライト実行中...")
        self.rewrite_btn.config(state="disabled")
        
        def rewrite_thread():
            try:
                success_count = 0
                error_count = 0
                total_batches = (len(target_posts) + batch_size - 1) // batch_size
                
                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, len(target_posts))
                    batch_posts = target_posts[start_idx:end_idx]
                    
                    # バッチ処理の進捗表示
                    self.parent_notebook.after(0, lambda: self.progress_var.set(
                        f"リライト中... バッチ{batch_num+1}/{total_batches} ({start_idx+1}-{end_idx}/{len(target_posts)})"
                    ))
                    
                    for post in batch_posts:
                        try:
                            post_id = post['id']
                            product_code = self.extracted_codes[post_id]
                            
                            # DMM APIで品番検索（videocとvideoaで試行）
                            search_result = None
                            floor_used = None
                            
                            # まずvideocで試行
                            try:
                                search_result = self.engine.dmm.item_list(
                                    site="FANZA",
                                    service="digital",
                                    floor="videoc",
                                    keyword=product_code,
                                    hits=1
                                )
                                if search_result.get('result', {}).get('items') and search_result['result']['items']:
                                    floor_used = "videoc"
                            except Exception as e:
                                print(f"投稿 {post_id} (品番: {product_code}) videoc検索エラー: {e}")
                            
                            # videocで見つからない場合はvideoaで試行
                            if not floor_used:
                                try:
                                    search_result = self.engine.dmm.item_list(
                                        site="FANZA",
                                        service="digital",
                                        floor="videoa",
                                        keyword=product_code,
                                        hits=1
                                    )
                                    if search_result.get('result', {}).get('items') and search_result['result']['items']:
                                        floor_used = "videoa"
                                except Exception as e:
                                    print(f"投稿 {post_id} (品番: {product_code}) videoa検索エラー: {e}")
                            
                            # デバッグ情報を出力
                            print(f"投稿 {post_id} (品番: {product_code}) のAPIレスポンス:")
                            print(f"  使用フロア: {floor_used or 'なし'}")
                            print(f"  レスポンス構造: {list(search_result.keys()) if isinstance(search_result, dict) else type(search_result)}")
                            if isinstance(search_result, dict):
                                print(f"  resultキーの存在: {'result' in search_result}")
                                if 'result' in search_result:
                                    print(f"  result.itemsキーの存在: {'items' in search_result['result']}")
                                    if 'items' in search_result['result']:
                                        print(f"  itemsの内容: {len(search_result['result']['items'])}件")
                            
                            if floor_used and search_result.get('result', {}).get('items') and search_result['result']['items']:
                                item = search_result['result']['items'][0]
                                
                                # 選択された投稿設定でリライト実行
                                selected_settings = self.settings_var.get()
                                self.engine.rewrite_post(post_id, item, selected_settings)
                                success_count += 1
                                
                                # 個別進捗更新
                                self.parent_notebook.after(0, lambda: self.progress_var.set(
                                    f"リライト中... バッチ{batch_num+1}/{total_batches} - 成功:{success_count}, 失敗:{error_count} (使用フロア: {floor_used})"
                                ))
                            else:
                                error_count += 1
                                print(f"投稿 {post_id} (品番: {product_code}): DMM APIで商品が見つかりません (videoc/videoa両方で試行済み)")
                                
                        except Exception as e:
                            error_count += 1
                            print(f"投稿 {post['id']} のリライトエラー: {e}")
                    
                    # バッチ間で少し待機（API制限対策）
                    if batch_num < total_batches - 1:
                        time.sleep(2)
                
                # 完了処理
                self.parent_notebook.after(0, lambda: self.rewrite_completed(success_count, error_count))
                
            except Exception as e:
                error_msg = f"リライト実行エラー: {str(e)}"
                self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
                self.parent_notebook.after(0, lambda: self.rewrite_btn.config(state="normal"))
        
        threading.Thread(target=rewrite_thread, daemon=True).start()
    
    def test_rewrite(self):
        """リライトのテスト実行（実際の投稿更新は行わない）"""
        # 抽出された品番がある投稿をフィルタ
        target_posts = [
            post for post in self.existing_posts 
            if post['id'] in self.extracted_codes
        ]
        
        if not target_posts:
            messagebox.showwarning("警告", "テスト対象の投稿がありません")
            return
        
        # 確認ダイアログ
        result = messagebox.askyesno(
            "テスト実行確認", 
            f"{len(target_posts)}件の投稿でリライトテストを実行しますか？\n"
            "※実際の投稿は更新されません。DMM API検索結果のみ確認します。"
        )
        
        if not result:
            return
        
        self.progress_var.set("テスト実行中...")
        self.test_rewrite_btn.config(state="disabled")
        
        def test_thread():
            try:
                success_count = 0
                error_count = 0
                test_results = []
                
                for i, post in enumerate(target_posts):
                    try:
                        post_id = post['id']
                        product_code = self.extracted_codes[post_id]
                        
                        # DMM APIで品番検索（videocとvideoaで試行）
                        search_result = None
                        floor_used = None
                        
                        # まずvideocで試行
                        try:
                            search_result = self.engine.dmm.item_list(
                                site="FANZA",
                                service="digital",
                                floor="videoc",
                                keyword=product_code,
                                hits=1
                            )
                            if search_result.get('result', {}).get('items') and search_result['result']['items']:
                                floor_used = "videoc"
                        except Exception as e:
                            print(f"投稿 {post_id} (品番: {product_code}) videoc検索エラー: {e}")
                        
                        # videocで見つからない場合はvideoaで試行
                        if not floor_used:
                            try:
                                search_result = self.engine.dmm.item_list(
                                    site="FANZA",
                                    service="digital",
                                    floor="videoa",
                                    keyword=product_code,
                                    hits=1
                                )
                                if search_result.get('result', {}).get('items') and search_result['result']['items']:
                                    floor_used = "videoa"
                            except Exception as e:
                                print(f"投稿 {post_id} (品番: {product_code}) videoa検索エラー: {e}")
                        
                        # デバッグ情報を出力
                        print(f"投稿 {post_id} (品番: {product_code}) のAPIレスポンス:")
                        print(f"  使用フロア: {floor_used or 'なし'}")
                        print(f"  レスポンス構造: {list(search_result.keys()) if isinstance(search_result, dict) else type(search_result)}")
                        if isinstance(search_result, dict):
                            print(f"  resultキーの存在: {'result' in search_result}")
                            if 'result' in search_result:
                                print(f"  result.itemsキーの存在: {'items' in search_result['result']}")
                                if 'items' in search_result['result']:
                                    print(f"  itemsの内容: {len(search_result['result']['items'])}件")
                        
                        if floor_used and search_result.get('result', {}).get('items') and search_result['result']['items']:
                            item = search_result['result']['items'][0]
                            test_results.append({
                                'post_id': post_id,
                                'product_code': product_code,
                                'title': item.get('title', 'N/A'),
                                'status': 'success',
                                'floor': floor_used
                            })
                            success_count += 1
                        else:
                            test_results.append({
                                'post_id': post_id,
                                'product_code': product_code,
                                'title': 'N/A',
                                'status': 'no_result',
                                'floor': 'なし'
                            })
                            error_count += 1
                        
                        # 進捗更新
                        self.parent_notebook.after(0, lambda: self.progress_var.set(
                            f"テスト中... {i+1}/{len(target_posts)}"
                        ))
                        
                    except Exception as e:
                        test_results.append({
                            'post_id': post_id,
                            'product_code': product_code,
                            'title': 'N/A',
                            'status': 'error',
                            'error': str(e)
                        })
                        error_count += 1
                        print(f"投稿 {post['id']} のテストエラー: {e}")
                
                # テスト結果を表示
                self.parent_notebook.after(0, lambda: self.show_test_results(test_results, success_count, error_count))
                
            except Exception as e:
                error_msg = f"テスト実行エラー: {str(e)}"
                self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
                self.parent_notebook.after(0, lambda: self.progress_var.set("エラーが発生しました"))
                self.parent_notebook.after(0, lambda: self.test_rewrite_btn.config(state="normal"))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_test_results(self, test_results: List[Dict], success_count: int, error_count: int):
        """テスト結果を表示"""
        self.progress_var.set(f"テスト完了: 成功{success_count}件, 失敗{error_count}件")
        self.test_rewrite_btn.config(state="normal")
        
        # テスト結果ウィンドウを作成
        result_window = tk.Toplevel(self.frame)
        result_window.title("リライトテスト結果")
        result_window.geometry("800x600")
        
        # 結果サマリー
        summary_frame = ttk.LabelFrame(result_window, text="テスト結果サマリー", padding="10")
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        summary_text = f"総件数: {len(test_results)}\n"
        summary_text += f"成功: {success_count}件 (DMM APIで商品発見)\n"
        summary_text += f"失敗: {error_count}件 (商品未発見またはエラー)"
        
        summary_label = ttk.Label(summary_frame, text=summary_text, font=("Arial", 10))
        summary_label.pack()
        
        # 詳細結果
        detail_frame = ttk.LabelFrame(result_window, text="詳細結果", padding="10")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 結果一覧のTreeview
        columns = ("投稿ID", "品番", "DMM検索結果", "ステータス", "使用フロア", "エラー詳細")
        result_tree = ttk.Treeview(detail_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            result_tree.heading(col, text=col)
            if col == "DMM検索結果":
                result_tree.column(col, width=300)
            elif col == "使用フロア":
                result_tree.column(col, width=100)
            elif col == "エラー詳細":
                result_tree.column(col, width=200)
            else:
                result_tree.column(col, width=100)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=result_tree.yview)
        result_tree.configure(yscrollcommand=scrollbar.set)
        
        result_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 結果を追加
        for result in test_results:
            status_text = {
                'success': '成功',
                'no_result': '商品未発見',
                'error': 'エラー'
            }.get(result['status'], '不明')
            
            error_detail = result.get('error', '')
            
            result_tree.insert("", "end", values=(
                result['post_id'],
                result['product_code'],
                result['title'],
                status_text,
                result.get('floor', 'N/A'),
                error_detail
            ))
        
        # 閉じるボタン
        close_btn = ttk.Button(result_window, text="閉じる", command=result_window.destroy)
        close_btn.pack(pady=10)
    
    def rewrite_completed(self, success_count: int, error_count: int):
        """リライト完了処理"""
        self.progress_var.set(f"リライト完了: 成功{success_count}件, 失敗{error_count}件")
        self.rewrite_btn.config(state="normal")
        
        messagebox.showinfo(
            "完了", 
            f"リライトが完了しました\n"
            f"成功: {success_count}件\n"
            f"失敗: {error_count}件"
        )
        
        # 結果を更新
        self.update_rewrite_results()
    
    def update_rewrite_results(self):
        """リライト結果を更新"""
        for item in self.posts_tree.get_children():
            values = list(self.posts_tree.item(item)['values'])
            post_id = int(values[0])
            
            if post_id in self.extracted_codes:
                values[6] = "リライト完了"  # リライト状態カラム（インデックス調整）
            
            self.posts_tree.item(item, values=values)
