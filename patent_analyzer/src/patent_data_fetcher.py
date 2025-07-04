#!/usr/bin/env python3
"""
PatentDataFetcher: JSONファイルから特許データを抽出し、URLリストを準備する
"""

import json
import logging
from typing import List, Dict
from urllib.parse import urlparse


class PatentDataFetcher:
    """JSONファイルから特許データを抽出し、アブストラクト取得用のURLリストを準備する"""
    
    def __init__(self, json_file_path: str):
        """JSONファイルパスを初期化"""
        self.json_file_path = json_file_path
        self.logger = logging.getLogger(__name__)
        
    def extract_patent_data(self) -> List[Dict[str, str]]:
        """JSONから特許データを抽出"""
        try:
            # JSONファイル読み込み
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                patent_data = json.load(f)
            
            self.logger.info(f"Loaded {len(patent_data)} patents from {self.json_file_path}")
            
            # 特許データの抽出とバリデーション
            extracted_data = []
            invalid_count = 0
            
            for patent in patent_data:
                if self._validate_patent_record(patent):
                    extracted_data.append({
                        "ID": patent.get("id"),
                        "URL": patent.get("result_link")
                    })
                else:
                    invalid_count += 1
                    self.logger.warning(f"Invalid patent record: {patent.get('id', 'Unknown')}")
            
            if invalid_count > 0:
                self.logger.warning(f"Skipped {invalid_count} invalid patent records")
            
            self.logger.info(f"Successfully extracted {len(extracted_data)} valid patents")
            return extracted_data
            
        except FileNotFoundError:
            self.logger.error(f"JSON file not found: {self.json_file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during data extraction: {e}")
            raise
    
    def _validate_patent_record(self, patent: Dict) -> bool:
        """特許レコードのバリデーション"""
        # 必須フィールドの確認
        if not patent.get("id") or not patent.get("result_link"):
            return False
        
        # URLバリデーション
        if not self.validate_url(patent.get("result_link")):
            return False
        
        return True
    
    def validate_url(self, url: str) -> bool:
        """URLがGoogle Patentsの有効なURLかチェック"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc == 'patents.google.com' and
                '/patent/' in parsed.path
            )
        except Exception:
            return False


if __name__ == "__main__":
    # テスト用
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python patent_data_fetcher.py <json_file_path>")
        sys.exit(1)
    
    fetcher = PatentDataFetcher(sys.argv[1])
    try:
        data = fetcher.extract_patent_data()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 