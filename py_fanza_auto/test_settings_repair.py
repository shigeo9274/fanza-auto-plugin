#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
設定修復機能のテストスクリプト
"""

import os
import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from settings_manager import SettingsManager

def test_settings_repair():
    """設定修復機能をテスト"""
    print("=== 設定修復機能テスト ===")
    
    # 設定マネージャーを初期化
    settings_manager = SettingsManager(str(project_root))
    
    print(f"設定ファイルパス: {settings_manager.post_settings_file}")
    print(f"バックアップディレクトリ: {settings_manager.backup_dir}")
    
    # 現在の設定を読み込み
    try:
        current_settings = settings_manager.load_post_settings()
        print(f"現在の設定: {len(current_settings.get('post_settings', {}))}件")
    except Exception as e:
        print(f"設定読み込みエラー: {e}")
    
    # バックアップ一覧を表示
    backups = settings_manager.get_backup_list()
    print(f"利用可能なバックアップ: {len(backups)}件")
    for backup in backups[:5]:  # 最新5件を表示
        print(f"  - {backup}")
    
    # 設定修復を実行
    print("\n設定修復を実行中...")
    if settings_manager.repair_settings():
        print("設定修復が完了しました")
        
        # 修復後の設定を確認
        try:
            repaired_settings = settings_manager.load_post_settings()
            print(f"修復後の設定: {len(repaired_settings.get('post_settings', {}))}件")
        except Exception as e:
            print(f"修復後の設定読み込みエラー: {e}")
    else:
        print("設定修復に失敗しました")

def test_corrupted_settings():
    """破損した設定ファイルのテスト"""
    print("\n=== 破損した設定ファイルのテスト ===")
    
    settings_manager = SettingsManager(str(project_root))
    
    # 破損した設定ファイルを作成
    corrupted_file = settings_manager.post_settings_file + ".corrupted"
    with open(corrupted_file, 'w', encoding='utf-8') as f:
        f.write('{"invalid": json}')
    
    print(f"破損した設定ファイルを作成: {corrupted_file}")
    
    # 破損したファイルで設定マネージャーをテスト
    try:
        test_manager = SettingsManager(str(project_root))
        test_manager.post_settings_file = corrupted_file
        
        print("破損したファイルの修復をテスト...")
        if test_manager.repair_settings():
            print("破損したファイルの修復が完了しました")
        else:
            print("破損したファイルの修復に失敗しました")
            
    except Exception as e:
        print(f"破損したファイルのテストエラー: {e}")
    finally:
        # テストファイルを削除
        if os.path.exists(corrupted_file):
            os.remove(corrupted_file)
            print("テストファイルを削除しました")

if __name__ == "__main__":
    try:
        test_settings_repair()
        test_corrupted_settings()
        print("\n=== テスト完了 ===")
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
