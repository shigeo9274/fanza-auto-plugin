# FANZA Auto Plugin

FANZAの商品情報を自動的に取得・投稿するPythonアプリケーションです。

## 機能

- FANZAからの商品情報の自動取得
- WordPressへの自動投稿
- スケジュール実行
- GUI設定画面
- カテゴリ管理
- ログ管理

## セットアップ

### 必要な環境

- Python 3.7以上
- Chrome/Chromium ブラウザ
- WordPressサイト

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/fanza-auto-plugin.git
cd fanza-auto-plugin
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. 設定ファイルを作成
```bash
cp config/settings.json.example config/settings.json
```

4. 設定を編集
- `config/settings.json` - 基本設定
- `config/post_settings.json` - 投稿設定
- `config/schedule_settings.json` - スケジュール設定

## 使用方法

### GUI起動
```bash
python run_gui.py
```

### コマンドライン実行
```bash
python cli.py
```

### スケジュール実行
```bash
python scheduler.py
```

## 設定

詳細な設定方法については、各設定ファイルのコメントを参照してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 注意事項

- このツールは個人的な使用目的でのみ使用してください
- FANZAの利用規約を遵守してください
- 過度なアクセスは避けてください

