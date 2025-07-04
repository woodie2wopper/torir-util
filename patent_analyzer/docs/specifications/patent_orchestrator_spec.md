# Patent Orchestrator 詳細仕様書

## 概要
特許分析システム全体を統合し、ワークフローを管理するメインコンポーネント

## 機能仕様

### 主要機能
1. **ワークフロー管理**
   - 各コンポーネントの実行順序制御
   - 依存関係の管理
   - エラー時の処理継続/中断制御

2. **データパイプライン**
   - CSV → JSON → スコアリング → 結果出力
   - 中間データの保存と管理
   - 処理状況の監視

3. **設定管理**
   - 設定ファイルの読み込みと検証
   - 環境変数の管理
   - 動的設定の適用

4. **スコアリング結果のソート機能**
   - 関連度スコア順（降順）での自動ソート
   - NaNスコアの除外処理
   - 既存ファイルからのソート済みファイル生成

### 入力仕様
- **設定ファイル（JSON形式）**
  ```json
  {
    "input": {
      "csv_file": "data/raw_search_results/gp-search-20250703-183545.csv",
      "encoding": "utf-8"
    },
    "output": {
      "base_dir": "data/processed",
      "timestamp_format": "%Y%m%d_%H%M%S"
    },
    "components": {
      "patent_data_fetcher": {
        "enabled": true,
        "delay": 2,
        "max_retries": 3,
        "timeout": 30
      },
      "abstract_integrator": {
        "enabled": true,
        "fuzzy_match": false
      },
      "relevance_scorer": {
        "enabled": true,
        "keywords_file": "config/scoring_keywords.json"
      }
    },
    "logging": {
      "level": "INFO",
      "file": "logs/orchestrator.log",
      "console": true
    }
  }
  ```

### 出力仕様
- **処理結果サマリー（JSON形式）**
  ```json
  {
    "execution_summary": {
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T10:30:00Z",
      "total_duration": "00:30:00",
      "status": "completed"
    },
    "component_results": {
      "patent_data_fetcher": {
        "status": "completed",
        "processed_count": 4,
        "success_count": 4,
        "error_count": 0,
        "output_file": "data/processed/patents_with_abstracts_20240115_100000.json"
      },
      "abstract_integrator": {
        "status": "completed",
        "processed_count": 4,
        "matched_count": 4,
        "unmatched_count": 0,
        "output_file": "data/processed/integrated_patents_20240115_100500.json"
      },
      "relevance_scorer": {
        "status": "completed",
        "processed_count": 4,
        "scored_count": 4,
        "valid_scored_count": 4,
        "output_file": "data/processed/scored_patents_20240115_101000.json",
        "sorted_output_file": "data/processed/scored_patents_20240115_101000_sorted.json"
      }
    },
    "final_results": {
      "total_patents": 4,
      "high_relevance_count": 2,
      "medium_relevance_count": 1,
      "low_relevance_count": 1,
      "nan_score_count": 0,
      "top_patents": [
        {
          "patent_id": "US-9254383-B2",
          "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
          "relevance_score": 88,
          "ranking": 1
        }
      ]
    },
    "error_log": [],
    "warnings": []
  }
  ```

#### 出力ファイル
1. **`scored_patents_YYYYMMDD_HHMMSS.json`** - 元の順序でスコアリングされた特許データ
2. **`scored_patents_YYYYMMDD_HHMMSS_sorted.json`** - 関連度スコア順（降順）でソートされた特許データ
   - NaNスコアの特許は除外
   - 関連度の高い特許が上位に表示

## 技術仕様

### 依存関係
- `json`: JSON処理
- `datetime`: 日時処理
- `logging`: ログ機能
- `pathlib`: パス処理
- `subprocess`: 外部プロセス実行

### ワークフローフロー
1. **初期化**
   - 設定ファイル読み込み
   - ログ設定
   - 出力ディレクトリ作成

2. **データ取得**
   - CSVファイル読み込み
   - 特許URL抽出
   - アブストラクト取得

3. **データ統合**
   - CSVとアブストラクトデータ結合
   - データ検証
   - 中間ファイル保存

4. **スコアリング**
   - キーワードマッチング
   - 関連性スコア計算
   - 結果ランキング

5. **結果出力**
   - 最終結果保存
   - サマリーレポート生成
   - ログファイル作成
   - スコア順ソート済みファイルの自動生成

### エラーハンドリング
1. **コンポーネントエラー**
   - 個別コンポーネントの失敗処理
   - 部分的な結果の保持
   - エラー統計の記録

2. **設定エラー**
   - 設定ファイルの検証
   - デフォルト値の適用
   - ユーザー通知

3. **システムエラー**
   - メモリ不足の処理
   - ディスク容量不足の処理
   - ネットワークエラーの処理

## 設定ファイル

