#!/usr/bin/env python3
"""
Test Orchestrator Integration - オーケストレーターの統合テスト

テストデータを使ってPatent Orchestratorの全体的なワークフローをテストします。
実際のWebアクセスを避けるため、モックコンポーネントを使用します。
"""

import json
import sys
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrchestratorIntegrationTester:
    """オーケストレーター統合テストクラス"""
    
    def __init__(self, test_data_dir: str = "data/test_data", output_dir: str = "test_output"):
        """
        初期化
        
        Args:
            test_data_dir: テストデータディレクトリ
            output_dir: 出力ディレクトリ
        """
        self.test_data_dir = Path(test_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # テスト結果
        self.results = {
            "test_info": {
                "start_time": None,
                "end_time": None,
                "duration": None,
                "test_data_dir": str(test_data_dir),
                "output_dir": str(output_dir)
            },
            "workflow_steps": [],
            "component_results": {},
            "final_results": {},
            "errors": [],
            "warnings": []
        }
        
        # テスト用の一時ディレクトリ
        self.temp_dir = self.output_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def setup_test_environment(self) -> bool:
        """テスト環境のセットアップ"""
        try:
            logger.info("Setting up test environment")
            
            # テスト用のディレクトリ構造を作成
            test_dirs = [
                self.temp_dir / "raw_search_results",
                self.temp_dir / "processed",
                self.temp_dir / "logs"
            ]
            
            for dir_path in test_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # テスト用CSVファイルをコピー
            source_csv = self.test_data_dir / "sample_patents.csv"
            target_csv = self.temp_dir / "raw_search_results" / "gp_search_results.csv"
            
            if source_csv.exists():
                shutil.copy2(source_csv, target_csv)
                logger.info(f"Copied test CSV: {target_csv}")
            else:
                logger.warning(f"Test CSV not found: {source_csv}")
                return False
            
            # テスト用アブストラクトファイルをコピー
            source_abstracts = self.test_data_dir / "sample_abstracts.json"
            target_abstracts = self.temp_dir / "sample_abstracts.json"
            
            if source_abstracts.exists():
                shutil.copy2(source_abstracts, target_abstracts)
                logger.info(f"Copied test abstracts: {target_abstracts}")
            else:
                logger.warning(f"Test abstracts not found: {source_abstracts}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False
    
    def create_test_config(self) -> str:
        """テスト用の設定ファイルを作成"""
        config = {
            "input": {
                "csv_file": str(self.temp_dir / "raw_search_results" / "gp_search_results.csv"),
                "encoding": "utf-8"
            },
            "output": {
                "base_dir": str(self.temp_dir / "processed"),
                "timestamp_format": "%Y%m%d_%H%M%S"
            },
            "components": {
                "csv_to_json_converter": {
                    "enabled": True,
                    "use_jq": False,  # テストではPythonのcsvモジュールを使用
                    "jq_timeout": 30
                },
                "patent_data_fetcher": {
                    "enabled": True,
                    "delay": 0,  # テストでは遅延なし
                    "max_retries": 1,
                    "timeout": 10
                },
                "abstract_integrator": {
                    "enabled": True,
                    "use_jq": True,
                    "jq_timeout": 30,
                    "temp_file_cleanup": True
                },
                "relevance_scorer": {
                    "enabled": True,
                    "keywords_file": str(self.test_data_dir / "scoring_keywords.json")
                }
            },
            "logging": {
                "level": "INFO",
                "file": str(self.temp_dir / "logs" / "orchestrator_test.log"),
                "console": True
            },
            "error_handling": {
                "continue_on_error": True,
                "max_retries": 2,
                "retry_delay": 1,
                "save_partial_results": True
            }
        }
        
        config_file = self.temp_dir / "test_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created test config: {config_file}")
        return str(config_file)
    
    def run_orchestrator_with_mock(self, config_file: str) -> Dict[str, Any]:
        """
        モックコンポーネントを使ってオーケストレーターを実行
        
        Args:
            config_file: 設定ファイルパス
            
        Returns:
            dict: 実行結果
        """
        try:
            # モックモードでオーケストレーターを実行
            cmd = [
                sys.executable,
                "src/patent_orchestrator.py",
                "--input", str(self.temp_dir / "raw_search_results" / "gp_search_results.csv"),
                "--config", config_file,
                "--test-mode",
                "--mock-abstracts", str(self.temp_dir / "sample_abstracts.json")
            ]
            
            logger.info(f"Running orchestrator: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
                cwd=Path.cwd()
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout expired",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def analyze_results(self, orchestrator_result: Dict[str, Any]) -> Dict[str, Any]:
        """実行結果を分析"""
        analysis = {
            "orchestrator_success": orchestrator_result["success"],
            "output_files": [],
            "processed_data": {},
            "errors": []
        }
        
        try:
            # 出力ファイルを確認
            processed_dir = self.temp_dir / "processed"
            if processed_dir.exists():
                for file_path in processed_dir.glob("*.json"):
                    analysis["output_files"].append(str(file_path))
                    
                    # ファイル内容を読み込み
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        analysis["processed_data"][file_path.name] = {
                            "type": "json",
                            "size": len(data) if isinstance(data, list) else 1,
                            "keys": list(data.keys()) if isinstance(data, dict) else None
                        }
                    except Exception as e:
                        analysis["errors"].append(f"Failed to read {file_path}: {e}")
            
            # ログファイルを確認
            log_file = self.temp_dir / "logs" / "orchestrator_test.log"
            if log_file.exists():
                analysis["log_file"] = str(log_file)
            
            # エラー情報を収集
            if not orchestrator_result["success"]:
                analysis["errors"].append(f"Orchestrator failed: {orchestrator_result['stderr']}")
            
        except Exception as e:
            analysis["errors"].append(f"Analysis failed: {e}")
        
        return analysis
    
    def run_test(self) -> Dict[str, Any]:
        """統合テストを実行"""
        start_time = datetime.now()
        self.results["test_info"]["start_time"] = start_time.isoformat()
        
        logger.info("Starting orchestrator integration test")
        
        try:
            # 1. テスト環境のセットアップ
            self.results["workflow_steps"].append({
                "step": "setup_environment",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
            if not self.setup_test_environment():
                raise Exception("Failed to setup test environment")
            
            self.results["workflow_steps"][-1]["status"] = "completed"
            
            # 2. テスト設定ファイルの作成
            self.results["workflow_steps"].append({
                "step": "create_config",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
            config_file = self.create_test_config()
            self.results["workflow_steps"][-1]["status"] = "completed"
            
            # 3. オーケストレーターの実行
            self.results["workflow_steps"].append({
                "step": "run_orchestrator",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
            orchestrator_result = self.run_orchestrator_with_mock(config_file)
            self.results["component_results"]["orchestrator"] = orchestrator_result
            self.results["workflow_steps"][-1]["status"] = "completed"
            
            # 4. 結果の分析
            self.results["workflow_steps"].append({
                "step": "analyze_results",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })
            
            analysis = self.analyze_results(orchestrator_result)
            self.results["final_results"] = analysis
            self.results["workflow_steps"][-1]["status"] = "completed"
            
            # 終了時間を記録
            end_time = datetime.now()
            self.results["test_info"]["end_time"] = end_time.isoformat()
            self.results["test_info"]["duration"] = str(end_time - start_time)
            
            logger.info(f"Integration test completed in {end_time - start_time}")
            
            return self.results
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            self.results["errors"].append({"error": str(e)})
            raise
    
    def save_results(self, output_file: str = None) -> str:
        """結果をJSONファイルに保存"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"orchestrator_integration_test_{timestamp}.json"
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
        test_info = self.results["test_info"]
        final_results = self.results.get("final_results", {})
        
        print("\n" + "="*60)
        print("Orchestrator Integration Test Results")
        print("="*60)
        
        print(f"Test Duration: {test_info.get('duration', 'N/A')}")
        print(f"Orchestrator Success: {final_results.get('orchestrator_success', 'N/A')}")
        print(f"Output Files: {len(final_results.get('output_files', []))}")
        
        if final_results.get("output_files"):
            print(f"\nGenerated Files:")
            for file_path in final_results["output_files"]:
                print(f"  - {Path(file_path).name}")
        
        if final_results.get("processed_data"):
            print(f"\nProcessed Data:")
            for file_name, data_info in final_results["processed_data"].items():
                print(f"  - {file_name}: {data_info['type']}, size={data_info['size']}")
        
        if final_results.get("errors"):
            print(f"\nErrors ({len(final_results['errors'])}):")
            for error in final_results["errors"][:3]:  # 最初の3件のみ表示
                print(f"  - {error}")
        
        # ワークフローステップの状況
        print(f"\nWorkflow Steps:")
        for step in self.results.get("workflow_steps", []):
            status_icon = "✓" if step["status"] == "completed" else "✗"
            print(f"  {status_icon} {step['step']}: {step['status']}")
    
    def cleanup(self):
        """一時ファイルのクリーンアップ"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("Usage: python test_orchestrator_integration.py <test_data_dir> [output_dir]")
        print("Example: python test_orchestrator_integration.py ../data/test_data")
        sys.exit(1)
    
    test_data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "test_output"
    
    # テストデータディレクトリの存在確認
    if not Path(test_data_dir).exists():
        print(f"Error: Test data directory not found: {test_data_dir}")
        sys.exit(1)
    
    # テスト実行
    tester = OrchestratorIntegrationTester(test_data_dir, output_dir)
    
    try:
        results = tester.run_test()
        tester.save_results()
        tester.display_summary()
        
        # 終了コード
        final_results = results.get("final_results", {})
        orchestrator_success = final_results.get("orchestrator_success", False)
        sys.exit(0 if orchestrator_success else 1)
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        sys.exit(1)
    finally:
        # クリーンアップ（テスト結果を保持するため、コメントアウト）
        # tester.cleanup()
        pass

if __name__ == "__main__":
    main() 