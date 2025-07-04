#!/usr/bin/env python3
"""
RelevanceScorer: アブストラクトが統合された特許データに対し、キーワードベースの関連性スコアを計算する
"""

import json
import logging
import re
from typing import List, Dict


class RelevanceScorer:
    """キーワードベースの関連性スコアリング"""
    
    def __init__(self, config_path: str = "patent_analyzer/config/scoring_keywords.json"):
        """キーワード設定ファイルを読み込み"""
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.keywords_config = self.load_keywords_config()
        
    def load_keywords_config(self) -> Dict:
        """キーワード設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Loaded keywords configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Keywords config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in keywords config: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading keywords config: {e}")
            raise
    
    def calculate_relevance_scores(self, patent_data: List[Dict]) -> List[Dict]:
        """関連性スコアを計算"""
        self.logger.info(f"Calculating relevance scores for {len(patent_data)} patents")
        
        scored_data = []
        for patent in patent_data:
            score = self._calculate_patent_score(patent)
            scored_patent = patent.copy()
            scored_patent["relevance_score"] = score
            scored_data.append(scored_patent)
        
        # スコア降順でソート
        scored_data.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        self.logger.info(f"Relevance scoring completed for {len(scored_data)} patents")
        return scored_data
    
    def _calculate_patent_score(self, patent: Dict) -> int:
        """個別特許のスコアを計算"""
        # タイトルとアブストラクトを結合
        title = patent.get("title", "") or ""
        abstract = patent.get("abstract", "") or ""
        
        # テキストを結合して小文字に変換
        combined_text = f"{title} {abstract}".lower()
        
        total_score = 0
        matched_keywords = []
        
        # 各カテゴリのキーワードをチェック
        for category in self.keywords_config.get("keyword_categories", []):
            category_name = category.get("name", "Unknown")
            category_score = category.get("score", 0)
            keywords = category.get("keywords", [])
            
            category_matches = 0
            for keyword in keywords:
                # キーワードの出現回数をカウント（大文字小文字を区別しない）
                pattern = re.compile(re.escape(keyword.lower()), re.IGNORECASE)
                matches = len(pattern.findall(combined_text))
                
                if matches > 0:
                    category_matches += 1
                    matched_keywords.append(f"{keyword} ({category_name})")
            
            # カテゴリのスコアを加算（同一キーワードの複数出現は1回としてカウント）
            category_total = category_matches * category_score
            total_score += category_total
            
            if category_matches > 0:
                self.logger.debug(f"Category '{category_name}': {category_matches} keywords matched, score: {category_total}")
        
        if matched_keywords:
            self.logger.debug(f"Patent {patent.get('id', 'Unknown')}: matched keywords: {', '.join(matched_keywords)}")
        
        return total_score
    
    def get_score_statistics(self, scored_data: List[Dict]) -> Dict:
        """スコア統計情報を取得"""
        if not scored_data:
            return {}
        
        scores = [patent.get("relevance_score", 0) for patent in scored_data]
        
        return {
            "total_patents": len(scored_data),
            "max_score": max(scores),
            "min_score": min(scores),
            "average_score": sum(scores) / len(scores),
            "zero_score_count": scores.count(0),
            "high_score_count": len([s for s in scores if s >= 20])  # 高スコア（20以上）の件数
        }
    
    def save_scored_data(self, scored_data: List[Dict], output_path: str):
        """スコア付きデータをJSONファイルに保存"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(scored_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Scored data saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save scored data: {e}")
            raise


if __name__ == "__main__":
    # テスト用
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python relevance_scorer.py <patent_data_json_path>")
        sys.exit(1)
    
    scorer = RelevanceScorer()
    
    try:
        # 特許データを読み込み
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            patent_data = json.load(f)
        
        # スコア計算
        scored_data = scorer.calculate_relevance_scores(patent_data)
        
        # 統計情報を表示
        stats = scorer.get_score_statistics(scored_data)
        print("Score Statistics:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # 上位10件を表示
        print("\nTop 10 Most Relevant Patents:")
        for i, patent in enumerate(scored_data[:10], 1):
            print(f"{i}. {patent.get('id', 'Unknown')} (Score: {patent.get('relevance_score', 0)})")
            print(f"   Title: {patent.get('title', 'N/A')}")
            print()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 