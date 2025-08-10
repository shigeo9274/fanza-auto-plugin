# FANZA Auto Plugin - Python版

FANZA Auto PluginをPHPからPythonに変換したバージョンです。DMM WEB APIを使用してコンテンツを検索し、WordPressに自動投稿します。

## 機能

- DMM WEB APIを使用したコンテンツ検索
- 年齢認証対応のスクレイピング（Selenium使用）
- WordPress REST APIを使用した投稿作成
- 重複投稿防止
- スケジュール実行（APScheduler使用）
- テンプレートベースのコンテンツ生成
- 画像の自動ダウンロードと設定

## インストール

### 1. 依存関係のインストール

```bash
python -m pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成するか、環境変数を設定してください：

```bash
# DMM API設定
DMM_API_ID=あなたのAPI_ID
DMM_AFFILIATE_ID=xxxxx-990

# WordPress設定
WORDPRESS_BASE_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APPLICATION_PASSWORD=your_app_password

# DMM検索設定
SITE=FANZA
SERVICE=digital
FLOOR=videoc
HITS=1
SORT=date
KEYWORD=

# ブラウザ設定（年齢認証対応）
USE_BROWSER=true
HEADLESS=true
CLICK_XPATH=//*[@id=":R6:"]/div[2]/div[2]/div[3]/div[1]/a
PAGE_WAIT_SEC=5

# スケジュール設定
CRON_MINUTE=0
CRON_HOURS=0,6,12,18
```

## 使用方法

### コマンドライン

#### 1回実行
```bash
python -m py_fanza_auto.cli once
```

#### テスト実行（投稿なし）
```bash
python -m py_fanza_auto.cli test
```

#### スケジュール実行
```bash
python -m py_fanza_auto.cli schedule
```

### GUIアプリケーション

#### 起動方法
```bash
python py_fanza_auto/run_gui.py
```

または

```bash
python -m py_fanza_auto.gui
```

#### GUI機能

- **設定画面**: すべての設定項目を視覚的に編集
- **実行制御**: 1回実行、テスト実行、スケジュール実行
- **ログ表示**: リアルタイムでの実行ログ
- **設定保存/読み込み**: 環境変数への設定の保存と読み込み

## 設定項目

### DMM API設定
- `DMM_API_ID`: DMM APIのID
- `DMM_AFFILIATE_ID`: DMMアフィリエイトID

### WordPress設定
- `WORDPRESS_BASE_URL`: WordPressサイトのURL
- `WORDPRESS_USERNAME`: WordPressユーザー名
- `WORDPRESS_APPLICATION_PASSWORD`: WordPressアプリケーションパスワード

### DMM検索設定
- `SITE`: サイト（FANZA/DMM）
- `SERVICE`: サービス（digital/mono）
- `FLOOR`: フロア（videoc/videoa/videom/videon）
- `HITS`: 取得件数
- `SORT`: ソート順（date/rank/review/price）
- `KEYWORD`: 検索キーワード

### ブラウザ設定
- `USE_BROWSER`: Selenium使用の有無
- `HEADLESS`: 無画面実行の有無
- `CLICK_XPATH`: 年齢認証ボタンのXPath
- `PAGE_WAIT_SEC`: ページ読み込み後の待機秒数

### スケジュール設定
- `CRON_MINUTE`: 実行分（0-59）
- `CRON_HOURS`: 実行時（0-23、カンマ区切り）

## ファイル構成

```
py_fanza_auto/
├── config.py          # 設定管理
├── dmm_client.py      # DMM API クライアント
├── wp_client.py       # WordPress API クライアント
├── template.py        # テンプレート処理
├── scrape.py          # スクレイピング処理
├── browser.py         # ブラウザ自動化
├── engine.py          # メインエンジン
├── cli.py            # コマンドラインインターフェース
├── gui.py            # GUIアプリケーション
├── run_gui.py        # GUI起動スクリプト
├── requirements.txt   # 依存関係
└── README.md         # このファイル
```

## トラブルシューティング

### 依存関係エラー
```bash
ModuleNotFoundError: No module named 'selenium'
```
→ `python -m pip install -r requirements.txt` を実行

### ブラウザエラー
- ChromeDriverが自動でダウンロードされます
- 年齢認証のXPathが正しいか確認してください
- `HEADLESS=false` で動作確認してください

### WordPress接続エラー
- URL、ユーザー名、アプリケーションパスワードが正しいか確認
- WordPress REST APIが有効になっているか確認

## 注意事項

- DMM APIの利用規約を遵守してください
- スクレイピングは適切な間隔を空けて実行してください
- WordPressの投稿制限に注意してください
- 大量の画像ダウンロードはサーバー負荷に注意してください

## ライセンス

元のPHPプラグインのライセンスに準拠します。

