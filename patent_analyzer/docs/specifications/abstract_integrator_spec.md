# Abstract Integrator 詳細仕様書

## 概要
特許データとアブストラクト情報を統合し、構造化されたJSONデータを生成するコンポーネント

## 機能仕様

### 主要機能
1. **データ統合**
   - CSV特許データとアブストラクトデータの結合
   - 特許IDによるマッチング
   - JSON形式での出力

2. **データ検証**
   - 必須フィールドの存在確認
   - データ型の検証

### 入力仕様
- **特許データ（CSV形式）**
  ```csv
  id,title,assignee,inventor/author,priority date,filing/creation date,publication date,grant date,result link
  US-9254383-B2,Devices and methods for monitoring non-invasive vagus nerve stimulation,"ElectroCore, LLC","Bruce J. Simon, Joseph P. Errico",2009-03-20,2013-04-28,2016-02-09,2016-02-09,https://patents.google.com/patent/US9254383B2/en
  ```

- **アブストラクトデータ（JSON形式）**
  ```json
  {
    "US-9254383-B2": {
      "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
      "abstract": "A system for monitoring non-invasive vagus nerve stimulation...",
      "url": "https://patents.google.com/patent/US9254383B2/en"
    }
  }
  ```

### 出力仕様
- **統合JSON形式**
  ```json
  [
    {
      "id": "US-9254383-B2",
      "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
      "abstract": "A system for monitoring non-invasive vagus nerve stimulation...",
      "assignee": "ElectroCore, LLC",
      "inventors": "Bruce J. Simon, Joseph P. Errico",
      "priority_date": "2009-03-20",
      "filing_date": "2013-04-28",
      "publication_date": "2016-02-09",
      "grant_date": "2016-02-09",
      "result_link": "https://patents.google.com/patent/US9254383B2/en"
    }
  ]
  ```

## 実装方法

### 方法1: jqを使用した変換（推奨）

#### ステップ1: CSVからJSONへの変換
```bash
# CSVをJSONに変換
cat patents.csv | jq -R -s -c 'split("\n") | .[1:-1] | map(split(",")) | map({
  "id": .[0],
  "title": .[1],
  "assignee": .[2],
  "inventors": .[3],
  "priority_date": .[4],
  "filing_date": .[5],
  "publication_date": .[6],
  "grant_date": .[7],
  "result_link": .[8]
})' > patents.json
```

#### ステップ2: アブストラクトデータとの結合
```bash
# アブストラクトデータを統合
jq -s '.[0] as $patents | .[1] as $abstracts | 
  $patents | map(. + {abstract: $abstracts[.id].abstract})' \
  patents.json abstracts.json > integrated_patents.json
```

### 方法2: Pythonスクリプト（軽量版）

```python
#!/usr/bin/env python3
import json
import sys

def integrate_abstracts(patents_file, abstracts_file, output_file):
    """CSV特許データとJSONアブストラクトデータを統合"""
    
    # アブストラクトデータ読み込み
    with open(abstracts_file, 'r') as f:
        abstracts = json.load(f)
    
    # 特許データ読み込み（JSON形式を想定）
    with open(patents_file, 'r') as f:
        patents = json.load(f)
    
    # 統合処理
    integrated = []
    for patent in patents:
        patent_id = patent['id']
        if patent_id in abstracts:
            patent['abstract'] = abstracts[patent_id]['abstract']
        else:
            patent['abstract'] = None
        integrated.append(patent)
    
    # 結果保存
    with open(output_file, 'w') as f:
        json.dump(integrated, f, indent=2)
    
    return len(integrated)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: abstract_integrator.py <patents.json> <abstracts.json> <output.json>")
        sys.exit(1)
    
    patents_file = sys.argv[1]
    abstracts_file = sys.argv[2]
    output_file = sys.argv[3]
    
    count = integrate_abstracts(patents_file, abstracts_file, output_file)
    print(f"Integrated {count} patents")
```

## 使用例

### jqを使用した場合
```bash
# 1. CSVからJSONに変換
cat patents.csv | jq -R -s -c 'split("\n") | .[1:-1] | map(split(",")) | map({
  "id": .[0],
  "title": .[1],
  "assignee": .[2],
  "inventors": .[3],
  "priority_date": .[4],
  "filing_date": .[5],
  "publication_date": .[6],
  "grant_date": .[7],
  "result_link": .[8]
})' > patents.json

# 2. アブストラクト統合
jq -s '.[0] as $patents | .[1] as $abstracts | 
  $patents | map(. + {abstract: $abstracts[.id].abstract})' \
  patents.json abstracts.json > integrated_patents.json
```

### Pythonスクリプトを使用した場合
```bash
python3 abstract_integrator.py patents.json abstracts.json integrated_patents.json
```

## エラーハンドリング

### よくある問題と対処法

1. **CSV形式エラー**
   - カンマ区切りの確認
   - 引用符の適切な使用
   - エンコーディング（UTF-8）の確認

2. **マッチング失敗**
   - 特許ID形式の統一
   - 前後の空白文字の除去

3. **jqコマンドエラー**
   - jqのインストール確認
   - JSON形式の構文チェック

## トラブルシューティング

### jqがインストールされていない場合
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# CentOS/RHEL
sudo yum install jq
```

### CSV形式の確認
```bash
# 最初の数行を確認
head -5 patents.csv

# フィールド数を確認
head -1 patents.csv | tr ',' '\n' | wc -l
```
