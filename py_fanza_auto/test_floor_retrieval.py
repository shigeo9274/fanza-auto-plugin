#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
フロア取得機能のテストスクリプト
"""

import os
import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dmm_client import DMMClient

def test_floor_retrieval():
    """フロア取得機能をテスト"""
    print("=== フロア取得機能テスト ===")
    
    # 環境変数からAPI情報を取得
    api_id = os.getenv('DMM_API_ID')
    affiliate_id = os.getenv('DMM_AFFILIATE_ID')
    
    if not api_id or not affiliate_id:
        print("環境変数 DMM_API_ID または DMM_AFFILIATE_ID が設定されていません")
        print("以下のように設定してください:")
        print("export DMM_API_ID='your_api_id'")
        print("export DMM_AFFILIATE_ID='your_affiliate_id'")
        return False
    
    print(f"API ID: {api_id[:8]}...")
    print(f"Affiliate ID: {affiliate_id[:8]}...")
    
    try:
        # DMMクライアントを作成
        client = DMMClient(api_id=api_id, affiliate_id=affiliate_id)
        
        # フロア一覧を取得
        print("\nフロア一覧を取得中...")
        floor_data = client.floor_list(use_cache=True, cache_file="test_floor_cache.json")
        
        if 'result' in floor_data and 'site' in floor_data['result']:
            sites = floor_data['result']['site']
            print(f"サイト数: {len(sites)}")
            
            total_floors = 0
            for site in sites:
                site_name = site.get('name', 'Unknown')
                print(f"\nサイト: {site_name}")
                
                if 'service' in site:
                    services = site['service']
                    print(f"  サービス数: {len(services)}")
                    
                    for service in services:
                        service_name = service.get('name', 'Unknown')
                        print(f"    サービス: {service_name}")
                        
                        if 'floor' in service:
                            floors = service['floor']
                            print(f"      フロア数: {len(floors)}")
                            
                            for floor in floors:
                                floor_name = floor.get('name', '')
                                floor_code = floor.get('code', '')
                                if floor_name and floor_code:
                                    print(f"        - {floor_name} ({floor_code})")
                                    total_floors += 1
            
            print(f"\n総フロア数: {total_floors}")
            
            # フロアサマリーを取得
            print("\nフロアサマリーを取得中...")
            summary = client.get_floor_summary()
            if summary:
                print(f"サマリー - 総フロア数: {summary.get('total_floors', 0)}")
                if summary.get('floors_by_site'):
                    print("サイト別フロア数:")
                    for site, count in summary['floors_by_site'].items():
                        print(f"  {site}: {count}")
            
            return True
            
        else:
            print("フロア一覧の取得に失敗しました")
            print(f"レスポンス: {json.dumps(floor_data, indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"フロア取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_functionality():
    """キャッシュ機能をテスト"""
    print("\n=== キャッシュ機能テスト ===")
    
    api_id = os.getenv('DMM_API_ID')
    affiliate_id = os.getenv('DMM_AFFILIATE_ID')
    
    if not api_id or not affiliate_id:
        print("API情報が設定されていないため、キャッシュテストをスキップします")
        return
    
    try:
        client = DMMClient(api_id=api_id, affiliate_id=affiliate_id)
        
        # キャッシュファイルのパス
        cache_file = "test_floor_cache.json"
        
        # 1回目の取得（APIから）
        print("1回目のフロア取得（APIから）...")
        floor_data1 = client.floor_list(use_cache=False, cache_file=cache_file)
        
        # 2回目の取得（キャッシュから）
        print("2回目のフロア取得（キャッシュから）...")
        floor_data2 = client.floor_list(use_cache=True, cache_file=cache_file)
        
        # 結果を比較
        if floor_data1 == floor_data2:
            print("キャッシュ機能が正常に動作しています")
        else:
            print("キャッシュ機能に問題があります")
            
        # テスト用キャッシュファイルを削除
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("テスト用キャッシュファイルを削除しました")
            
    except Exception as e:
        print(f"キャッシュ機能テストエラー: {e}")

if __name__ == "__main__":
    print("フロア取得機能のテストを開始します")
    print("注意: このテストを実行するには、有効なDMM API IDとAffiliate IDが必要です")
    print()
    
    try:
        success = test_floor_retrieval()
        if success:
            test_cache_functionality()
        
        print("\n=== テスト完了 ===")
        if success:
            print("フロア取得機能は正常に動作しています")
        else:
            print("フロア取得機能に問題があります")
            
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
