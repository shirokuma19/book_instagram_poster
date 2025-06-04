#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
from googleapiclient.discovery import build
from PIL import Image
from dotenv import load_dotenv
import json
import urllib.parse
import click
from instagrapi import Client
from bs4 import BeautifulSoup
import io
import re

# 環境変数の読み込み
load_dotenv()

class BookPoster:
    def __init__(self):
        self.google_books_api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
        self.instagram_username = os.getenv('INSTAGRAM_USERNAME')
        self.instagram_password = os.getenv('INSTAGRAM_PASSWORD')
        self.service = build('books', 'v1', developerKey=self.google_books_api_key)
        self.cl = Client()
        self.cl.login(self.instagram_username, self.instagram_password)

    def modify_amazon_image_url(self, url):
        """Amazon画像URLを高解像度版に変更"""
        if not url:
            return None
        
        # URLから基本部分を抽出
        base_url = re.sub(r'\.[^.]+\.jpg', '', url)
        if not base_url:
            return url
            
        # SL1500.jpgを付加
        return f"{base_url}.SL1500.jpg"

    def get_amazon_image_url(self, title, author=None):
        """Amazonから書籍の画像URLを取得"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 著者名がある場合は検索クエリに追加
        search_query = f"{title}"
        if author:
            search_query += f" {author}"
            
        search_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(search_query)}&i=stripbooks"
        
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 商品画像を探す
            img_element = soup.select_one('img.s-image')
            if img_element and 'src' in img_element.attrs:
                # 画像URLを高解像度版に変更
                return self.modify_amazon_image_url(img_element['src'])
        except Exception as e:
            print(f"画像URL取得中にエラーが発生しました: {e}")
        
        return None

    def search_books(self, title):
        """Google Books APIで詳細検索を実行"""
        try:
            # 基本の検索クエリ
            request = self.service.volumes().list(
                q=title,
                langRestrict='ja',  # 日本語の書籍に限定
                maxResults=5,  # 最大5件の結果を取得
                orderBy='relevance',  # 関連性順にソート
                printType='BOOKS'  # 書籍のみを検索
            )
            response = request.execute()

            if 'items' not in response:
                return None

            # 検索結果を表示して選択させる
            print("\n検索結果:")
            for i, item in enumerate(response['items'], 1):
                book_info = item['volumeInfo']
                authors = ', '.join(book_info.get('authors', ['不明']))
                publisher = book_info.get('publisher', '不明')
                published_date = book_info.get('publishedDate', '不明')[:4] if book_info.get('publishedDate') else '不明'
                
                print(f"\n{i}. タイトル: {book_info.get('title', '不明')}")
                print(f"   著者: {authors}")
                print(f"   出版社: {publisher}")
                print(f"   出版年: {published_date}")

            # ユーザーに選択させる
            while True:
                choice = input("\n該当する書籍の番号を選択してください（該当なしの場合は0）: ")
                if choice.isdigit() and 0 <= int(choice) <= len(response['items']):
                    break
                print("無効な選択です。もう一度試してください。")

            choice = int(choice)
            if choice == 0:
                return None

            selected_book = response['items'][choice - 1]['volumeInfo']
            return selected_book

        except Exception as e:
            print(f"書籍検索中にエラーが発生しました: {e}")
            return None

    def get_book_info(self, title):
        # Google Books APIで検索
        book = self.search_books(title)
        
        if book:
            info = {
                'title': book.get('title', '不明'),
                'authors': ', '.join(book.get('authors', ['不明'])),
                'published_date': book.get('publishedDate', '不明')[:4] if book.get('publishedDate') else '不明',
                'publisher': book.get('publisher', '不明'),
                'categories': ', '.join(book.get('categories', ['不明']))
            }
        else:
            return self.manual_input()

        # 情報を手動で編集
        print("\n取得した情報を編集できます。Enter キーを押すと現在の値を保持します：")
        for key, value in info.items():
            new_value = input(f"{key} [{value}]: ").strip()
            if new_value:
                info[key] = new_value

        return info

    def manual_input(self):
        print("\n書籍情報を手動で入力してください:")
        info = {
            'title': input("タイトル: "),
            'authors': input("著者名: "),
            'published_date': input("出版年: "),
            'publisher': input("出版社: "),
            'categories': input("分類: ")
        }
        return info

    def download_and_save_image(self, image_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_url, headers=headers)
            if response.status_code != 200:
                print(f"高解像度画像の取得に失敗しました。ステータスコード: {response.status_code}")
                return None
                
            image = Image.open(io.BytesIO(response.content))
            
            # 画像のリサイズ（アスペクト比を保持）
            max_size = (1080, 1080)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 正方形のキャンバスを作成
            square_size = max(image.size)
            background = Image.new('RGB', (square_size, square_size), 'white')
            
            # 画像を中央に配置
            offset = ((square_size - image.size[0]) // 2, (square_size - image.size[1]) // 2)
            background.paste(image, offset)
            
            # 一時ファイルとして保存
            temp_image_path = 'temp_book_post.jpg'
            background.save(temp_image_path, quality=95)
            return temp_image_path
        except Exception as e:
            print(f"画像の処理中にエラーが発生しました: {e}")
            return None

    def post_to_instagram(self, image_path, book_info):
        try:
            caption = f"""
{book_info['title']}

著者: {book_info['authors']}
出版年: {book_info['published_date']}
出版社: {book_info['publisher']}
分類: {book_info['categories']}
"""
            # 投稿を実行
            media = self.cl.photo_upload(
                image_path,
                caption=caption
            )
            print("投稿が完了しました！")
            
        except Exception as e:
            print(f"投稿中にエラーが発生しました: {e}")

@click.group()
def cli():
    """書籍情報をInstagramに投稿するツール"""
    pass

@cli.command()
def post_book():
    """書籍情報を投稿します"""
    poster = BookPoster()
    
    title = click.prompt("\n本のタイトルを入力してください")
    book_info = poster.get_book_info(title)
    
    click.echo("\n最終的な書籍情報:")
    for key, value in book_info.items():
        click.echo(f"{key}: {value}")

    if click.confirm("\nこの情報でInstagramに投稿しますか？", default=True):
        # Amazonから画像を取得（著者名も含めて検索）
        amazon_image_url = poster.get_amazon_image_url(title, book_info['authors'])
        if not amazon_image_url:
            print("エラー: Amazonの画像を取得できませんでした。")
            return
        
        # 画像をダウンロードして保存
        image_path = poster.download_and_save_image(amazon_image_url)
        if image_path:
            poster.post_to_instagram(image_path, book_info)
            os.remove(image_path)
        else:
            print("エラー: 画像の処理に失敗しました。")

if __name__ == "__main__":
    cli()

