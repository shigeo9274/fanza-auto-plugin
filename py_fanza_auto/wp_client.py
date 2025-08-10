from __future__ import annotations
from typing import Any, Dict, Optional, List
import base64
import requests


class WordPressClient:
    def __init__(self, base_url: str, username: str, application_password: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        token = f"{username}:{application_password}".encode("utf-8")
        self.headers = {
            "Authorization": "Basic " + base64.b64encode(token).decode("utf-8"),
        }

    def create_post(self, title: str, content: str, status: str = "publish", slug: Optional[str] = None, excerpt: Optional[str] = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {"title": title, "content": content, "status": status}
        if slug:
            data["slug"] = slug
        if excerpt is not None:
            data["excerpt"] = excerpt
        url = f"{self.base_url}/wp-json/wp/v2/posts"
        res = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def get_post_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/wp-json/wp/v2/posts"
        res = requests.get(url, headers=self.headers, params={"slug": slug}, timeout=self.timeout)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, list) and data:
            return data[0]
        return None

    def upload_media(self, filename: str, bytes_data: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        url = f"{self.base_url}/wp-json/wp/v2/media"
        headers = dict(self.headers)
        headers.update({
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": mime_type,
        })
        res = requests.post(url, headers=headers, data=bytes_data, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def set_featured_media(self, post_id: int, media_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        res = requests.post(url, headers=self.headers, json={"featured_media": media_id}, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def delete_post(self, post_id: int, force: bool = True) -> Dict[str, Any]:
        """投稿を削除する"""
        url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        params = {"force": force}
        res = requests.delete(url, headers=self.headers, params=params, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def update_post(self, post_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """投稿を更新する"""
        url = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        res = requests.put(url, headers=self.headers, json=data, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def get_categories(self) -> List[Dict[str, Any]]:
        """カテゴリ一覧を取得する"""
        url = f"{self.base_url}/wp-json/wp/v2/categories"
        res = requests.get(url, headers=self.headers, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def get_tags(self) -> List[Dict[str, Any]]:
        """タグ一覧を取得する"""
        url = f"{self.base_url}/wp-json/wp/v2/tags"
        res = requests.get(url, headers=self.headers, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def get_or_create_category(self, category_name: str) -> int:
        """カテゴリ名からIDを取得、存在しない場合は作成"""
        categories = self.get_categories()
        for cat in categories:
            if cat.get('name') == category_name:
                return cat.get('id')
        
        # カテゴリが存在しない場合は作成
        create_data = {"name": category_name}
        url = f"{self.base_url}/wp-json/wp/v2/categories"
        res = requests.post(url, headers=self.headers, json=create_data, timeout=self.timeout)
        res.raise_for_status()
        new_cat = res.json()
        return new_cat.get('id')

    def get_or_create_tag(self, tag_name: str) -> int:
        """タグ名からIDを取得、存在しない場合は作成"""
        tags = self.get_tags()
        for tag in tags:
            if tag.get('name') == tag_name:
                return tag.get('id')
        
        # タグが存在しない場合は作成
        create_data = {"name": tag_name}
        url = f"{self.base_url}/wp-json/wp/v2/tags"
        res = requests.post(url, headers=self.headers, json=create_data, timeout=self.timeout)
        res.raise_for_status()
        new_tag = res.json()
        return new_tag.get('id')