### orchestrator_config.json
```json
{
  "system": {
    "name": "PatentInsight Orchestrator",
    "version": "1.0.0",
    "description": "Patent analysis workflow orchestrator"
  },
  "input": {
    "csv_file": "data/raw_search_results/gp-search-20250703-183545.csv",
    "encoding": "utf-8",
    "delimiter": ",",
    "skip_rows": 1
  },
  "output": {
    "base_dir": "data/processed",
    "timestamp_format": "%Y%m%d_%H%M%S",
    "create_backup": true,
    "compress_results": false
  },
  "components": {
    "patent_data_fetcher": {
      "enabled": true,
      "class": "PatentDataFetcher",
      "config": {
        "delay": 2,
        "max_retries": 3,
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      }
    },
    "abstract_integrator": {
      "enabled": true,
      "class": "AbstractIntegrator",
      "config": {
        "encoding": "utf-8",
        "use_jq": true,
        "jq_timeout": 30,
        "temp_file_cleanup": true
      }
    },
    "relevance_scorer": {
      "enabled": true,
      "class": "RelevanceScorer",
      "config": {
        "keywords_file": "config/scoring_keywords.json",
        "case_sensitive": false,
        "partial_match": true
      }
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/orchestrator.log",
    "console": true,
    "max_file_size": "10MB",
    "backup_count": 5
  },
  "error_handling": {
    "continue_on_error": true,
    "max_retries": 3,
    "retry_delay": 5,
    "save_partial_results": true
  },
  "performance": {
    "parallel_processing": false,
    "max_workers": 4,
    "batch_size": 100,
    "memory_limit": "1GB"
  }
}
```

## ログ機能

### ログレベル
- **DEBUG**: 詳細な実行情報
- **INFO**: ワークフロー進行状況
- **WARNING**: 部分的な失敗、設定警告
- **ERROR**: コンポーネント失敗、システムエラー

### ログ出力
- **ファイル出力**: `logs/orchestrator_YYYY-MM-DD.log`
- **コンソール出力**: 重要な進行状況とエラー
- **統計情報**: 実行時間、成功率、エラー率

## テスト仕様

### テストデータ
- **正常ケース**: 完全なワークフロー実行
- **部分エラー**: 一部コンポーネントの失敗
- **設定エラー**: 無効な設定ファイル
- **システムエラー**: リソース不足

### テスト実行
```bash
python -m pytest tests/test_patent_orchestrator.py -v
```

## 使用方法

### コマンドライン実行

#### 基本的なワークフロー実行
```bash
python src/patent_orchestrator.py --input data/raw/patents.csv
```

#### 設定ファイルを指定した実行
```bash
python src/patent_orchestrator.py --input data/raw/patents.csv --config config/orchestrator_config.json
```

#### バッチ処理（部分実行）
```bash
# 1番目から10件の特許のみ処理
python src/patent_orchestrator.py --input data/raw/patents.csv --start_number 1 --batch_size 10

# 11番目から20件の特許のみ処理
python src/patent_orchestrator.py --input data/raw/patents.csv --start_number 11 --batch_size 10
```

#### アブストラクト取得をスキップ
```bash
# 既存のアブストラクトのみを使用して高速処理
python src/patent_orchestrator.py --input data/raw/patents.csv --skip_abstract_fetch
```

#### 既存のスコアリング結果ファイルをソート
```bash
# 既存のスコアリング結果ファイルからソート済みファイルを生成
python src/patent_orchestrator.py --sort-scored-file data/processed/scored_patents_20250704_185141.json
```

#### テストモード実行
```bash
# モックデータを使用したテスト実行
python src/patent_orchestrator.py --input data/raw/patents.csv --test-mode --mock-abstracts data/mock_abstracts.json
```

#### 個別コンポーネントのテスト
```bash
# CSV→JSON変換のテスト
python src/patent_orchestrator.py --input data/raw/patents.csv --test csv-converter

# 特許データ取得のテスト
python src/patent_orchestrator.py --input data/raw/patents.csv --test data-fetcher

# アブストラクト統合のテスト
python src/patent_orchestrator.py --input data/raw/patents.csv --test abstract-integrator

# 関連度スコアリングのテスト
python src/patent_orchestrator.py --input data/raw/patents.csv --test relevance-scorer

# 全コンポーネントのテスト
python src/patent_orchestrator.py --input data/raw/patents.csv --test all
```

### コマンドライン引数一覧

| 引数 | 短縮形 | 説明 | 必須 |
|------|--------|------|------|
| `--input` | `-i` | 入力CSVファイルパス | ワークフロー実行時 |
| `--config` | `-c` | 設定ファイルパス | 任意 |
| `--output` | `-o` | 出力ディレクトリ | 任意 |
| `--start_number` | - | バッチ処理の開始番号（1ベース） | 任意 |
| `--batch_size` | - | バッチ処理のサイズ | 任意 |
| `--skip_abstract_fetch` | - | アブストラクト取得をスキップ | 任意 |
| `--sort-scored-file` | - | 既存スコアリング結果ファイルをソート | 任意 |
| `--test-mode` | - | テストモード有効化 | 任意 |
| `--mock-abstracts` | - | モックアブストラクトファイル | 任意 |
| `--test` | `-t` | 個別コンポーネントテスト | 任意 |
| `--verbose` | `-v` | 詳細出力 | 任意 |

