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
        "output_file": "data/processed/scored_patents_20240115_101000.json"
      }
    },
    "final_results": {
      "total_patents": 4,
      "high_relevance_count": 2,
      "medium_relevance_count": 1,
      "low_relevance_count": 1,
      "top_patents": [
        {
          "patent_id": "US-9254383-B2",
          "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
          "overall_score": 85.5,
          "ranking": 1
        }
      ]
    },
    "error_log": [],
    "warnings": []
  }
  ```

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

## 使用例

### 基本的な使用
```python
from patent_orchestrator import PatentOrchestrator

orchestrator = PatentOrchestrator("orchestrator_config.json")
result = orchestrator.run_workflow()
```

### カスタム設定
```python
orchestrator = PatentOrchestrator(
    config_file="custom_config.json",
    continue_on_error=True,
    save_partial_results=True
)
```

### 結果の分析
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

## 将来の拡張
- Web UI インターフェース
- リアルタイム監視ダッシュボード
- 分散処理対応
- クラウド統合
- API エンドポイント提供 