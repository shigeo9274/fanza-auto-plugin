#!/usr/bin/env python3
"""
WordPress投稿更新のテストスクリプト
"""

import os
from dotenv import load_dotenv
from wp_client import WordPressClient

def test_post_update():
    # 環境変数を読み込み
    load_dotenv()
    
    # WordPressクライアントを初期化
    wp = WordPressClient(
        base_url=os.getenv("WORDPRESS_BASE_URL"),
        username=os.getenv("WORDPRESS_USERNAME"),
        application_password=os.getenv("WORDPRESS_APPLICATION_PASSWORD")
    )
    
    print("=== WordPress投稿更新テスト ===")
    print(f"Base URL: {os.getenv('WORDPRESS_BASE_URL')}")
    print(f"Username: {os.getenv('WORDPRESS_USERNAME')}")
    print(f"App Password: {'*' * len(os.getenv('WORDPRESS_APPLICATION_PASSWORD', ''))}")
    
    try:
        # 1. 既存投稿の取得テスト
        print("\n1. 既存投稿の取得テスト...")
        existing_post = wp.get_post_by_slug("deas016")
        if existing_post:
            post_id = existing_post.get('id')
            print(f"投稿ID: {post_id}")
            print(f"現在のタイトル: {existing_post.get('title', {}).get('rendered', 'N/A')}")
        else:
            print("投稿が見つかりません")
            return
        
        # 2. 投稿更新テスト（最小限のデータ）
        print("\n2. 投稿更新テスト...")
        update_data = {
            "title": "テスト更新 - ういさん",
            "content": "これはテスト更新です。"
        }
        
        print(f"更新データ: {update_data}")
        print(f"認証ヘッダー: {wp.headers}")
        
        updated_post = wp.update_post(post_id, update_data)
        print(f"更新成功: {updated_post.get('id')}")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    test_post_update()
