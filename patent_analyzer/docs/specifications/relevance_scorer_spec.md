# Relevance Scorer 詳細仕様書

## 概要
特許データの関連性をスコアリングし、キーワードベースの分析を行うコンポーネント

## 機能仕様

### 主要機能
1. **キーワードマッチング**
   - タイトルとアブストラクトのキーワード検索
   - 部分一致と完全一致の処理
   - 重み付けスコアリング

2. **関連性スコアリング**
   - 複数カテゴリのスコア計算
   - 正規化されたスコア（0-100）
   - 総合スコアの算出

3. **結果ランキング**
   - スコアによる降順ソート
   - カテゴリ別ランキング
   - フィルタリング機能

### 入力仕様
- **特許データ（JSON形式）**
  ```json
  {
    "patent_id": "US-9254383-B2",
    "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
    "abstract": "A system for monitoring non-invasive vagus nerve stimulation...",
    "metadata": {
      "assignee": "ElectroCore, LLC",
      "inventors": ["Bruce J. Simon", "Joseph P. Errico"]
    }
  }
  ```

- **キーワード設定（JSON形式）**
  ```json
  {
    "mental_health": {
      "keywords": ["mental health", "anxiety", "depression", "stress", "well-being"],
      "weight": 1.0,
      "description": "Mental health related technologies"
    },
    "biosensor": {
      "keywords": ["biosensor", "wearable", "sensor", "monitoring", "biometric"],
      "weight": 0.8,
      "description": "Biosensor and wearable technologies"
    },
    "intervention": {
      "keywords": ["intervention", "therapy", "treatment", "modulation", "stimulation"],
      "weight": 0.9,
      "description": "Intervention and therapy methods"
    }
  }
  ```

### 出力仕様
- **スコアリング結果（JSON形式）**
  ```json
  {
    "patent_id": "US-9254383-B2",
    "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
    "overall_score": 85.5,
    "category_scores": {
      "mental_health": 90.0,
      "biosensor": 75.0,
      "intervention": 95.0
    },
    "matched_keywords": {
      "mental_health": ["stimulation", "monitoring"],
      "biosensor": ["monitoring"],
      "intervention": ["stimulation", "therapy"]
    },
    "keyword_details": [
      {
        "category": "intervention",
        "keyword": "stimulation",
        "count": 3,
        "positions": ["title", "abstract"],
        "score": 30.0
      }
    ],
    "ranking": 1,
    "processing_info": {
      "scoring_timestamp": "2024-01-15T10:30:00Z",
      "algorithm_version": "1.0"
    }
  }
  ```

## 技術仕様

### 依存関係
- `json`: JSON処理
- `re`: 正規表現
- `collections`: データ構造
- `logging`: ログ機能

### スコアリングアルゴリズム
1. **キーワードマッチング**
   - 大文字小文字を区別しない検索
   - 部分一致と完全一致の組み合わせ
   - 正規表現による柔軟なマッチング

2. **スコア計算**
   ```
   カテゴリスコア = (マッチしたキーワード数 / 総キーワード数) × 重み × 100
   総合スコア = Σ(カテゴリスコア) / カテゴリ数
   ```

3. **正規化処理**
   - スコアを0-100の範囲に正規化
   - 外れ値の処理
   - 重み付けの適用

### エラーハンドリング
1. **データ不整合**
   - 必須フィールドの欠損処理
   - 空のテキストフィールドの処理
   - 不正なデータ形式の検出

2. **キーワード設定エラー**
   - 設定ファイルの検証
   - 重複キーワードの検出
   - 無効な重み値の処理

3. **スコアリングエラー**
   - ゼロ除算の回避
   - 数値オーバーフローの防止
   - 異常値の検出と処理

## 設定ファイル

### scoring_keywords.json
```json
{
  "categories": {
    "mental_health": {
      "keywords": [
        "mental health", "anxiety", "depression", "stress", "well-being",
        "psychological", "cognitive", "behavioral", "emotional"
      ],
      "weight": 1.0,
      "description": "Mental health related technologies"
    },
    "biosensor": {
      "keywords": [
        "biosensor", "wearable", "sensor", "monitoring", "biometric",
        "physiological", "vital signs", "heart rate", "blood pressure"
      ],
      "weight": 0.8,
      "description": "Biosensor and wearable technologies"
    },
    "intervention": {
      "keywords": [
        "intervention", "therapy", "treatment", "modulation", "stimulation",
        "therapeutic", "rehabilitation", "prevention", "management"
      ],
      "weight": 0.9,
      "description": "Intervention and therapy methods"
    },
    "digital_health": {
      "keywords": [
        "digital", "mobile", "app", "software", "algorithm",
        "artificial intelligence", "machine learning", "data analysis"
      ],
      "weight": 0.7,
      "description": "Digital health technologies"
    }
  },
  "scoring_settings": {
    "case_sensitive": false,
    "partial_match": true,
    "exact_match_bonus": 1.2,
    "title_weight": 1.5,
    "abstract_weight": 1.0,
    "min_score_threshold": 10.0
  }
}
```

## ログ機能

### ログレベル
- **DEBUG**: 詳細なスコアリング情報
- **INFO**: スコアリング処理状況
- **WARNING**: 低スコア、部分マッチング
- **ERROR**: スコアリング失敗、設定エラー

### ログ出力
- **ファイル出力**: `logs/relevance_scorer_YYYY-MM-DD.log`
- **統計情報**: 処理件数、平均スコア、カテゴリ別統計

## テスト仕様

### テストデータ
- **高関連性**: 多くのキーワードがマッチ
- **中関連性**: 一部のキーワードがマッチ
- **低関連性**: 少数のキーワードがマッチ
- **無関連性**: キーワードがマッチしない

### テスト実行
```bash
python -m pytest tests/test_relevance_scorer.py -v
```

## 使用例

### 基本的な使用
```python
from relevance_scorer import RelevanceScorer

scorer = RelevanceScorer("scoring_keywords.json")
results = scorer.score_patents("patents.json", "scored_patents.json")
```

### カスタム設定
```python
scorer = RelevanceScorer(
    keywords_file="custom_keywords.json",
    case_sensitive=True,
    partial_match=False
)
```

### 結果の分析
```python
# 高スコア特許の抽出
high_score_patents = [p for p in results if p["overall_score"] > 80]

# カテゴリ別ランキング
mental_health_patents = sorted(
    results, 
    key=lambda x: x["category_scores"]["mental_health"], 
    reverse=True
)
```

## パフォーマンス最適化

### 処理速度
- キーワードインデックス作成
- 並列処理対応
- キャッシュ機能

### メモリ効率
- ストリーミング処理
- バッチ処理
- 不要データの削除

## トラブルシューティング

### よくある問題
1. **スコアが低い**
   - キーワード設定の見直し
   - 部分一致設定の確認
   - 重み付けの調整

2. **処理速度が遅い**
   - キーワード数の削減
   - 並列処理の有効化
   - バッチサイズの調整

3. **結果が期待と異なる**
   - キーワードの確認
   - スコアリングアルゴリズムの検証
   - テストデータでの動作確認

## 将来の拡張
- 機械学習による自動キーワード抽出
- セマンティック分析
- 特許引用関係の考慮
- 時系列分析機能 