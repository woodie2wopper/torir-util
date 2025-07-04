# Patent Analyzer Test Suite

このディレクトリには、Patent Analyzerシステムのテスト用スクリプトが含まれています。

## ファイル構成

- `mock_get_abst_patent.py` - テスト用のモックアブストラクト取得スクリプト
- `test_abstract_fetching.py` - アブストラクト取得の統合テストスクリプト
- `README.md` - このファイル

## テストの概要

### 1. モックアブストラクト取得テスト

実際のGoogle Patentsアクセスを模擬し、テストデータ（`sample_abstracts.json`）から
アブストラクトを取得します。本番の`get_abst_patent.py`と同じ出力形式を返します。

#### 使用方法

```bash
# 単一の特許IDに対してテスト
python3 test/mock_get_abst_patent.py <patent_id> <abstracts_json_file>

# 例
python3 test/mock_get_abst_patent.py US-9254383-B2 ../data/test_data/sample_abstracts.json
```

#### 出力形式

```json
{
  "ID": "US-9254383-B2",
  "Title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
  "Abstract": "A system for monitoring non-invasive vagus nerve stimulation...",
  "URL": "https://patents.google.com/patent/US9254383B2/en",
  "Error": null,
  "ErrorCode": null,
  "ErrorMessage": null,
  "RetryCount": 0,
  "Timestamp": null
}
```

### 2. 統合アブストラクト取得テスト

CSVから変換されたJSONファイルを使って、複数の特許に対して
アブストラクト取得を一括テストします。

#### 使用方法

```bash
# 統合テストの実行
python3 test/test_abstract_fetching.py <patents_json> <abstracts_json> [output_dir]

# 例
python3 test/test_abstract_fetching.py ../data/processed/converted_patents_20250704_174252.json ../data/test_data/sample_abstracts.json
```

#### テスト結果

テスト結果は以下の情報を含むJSONファイルとして保存されます：

- **test_info**: テスト実行情報（開始時刻、終了時刻、実行時間など）
- **summary**: 統計情報（総特許数、成功数、失敗数、成功率）
- **patent_results**: 各特許の詳細結果
- **errors**: エラー情報

#### 出力例

```
============================================================
Abstract Fetching Test Results
============================================================
Test Duration: 0:00:00.117532
Total Patents: 4
Successful Fetches: 4
Failed Fetches: 0
Success Rate: 100.0%

Sample Successful Results:
  - US-9254383-B2: Devices and methods for monitoring non-invasive vagus nerve stimulation
    Abstract: A system for monitoring non-invasive vagus nerve stimulation includes a device that applies electric...
  - US-10123456-A1: System for brain network analysis and intervention
    Abstract: A comprehensive system for analyzing brain network dynamics and providing targeted interventions. Th...
```

## テストデータ

テストには以下のデータファイルを使用します：

- `../data/test_data/sample_abstracts.json` - サンプルアブストラクトデータ
- `../data/processed/converted_patents_*.json` - CSVから変換された特許データ

## エラーハンドリング

### モックスクリプトのエラーケース

1. **NOT_FOUND**: 特許IDがテストデータに存在しない場合
2. **FILE_NOT_FOUND**: アブストラクトファイルが見つからない場合
3. **INVALID_JSON**: JSONファイルの形式が不正な場合
4. **UNEXPECTED_ERROR**: 予期しないエラーが発生した場合

### 統合テストのエラーケース

1. **timeout**: アブストラクト取得がタイムアウトした場合
2. **failed**: モックスクリプトが失敗した場合
3. **error**: 予期しないエラーが発生した場合

## 終了コード

- **0**: テスト成功（成功率80%以上）
- **1**: テスト失敗（成功率80%未満またはエラー発生）

## 注意事項

1. モックスクリプトは実際のWebアクセスを行いません
2. テストデータは限定的なため、本番環境とは異なる結果になる場合があります
3. テスト結果は`test_output/`ディレクトリに保存されます
4. 本番環境でのテストには`get_abst_patent.py`を使用してください

## トラブルシューティング

### よくある問題

1. **ファイルが見つからない**
   - ファイルパスが正しいか確認
   - 相対パスが正しいか確認

2. **JSON形式エラー**
   - テストデータファイルの形式を確認
   - UTF-8エンコーディングで保存されているか確認

3. **権限エラー**
   - スクリプトに実行権限があるか確認
   - 出力ディレクトリに書き込み権限があるか確認

### デバッグ方法

```bash
# 詳細ログを有効にする
export PYTHONPATH=.
python3 -u test/test_abstract_fetching.py <patents_json> <abstracts_json>

# 個別のモックテスト
python3 -u test/mock_get_abst_patent.py <patent_id> <abstracts_json>
``` 