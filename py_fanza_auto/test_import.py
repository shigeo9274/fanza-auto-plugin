#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("インポートテスト開始...")

try:
    print("template.pyのインポートテスト...")
    from template import Renderer
    print("✓ template.pyのインポート成功")
    
    print("Rendererクラスのインスタンス化テスト...")
    renderer = Renderer()
    print("✓ Rendererクラスのインスタンス化成功")
    
    print("engine.pyのインポートテスト...")
    from engine import Engine
    print("✓ engine.pyのインポート成功")
    
    print("すべてのインポートテストが成功しました！")
    
except ImportError as e:
    print(f"✗ インポートエラー: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ その他のエラー: {e}")
    import traceback
    traceback.print_exc()
