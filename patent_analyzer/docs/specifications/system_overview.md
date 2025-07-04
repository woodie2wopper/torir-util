# PatentInsight Orchestrator システム概要仕様書

## システム概要

### 目的
Google Patentsの特許検索結果を分析し、指定されたキーワードに基づいて関連性をスコアリングする統合システム

### アーキテクチャ
```
CSV Input → Patent Data Fetcher → Abstract Integrator → Relevance Scorer → Final Results
     ↓              ↓                    ↓                    ↓              ↓
Raw Search    Patent URLs        Integrated Data      Scored Patents   Analysis Report
Results       + Abstracts        (CSV + JSON)         + Rankings       + Statistics
```

## コンポーネント構成

### 1. Patent Data Fetcher (`patent_data_fetcher.py`)
- **役割**: Google Patentsから特許アブストラクトを取得
- **入力**: CSV形式の特許検索結果
- **出力**: JSON形式の特許データ（アブストラクト付き）
- **主要機能**: Webスクレイピング、エラーハンドリング、リトライ機能

### 2. Abstract Integrator (`abstract_integrator.py`)
- **役割**: CSV特許データとアブストラクトデータを統合
- **入力**: CSV特許データ + JSONアブストラクトデータ
- **出力**: 統合されたJSON形式データ
- **主要機能**: データマッチング、クリーニング、検証

### 3. Relevance Scorer (`relevance_scorer.py`)
- **役割**: キーワードベースの関連性スコアリング
- **入力**: 統合された特許データ + キーワード設定
- **出力**: スコアリング結果 + ランキング
- **主要機能**: キーワードマッチング、スコア計算、ランキング

### 4. Patent Orchestrator (`patent_orchestrator.py`)
- **役割**: 全体ワークフローの管理と統合
- **入力**: 設定ファイル + 各コンポーネント
- **出力**: 実行結果サマリー + 最終結果
- **主要機能**: ワークフロー制御、エラー管理、ログ記録

## データフロー

### 1. 入力データ
```csv
id,title,assignee,inventor/author,priority date,filing/creation date,publication date,grant date,result link
US-9254383-B2,Devices and methods for monitoring non-invasive vagus nerve stimulation,"ElectroCore, LLC","Bruce J. Simon, Joseph P. Errico",2009-03-20,2013-04-28,2016-02-09,2016-02-09,https://patents.google.com/patent/US9254383B2/en
```

### 2. 中間データ（Patent Data Fetcher出力）
```json
{
  "US-9254383-B2": {
    "title": "Devices and methods for monitoring non-invasive vagus nerve stimulation",
    "abstract": "A system for monitoring non-invasive vagus nerve stimulation...",
    "url": "https://patents.google.com/patent/US9254383B2/en"
  }
}
```

### 3. 統合データ（Abstract Integrator出力）
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

### 4. 最終結果（Relevance Scorer出力）
```json
{
  "patent_id": "US-9254383-B2",
  "overall_score": 85.5,
  "category_scores": {
    "mental_health": 90.0,
    "biosensor": 75.0,
    "intervention": 95.0
  },
  "ranking": 1
}
```

## 設定ファイル

### 主要設定ファイル
1. **`orchestrator_config.json`**: システム全体の設定
2. **`scoring_keywords.json`**: キーワードカテゴリとスコアリング設定
3. **各コンポーネント固有の設定**: 個別の動作パラメータ

### 環境設定
- Python 3.8以上
- 必要なライブラリ: requests, beautifulsoup4, pandas, lxml
- ログディレクトリ: `logs/`
- データディレクトリ: `data/`

## エラーハンドリング

### エラー分類
1. **ネットワークエラー**: 接続失敗、タイムアウト
2. **データエラー**: 形式不正、欠損データ
3. **設定エラー**: 無効な設定ファイル
4. **システムエラー**: メモリ不足、ディスク容量不足

### エラー処理戦略
- **継続処理**: 一部エラーでも処理を継続
- **リトライ機能**: ネットワークエラーの自動リトライ
- **部分結果保存**: エラーが発生しても部分的な結果を保存
- **詳細ログ**: エラーの詳細情報を記録

## パフォーマンス

### 処理能力
- **小規模**: 100件以下（数分）
- **中規模**: 100-1000件（10-30分）
- **大規模**: 1000件以上（30分以上）

### 最適化機能
- **並列処理**: マルチスレッド対応
- **バッチ処理**: メモリ効率の良い処理
- **ストリーミング**: 大規模データの効率的処理

## セキュリティ

### 考慮事項
- **レート制限**: サーバー負荷を考慮した遅延設定
- **User-Agent**: 適切なブラウザ識別子の使用
- **エラーハンドリング**: 機密情報の漏洩防止

## 拡張性

### 将来の拡張案
1. **多言語対応**: 日本語、中国語、韓国語の特許対応
2. **機械学習**: 自動キーワード抽出、セマンティック分析
3. **Web UI**: ブラウザベースの操作インターフェース
4. **API化**: RESTful API エンドポイントの提供
5. **クラウド統合**: AWS、Azure、GCP対応

## テスト戦略

### テストデータ
- **正常ケース**: 4件の特許データ（テスト用）
- **エラーケース**: 無効URL、ネットワークエラー
- **エッジケース**: 空データ、特殊文字

### テスト実行
```bash
# 個別コンポーネントテスト
python -m pytest tests/test_patent_data_fetcher.py
python -m pytest tests/test_abstract_integrator.py
python -m pytest tests/test_relevance_scorer.py
python -m pytest tests/test_patent_orchestrator.py

# 統合テスト
python -m pytest tests/test_integration.py
```

## 運用ガイド

### 基本的な使用手順
1. 設定ファイルの準備
2. 入力CSVファイルの配置
3. システム実行
4. 結果の確認と分析

### トラブルシューティング
- ログファイルの確認
- 設定ファイルの検証
- ネットワーク接続の確認
- リソース使用量の監視

## ライセンス・著作権
- 本システムは研究・教育目的で開発
- Google Patentsの利用規約に準拠
- 適切なクレジット表示が必要 