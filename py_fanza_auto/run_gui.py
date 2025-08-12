#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fanza Auto Plugin - メイン実行ファイル
"""

import sys
import argparse
import logging
from gui_main import FanzaAutoGUI

def main():
    """メイン関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Fanza Auto Plugin')
    parser.add_argument('--auto-run', action='store_true', 
                       help='自動実行モードで起動（GUIなし）')
    parser.add_argument('--headless', action='store_true',
                       help='ヘッドレスモードで起動')
    
    args = parser.parse_args()
    
    if args.auto_run:
        # 自動実行モード
        print("自動実行モードで起動しています...")
        try:
            # クロスプラットフォームスケジューラーを使用
            from platform_scheduler import PlatformSchedulerManager
            
            # スケジューラーマネージャーを作成
            manager = PlatformSchedulerManager()
            
            # スケジューラー情報を表示
            info = manager.get_scheduler_info()
            print(f"スケジューラー: {info['name']}")
            print(f"プラットフォーム: {info['platform']}")
            
            # 設定ファイルからスケジュール設定を読み込み
            import json
            import os
            schedule_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "schedule_settings.json")
            
            if os.path.exists(schedule_file):
                with open(schedule_file, 'r', encoding='utf-8') as f:
                    schedule_config = json.load(f)
                print(f"スケジュール設定を読み込みました: {schedule_file}")
            else:
                print(f"スケジュール設定ファイルが見つかりません: {schedule_file}")
                return 1
            
            if schedule_config.get("AUTO_ON") == "on":
                print("スケジュール設定を検出しました。自動実行を開始します...")
                
                # スケジュールを設定
                if manager.setup_schedule(schedule_config):
                    print("スケジュール設定が完了しました")
                    
                    # スケジュール一覧を表示
                    schedules = manager.list_schedules()
                    print(f"登録済みスケジュール: {schedules}")
                    
                    # 即座にテスト実行
                    print("テスト実行を開始します...")
                    if manager.test_schedule("FanzaAutoPlugin"):
                        print("テスト実行が完了しました")
                    else:
                        print("テスト実行に失敗しました")
                else:
                    print("スケジュール設定に失敗しました")
            else:
                print("自動実行が無効になっています")
                
        except Exception as e:
            print(f"自動実行モードでエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return 1
            
    else:
        # 通常のGUIモード
        print("GUIを起動しています...")
        try:
            import tkinter as tk
            root = tk.Tk()
            app = FanzaAutoGUI(root)
            
            # ウィンドウを閉じる際の処理
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            
            # メインループの開始
            root.mainloop()
        except Exception as e:
            print(f"GUI起動でエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
