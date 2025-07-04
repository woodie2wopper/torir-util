# get_abst_patent.py 仕様書

**作成日**: 2025-07-04 16:26:19  
**バージョン**: 1.0  
**作成者**: torir-util

## 概要

`get_abst_patent.py`は、Google PatentsのURLから特許のタイトルとアブストラクトを抽出するPythonスクリプトです。コマンドライン引数またはパイプ入力からURLを受け取り、JSON形式で結果を出力します。

## 機能

### 主要機能
- Google Patents URLからの特許情報抽出
- 特許ID、タイトル、アブストラクトの取得
- 複数URLの一括処理対応
- JSON形式での出力

### 抽出情報
- **特許ID**: URLから自動抽出
- **タイトル**: 特許のタイトル
- **アブストラクト**: 特許の要約

## 使用方法

### 基本的な使用方法

#### 1. コマンドライン引数での使用
```bash
python3 bin/get_abst_patent.py -i "https://patents.google.com/patent/US12345678A1/en"
```

#### 2. パイプ入力での使用
```bash
echo "https://patents.google.com/patent/US12345678A1/en" | python3 bin/get_abst_patent.py
```

#### 3. 複数URLの一括処理
```bash
cat urls.txt | python3 bin/get_abst_patent.py
```

### 出力形式

#### 単一URLの場合
```json
{
  "ID": "US12345678A1",
  "Title": "特許のタイトル",
  "Abstract": "特許のアブストラクト内容..."
}
```

#### 複数URLの場合
```json
[
  {
    "ID": "US12345678A1",
    "Title": "特許1のタイトル",
    "Abstract": "特許1のアブストラクト..."
  },
  {
    "ID": "US87654321A1",
    "Title": "特許2のタイトル",
    "Abstract": "特許2のアブストラクト..."
  }
]
```

## 技術仕様

### 依存関係
- Python 3.x
- requests
- beautifulsoup4

### 主要関数

#### `extract_patent_id(url)`
- **目的**: URLから特許IDを抽出
- **入力**: Google Patents URL
- **出力**: 特許ID（文字列）またはNone
- **正規表現**: `/patent/([^/]+)`

#### `scrape_patent_info(url)`
- **目的**: 特許情報のスクレイピング実行
- **入力**: Google Patents URL
- **出力**: 辞書形式の特許情報
- **処理内容**:
  1. HTTPリクエスト送信（User-Agent設定）
  2. HTML解析（BeautifulSoup）
  3. タイトル抽出（複数セレクタ対応）
  4. アブストラクト抽出（複数セレクタ対応）
  5. エラーハンドリング

### HTML要素の抽出戦略

#### タイトル抽出
1. `span[itemprop="title"]`
2. `h1`要素

#### アブストラクト抽出
1. `div[itemprop="abstract"]`
2. `section[itemprop="abstract"]`
3. `div.abstract`

### エラーハンドリング
- **ネットワークエラー**: requests.RequestException
- **一般エラー**: Exception
- **無効なURL**: スキップしてエラーメッセージ出力

## 制限事項

### 技術的制限
- Google PatentsのHTML構造変更に依存
- レート制限の可能性
- JavaScriptで動的に生成されるコンテンツには対応不可

### 対応URL形式
- `https://patents.google.com/patent/[PATENT_ID]/[LANG]`
- 例: `https://patents.google.com/patent/US12345678A1/en`

## インストール

### 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 必要なパッケージ
```
requests
beautifulsoup4
```

## 使用例

### 例1: 単一特許の情報取得
```bash
python3 bin/get_abst_patent.py -i "https://patents.google.com/patent/US10123456A1/en"
```

### 例2: ファイルから複数特許を処理
```bash
# urls.txt に特許URLを1行ずつ記載
python3 bin/get_abst_patent.py < urls.txt
```

### 例3: 結果をファイルに保存
```bash
python3 bin/get_abst_patent.py -i "https://patents.google.com/patent/US10123456A1/en" > result.json
```

## トラブルシューティング

### よくある問題

#### 1. "Title not found" または "Abstract not found"
- **原因**: HTML構造の変更
- **対処法**: セレクタの更新が必要

#### 2. ネットワークエラー
- **原因**: 接続問題またはレート制限
- **対処法**: 時間をおいて再実行

#### 3. 無効なURLエラー
- **原因**: Google Patents以外のURL
- **対処法**: 正しいGoogle Patents URLを使用

## 今後の改善案

1. **レート制限対応**: リクエスト間隔の調整
2. **キャッシュ機能**: 重複リクエストの回避
3. **並列処理**: 複数URLの同時処理
4. **ログ機能**: 詳細な実行ログ
5. **設定ファイル**: カスタマイズ可能な設定

## ライセンス

このツールは教育・研究目的で作成されています。商用利用の際は、Google Patentsの利用規約を確認してください。

## 更新履歴

- **2025-07-04**: 初版作成
  - 基本的なスクレイピング機能
  - コマンドライン引数対応
  - パイプ入力対応
  - JSON出力対応 