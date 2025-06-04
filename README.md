# Book Instagram Bot

本の情報を自動でInstagramに投稿するボットアプリケーションです。

## 概要

このボットは以下の機能を提供します：
- 本の情報を自動で取得
- 投稿用の美しい画像を自動生成
- Instagramへの自動投稿機能
- 投稿スケジュールの管理
- 投稿履歴の管理

## 必要要件

- Python 3.8以上
- Instagram アカウント
- インターネット接続

## セットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/[your-username]/book-instagram-bot.git
cd book-instagram-bot
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
`.env`ファイルを作成し、以下の環境変数を設定してください：

```env
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
POST_INTERVAL=24  # 投稿間隔（時間）
```

## 使用方法

1. 設定の確認:
   - 環境変数が正しく設定されていることを確認
   - Instagramアカウントの認証情報が正しいことを確認

2. ボットの実行:
```bash
python main.py
```

3. スケジュール設定（オプション）:
```bash
python main.py --schedule "09:00"  # 毎日午前9時に投稿
```

## 機能詳細

### 本の情報取得
- 複数の書籍APIを利用して情報を取得
- 書籍のメタデータを自動で解析

### 画像生成
- 本のカバー画像を自動でフォーマット
- カスタマイズ可能なテンプレート
- テキストの自動レイアウト

### Instagram投稿
- 自動ログイン
- ハッシュタグの自動生成
- エラー時の自動リトライ

## トラブルシューティング

よくある問題と解決方法：

1. 認証エラー
   - Instagramの認証情報を確認
   - 2要素認証が有効な場合は無効化

2. API制限
   - 投稿間隔を長めに設定
   - 複数のAPIキーをローテーション

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 作者

shirokuma - [@your-twitter](https://twitter.com/your-twitter)

プロジェクトへの貢献や質問は大歓迎です！ 