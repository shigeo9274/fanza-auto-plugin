#!/usr/bin/env python3
"""
FANZA Auto Plugin - GUI起動スクリプト
"""

import sys
import os

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import main
    print("GUIを起動しています...")
    main()
except ImportError as e:
    print(f"エラー: 必要なモジュールが見つかりません: {e}")
    print("以下のコマンドで依存関係をインストールしてください:")
    print("python -m pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"エラー: GUIの起動に失敗しました: {e}")
    sys.exit(1)
