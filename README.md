# torir-util : 個人的なユーティリティ集

## ディレクトリ構成

/doc : 仕様書
/patent_analyzer : 特許分析システム
/mail_converter : メール変換システム

## アプリケーション一覧

### mail-converter
AppleMailのメールをテキストファイルに変換するツール
- メールの内容をテキストファイルとして保存
- ファイル名に日時と件名を含める
- 文字コードをUTF-8に変換
- 詳細は [mail_converter/README.md](mail_converter/README.md) を参照

### PatentInsight Orchestrator
Google Patentsの検索結果から関連性の高い特許文献を自動抽出・分析するシステム
- CSV形式の特許検索結果を入力として受け取り
- 各特許のアブストラクトを自動取得
- 設定可能なキーワードに基づく関連性スコアリング
- 優先順位付けされた特許リストを生成
- 詳細は [patent_analyzer/README.md](patent_analyzer/README.md) を参照