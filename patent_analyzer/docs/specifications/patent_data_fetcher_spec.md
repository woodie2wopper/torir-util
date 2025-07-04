# Patent Data Fetcher 詳細仕様書

## 概要
Google Patentsから特許情報を取得し、アブストラクトを含む詳細データを抽出するコンポーネント

## 機能仕様

### 主要機能
1. **特許URLからのデータ抽出**
   - 特許ID、タイトル、アブストラクトの取得
   - 複数のHTML要素パターンに対応
   - エラーハンドリングとリトライ機能

2. **CSVファイル処理**
   - Google Patents検索結果CSVの読み込み
   - 特許URLの抽出と正規化
   - バッチ処理対応

3. **データ形式変換**
   - CSV → JSON形式への変換
   - 構造化データの生成

### 入力仕様
- **CSVファイル形式**
  ```
  id,title,assignee,inventor/author,priority date,filing/creation date,publication date,grant date,result link,representative figure link
  US-9254383-B2,Devices and methods for monitoring non-invasive vagus nerve stimulation,"ElectroCore, LLC","Bruce J. Simon, Joseph P. Errico",2009-03-20,2013-04-28,2016-02-09,2016-02-09,https://patents.google.com/patent/US9254383B2/en,...
  ```

- **コマンドライン引数**
  ```bash
  python patent_data_fetcher.py --input input.csv --output output.json --delay 2 --retries 3
  ```

### 出力仕様
- **JSON形式**
  ```json
  {
    "patent_id": "US-9254383-B2",
    "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
    "abstract": "A system for monitoring non-invasive vagus nerve stimulation...",
    "url": "https://patents.google.com/patent/US9254383B2/en",
    "metadata": {
      "assignee": "ElectroCore, LLC",
      "inventors": ["Bruce J. Simon", "Joseph P. Errico"],
      "priority_date": "2009-03-20",
      "filing_date": "2013-04-28",
      "publication_date": "2016-02-09",
      "grant_date": "2016-02-09"
    }
  }
  ```

## 技術仕様

### 依存関係
- `requests`: HTTP通信
- `beautifulsoup4`: HTML解析
- `pandas`: CSV処理
- `lxml`: XML/HTMLパーサー

### エラーハンドリング
1. **ネットワークエラー**
   - 接続タイムアウト: 30秒
   - リトライ回数: 3回（設定可能）
   - 指数バックオフ: 2秒、4秒、8秒

2. **HTML解析エラー**
   - 複数のセレクターパターン対応
   - フォールバック処理
   - 部分的なデータ取得

3. **CAPTCHA検出**
   - 特定のHTML要素パターン検出
   - 自動待機とリトライ
   - ユーザー通知機能

### パフォーマンス設定
- **遅延設定**: デフォルト2秒（設定可能）
- **並列処理**: 最大5スレッド
- **メモリ管理**: ストリーミング処理対応

## 設定ファイル

### config.json
```json
{
  "request_settings": {
    "timeout": 30,
    "max_retries": 3,
    "delay_between_requests": 2,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  },
  "html_selectors": {
    "title": ["span[itemprop='title']", "h1"],
    "abstract": ["div[itemprop='abstract']", "section[itemprop='abstract']", "div.abstract"]
  },
  "output_settings": {
    "format": "json",
    "encoding": "utf-8",
    "indent": 2
  }
}
```

## ログ機能

### ログレベル
- **DEBUG**: 詳細な処理情報
- **INFO**: 一般的な処理状況
- **WARNING**: 警告（リトライ、部分データ取得）
- **ERROR**: エラー（接続失敗、解析失敗）

### ログ出力
- **ファイル出力**: `logs/patent_fetcher_YYYY-MM-DD.log`
- **コンソール出力**: エラーと警告のみ
- **統計情報**: 処理件数、成功件数、失敗件数

## テスト仕様

### テストデータ
- **正常ケース**: 4件の特許データ
- **エラーケース**: 無効URL、ネットワークエラー
- **エッジケース**: 空のアブストラクト、特殊文字

### テスト実行
```bash
python -m pytest tests/test_patent_data_fetcher.py -v
```

## 使用例

### 基本的な使用
```python
from patent_data_fetcher import PatentDataFetcher

fetcher = PatentDataFetcher()
results = fetcher.process_csv("input.csv", "output.json")
```

### カスタム設定
```python
fetcher = PatentDataFetcher(
    delay=3,
    max_retries=5,
    timeout=60
)
```

## トラブルシューティング

### よくある問題
1. **CAPTCHA表示**
   - 遅延時間を増加
   - User-Agent変更
   - プロキシ使用

2. **データ取得失敗**
   - HTMLセレクター確認
   - サイト構造変更対応
   - 手動確認推奨

3. **メモリ不足**
   - バッチサイズ調整
   - ストリーミング処理使用

## 将来の拡張
- 多言語対応（日本語、中国語、韓国語）
- 画像データ取得
- 引用情報取得
- 機械学習による自動セレクター調整 