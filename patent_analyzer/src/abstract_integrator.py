#!/usr/bin/env python3
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
    
    def integrate_abstracts(self, patents_file: str, abstracts_file: str, 
                          output_file: str) -> bool:
        """
        特許データとアブストラクトデータを統合
        
        Args:
            patents_file: 特許データJSONファイルパス
            abstracts_file: アブストラクトデータJSONファイルパス
            output_file: 出力JSONファイルパス
            
        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            # jqコマンドでデータ統合
            jq_script = '''
            .[0] as $patents | .[1] as $abstracts | 
            $patents | map(. + {abstract: $abstracts[.id].abstract})
            '''
            
            cmd = ['jq', '-s', jq_script, patents_file, abstracts_file]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # 結果をファイルに保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                self.logger.info(f"Abstract integration completed: {output_file}")
                return True
            else:
                self.logger.error(f"jq integration failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Abstract integration error: {e}")
            return False
    
    def process(self, csv_file: str, abstracts_file: str, 
               output_file: str) -> Dict:
        """
        メイン処理：CSV変換とアブストラクト統合を実行
        
        Args:
            csv_file: 入力CSVファイルパス
            abstracts_file: アブストラクトデータJSONファイルパス
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
            self.logger.info(f"Starting abstract integration: {abstracts_file}")
            if not self.integrate_abstracts(temp_json_file, abstracts_file, output_file):
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