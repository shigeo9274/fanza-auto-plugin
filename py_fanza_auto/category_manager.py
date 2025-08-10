from __future__ import annotations
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class CategoryType(Enum):
    """カテゴリタイプ"""
    JAN = "jan"           # JANコードベース
    ACTRESS = "act"       # 女優ベース
    DIRECTOR = "director" # 監督ベース
    SERIES = "seri"       # シリーズベース
    GENRE = "genre"       # ジャンルベース
    MAKER = "maker"       # メーカーベース
    LABEL = "label"       # レーベルベース
    CUSTOM = "custom"     # カスタム


@dataclass
class CategoryConfig:
    """カテゴリ設定"""
    type: CategoryType
    name: str
    slug: str
    description: str = ""
    parent_id: Optional[int] = None
    auto_create: bool = True
    mapping_rules: Dict[str, str] = None  # カスタムマッピングルール


class CategoryManager:
    """WordPressのカテゴリ・タグ管理クラス"""
    
    def __init__(self, wp_client):
        self.wp_client = wp_client
        self.category_cache: Dict[str, Dict[str, Any]] = {}
        self.tag_cache: Dict[str, Dict[str, Any]] = {}
        self._load_categories()
        self._load_tags()
    
    def _load_categories(self):
        """カテゴリ一覧を読み込み"""
        try:
            categories = self.wp_client.get_categories()
            for cat in categories:
                self.category_cache[cat['slug']] = cat
            logger.info(f"{len(self.category_cache)}個のカテゴリをキャッシュしました")
        except Exception as e:
            logger.error(f"カテゴリ読み込みエラー: {e}")
    
    def _load_tags(self):
        """タグ一覧を読み込み"""
        try:
            tags = self.wp_client.get_tags()
            for tag in tags:
                self.tag_cache[tag['slug']] = tag
            logger.info(f"{len(self.tag_cache)}個のタグをキャッシュしました")
        except Exception as e:
            logger.error(f"タグ読み込みエラー: {e}")
    
    def get_categories_for_item(self, item: Dict[str, Any], category_type: str) -> List[int]:
        """アイテムに基づいてカテゴリIDを取得"""
        try:
            category_ids = []
            
            if category_type == CategoryType.JAN.value:
                category_ids = self._get_jan_categories(item)
            elif category_type == CategoryType.ACTRESS.value:
                category_ids = self._get_actress_categories(item)
            elif category_type == CategoryType.DIRECTOR.value:
                category_ids = self._get_director_categories(item)
            elif category_type == CategoryType.SERIES.value:
                category_ids = self._get_series_categories(item)
            elif category_type == CategoryType.GENRE.value:
                category_ids = self._get_genre_categories(item)
            elif category_type == CategoryType.MAKER.value:
                category_ids = self._get_maker_categories(item)
            elif category_type == CategoryType.LABEL.value:
                category_ids = self._get_label_categories(item)
            elif category_type == CategoryType.CUSTOM.value:
                category_ids = self._get_custom_categories(item)
            
            return category_ids
            
        except Exception as e:
            logger.error(f"カテゴリ取得エラー: {e}")
            return []
    
    def _get_jan_categories(self, item: Dict[str, Any]) -> List[int]:
        """JANコードベースのカテゴリを取得"""
        category_ids = []
        jancode = item.get('jancode', '')
        
        if jancode:
            # JANコードの最初の2桁（国コード）でカテゴリを作成
            country_code = jancode[:2]
            if country_code == '49':  # 日本
                category_name = "日本製"
                category_slug = "japan-made"
            elif country_code == '45':  # 日本
                category_name = "日本製"
                category_slug = "japan-made"
            else:
                category_name = "輸入品"
                category_slug = "imported"
            
            category_id = self._get_or_create_category(category_name, category_slug)
            if category_id:
                category_ids.append(category_id)
        
        return category_ids
    
    def _get_actress_categories(self, item: Dict[str, Any]) -> List[int]:
        """女優ベースのカテゴリを取得"""
        category_ids = []
        actresses = item.get('actress', [])
        
        for actress in actresses:
            name = actress.get('name', '')
            if name:
                # 女優名をサニタイズしてスラッグを作成
                slug = self._sanitize_slug(name)
                category_id = self._get_or_create_category(name, slug, f"女優: {name}")
                if category_id:
                    category_ids.append(category_id)
        
        return category_ids
    
    def _get_director_categories(self, item: Dict[str, Any]) -> List[int]:
        """監督ベースのカテゴリを取得"""
        category_ids = []
        directors = item.get('director', [])
        
        for director in directors:
            name = director.get('name', '')
            if name:
                slug = self._sanitize_slug(name)
                category_id = self._get_or_create_category(name, slug, f"監督: {name}")
                if category_id:
                    category_ids.append(category_id)
        
        return category_ids
    
    def _get_series_categories(self, item: Dict[str, Any]) -> List[int]:
        """シリーズベースのカテゴリを取得"""
        category_ids = []
        series = item.get('series', [])
        
        for ser in series:
            name = ser.get('name', '')
            if name:
                slug = self._sanitize_slug(name)
                category_id = self._get_or_create_category(name, slug, f"シリーズ: {name}")
                if category_id:
                    category_ids.append(category_id)
        
        return category_ids
    
    def _get_genre_categories(self, item: Dict[str, Any]) -> List[int]:
        """ジャンルベースのカテゴリを取得"""
        category_ids = []
        genres = item.get('genre', [])
        
        for genre in genres:
            name = genre.get('name', '')
            if name:
                slug = self._sanitize_slug(name)
                category_id = self._get_or_create_category(name, slug, f"ジャンル: {name}")
                if category_id:
                    category_ids.append(category_id)
        
        return category_ids
    
    def _get_maker_categories(self, item: Dict[str, Any]) -> List[int]:
        """メーカーベースのカテゴリを取得"""
        category_ids = []
        makers = item.get('maker', [])
        
        for maker in makers:
            name = maker.get('name', '')
            if name:
                slug = self._sanitize_slug(name)
                category_id = self._get_or_create_category(name, slug, f"メーカー: {name}")
                if category_id:
                    category_ids.append(category_id)
        
        return category_ids
    
    def _get_label_categories(self, item: Dict[str, Any]) -> List[int]:
        """レーベルベースのカテゴリを取得"""
        category_ids = []
        labels = item.get('label', [])
        
        for label in labels:
            name = label.get('name', '')
            if name:
                slug = self._sanitize_slug(name)
                category_id = self._get_or_create_category(name, slug, f"レーベル: {name}")
                if category_id:
                    category_id.append(category_id)
        
        return category_ids
    
    def _get_custom_categories(self, item: Dict[str, Any]) -> List[int]:
        """カスタムカテゴリを取得"""
        category_ids = []
        
        # コンテンツIDベース
        content_id = item.get('content_id', '')
        if content_id:
            # 品番の最初の文字でカテゴリを作成
            prefix = content_id[:1].upper()
            category_name = f"品番{prefix}系"
            category_slug = f"content-prefix-{prefix.lower()}"
            category_id = self._get_or_create_category(category_name, category_slug)
            if category_id:
                category_ids.append(category_id)
        
        # 価格ベース
        prices = item.get('prices', {})
        if prices.get('list_price'):
            try:
                price = int(prices['list_price'])
                if price < 1000:
                    category_name = "1000円未満"
                    category_slug = "under-1000"
                elif price < 3000:
                    category_name = "1000-3000円"
                    category_slug = "1000-3000"
                elif price < 5000:
                    category_name = "3000-5000円"
                    category_slug = "3000-5000"
                else:
                    category_name = "5000円以上"
                    category_slug = "over-5000"
                
                category_id = self._get_or_create_category(category_name, category_slug)
                if category_id:
                    category_ids.append(category_id)
            except (ValueError, TypeError):
                pass
        
        return category_ids
    
    def _get_or_create_category(self, name: str, slug: str, description: str = "") -> Optional[int]:
        """カテゴリを取得または作成"""
        try:
            # キャッシュから検索
            if slug in self.category_cache:
                return self.category_cache[slug]['id']
            
            # WordPressから検索
            existing = self.wp_client.get_category_by_slug(slug)
            if existing:
                # キャッシュに追加
                self.category_cache[slug] = existing
                return existing['id']
            
            # 新規作成
            new_category = self.wp_client.create_category(name, slug, description)
            if new_category:
                # キャッシュに追加
                self.category_cache[slug] = new_category
                logger.info(f"カテゴリを作成しました: {name} ({slug})")
                return new_category['id']
            
            return None
            
        except Exception as e:
            logger.error(f"カテゴリ取得・作成エラー: {e}")
            return None
    
    def get_tags_for_item(self, item: Dict[str, Any], tag_type: str = "auto") -> List[int]:
        """アイテムに基づいてタグIDを取得"""
        try:
            tag_ids = []
            
            if tag_type == "auto":
                # 自動タグ生成
                tag_ids = self._get_auto_tags(item)
            elif tag_type == "manual":
                # 手動タグ生成（設定ファイルから）
                tag_ids = self._get_manual_tags(item)
            
            return tag_ids
            
        except Exception as e:
            logger.error(f"タグ取得エラー: {e}")
            return []
    
    def _get_auto_tags(self, item: Dict[str, Any]) -> List[int]:
        """自動タグを生成"""
        tag_ids = []
        
        # 出演者タグ
        actresses = item.get('actress', [])
        for actress in actresses:
            name = actress.get('name', '')
            if name:
                tag_id = self._get_or_create_tag(name, f"actress-{self._sanitize_slug(name)}")
                if tag_id:
                    tag_ids.append(tag_id)
        
        # 監督タグ
        directors = item.get('director', [])
        for director in directors:
            name = director.get('name', '')
            if name:
                tag_id = self._get_or_create_tag(name, f"director-{self._sanitize_slug(name)}")
                if tag_id:
                    tag_ids.append(tag_id)
        
        # シリーズタグ
        series = item.get('series', [])
        for ser in series:
            name = ser.get('name', '')
            if name:
                tag_id = self._get_or_create_tag(name, f"series-{self._sanitize_slug(name)}")
                if tag_id:
                    tag_ids.append(tag_id)
        
        # ジャンルタグ
        genres = item.get('genre', [])
        for genre in genres:
            name = genre.get('name', '')
            if name:
                tag_id = self._get_or_create_tag(name, f"genre-{self._sanitize_slug(name)}")
                if tag_id:
                    tag_ids.append(tag_id)
        
        # メーカータグ
        makers = item.get('maker', [])
        for maker in makers:
            name = maker.get('name', '')
            if name:
                tag_id = self._get_or_create_tag(name, f"maker-{self._sanitize_slug(name)}")
                if tag_id:
                    tag_ids.append(tag_id)
        
        # レーベルタグ
        labels = item.get('label', [])
        for label in labels:
            name = label.get('name', '')
            if name:
                tag_id = self._get_or_create_tag(name, f"label-{self._sanitize_slug(name)}")
                if tag_id:
                    tag_ids.append(tag_id)
        
        # コンテンツIDタグ
        content_id = item.get('content_id', '')
        if content_id:
            tag_id = self._get_or_create_tag(content_id, f"content-id-{content_id.lower()}")
            if tag_id:
                tag_ids.append(tag_id)
        
        # JANコードタグ
        jancode = item.get('jancode', '')
        if jancode:
            tag_id = self._get_or_create_tag(jancode, f"jancode-{jancode}")
            if tag_id:
                tag_ids.append(tag_id)
        
        return tag_ids
    
    def _get_manual_tags(self, item: Dict[str, Any]) -> List[int]:
        """手動タグを生成（設定ファイルから）"""
        # この機能は設定ファイルの実装後に拡張
        return []
    
    def _get_or_create_tag(self, name: str, slug: str) -> Optional[int]:
        """タグを取得または作成"""
        try:
            # キャッシュから検索
            if slug in self.tag_cache:
                return self.tag_cache[slug]['id']
            
            # WordPressから検索
            existing = self.wp_client.get_tag_by_slug(slug)
            if existing:
                # キャッシュに追加
                self.tag_cache[slug] = existing
                return existing['id']
            
            # 新規作成
            new_tag = self.wp_client.create_tag(name, slug)
            if new_tag:
                # キャッシュに追加
                self.tag_cache[slug] = new_tag
                logger.info(f"タグを作成しました: {name} ({slug})")
                return new_tag['id']
            
            return None
            
        except Exception as e:
            logger.error(f"タグ取得・作成エラー: {e}")
            return None
    
    def _sanitize_slug(self, text: str) -> str:
        """テキストをスラッグ用にサニタイズ"""
        # 日本語をローマ字に変換（簡易版）
        japanese_map = {
            'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
            'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
            'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
            'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
            'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
            'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
            'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
            'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
            'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
            'わ': 'wa', 'を': 'wo', 'ん': 'n'
        }
        
        # ひらがなをローマ字に変換
        for jp, rom in japanese_map.items():
            text = text.replace(jp, rom)
        
        # 英数字以外を除去
        text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
        
        # スペースをハイフンに変換
        text = re.sub(r'\s+', '-', text)
        
        # 連続するハイフンを単一のハイフンに
        text = re.sub(r'-+', '-', text)
        
        # 先頭と末尾のハイフンを除去
        text = text.strip('-')
        
        # 小文字に変換
        text = text.lower()
        
        return text
    
    def assign_categories_to_post(self, post_id: int, category_ids: List[int]) -> bool:
        """投稿にカテゴリを割り当て"""
        try:
            if not category_ids:
                return True
            
            result = self.wp_client.set_post_categories(post_id, category_ids)
            if result:
                logger.info(f"投稿{post_id}にカテゴリ{category_ids}を割り当てました")
                return True
            return False
            
        except Exception as e:
            logger.error(f"カテゴリ割り当てエラー: {e}")
            return False
    
    def assign_tags_to_post(self, post_id: int, tag_ids: List[int]) -> bool:
        """投稿にタグを割り当て"""
        try:
            if not tag_ids:
                return True
            
            result = self.wp_client.set_post_tags(post_id, tag_ids)
            if result:
                logger.info(f"投稿{post_id}にタグ{tag_ids}を割り当てました")
                return True
            return False
            
        except Exception as e:
            logger.error(f"タグ割り当てエラー: {e}")
            return False
    
    def get_category_hierarchy(self) -> Dict[str, Any]:
        """カテゴリ階層を取得"""
        try:
            categories = list(self.category_cache.values())
            hierarchy = {}
            
            # 親カテゴリを探す
            for cat in categories:
                if not cat.get('parent'):
                    hierarchy[cat['id']] = {
                        'id': cat['id'],
                        'name': cat['name'],
                        'slug': cat['slug'],
                        'children': []
                    }
            
            # 子カテゴリを追加
            for cat in categories:
                if cat.get('parent'):
                    parent_id = cat['parent']
                    if parent_id in hierarchy:
                        hierarchy[parent_id]['children'].append({
                            'id': cat['id'],
                            'name': cat['name'],
                            'slug': cat['slug']
                        })
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"カテゴリ階層取得エラー: {e}")
            return {}
    
    def cleanup_unused_categories(self) -> int:
        """使用されていないカテゴリを削除"""
        try:
            deleted_count = 0
            
            for slug, category in self.category_cache.items():
                # 投稿数が0のカテゴリを削除
                if category.get('count', 0) == 0:
                    if self.wp_client.delete_category(category['id']):
                        del self.category_cache[slug]
                        deleted_count += 1
                        logger.info(f"未使用カテゴリを削除: {category['name']}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"未使用カテゴリ削除エラー: {e}")
            return 0
    
    def cleanup_unused_tags(self) -> int:
        """使用されていないタグを削除"""
        try:
            deleted_count = 0
            
            for slug, tag in self.tag_cache.items():
                # 投稿数が0のタグを削除
                if tag.get('count', 0) == 0:
                    if self.wp_client.delete_tag(tag['id']):
                        del self.tag_cache[slug]
                        deleted_count += 1
                        logger.info(f"未使用タグを削除: {tag['name']}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"未使用タグ削除エラー: {e}")
            return 0
