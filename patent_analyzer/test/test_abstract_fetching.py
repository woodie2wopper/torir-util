#!/usr/bin/env python3
"""
Test Abstract Fetching - CSVから変換されたJSONを使ってアブストラクト取得をテスト

このスクリプトは以下の流れでテストを実行します：
1. CSVから変換されたJSONファイルを読み込み
2. 各特許IDに対してモックアブストラクト取得を実行
3. 結果を集計してレポートを生成
"""

import json
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AbstractFetchingTester:
    """アブストラクト取得のテストクラス"""
    
    def __init__(self, patents_json_path: str, abstracts_json_path: str, output_dir: str = "test_output"):
        """
        初期化
        
        Args:
            patents_json_path: 特許データJSONファイルパス
            abstracts_json_path: アブストラクトデータJSONファイルパス
            output_dir: 出力ディレクトリ
        """
        self.patents_json_path = patents_json_path
        self.abstracts_json_path = abstracts_json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # テスト結果
        self.results = {
            "test_info": {
                "start_time": None,
                "end_time": None,
                "duration": None,
                "patents_json": patents_json_path,
                "abstracts_json": abstracts_json_path
            },
            "summary": {
                "total_patents": 0,
                "successful_fetches": 0,
                "failed_fetches": 0,
                "success_rate": 0.0
            },
            "patent_results": [],
            "errors": []
        }
    
    def load_patents(self) -> List[Dict[str, Any]]:
        """特許データを読み込み"""
        try:
            with open(self.patents_json_path, 'r', encoding='utf-8') as f:
                patents = json.load(f)
            logger.info(f"Loaded {len(patents)} patents from {self.patents_json_path}")
            return patents
        except Exception as e:
            logger.error(f"Failed to load patents: {e}")
            raise
    
    def fetch_abstract_for_patent(self, patent_id: str) -> Dict[str, Any]:
        """
        単一の特許に対してアブストラクト取得を実行
        
        Args:
            patent_id: 特許ID
            
        Returns:
            dict: アブストラクト取得結果
        """
        try:
            # モックアブストラクト取得スクリプトを実行
            cmd = [
                sys.executable, 
                "test/mock_get_abst_patent.py",
                patent_id,
                self.abstracts_json_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 成功時
                abstract_data = json.loads(result.stdout)
                return {
                    "patent_id": patent_id,
                    "status": "success",
                    "abstract_data": abstract_data,
                    "error": None
                }
            else:
                # 失敗時
                return {
                    "patent_id": patent_id,
                    "status": "failed",
                    "abstract_data": None,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "patent_id": patent_id,
                "status": "timeout",
                "abstract_data": None,
                "error": "Timeout while fetching abstract"
            }
        except Exception as e:
            return {
                "patent_id": patent_id,
                "status": "error",
                "abstract_data": None,
                "error": str(e)
            }
    
    def run_test(self) -> Dict[str, Any]:
        """テストを実行"""
        start_time = datetime.now()
        self.results["test_info"]["start_time"] = start_time.isoformat()
        
        logger.info("Starting abstract fetching test")
        
        try:
            # 特許データを読み込み
            patents = self.load_patents()
            self.results["summary"]["total_patents"] = len(patents)
            
            # 各特許に対してアブストラクト取得を実行
            for i, patent in enumerate(patents, 1):
                patent_id = patent.get("id")
                if not patent_id:
                    logger.warning(f"Patent {i} has no ID, skipping")
                    continue
                
                logger.info(f"Fetching abstract {i}/{len(patents)}: {patent_id}")
                
                # アブストラクト取得
                result = self.fetch_abstract_for_patent(patent_id)
                self.results["patent_results"].append(result)
                
                # 統計更新
                if result["status"] == "success":
                    self.results["summary"]["successful_fetches"] += 1
                else:
                    self.results["summary"]["failed_fetches"] += 1
                    self.results["errors"].append({
                        "patent_id": patent_id,
                        "error": result["error"]
                    })
            
            # 成功率を計算
            total = self.results["summary"]["total_patents"]
            successful = self.results["summary"]["successful_fetches"]
            self.results["summary"]["success_rate"] = (successful / total * 100) if total > 0 else 0
            
            # 終了時間を記録
            end_time = datetime.now()
            self.results["test_info"]["end_time"] = end_time.isoformat()
            self.results["test_info"]["duration"] = str(end_time - start_time)
            
            logger.info(f"Test completed: {successful}/{total} successful ({self.results['summary']['success_rate']:.1f}%)")
            
            return self.results
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.results["errors"].append({"error": str(e)})
            raise
    
    def save_results(self, output_file: str = None) -> str:
        """結果をJSONファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"abstract_fetching_test_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Results saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def display_summary(self):
        """結果サマリーを表示"""
        summary = self.results["summary"]
        test_info = self.results["test_info"]
        
        print("\n" + "="*60)
        print("Abstract Fetching Test Results")
        print("="*60)
        
        print(f"Test Duration: {test_info.get('duration', 'N/A')}")
        print(f"Total Patents: {summary['total_patents']}")
        print(f"Successful Fetches: {summary['successful_fetches']}")
        print(f"Failed Fetches: {summary['failed_fetches']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if self.results["errors"]:
            print(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results["errors"][:5]:  # 最初の5件のみ表示
                if "patent_id" in error:
                    print(f"  - {error['patent_id']}: {error['error']}")
                else:
                    print(f"  - {error['error']}")
        
        # 成功したアブストラクトの例を表示
        successful_results = [r for r in self.results["patent_results"] if r["status"] == "success"]
        if successful_results:
            print(f"\nSample Successful Results:")
            for result in successful_results[:3]:  # 最初の3件のみ表示
                abstract_data = result["abstract_data"]
                print(f"  - {abstract_data['ID']}: {abstract_data.get('Title', 'N/A')}")
                if abstract_data.get('Abstract'):
                    abstract_preview = abstract_data['Abstract'][:100] + "..." if len(abstract_data['Abstract']) > 100 else abstract_data['Abstract']
                    print(f"    Abstract: {abstract_preview}")

def main():
    """メイン関数"""
    if len(sys.argv) < 3:
        print("Usage: python test_abstract_fetching.py <patents_json> <abstracts_json> [output_dir]")
        print("Example: python test_abstract_fetching.py ../data/processed/converted_patents_20250704_174252.json ../data/test_data/sample_abstracts.json")
        sys.exit(1)
    
    patents_json = sys.argv[1]
    abstracts_json = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "test_output"
    
    # ファイルの存在確認
    if not Path(patents_json).exists():
        print(f"Error: Patents JSON file not found: {patents_json}")
        sys.exit(1)
    
    if not Path(abstracts_json).exists():
        print(f"Error: Abstracts JSON file not found: {abstracts_json}")
        sys.exit(1)
    
    # テスト実行
    tester = AbstractFetchingTester(patents_json, abstracts_json, output_dir)
    
    try:
        results = tester.run_test()
        tester.save_results()
        tester.display_summary()
        
        # 終了コード
        success_rate = results["summary"]["success_rate"]
        sys.exit(0 if success_rate >= 80 else 1)  # 80%以上で成功
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 