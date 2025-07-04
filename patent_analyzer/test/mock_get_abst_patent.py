#!/usr/bin/env python3
"""
Mock Abstract Patent Fetcher - テスト用のアブストラクト取得スクリプト

実際のGoogle Patentsアクセスを模擬し、テストデータ（sample_abstracts.json）から
アブストラクトを取得します。本番のget_abst_patent.pyと同じ出力形式を返します。
"""

import json
import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_abstract_from_test_data(patent_id: str, abstracts_file: str) -> dict:
    """
    テストデータからアブストラクトを取得
    
    Args:
        patent_id: 特許ID
        abstracts_file: アブストラクトデータファイルパス
        
    Returns:
        dict: アブストラクト情報（get_abst_patent.pyと同じ形式）
    """
    try:
        # アブストラクトデータを読み込み
        with open(abstracts_file, 'r', encoding='utf-8') as f:
            abstracts = json.load(f)
        
        # 指定された特許IDのデータを取得
        if patent_id in abstracts:
            abstract_data = abstracts[patent_id]
            return {
                "ID": patent_id,
                "Title": abstract_data.get("title"),
                "Abstract": abstract_data.get("abstract"),
                "URL": abstract_data.get("url"),
                "Error": None,
                "ErrorCode": None,
                "ErrorMessage": None,
                "RetryCount": 0,
                "Timestamp": None
            }
        else:
            # 特許IDが見つからない場合
            return {
                "ID": patent_id,
                "Title": None,
                "Abstract": None,
                "URL": None,
                "Error": "NOT_FOUND",
                "ErrorCode": "404",
                "ErrorMessage": f"Patent ID {patent_id} not found in test data",
                "RetryCount": 0,
                "Timestamp": None
            }
            
    except FileNotFoundError:
        logger.error(f"Abstracts file not found: {abstracts_file}")
        return {
            "ID": patent_id,
            "Title": None,
            "Abstract": None,
            "URL": None,
            "Error": "FILE_NOT_FOUND",
            "ErrorCode": "500",
            "ErrorMessage": f"Abstracts file not found: {abstracts_file}",
            "RetryCount": 0,
            "Timestamp": None
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in abstracts file: {e}")
        return {
            "ID": patent_id,
            "Title": None,
            "Abstract": None,
            "URL": None,
            "Error": "INVALID_JSON",
            "ErrorCode": "500",
            "ErrorMessage": f"Invalid JSON in abstracts file: {e}",
            "RetryCount": 0,
            "Timestamp": None
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "ID": patent_id,
            "Title": None,
            "Abstract": None,
            "URL": None,
            "Error": "UNEXPECTED_ERROR",
            "ErrorCode": "500",
            "ErrorMessage": str(e),
            "RetryCount": 0,
            "Timestamp": None
        }

def main():
    """メイン関数"""
    if len(sys.argv) != 3:
        print("Usage: python mock_get_abst_patent.py <patent_id> <abstracts_json_file>")
        print("Example: python mock_get_abst_patent.py US-9254383-B2 ../data/test_data/sample_abstracts.json")
        sys.exit(1)
    
    patent_id = sys.argv[1]
    abstracts_file = sys.argv[2]
    
    logger.info(f"Fetching abstract for patent ID: {patent_id}")
    logger.info(f"Using test data file: {abstracts_file}")
    
    # アブストラクトを取得
    result = get_abstract_from_test_data(patent_id, abstracts_file)
    
    # 結果をJSON形式で出力（get_abst_patent.pyと同じ形式）
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # エラーがある場合は終了コード1を返す
    if result.get("Error"):
        logger.warning(f"Error occurred: {result.get('Error')} - {result.get('ErrorMessage')}")
        sys.exit(1)
    else:
        logger.info(f"Successfully retrieved abstract for {patent_id}")
        sys.exit(0)

if __name__ == "__main__":
    main() 