# Fanza Auto Plugin

WordPress用のFANZA自動投稿プラグインです。PythonスクリプトとWordPressプラグインを組み合わせて、FANZAのコンテンツを自動的にWordPressサイトに投稿します。

## 機能

- FANZAからの自動コンテンツ取得
- WordPressへの自動投稿
- カテゴリ管理
- スケジュール投稿
- GUIインターフェース
- ログ管理

## セットアップ

### 必要な環境

- Python 3.7+
- WordPress 5.0+
- PHP 7.4+

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/fanza-auto-plugin.git
cd fanza-auto-plugin
```

2. Python依存関係をインストール
```bash
cd py_fanza_auto
pip install -r requirements.txt
```

3. WordPressプラグインを有効化
   - `fanza-auto-plugin.php`をWordPressの`wp-content/plugins/`ディレクトリにコピー
   - WordPress管理画面でプラグインを有効化

### 設定

1. `py_fanza_auto/config/post_settings.json`を編集して、WordPressの設定を入力
2. FANZAの認証情報を設定
3. 投稿設定をカスタマイズ

## 使用方法

### GUIアプリケーション

```bash
cd py_fanza_auto
python run_gui.py
```

### コマンドライン

```bash
cd py_fanza_auto
python cli.py --help
```

### スケジューラー

```bash
cd py_fanza_auto
python scheduler.py
```

## ファイル構成

```
fanza-auto-plugin/
├── fanza-auto-plugin.php          # WordPressプラグインファイル
├── py_fanza_auto/                 # Pythonスクリプト
│   ├── browser.py                 # ブラウザ制御
│   ├── category_manager.py        # カテゴリ管理
│   ├── cli.py                     # コマンドラインインターフェース
│   ├── config/                    # 設定ファイル
│   ├── engine.py                  # メインエンジン
│   ├── gui.py                     # GUIインターフェース
│   ├── wp_client.py               # WordPress API クライアント
│   └── requirements.txt           # Python依存関係
└── templates/                      # HTMLテンプレート
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 注意事項

- このプラグインは教育目的で作成されています
- 商用利用の前に適切なライセンス確認を行ってください
- FANZAの利用規約を遵守してください
