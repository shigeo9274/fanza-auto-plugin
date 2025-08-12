from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import random
from scrape import get_sample_movie_url, generate_sample_movie_html


class Renderer:
    """テンプレートレンダリングと変数タグ置き換えを行うクラス"""
    
    def __init__(self):
        # ランダム値の生成用
        self.random_values = {
            'random1': str(random.randint(1000, 9999)),
            'random2': str(random.randint(10000, 99999)),
            'random3': str(random.randint(100000, 999999))
        }
    
    def replace_variables(self, template_content: str, item: Dict[str, Any]) -> str:
        """テンプレート内の変数を置き換える（PHPのTemplateEngine::renderInline相当）"""
        if not template_content:
            return ""
        
        content = template_content
        
        # 基本的な変数置き換え
        variables = {
            '[title]': item.get('title', ''),
            '[aff-link]': item.get('affiliateURL', ''),
            '[cid]': item.get('content_id', ''),
            '[content-id]': item.get('content_id', ''),
            '[url]': item.get('URL', ''),
            '[comment]': item.get('comment', ''),
            '[user-comment]': item.get('comment', ''),
            '[price]': item.get('price', ''),
            '[review]': item.get('review', ''),
            '[date]': item.get('date', ''),
            '[actress]': self._get_actress_string(item),
            '[performer]': self._get_performer_string(item),
            '[maker]': self._get_maker_string(item),
            '[label]': self._get_label_string(item),
            '[publisher]': self._get_manufacture_string(item),
            '[manufacture]': self._get_manufacture_string(item),
            '[director]': self._get_director_string(item),
            '[series]': self._get_series_string(item),
            '[author]': self._get_author_string(item),
            '[genre]': self._get_genre_string(item),
            '[volume]': item.get('volume', ''),
            '[random1]': self.random_values['random1'],
            '[random2]': self.random_values['random2'],
            '[random3]': self.random_values['random3'],
            '[review-count]': str(item.get('review_count', '')),
            '[review-average]': str(item.get('review_average', '')),
        }
        
        # 変数を置き換え
        for key, value in variables.items():
            content = content.replace(key, str(value))
        
        return content
    
    def _get_image_url(self, item: Dict[str, Any], key: str) -> str:
        """画像URLを取得（PHPプラグインのデータ構造に合わせて修正）"""
        print(f"_get_image_url: key={key}, item keys={list(item.keys())}")
        
        if key == 'imageURL':
            # パッケージ画像の場合
            image_data = item.get('imageURL', {})
            print(f"_get_image_url: imageURL data={image_data}, type={type(image_data)}")
            
            if isinstance(image_data, dict):
                # PHPプラグインでは imageURL->large を使用
                large_url = image_data.get('large', '')
                if large_url:
                    print(f"_get_image_url: found large URL: {large_url}")
                    return large_url
                
                # largeがない場合は最初の有効なURLを使用
                for size_key, url in image_data.items():
                    if url and isinstance(url, str):
                        print(f"_get_image_url: using {size_key} URL: {url}")
                        return url
            elif isinstance(image_data, str):
                print(f"_get_image_url: returning string image_data: {image_data}")
                return image_data
        
        print(f"_get_image_url: no valid image found, returning empty string")
        return ''
    
    def generate_package_image(self, item: Dict[str, Any], affiliate_url: str, title: str = '', width: str = '', height: str = '') -> str:
        """パッケージ画像HTMLを生成（PHPプラグインのデータ構造に合わせて修正）"""
        print(f"generate_package_image: item keys={list(item.keys())}")
        image_url = self._get_image_url(item, 'imageURL')
        print(f"generate_package_image: image_url={image_url}")
        if not image_url:
            print("generate_package_image: no image_url found, returning empty string")
            return ''
        
        width_attr = f' width="{width}"' if width else ''
        height_attr = f' height="{height}"' if height else ''
        
        html = f'''<div class="package-image-container">
<a href="{affiliate_url}" target="_blank" rel="noreferrer noopener">
<img src="{image_url}" alt="{title}" class="package-image" style="max-width: 100%; height: auto;"{width_attr}{height_attr} />
</a>
</div>'''
        print(f"generate_package_image: generated HTML: {html}")
        return html
    
    def generate_sample_images(self, item: Dict[str, Any], title: str = '', max_images: int = 10, show_caption: bool = True, show_link: bool = True, size: str = 'normal') -> str:
        """サンプル画像HTMLを生成（PHPプラグインのデータ構造に合わせて修正）"""
        print(f"generate_sample_images: item keys={list(item.keys())}")
        sample_images = item.get('sampleImageURL', {})
        print(f"generate_sample_images: sampleImageURL data={sample_images}, type={type(sample_images)}")
        
        if not sample_images:
            print("generate_sample_images: no sampleImageURL found, returning empty string")
            return ''
        
        # PHPプラグインのデータ構造に合わせて処理
        img_urls = []
        
        if isinstance(sample_images, dict):
            # sample_l（大きな画像）を優先
            if 'sample_l' in sample_images and sample_images['sample_l']:
                large_images = sample_images['sample_l']
                if isinstance(large_images, dict) and 'image' in large_images:
                    large_img_array = large_images['image']
                    if isinstance(large_img_array, list):
                        img_urls.extend([url for url in large_img_array if url])
                        print(f"generate_sample_images: added large images: {img_urls}")
            
            # sample_lがない場合はsample_s（小さな画像）を使用
            if not img_urls and 'sample_s' in sample_images and sample_images['sample_s']:
                small_images = sample_images['sample_s']
                if isinstance(small_images, dict) and 'image' in small_images:
                    small_img_array = small_images['image']
                    if isinstance(small_img_array, list):
                        img_urls.extend([url for url in small_img_array if url])
                        print(f"generate_sample_images: added small images: {img_urls}")
            
            # 直接imageキーがある場合
            if not img_urls and 'image' in sample_images:
                image_array = sample_images['image']
                if isinstance(image_array, list):
                    img_urls.extend([url for url in image_array if url])
                    print(f"generate_sample_images: added direct images: {img_urls}")
        
        if not img_urls:
            print("generate_sample_images: no img_urls found, returning empty string")
            return ''
        
        # 最大画像数に制限
        img_urls = img_urls[:max_images]
        print(f"generate_sample_images: final img_urls: {img_urls}")
        
        html = '<div class="sample-image-container">'
        for i, img_url in enumerate(img_urls):
            if img_url:
                caption = f' alt="{title} サンプル画像{i+1}"' if show_caption else ''
                link_start = f'<a href="{img_url}" target="_blank" rel="noreferrer noopener">' if show_link else ''
                link_end = '</a>' if show_link else ''
                
                html += f'{link_start}<img src="{img_url}"{caption} class="sample-image" style="max-width: 100%; height: auto;" />{link_end}'
        html += '</div>'
        print(f"generate_sample_images: generated HTML: {html}")
        return html
    
    def generate_detail_table(self, details: List[Dict[str, str]]) -> str:
        """詳細テーブルHTMLを生成（PHPのContentGenerator::generateDetailTable相当）"""
        if not details:
            return ''
        
        html = '''<figure class="wp-block-table detail-table">
<table class="detail-table">
<tbody>'''
        
        for detail in details:
            label = detail.get('label', '')
            value = detail.get('value', '')
            html += f'<tr><td><strong>{label}</strong></td><td>{value}</td></tr>'
        
        html += '</tbody></table></figure>'
        return html
    
    def generate_sample_movie(self, cid: str, affiliate_url: str, movie_size: str = '720_480') -> str:
        """サンプル動画HTMLを生成（PHPのContentGenerator::generateSampleMovie相当）"""
        if not cid:
            return ''
        
        # MP4ファイルの直接URLを取得
        mp4_url = get_sample_movie_url({'content_id': cid})
        if not mp4_url:
            return ''
        
        # パッケージ画像をポスターとして使用
        poster_url = ""
        
        # MP4直接再生のHTMLを生成
        return generate_sample_movie_html(mp4_url, poster_url, cid)
    
    def generate_button(self, button_number: int, affiliate_url: str, button_text: str, text_color: str = '#ffffff', bg_color: str = '#007cba') -> str:
        """ボタンHTMLを生成（PHPのContentGenerator::generateButton相当）"""
        if not affiliate_url or not button_text:
            return ''
        
        return f'''<div class="button-container">
<a href="{affiliate_url}" target="_blank" rel="noreferrer noopener" style="display: inline-block; padding: 10px 20px; background-color: {bg_color}; color: {text_color}; text-decoration: none; border-radius: 5px; font-weight: bold;">
{button_text}
</a>
</div>'''
    
    def generate_api_mark(self, site: str = 'FANZA') -> str:
        """APIマークHTMLを生成（PHPのContentGenerator::generateApiMark相当）"""
        return f'''<p class="api-mark-container" style="margin: 20px 0; font-size: 12px; color: #666;">
このコンテンツは<a href="https://www.dmm.co.jp/digital/videoa/-/list/=/article=api/" target="_blank" rel="noreferrer noopener">{site} API</a>を使用して自動生成されています。
<img src="https://www.dmm.co.jp/digital/videoa/-/list/=/article=api/" alt="API" style="border: none;" />
</p>'''
    
    def generate_post_content(self, item: Dict[str, Any], template_content: str = '', affiliate_url: str = '', movie_size: str = 'auto') -> str:
        """投稿コンテンツを生成（PHPのContentGenerator::generatePostContent相当）"""
        if not template_content:
            # デフォルトテンプレートを使用
            template_content = self._get_default_template()
        
        # 基本的な変数置き換え
        content = self.replace_variables(template_content, item)
        
        # 特殊なタグの置き換え
        content = self._replace_special_tags(content, item, affiliate_url, movie_size)
        
        return content
    
    def _replace_special_tags(self, content: str, item: Dict[str, Any], affiliate_url: str, movie_size: str) -> str:
        """特殊なタグを置き換え"""
        # [package-image]タグの置き換え
        if '[package-image]' in content:
            package_image = self.generate_package_image(item, affiliate_url, item.get('title', ''))
            content = content.replace('[package-image]', package_image)
        
        # [sample-images]タグの置き換え
        if '[sample-images]' in content:
            sample_images = self.generate_sample_images(item, item.get('title', ''))
            content = content.replace('[sample-images]', sample_images)
        
        # [sample-photo]タグの置き換え（sample-imagesと同じ）
        if '[sample-photo]' in content:
            sample_images = self.generate_sample_images(item, item.get('title', ''))
            content = content.replace('[sample-photo]', sample_images)
        
        # [sample-movie]タグの置き換え
        if '[sample-movie]' in content:
            sample_movie = self.generate_sample_movie(item.get('content_id', ''), affiliate_url, movie_size)
            content = content.replace('[sample-movie]', sample_movie)
        
        # [sample-movie2]タグの置き換え（sample-movieと同じ）
        if '[sample-movie2]' in content:
            sample_movie = self.generate_sample_movie(item.get('content_id', ''), affiliate_url, movie_size)
            content = content.replace('[sample-movie2]', sample_movie)
        
        # [detail-table]タグの置き換え
        if '[detail-table]' in content:
            details = self._generate_detail_data(item)
            detail_table = self.generate_detail_table(details)
            content = content.replace('[detail-table]', detail_table)
        
        # [button]タグの置き換え
        if '[button]' in content:
            button = self.generate_button(1, affiliate_url, '詳細を見る')
            content = content.replace('[button]', button)
        
        # [api-mark]タグの置き換え
        if '[api-mark]' in content:
            api_mark = self.generate_api_mark()
            content = content.replace('[api-mark]', api_mark)
        
        # [user_reviews]タグの置き換え
        if '[user_reviews]' in content:
            user_reviews = self._generate_user_reviews(item)
            content = content.replace('[user_reviews]', user_reviews)
        
        return content
    
    def _generate_detail_data(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        """詳細データを生成"""
        details = []
        
        if item.get('title'):
            details.append({'label': 'タイトル', 'value': item['title']})
        
        if item.get('content_id'):
            details.append({'label': 'コンテンツID', 'value': item['content_id']})
        
        if item.get('price'):
            details.append({'label': '価格', 'value': item['price']})
        
        if item.get('date'):
            details.append({'label': '発売日', 'value': item['date']})
        
        actresses = self._get_actress_string(item)
        if actresses:
            details.append({'label': '出演者', 'value': actresses})
        
        makers = self._get_maker_string(item)
        if makers:
            details.append({'label': 'メーカー', 'value': makers})
        
        labels = self._get_label_string(item)
        if labels:
            details.append({'label': 'レーベル', 'value': labels})
        
        directors = self._get_director_string(item)
        if directors:
            details.append({'label': '監督', 'value': directors})
        
        series = self._get_series_string(item)
        if series:
            details.append({'label': 'シリーズ', 'value': series})
        
        genres = self._get_genre_string(item)
        if genres:
            details.append({'label': 'ジャンル', 'value': genres})
        
        return details
    
    def _get_default_template(self) -> str:
        """デフォルトテンプレートを取得"""
        return '''<!-- wp:group {"className":"fanza-post-content"} -->
<div class="wp-block-group fanza-post-content">

[package-image]

<h2>[title]の詳細情報</h2>

[detail-table]

<p>[comment]</p>

[sample-images]

[sample-movie]

[button]

[api-mark]

</div>
<!-- /wp:group -->'''

    def _get_actress_string(self, item: Dict[str, Any]) -> str:
        """女優名の文字列を取得"""
        actresses = item.get('actress', [])
        if not actresses:
            return ''
        return ' '.join([act.get('name', '') for act in actresses])
    
    def _get_performer_string(self, item: Dict[str, Any]) -> str:
        """出演者名の文字列を取得"""
        performers = item.get('performer', [])
        if not performers:
            return ''
        return ' '.join([perf.get('name', '') for perf in performers])
    
    def _get_maker_string(self, item: Dict[str, Any]) -> str:
        """メーカー名の文字列を取得"""
        makers = item.get('maker', [])
        if not makers:
            return ''
        return ' '.join([maker.get('name', '') for maker in makers])
    
    def _get_label_string(self, item: Dict[str, Any]) -> str:
        """レーベル名の文字列を取得"""
        labels = item.get('label', [])
        if not labels:
            return ''
        return ' '.join([label.get('name', '') for label in labels])
    
    def _get_manufacture_string(self, item: Dict[str, Any]) -> str:
        """出版社名の文字列を取得"""
        manufactures = item.get('manufacture', [])
        if not manufactures:
            return ''
        return ' '.join([manuf.get('name', '') for manuf in manufactures])
    
    def _get_director_string(self, item: Dict[str, Any]) -> str:
        """監督名の文字列を取得"""
        directors = item.get('director', [])
        if not directors:
            return ''
        return ' '.join([director.get('name', '') for director in directors])
    
    def _get_series_string(self, item: Dict[str, Any]) -> str:
        """シリーズ名の文字列を取得"""
        series = item.get('series', [])
        if not series:
            return ''
        return ' '.join([ser.get('name', '') for ser in series])
    
    def _get_author_string(self, item: Dict[str, Any]) -> str:
        """作者名の文字列を取得"""
        authors = item.get('author', [])
        if not authors:
            return ''
        return ' '.join([a.get('name', '') for a in authors])
    
    def _get_genre_string(self, item: Dict[str, Any]) -> str:
        """ジャンル名の文字列を取得"""
        genres = item.get('genre', [])
        if not genres:
            return ''
        return ' '.join([g.get('name', '') for g in genres])
    
    def _generate_user_reviews(self, item: Dict[str, Any]) -> str:
        """ユーザーレビューのHTMLを生成（PHPプラグインと同様に、レビューがない場合は空文字を返す）"""
        review_average = item.get('review_average', 0)
        review_count = item.get('review_count', 0)
        
        # レビューがない場合は空文字を返す
        if not review_average or review_average == '-' or review_average == 0:
            return ''
        
        html = '<div class="user-reviews">'
        
        if review_average:
            stars = self._generate_stars_html(review_average)
            html += f'<div class="review-rating">評価: {stars} {review_average}</div>'
        
        if review_count:
            html += f'<div class="review-count">レビュー数: {review_count}件</div>'
        
        html += '</div>'
        return html
    
    def _generate_stars_html(self, rating: float) -> str:
        """星評価のHTMLを生成"""
        full_stars = int(rating)
        has_half_star = rating % 1 >= 0.5
        
        html = ''
        for i in range(5):
            if i < full_stars:
                html += '★'
            elif i == full_stars and has_half_star:
                html += '☆'
            else:
                html += '☆'
        
        return html
    
    def render_template(self, template_content: str, item: Dict[str, Any], 
                       affiliate_url: str = "", movie_size: str = "auto") -> str:
        """テンプレートをレンダリングして投稿内容を生成（PHPのContentGenerator::generatePostContent相当）"""
        # 変数タグを置換
        content = template_content
        
        # 基本情報の置換
        content = content.replace('[title]', item.get('title', ''))
        content = content.replace('[cid]', item.get('content_id', ''))
        content = content.replace('[aff-link]', affiliate_url)
        content = content.replace('[comment]', item.get('comment', ''))
        content = content.replace('[user-comment]', item.get('comment', ''))
        
        # 詳細情報の置換
        content = content.replace('[detail-content-ul]', self.generate_detail_content_ul(item))
        content = content.replace('[detail-content-table]', self.generate_detail_content_table(item))
        content = content.replace('[detail-list]', self.generate_detail_content_ul(item))
        content = content.replace('[detail-table]', self.generate_detail_content_table(item))
        
        # 画像・動画の置換
        content = content.replace('[package-image]', self.generate_package_image(item, affiliate_url))
        content = content.replace('[package]', self.generate_package_image(item, affiliate_url))
        content = content.replace('[sample-movie]', self.generate_sample_movie(item.get('content_id', ''), affiliate_url, movie_size))
        content = content.replace('[sample-movie2]', self.generate_sample_movie(item.get('content_id', ''), affiliate_url, movie_size))
        content = content.replace('[sample-images]', self.generate_sample_images(item))
        content = content.replace('[sample-photo]', self.generate_sample_images(item))
        content = content.replace('[sample-cap]', self.generate_sample_images(item, show_caption=True))
        content = content.replace('[sample-flex]', self.generate_sample_images(item))
        
        # アフィリエイトボタンの置換
        content = content.replace('[affiliate-button]', 
                                self.generate_button(1, affiliate_url, "詳細を見る"))
        content = content.replace('[aff-button]', 
                                self.generate_button(1, affiliate_url, "詳細を見る"))
        content = content.replace('[aff-button2]', 
                                self.generate_button(1, affiliate_url, "詳細を見る"))
        
        # APIマークの置換
        content = content.replace('[api-mark]', self.generate_api_mark("FANZA"))
        
        # ユーザーレビューの置換
        content = content.replace('[user_reviews]', self._generate_user_reviews(item))
        
        # その他の変数タグの置換
        content = content.replace('[content_id]', item.get('content_id', ''))
        content = content.replace('[jancode]', item.get('jancode', ''))
        content = content.replace('[volume]', item.get('volume', ''))
        content = content.replace('[date]', item.get('date', '')[:10] if item.get('date') else '')
        
        # シリーズ情報
        series = item.get('series', [])
        if series:
            series_names = [s.get('name', '') for s in series if s.get('name')]
            content = content.replace('[series]', ' '.join(series_names))
        else:
            content = content.replace('[series]', '')
        
        # 作者情報
        author = item.get('author', [])
        if author:
            author_names = [a.get('name', '') for a in author if a.get('name')]
            content = content.replace('[author]', ' '.join(author_names))
        else:
            content = content.replace('[author]', '')
        
        # ジャンル情報
        genres = item.get('genre', [])
        if genres:
            genre_names = [g.get('name', '') for g in genres if g.get('name')]
            content = content.replace('[genre]', ' '.join(genre_names))
        else:
            content = content.replace('[genre]', '')
        
        # 出演者情報
        actresses = item.get('actress', [])
        if actresses:
            actress_names = [a.get('name', '') for a in actresses if a.get('name')]
            content = content.replace('[actress]', ' '.join(actress_names))
        else:
            content = content.replace('[actress]', '')
        
        # 価格情報
        if item.get('prices', {}).get('list_price'):
            content = content.replace('[price]', f'￥{item["prices"]["list_price"]}')
        else:
            content = content.replace('[price]', '')
        
        # ランダム値の置換
        content = content.replace('[random1]', self.random_values['random1'])
        content = content.replace('[random2]', self.random_values['random2'])
        content = content.replace('[random3]', self.random_values['random3'])
        
        # レビュー情報の置換
        review_average = item.get('review_average', 0)
        review_count = item.get('review_count', 0)
        if review_average:
            content = content.replace('[review-average]', str(review_average))
        else:
            content = content.replace('[review-average]', '')
        if review_count:
            content = content.replace('[review-count]', str(review_count))
        else:
            content = content.replace('[review-count]', '')
        
        return content
    
    def generate_detail_content_ul(self, item: Dict[str, Any]) -> str:
        """詳細情報のリスト形式HTMLを生成（WordPressブロックエディタ形式）"""
        html = '<!-- wp:list -->\n<ul>'
        
        # レビュー情報
        if item.get('review_average') or item.get('review_count'):
            review_html = self._generate_review_html(item)
            if review_html:
                html += f'<li>レビュー : {review_html}</li>'
        
        # 発売日
        if item.get('date'):
            date_str = item['date'][:10] if len(item['date']) >= 10 else item['date']
            html += f'<li>発売日 : {date_str}</li>'
        
        # 収録時間/ページ数
        volume = item.get('volume', '')
        if volume:
            service = item.get('service', '')
            if service == 'ebook':
                volume += 'ページ'
            elif service == 'doujin':
                if not any(word in volume for word in ['動画', '画像', '+α', '本', '分']):
                    volume += 'ページ'
            else:
                if ':' not in volume:
                    volume += '分'
            html += f'<li>収録 : {volume}</li>'
        
        # シリーズ
        series = item.get('series', [])
        if series:
            series_names = [s.get('name', '') for s in series if s.get('name')]
            if series_names:
                html += f'<li>シリーズ : {" ".join(series_names)}</li>'
        
        # 作者
        author = item.get('author', [])
        if author:
            author_names = [a.get('name', '') for a in author if a.get('name')]
            if author_names:
                html += f'<li>作者 : {" ".join(author_names)}</li>'
        
        # ジャンル
        genres = item.get('genre', [])
        if genres:
            genre_names = [g.get('name', '') for g in genres if g.get('name')]
            if genre_names:
                html += f'<li>ジャンル : {" ".join(genre_names)}</li>'
        
        # 出演者
        actresses = item.get('actress', [])
        if actresses:
            actress_names = [a.get('name', '') for a in actresses if a.get('name')]
            if actress_names:
                html += f'<li>女優 : {" ".join(actress_names)}</li>'
        
        # 品番
        if item.get('content_id'):
            html += f'<li>品番 : {item["content_id"]}</li>'
        
        # JANコード
        if item.get('jancode'):
            html += f'<li>JANコード : {item["jancode"]}</li>'
        
        # 価格
        if item.get('prices', {}).get('list_price'):
            html += f'<li>価格 : ￥{item["prices"]["list_price"]}</li>'
        
        html += '</ul><!-- /wp:list -->\n'
        return html
    
    def generate_detail_content_table(self, item: Dict[str, Any]) -> str:
        """詳細情報のテーブル形式HTMLを生成（WordPressブロックエディタ形式）"""
        html = '<!-- wp:table -->\n<figure class="wp-block-table"><table><tbody>'
        
        # レビュー情報
        if item.get('review_average') or item.get('review_count'):
            review_html = self._generate_review_html(item)
            if review_html:
                html += f'<tr><th>レビュー</th><td>{review_html}</td></tr>'
        
        # 発売日
        if item.get('date'):
            date_str = item['date'][:10] if len(item['date']) >= 10 else item['date']
            html += f'<tr><th>発売日</th><td>{date_str}</td></tr>'
        
        # 収録時間/ページ数
        volume = item.get('volume', '')
        if volume:
            service = item.get('service', '')
            if service == 'ebook':
                volume += 'ページ'
            elif service == 'doujin':
                if not any(word in volume for word in ['動画', '画像', '+α', '本', '分']):
                    volume += 'ページ'
            else:
                if ':' not in volume:
                    volume += '分'
            html += f'<tr><th>収録</th><td>{volume}</td></tr>'
        
        # シリーズ
        series = item.get('series', [])
        if series:
            series_names = [s.get('name', '') for s in series if s.get('name')]
            if series_names:
                html += f'<tr><th>シリーズ</th><td>{" ".join(series_names)}</td></tr>'
        
        # 作者
        author = item.get('author', [])
        if author:
            author_names = [a.get('name', '') for a in author if a.get('name')]
            if author_names:
                html += f'<tr><th>作者</th><td>{" ".join(author_names)}</td></tr>'
        
        # ジャンル
        genres = item.get('genre', [])
        if genres:
            genre_names = [g.get('name', '') for g in genres if g.get('name')]
            if genre_names:
                html += f'<tr><th>ジャンル</th><td>{" ".join(genre_names)}</td></tr>'
        
        # 出演者
        actresses = item.get('actress', [])
        if actresses:
            actress_names = [a.get('name', '') for a in actresses if a.get('name')]
            if actress_names:
                html += f'<tr><th>女優</th><td>{" ".join(actress_names)}</td></tr>'
        
        # 品番
        if item.get('content_id'):
            html += f'<tr><th>品番</th><td>{item["content_id"]}</td></tr>'
        
        # JANコード
        if item.get('jancode'):
            html += f'<tr><th>JANコード</th><td>{item["jancode"]}</td></tr>'
        
        # 価格
        if item.get('prices', {}).get('list_price'):
            html += f'<tr><th>価格</th><td>￥{item["prices"]["list_price"]}</td></tr>'
        
        html += '</tbody></table></figure>\n<!-- /wp:table -->\n'
        return html
    
    def _generate_review_html(self, item: Dict[str, Any]) -> str:
        """レビュー情報のHTMLを生成（PHPプラグインと同様に、レビューがない場合は空文字を返す）"""
        review_average = item.get('review_average', 0)
        review_count = item.get('review_count', 0)
        
        # レビューがない場合は空文字を返す（PHPプラグインのreview_html2と同様）
        if not review_average or review_average == '-' or review_average == 0:
            return ''
        
        html_parts = []
        
        if review_average:
            # 星評価を生成
            stars = self._generate_stars_html(review_average)
            html_parts.append(f'{stars} {review_average}')
        
        if review_count:
            html_parts.append(f'{review_count}件')
        
        return ' / '.join(html_parts)

    def _extract_affiliate_id(self, affiliate_url: str) -> str:
        """アフィリエイトURLからIDを抽出"""
        if not affiliate_url:
            return ''
        
        # URLからアフィリエイトIDを抽出する処理
        # 例: https://al.dmm.co.jp/?lurl=...&af_id=rimobai-996&ch=api/ から rimobai-996 を抽出
        import re
        match = re.search(r'af_id=([^&]+)', affiliate_url)
        if match:
            return match.group(1)
        
        # 直接IDが含まれている場合
        if 'rimobai-' in affiliate_url:
            match = re.search(r'rimobai-\d+', affiliate_url)
            if match:
                return match.group(0)
        
        return ''

