"""
リライト機能用のタブクラス
既存投稿から品番を抽出し、DMM APIで再検索してリライトする
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import threading
import time
from typing import List, Dict, Any, Optional
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
        
        # DMM API接続テストボタン
        self.test_api_btn = ttk.Button(
            control_frame, 
            text="DMM API接続テスト", 
            command=self.test_dmm_api,
            state="normal"
        )
        self.test_api_btn.pack(side="left", padx=(0, 10))
        
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
        posts_frame = ttk.LabelFrame(main_frame, text="投稿一覧", padding="5")
        posts_frame.pack(fill="both", expand=True)
        
        # 投稿一覧のTreeview
        columns = ("ID", "タイトル", "Slug", "品番", "抽出状態", "リライト状態")
        self.posts_tree = ttk.Treeview(posts_frame, columns=columns, show="headings", height=15)
        
        # カラム設定
        for col in columns:
            self.posts_tree.heading(col, text=col)
            if col == "タイトル":
                self.posts_tree.column(col, width=200)
            elif col == "Slug":
                self.posts_tree.column(col, width=120)
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
        
        # データ保存用
        self.existing_posts = []
        self.extracted_codes = {}
        
    def fetch_existing_posts(self):
        """既存投稿を取得"""
        self.progress_var.set("投稿取得中...")
        self.fetch_posts_btn.config(state="disabled")
        
        def fetch_thread():
            try:
                # WordPressから投稿を取得
                posts = self.engine.wp.get_posts(per_page=100, status='publish')
                
                # GUIスレッドで結果を更新
                self.parent_notebook.after(0, self.update_posts_list, posts)
                
            except Exception as e:
                error_msg = f"投稿取得エラー: {str(e)}"
                self.parent_notebook.after(0, lambda: messagebox.showerror("エラー", error_msg))
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
            
            self.posts_tree.insert("", "end", values=(
                post_id,
                title[:50] + "..." if len(title) > 50 else title,
                slug,
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
                """キーワードを反映してURLを更新"""
                current_params = params.copy()
                current_params["keyword"] = keyword_var.get()
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
            
            # キーワード変更時にURL更新
            keyword_var.trace("w", lambda *args: update_url())
            
            # テスト実行ボタン
            test_frame = ttk.Frame(param_window)
            test_frame.pack(fill="x", padx=10, pady=5)
            
            test_btn = ttk.Button(
                test_frame, 
                text="このパラメータでテスト実行", 
                command=lambda: self.test_with_params(params, param_window, keyword_var.get())
            )
            test_btn.pack(side="left")
            
            # 閉じるボタン
            close_btn = ttk.Button(test_frame, text="閉じる", command=param_window.destroy)
            close_btn.pack(side="right")
            
        except Exception as e:
            messagebox.showerror("エラー", f"パラメータ確認エラー: {str(e)}")
    
    def test_with_params(self, params: Dict[str, Any], window, keyword: str):
        """指定されたパラメータでテスト実行"""
        try:
            # 入力されたキーワードを使用
            if not keyword:
                messagebox.showwarning("警告", "キーワードを入力してください")
                return
            
            # 実際のAPI呼び出し
            search_result = self.engine.dmm.item_list(
                site=params['site'],
                service=params['service'],
                floor=params['floor'],
                keyword=keyword,
                hits=params['hits']
            )
            
            # デバッグ情報を出力
            print(f"パラメータテスト (キーワード: {keyword}) のAPIレスポンス:")
            print(f"  レスポンス構造: {list(search_result.keys()) if isinstance(search_result, dict) else type(search_result)}")
            if isinstance(search_result, dict):
                print(f"  itemsキーの存在: {'items' in search_result}")
                if 'items' in search_result:
                    print(f"  itemsの内容: {len(search_result['items'])}件")
            
            # 結果表示
            if search_result.get('items') and search_result['items']:
                item = search_result['items'][0]
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
                values[3] = self.extracted_codes[post_id]  # 品番カラム
                values[4] = "抽出済み"
                values[5] = "リライト可能"
            else:
                values[3] = "品番なし"
                values[4] = "抽出失敗"
                values[5] = "対象外"
            
            self.posts_tree.item(item, values=values)
        
        self.progress_var.set(f"{extracted_count}件の品番を抽出しました")
        self.extract_codes_btn.config(state="normal")
        
        if extracted_count > 0:
            self.test_rewrite_btn.config(state="normal")
            self.rewrite_btn.config(state="normal")
    
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
                            
                            # DMM APIで品番検索
                            search_result = self.engine.dmm.item_list(
                                site="FANZA",
                                service="digital",
                                floor="videoc",
                                keyword=product_code,
                                hits=1
                            )
                            
                            # デバッグ情報を出力
                            print(f"投稿 {post_id} (品番: {product_code}) のAPIレスポンス:")
                            print(f"  レスポンス構造: {list(search_result.keys()) if isinstance(search_result, dict) else type(search_result)}")
                            if isinstance(search_result, dict):
                                print(f"  itemsキーの存在: {'items' in search_result}")
                                if 'items' in search_result:
                                    print(f"  itemsの内容: {len(search_result['items'])}件")
                            
                            if search_result.get('items') and search_result['items']:
                                item = search_result['items'][0]
                                
                                # 投稿を更新
                                self.engine.rewrite_post(post_id, item)
                                success_count += 1
                                
                                # 個別進捗更新
                                self.parent_notebook.after(0, lambda: self.progress_var.set(
                                    f"リライト中... バッチ{batch_num+1}/{total_batches} - 成功:{success_count}, 失敗:{error_count}"
                                ))
                            else:
                                error_count += 1
                                print(f"投稿 {post_id} (品番: {product_code}): DMM APIで商品が見つかりません")
                                
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
                        
                        # DMM APIで品番検索
                        search_result = self.engine.dmm.item_list(
                            site="FANZA",
                            service="digital",
                            floor="videoc",
                            keyword=product_code,
                            hits=1
                        )
                        
                        # デバッグ情報を出力
                        print(f"投稿 {post_id} (品番: {product_code}) のAPIレスポンス:")
                        print(f"  レスポンス構造: {list(search_result.keys()) if isinstance(search_result, dict) else type(search_result)}")
                        if isinstance(search_result, dict):
                            print(f"  itemsキーの存在: {'items' in search_result}")
                            if 'items' in search_result:
                                print(f"  itemsの内容: {len(search_result['items'])}件")
                        
                        if search_result.get('items') and search_result['items']:
                            item = search_result['items'][0]
                            test_results.append({
                                'post_id': post_id,
                                'product_code': product_code,
                                'title': item.get('title', 'N/A'),
                                'status': 'success'
                            })
                            success_count += 1
                        else:
                            test_results.append({
                                'post_id': post_id,
                                'product_code': product_code,
                                'title': 'N/A',
                                'status': 'no_result'
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
        columns = ("投稿ID", "品番", "DMM検索結果", "ステータス", "エラー詳細")
        result_tree = ttk.Treeview(detail_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            result_tree.heading(col, text=col)
            if col == "DMM検索結果":
                result_tree.column(col, width=300)
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
                values[5] = "リライト完了"  # リライト状態カラム
            
            self.posts_tree.item(item, values=values)
