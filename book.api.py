#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from datetime import datetime
import requests
import os
from PIL import Image
from io import BytesIO
import json
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

@dataclass
class BookInfo:
    """書籍情報を管理するデータクラス"""
    title: str
    author: str
    publication_year: str = "不明"
    publisher: str = "不明"
    category: str = "その他"
    google_books_id: Optional[str] = None
    openlibrary_id: Optional[str] = None
    amazon_asin: Optional[str] = None
    image_url: Optional[str] = None
    purchase_date: Optional[datetime] = None
    read_status: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "author": self.author,
            "publication_year": self.publication_year,
            "publisher": self.publisher,
            "category": self.category,
            "google_books_id": self.google_books_id,
            "openlibrary_id": self.openlibrary_id,
            "amazon_asin": self.amazon_asin,
            "image_url": self.image_url,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "read_status": self.read_status,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BookInfo':
        """辞書形式からインスタンスを作成"""
        if "purchase_date" in data and data["purchase_date"]:
            data["purchase_date"] = datetime.fromisoformat(data["purchase_date"])
        return cls(**data)
    
    def __str__(self) -> str:
        """文字列表現"""
        status = "読了" if self.read_status else "未読"
        return f"{self.title} by {self.author} ({self.publication_year}, {self.publisher}) - {status}"

    def fetch_book_info(self) -> bool:
        """Google BooksとOpenLibrary APIから書籍情報を取得して更新"""
        # まずGoogle Books APIを試す
        if self._fetch_from_google_books():
            return True
        
        # Google Booksで見つからない場合はOpenLibraryを試す
        if self._fetch_from_openlibrary():
            return True
        
        return False

    def _fetch_from_google_books(self) -> bool:
        """Google Books APIから書籍情報を取得"""
        try:
            # 検索クエリの作成（タイトルのみで検索）
            query = f'intitle:"{self.title}"'
            if self.author:  # 著者名が指定されている場合は追加（オプション）
                query += f' inauthor:"{self.author}"'
            
            # 日本語の書籍を優先的に検索
            url = f"https://www.googleapis.com/books/v1/volumes?q={quote(query)}&langRestrict=ja&maxResults=10&orderBy=relevance"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    # 最も関連性の高い結果を選択
                    best_match = None
                    highest_score = -1

                    for item in data["items"]:
                        book = item["volumeInfo"]
                        # 関連性スコアを計算
                        score = self._calculate_relevance_score(book)
                        if score > highest_score:
                            highest_score = score
                            best_match = item

                    if best_match:
                        book = best_match["volumeInfo"]
                        self.google_books_id = best_match["id"]
                        
                        # 情報を更新
                        if "publisher" in book and book["publisher"]:
                            self.publisher = book["publisher"]
                        
                        if "publishedDate" in book and book["publishedDate"]:
                            self.publication_year = book["publishedDate"][:4]
                        
                        if "categories" in book and book["categories"]:
                            self.category = book["categories"][0]

                        if "authors" in book and book["authors"]:
                            self.author = ", ".join(book["authors"])
                        
                        if "imageLinks" in book:
                            # 高解像度の画像URLを取得
                            self.image_url = book["imageLinks"].get("thumbnail", "").replace("zoom=1", "zoom=2")
                            # HTTPSに変換
                            self.image_url = self.image_url.replace("http://", "https://")
                        
                        return True
            
            return False
            
        except Exception as e:
            print(f"Google Books APIでの検索に失敗: {e}")
            return False

    def _calculate_relevance_score(self, book: Dict) -> float:
        """書籍の関連性スコアを計算"""
        score = 0.0
        
        # タイトルの一致度をチェック
        if "title" in book:
            title_lower = book["title"].lower()
            search_title_lower = self.title.lower()
            if title_lower == search_title_lower:
                score += 10.0
            elif search_title_lower in title_lower or title_lower in search_title_lower:
                score += 5.0

        # 著者名が指定されている場合、著者の一致度をチェック
        if self.author and "authors" in book:
            author_lower = [a.lower() for a in book["authors"]]
            search_author_lower = self.author.lower()
            if any(search_author_lower in a or a in search_author_lower for a in author_lower):
                score += 3.0

        # 日本語の書籍を優先
        if "language" in book and book["language"] == "ja":
            score += 2.0

        # 画像がある書籍を優先
        if "imageLinks" in book:
            score += 1.0

        return score

    def _fetch_from_openlibrary(self) -> bool:
        """OpenLibrary APIから書籍情報を取得"""
        try:
            # 検索クエリの作成（タイトルのみで検索）
            query = f'title:"{self.title}"'
            if self.author:  # 著者名が指定されている場合は追加（オプション）
                query += f' author:"{self.author}"'
            
            url = f"https://openlibrary.org/search.json?q={quote(query)}&lang=jpn&limit=10"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if "docs" in data and len(data["docs"]) > 0:
                    # 最も関連性の高い結果を選択
                    best_match = None
                    highest_score = -1

                    for doc in data["docs"]:
                        score = self._calculate_openlibrary_relevance_score(doc)
                        if score > highest_score:
                            highest_score = score
                            best_match = doc

                    if best_match:
                        self.openlibrary_id = best_match.get("key")
                        
                        # 情報を更新
                        if "publisher" in best_match and best_match["publisher"]:
                            self.publisher = best_match["publisher"][0]
                        
                        if "first_publish_year" in best_match:
                            self.publication_year = str(best_match["first_publish_year"])
                        
                        if "subject" in best_match and best_match["subject"]:
                            self.category = best_match["subject"][0]

                        if "author_name" in best_match and best_match["author_name"]:
                            self.author = ", ".join(best_match["author_name"])
                        
                        # 画像URLの取得
                        if "cover_i" in best_match:
                            self.image_url = f"https://covers.openlibrary.org/b/id/{best_match['cover_i']}-L.jpg"
                        
                        return True
            
            return False
            
        except Exception as e:
            print(f"OpenLibrary APIでの検索に失敗: {e}")
            return False

    def _calculate_openlibrary_relevance_score(self, doc: Dict) -> float:
        """OpenLibrary検索結果の関連性スコアを計算"""
        score = 0.0
        
        # タイトルの一致度をチェック
        if "title" in doc:
            title_lower = doc["title"].lower()
            search_title_lower = self.title.lower()
            if title_lower == search_title_lower:
                score += 10.0
            elif search_title_lower in title_lower or title_lower in search_title_lower:
                score += 5.0

        # 著者名が指定されている場合、著者の一致度をチェック
        if self.author and "author_name" in doc:
            author_lower = [a.lower() for a in doc["author_name"]]
            search_author_lower = self.author.lower()
            if any(search_author_lower in a or a in search_author_lower for a in author_lower):
                score += 3.0

        # 日本語の書籍を優先
        if "language" in doc and "jpn" in doc["language"]:
            score += 2.0

        # 画像がある書籍を優先
        if "cover_i" in doc:
            score += 1.0

        return score

    def get_book_image(self) -> Tuple[Optional[bytes], Optional[str]]:
        """書籍の画像データを取得"""
        # まずAmazonから画像を取得を試みる
        amazon_image = self._get_amazon_image()
        if amazon_image:
            return amazon_image

        # Amazonで失敗した場合は他のAPIを試す
        if not self.image_url:
            if not self.fetch_book_info():
                return None, None
        
        if self.image_url:
            try:
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    return response.content, response.headers.get('content-type', 'image/jpeg')
            except Exception as e:
                print(f"画像の取得に失敗しました: {e}")
        
        return None, None

    def _get_amazon_image(self) -> Tuple[Optional[bytes], Optional[str]]:
        """Amazonから書籍の画像を取得"""
        try:
            # 検索クエリの作成
            search_query = f"{self.title}"
            if self.author:
                search_query += f" {self.author}"
            search_query += " 本"
            
            # Amazonの検索URL
            search_url = f"https://www.amazon.co.jp/s?k={requests.utils.quote(search_query)}&i=stripbooks"
            
            # ヘッダーを設定
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # 検索結果ページを取得
            search_response = requests.get(search_url, headers=headers)
            search_response.raise_for_status()
            
            # BeautifulSoupでパース
            search_soup = BeautifulSoup(search_response.text, 'html.parser')
            
            # 検索結果から最初の書籍のURLを取得
            product_link = search_soup.find('a', {'class': 's-link-style'})
            if not product_link:
                print(f"書籍が見つかりませんでした: {self.title}")
                return None, None
            
            # 商品ページのURLを取得してASINを抽出
            product_url = product_link['href']
            asin_match = re.search(r'/dp/([A-Z0-9]{10})(?:[/?]|$)', product_url)
            if asin_match:
                self.amazon_asin = asin_match.group(1)
            
            # 商品ページを取得
            amazon_url = f"https://www.amazon.co.jp/dp/{self.amazon_asin}" if self.amazon_asin else urljoin('https://www.amazon.co.jp', product_url)
            response = requests.get(amazon_url, headers=headers)
            response.raise_for_status()
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 画像URLを探す（複数の方法を試す）
            img_url = None
            
            # 方法1: メイン商品画像を探す
            main_image = soup.find('img', id='imgBlkFront')
            if main_image and 'src' in main_image.attrs:
                img_url = main_image['src']
            
            # 方法2: data-old-hires属性を持つ画像を探す
            if not img_url:
                image_div = soup.find('div', id='img-canvas')
                if image_div:
                    img = image_div.find('img', attrs={'data-old-hires': True})
                    if img:
                        img_url = img['data-old-hires']
            
            # 方法3: data-a-dynamic-image属性から高解像度画像を探す
            if not img_url:
                images = soup.find_all('img', attrs={'data-a-dynamic-image': True})
                for img in images:
                    data = img['data-a-dynamic-image']
                    if 'books' in data.lower() or 'images' in data.lower():
                        # JSON文字列から最大解像度の画像URLを抽出
                        urls = re.findall(r'\"(https://[^\"]+)\"', data)
                        if urls:
                            img_url = urls[0]
                            break
            
            if img_url:
                # 相対URLを絶対URLに変換
                img_url = urljoin(amazon_url, img_url)
                
                # URLを高解像度版に変換（SL1500_.jpg）
                img_url = re.sub(r'\._.*?_\.jpg', '._SL1500_.jpg', img_url)
                if not img_url.endswith('._SL1500_.jpg'):
                    base_url = img_url.split('?')[0]  # クエリパラメータを除去
                    if base_url.endswith('.jpg'):
                        img_url = base_url.rsplit('.jpg', 1)[0] + '._SL1500_.jpg'
                
                # 画像をダウンロード
                img_response = requests.get(img_url, headers=headers)
                img_response.raise_for_status()
                
                print(f"Amazonから画像を取得しました: {img_url}")
                return img_response.content, img_response.headers.get('content-type', 'image/jpeg')
            
            print(f"画像URLが見つかりませんでした: {self.title}")
            return None, None
            
        except Exception as e:
            print(f"Amazonからの画像取得に失敗しました: {e}")
            return None, None

    def save_image_for_instagram(self, image_data: bytes, content_type: str) -> str:
        """Instagramに投稿するための画像を保存"""
        # 一時ディレクトリの作成
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 画像の保存先ファイル名を設定
        temp_filename = os.path.join(temp_dir, f"book_image_{int(datetime.now().timestamp())}.jpg")
        
        # 画像をPILで開く
        img = Image.open(BytesIO(image_data))
        
        # RGBAの場合はRGBに変換
        if img.mode == 'RGBA':
            # 白背景を作成
            background = Image.new('RGB', img.size, 'white')
            # アルファチャンネルを考慮して合成
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Instagram要件に合わせてサイズ調整
        target_width = 1440  # Instagram推奨サイズ
        target_height = int(1440 * (5/4))  # 4:5のアスペクト比
        
        # 白背景の画像を作成
        new_img = Image.new("RGB", (target_width, target_height), "white")
        
        # 元画像のアスペクト比を保持しながら、新しいサイズに合わせてリサイズ
        aspect = img.height / img.width
        if aspect > (5/4):  # 元画像が4:5より縦長の場合
            new_height = target_height
            new_width = int(target_height / aspect)
        else:  # 元画像が4:5より横長の場合
            new_width = target_width
            new_height = int(target_width * aspect)
        
        # 高品質なリサイズ処理
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 画像を中央に配置
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        
        # 画像を貼り付け
        new_img.paste(img, (x, y))
        
        # 画像を保存（高品質設定）
        new_img.save(
            temp_filename,
            "JPEG",
            quality=95,  # 高品質設定
            optimize=True  # ファイルサイズの最適化
        )
        
        return temp_filename
