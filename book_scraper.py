#!/usr/bin/env python3
import requests
import os
import time
import json

def get_book_image(title, author=''):
    """
    OpenBD APIを使用して書籍の画像URLを取得する関数
    """
    # OpenBD APIのエンドポイント（書籍検索用）
    search_url = "https://api.openbd.jp/v1/search"
    
    # 検索パラメータの設定
    params = {
        'title': title,
        'author': author,
        'limit': 10
    }
    
    # ユーザーエージェントを設定
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # APIから書籍を検索
        search_response = requests.get(search_url, params=params)
        search_response.raise_for_status()
        
        # 検索結果をパース
        search_data = search_response.json()
        
        if search_data and len(search_data) > 0:
            # 最初の検索結果のISBNを取得
            isbn = search_data[0].get('isbn')
            if not isbn:
                print(f"ISBNが見つかりませんでした: {title}")
                return None, None
            
            # 書籍詳細を取得
            detail_url = f"https://api.openbd.jp/v1/get/{isbn}"
            detail_response = requests.get(detail_url)
            detail_response.raise_for_status()
            
            # JSONをパース
            data = detail_response.json()
            
            if data and data[0]:
                # 書影のURLを取得
                img_url = data[0].get('summary', {}).get('cover')
                if img_url:
                    # 画像をダウンロード
                    img_response = requests.get(img_url, headers=headers)
                    img_response.raise_for_status()
                    
                    # 一時ディレクトリを作成
                    os.makedirs('temp_images', exist_ok=True)
                    
                    # 画像を保存
                    image_path = os.path.join('temp_images', f'book_image_{int(time.time())}.jpg')
                    with open(image_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"OpenBD APIから画像を取得しました: {img_url}")
                    return image_path, img_response.headers.get('content-type', 'image/jpeg')
                else:
                    print(f"書影が見つかりませんでした: {title}")
        else:
            print(f"書籍が見つかりませんでした: {title}")
    
    except Exception as e:
        print(f"OpenBD APIからの画像取得に失敗しました: {e}")
    
    print(f"代替の画像取得方法を試みます: {title}")
    # Amazon APIや他の方法での画像取得を試みる
    return None, None

if __name__ == '__main__':
    # テスト用
    title = input("書籍のタイトルを入力してください: ")
    author = input("著者名を入力してください（省略可）: ")
    
    image_path, content_type = get_book_image(title, author)
    if image_path:
        print(f"画像を保存しました: {image_path}")
        # macOSの場合、プレビューで画像を表示
        if os.uname().sysname == "Darwin":
            os.system(f"open {image_path}")
    else:
        print("画像の取得に失敗しました。") 