### Python API使用例

#### 基本的な使用
```python
from patent_orchestrator import PatentOrchestrator

orchestrator = PatentOrchestrator("orchestrator_config.json")
result = orchestrator.run_workflow()
```

#### カスタム設定
```python
orchestrator = PatentOrchestrator(
    config_file="custom_config.json",
    continue_on_error=True,
    save_partial_results=True
)
```

#### 既存ファイルのソート
```python
# 既存のスコアリング結果ファイルからソート済みファイルを生成
output_file = orchestrator.create_sorted_scored_file(
    "data/processed/scored_patents_20250704_185141.json"
)
print(f"ソート済みファイル生成: {output_file}")
```

#### 結果の分析
```python
# 実行結果の確認
if result["execution_summary"]["status"] == "completed":
    print(f"処理完了: {result['final_results']['total_patents']}件の特許を処理")
    
# エラーの確認
if result["error_log"]:
    print(f"エラーが発生: {len(result['error_log'])}件")
```

## パフォーマンス最適化

### 並列処理
- コンポーネント間の並列実行
- マルチスレッド処理
- リソース使用量の監視

### メモリ管理
- ストリーミング処理
- 中間データの削除
- メモリ使用量の制限

## トラブルシューティング

### よくある問題
1. **コンポーネント失敗**
   - 個別コンポーネントの設定確認
   - 依存関係の確認
   - ログファイルの詳細確認

2. **処理時間が長い**
   - 並列処理の有効化
   - バッチサイズの調整
   - リソース使用量の確認

3. **メモリ不足**
   - バッチサイズの削減
   - ストリーミング処理の使用
   - 中間データの削除

## 新機能詳細

### スコアリング結果のソート機能

#### 自動ソート機能
- スコアリング完了時に自動的にソート済みファイルを生成
- ファイル名: `scored_patents_YYYYMMDD_HHMMSS_sorted.json`
- NaNスコアの特許は除外してソート

#### 手動ソート機能
- 既存のスコアリング結果ファイルからソート済みファイルを生成
- コマンド: `--sort-scored-file <ファイルパス>`
- 出力ファイル: `<元ファイル名>_sorted.json`

#### ソート仕様
- **ソート基準**: `relevance_score`フィールド（降順）
- **除外条件**: `relevance_score`がNaNの特許
- **出力形式**: JSON形式（元データと同じ構造）

#### 使用例
```bash
# 既存ファイルからソート済みファイルを生成
python src/patent_orchestrator.py --sort-scored-file data/processed/scored_patents_20250704_185141.json

# 出力: data/processed/scored_patents_20250704_185141_sorted.json
```

### バッチ処理機能

#### 部分実行
- 大量データの分割処理が可能
- `--start_number`: 開始番号（1ベース）
- `--batch_size`: 処理件数

#### 使用例
```bash
# 1-10件目を処理
python src/patent_orchestrator.py --input data.csv --start_number 1 --batch_size 10

# 11-20件目を処理
python src/patent_orchestrator.py --input data.csv --start_number 11 --batch_size 10
```

### アブストラクト取得スキップ機能

#### 高速処理モード
- `--skip_abstract_fetch`オプションでアブストラクト取得をスキップ
- 既存のアブストラクトファイルのみを使用
- 処理時間を大幅に短縮

#### 使用例
```bash
# アブストラクト取得をスキップして高速処理
python src/patent_orchestrator.py --input data.csv --skip_abstract_fetch
```

## ファイル管理

### 出力ファイル
1. **`scored_patents_YYYYMMDD_HHMMSS.json`** - 元の順序
2. **`scored_patents_YYYYMMDD_HHMMSS_sorted.json`** - スコア順ソート済み
3. **`orchestrator_results_YYYYMMDD_HHMMSS.json`** - 実行結果サマリー

### 中間ファイル
- **`patents_with_abstracts_YYYYMMDD_HHMMSS.json`** - アブストラクト取得結果
- **`integrated_patents_YYYYMMDD_HHMMSS.json`** - 統合済みデータ

### ログファイル
- **`logs/orchestrator_YYYY-MM-DD.log`** - 実行ログ
- **`logs/patent_data_fetcher_YYYY-MM-DD.log`** - 特許データ取得ログ

## 将来の拡張
- Web UI インターフェース
- リアルタイム監視ダッシュボード
- 分散処理対応
- クラウド統合
- API エンドポイント提供 