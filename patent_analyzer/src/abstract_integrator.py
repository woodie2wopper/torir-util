#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abstract Integrator - CSV特許データとJSONアブストラクトデータを統合するコンポーネント

jqを使用してCSVからJSONへの変換とアブストラクトデータの統合を行います。
オーケストレーションプログラムから呼び出されることを想定しています。
"""

import json
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class AbstractIntegrator:
    """CSV特許データとJSONアブストラクトデータを統合するクラス"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        AbstractIntegratorの初期化
        
        Args:
            config: 設定辞書（オーケストレーターから渡される）
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # jqの存在確認
        self._check_jq_availability()
    
    def _check_jq_availability(self) -> bool:
        """jqが利用可能かチェック"""
        try:
            result = subprocess.run(['jq', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info(f"jq version: {result.stdout.strip()}")
                return True
            else:
                self.logger.error("jq is not available")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.error("jq command not found. Please install jq.")
            return False
    
    def csv_to_json(self, csv_file: str, output_file: str) -> bool:
        """
        CSVファイルをJSONに変換
        
        Args:
            csv_file: 入力CSVファイルパス
            output_file: 出力JSONファイルパス
            
        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            # jqコマンドでCSVをJSONに変換
            jq_script = '''
            split("\n") | .[1:-1] | map(split(",")) | map({
              "id": .[0],
              "title": .[1],
              "assignee": .[2],
              "inventors": .[3],
              "priority_date": .[4],
              "filing_date": .[5],
              "publication_date": .[6],
              "grant_date": .[7],
              "result_link": .[8]
            })
            '''
            
            cmd = ['jq', '-R', '-s', '-c', jq_script]
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(cmd, input=f.read(), 
                                      capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # 結果をファイルに保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                self.logger.info(f"CSV to JSON conversion completed: {output_file}")
                return True
            else:
                self.logger.error(f"jq conversion failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"CSV to JSON conversion error: {e}")
            return False
    
    def integrate_abstracts(self, patents_file: str, abstracts_dir: str, 
                          output_file: str) -> bool:
        """
        特許データと個別アブストラクトファイルを統合
        
        Args:
            patents_file: 特許データJSONファイルパス
            abstracts_dir: アブストラクト個別ファイルディレクトリパス
            output_file: 出力JSONファイルパス
            
        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            # 特許データを読み込み
            with open(patents_file, 'r', encoding='utf-8') as f:
                patents = json.load(f)
            
            # 個別アブストラクトファイルを読み込み
            abstracts_dir_path = Path(abstracts_dir)
            abstracts = {}
            
            if abstracts_dir_path.exists():
                for abstract_file in abstracts_dir_path.glob("*.json"):
                    patent_id = abstract_file.stem
                    try:
                        with open(abstract_file, 'r', encoding='utf-8') as f:
                            abstract_data = json.load(f)
                        abstracts[patent_id] = abstract_data
                    except Exception as e:
                        self.logger.warning(f"Failed to load abstract file {abstract_file}: {e}")
            
            # 特許データとアブストラクトを統合
            integrated_patents = []
            for patent in patents:
                patent_id = patent.get("id")
                integrated_patent = patent.copy()
                
                if patent_id in abstracts:
                    abstract_data = abstracts[patent_id]
                    integrated_patent.update({
                        "abstract": abstract_data.get("Abstract"),
                        "abstract_title": abstract_data.get("Title"),
                        "abstract_url": abstract_data.get("URL"),
                        "abstract_error": abstract_data.get("Error"),
                        "abstract_retry_count": abstract_data.get("RetryCount", 0),
                        "abstract_source": "integrated_from_file"
                    })
                else:
                    # アブストラクトファイルが存在しない場合
                    integrated_patent.update({
                        "abstract": None,
                        "abstract_title": None,
                        "abstract_url": None,
                        "abstract_error": "Abstract file not found",
                        "abstract_retry_count": 0,
                        "abstract_source": "not_found"
                    })
                
                integrated_patents.append(integrated_patent)
            
            # 結果をファイルに保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(integrated_patents, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Abstract integration completed: {output_file}")
            self.logger.info(f"Loaded {len(abstracts)} abstract files from {abstracts_dir}")
            return True
                
        except Exception as e:
            self.logger.error(f"Abstract integration error: {e}")
            return False
    
    def process(self, csv_file: str, abstracts_dir: str, 
               output_file: str) -> Dict:
        """
        メイン処理：CSV変換とアブストラクト統合を実行
        
        Args:
            csv_file: 入力CSVファイルパス
            abstracts_dir: アブストラクト個別ファイルディレクトリパス
            output_file: 最終出力JSONファイルパス
            
        Returns:
            Dict: 処理結果の辞書
        """
        start_time = datetime.now()
        
        # 一時ファイルパス
        temp_json_file = output_file.replace('.json', '_temp.json')
        
        result = {
            "status": "failed",
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration": None,
            "processed_count": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "error_count": 0,
            "output_file": output_file,
            "errors": []
        }
        
        try:
            # ステップ1: CSVからJSONに変換
            self.logger.info(f"Starting CSV to JSON conversion: {csv_file}")
            if not self.csv_to_json(csv_file, temp_json_file):
                result["errors"].append("CSV to JSON conversion failed")
                return result
            
            # ステップ2: アブストラクト統合
            self.logger.info(f"Starting abstract integration: {abstracts_dir}")
            if not self.integrate_abstracts(temp_json_file, abstracts_dir, output_file):
                result["errors"].append("Abstract integration failed")
                return result
            
            # 統計情報の取得
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    integrated_data = json.load(f)
                
                result["processed_count"] = len(integrated_data)
                result["matched_count"] = sum(1 for item in integrated_data 
                                            if item.get("abstract") is not None)
                result["unmatched_count"] = result["processed_count"] - result["matched_count"]
                
            except Exception as e:
                self.logger.warning(f"Could not calculate statistics: {e}")
            
            # 一時ファイルの削除
            try:
                Path(temp_json_file).unlink()
            except FileNotFoundError:
                pass
            
            # 成功時の結果更新
            end_time = datetime.now()
            result.update({
                "status": "completed",
                "end_time": end_time.isoformat(),
                "duration": str(end_time - start_time)
            })
            
            self.logger.info(f"Abstract integration completed successfully: {result['processed_count']} patents processed")
            
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")
            self.logger.error(f"Unexpected error in abstract integration: {e}")
        
        return result

def main():
    """コマンドライン実行用のメイン関数"""
    if len(sys.argv) != 4:
        print("Usage: abstract_integrator.py <csv_file> <abstracts_file> <output_file>")
        sys.exit(1)
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    csv_file = sys.argv[1]
    abstracts_file = sys.argv[2]
    output_file = sys.argv[3]
    
    # AbstractIntegratorの実行
    integrator = AbstractIntegrator()
    result = integrator.process(csv_file, abstracts_file, output_file)
    
    # 結果の出力
    print(json.dumps(result, indent=2))
    
    # 終了コード
    sys.exit(0 if result["status"] == "completed" else 1)

if __name__ == "__main__":
    main() 