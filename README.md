# Book Instagram Bot

このプロジェクトは、本の情報をInstagramに投稿するボットです。

## 機能

- 本の情報を取得し、画像を生成
- Instagramへの自動投稿
- 定期的な投稿スケジューリング

## セットアップ

1. リポジトリのクローン:
```bash
git clone [your-repository-url]
cd book_instagram_temp
```

2. 仮想環境の作成と有効化:
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# または
.\venv\Scripts\activate  # Windows
```

3. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

4. 環境変数の設定:
`.env`ファイルを作成し、必要な環境変数を設定してください。

## 使用方法

1. 環境変数の設定を確認
2. スクリプトを実行:
```bash
python main.py
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。 