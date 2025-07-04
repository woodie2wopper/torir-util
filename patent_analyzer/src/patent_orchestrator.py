#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patent Orchestrator - 特許分析システム全体を統合し、ワークフローを管理するメインコンポーネント

jqベースのAbstract Integratorを含む各コンポーネントの実行順序とデータ連携を管理します。
"""

import json
import logging
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import math

# ローカルモジュールのインポート
from patent_data_fetcher import PatentDataFetcher
from abstract_integrator import AbstractIntegrator
from relevance_scorer import RelevanceScorer

class PatentOrchestrator:
    """特許分析システム全体のオーケストレーター"""
    
    def __init__(self, config_file: Optional[str] = None, test_mode: bool = False, mock_abstracts_file: Optional[str] = None, scoring_keywords_file: Optional[str] = None, **kwargs):
        """
        PatentOrchestratorの初期化
        
        Args:
            config_file: 設定ファイルパス
            test_mode: テストモードフラグ
            mock_abstracts_file: モックアブストラクトファイルパス（テストモード時）
            scoring_keywords_file: スコアリングキーワードファイルパス
            **kwargs: 追加の設定オプション
        """
        self.test_mode = test_mode
        self.mock_abstracts_file = mock_abstracts_file
        self.scoring_keywords_file = scoring_keywords_file
        self.config = self._load_config(config_file, **kwargs)
        self.logger = self._setup_logging()
        self.results = {
            "execution_summary": {
                "start_time": None,
                "end_time": None,
                "total_duration": None,
                "status": "not_started"
            },
            "component_results": {},
            "final_results": {},
            "error_log": [],
            "warnings": []
        }
        
        # 出力ディレクトリの作成
        self._create_output_directories()
    
    def _load_config(self, config_file: Optional[str], **kwargs) -> Dict:
        """設定ファイルの読み込みとデフォルト値の設定"""
        default_config = {
            "input": {
                "csv_file": "data/raw_search_results/gp_search_results.csv",
                "encoding": "utf-8"
            },
            "output": {
                "base_dir": "data/processed",
                "timestamp_format": "%Y%m%d_%H%M%S"
            },
            "components": {
                "csv_to_json_converter": {
                    "enabled": True,
                    "use_jq": True,
                    "jq_timeout": 30
                },
                "patent_data_fetcher": {
                    "enabled": True,
                    "delay": 2,
                    "max_retries": 3,
                    "timeout": 30
                },
                "abstract_integrator": {
                    "enabled": True,
                    "use_jq": True,
                    "jq_timeout": 30,
                    "temp_file_cleanup": True
                },
                "relevance_scorer": {
                    "enabled": True,
                    "keywords_file": "config/scoring_keywords.json"
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/orchestrator.log",
                "console": True
            },
            "error_handling": {
                "continue_on_error": False,  # デフォルトでFalseに変更
                "max_retries": 3,
                "retry_delay": 5,
                "save_partial_results": True
            }
        }
        
        # 設定ファイルから読み込み
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                default_config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        # コマンドライン引数で上書き
        for key, value in kwargs.items():
            if key in default_config:
                default_config[key].update(value)
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config["logging"]["level"]))
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # ファイルハンドラー
        if self.config["logging"]["file"]:
            log_file = Path(self.config["logging"]["file"])
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # コンソールハンドラー
        if self.config["logging"]["console"]:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _create_output_directories(self):
        """出力ディレクトリの作成"""
        output_dir = Path(self.config["output"]["base_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ログディレクトリ
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    def _get_timestamped_filename(self, base_name: str, extension: str = "json") -> str:
        """タイムスタンプ付きファイル名の生成"""
        timestamp = datetime.now().strftime(self.config["output"]["timestamp_format"])
        return f"{base_name}_{timestamp}.{extension}"
    
    def _convert_csv_to_json(self, csv_file: str, output_file: str) -> bool:
        """
        CSVファイルをPythonのcsvモジュールを使用してJSONに変換
        
        Args:
            csv_file: 入力CSVファイルパス
            output_file: 出力JSONファイルパス
            
        Returns:
            bool: 成功時True、失敗時False
        """
        try:
            import csv
            
            self.logger.info(f"Converting CSV to JSON: {csv_file}")
            
            # CSVファイルを読み込み
            patents = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                # 先頭行がカラム名でない場合を自動スキップ
                first_line = f.readline()
                if not first_line.lower().startswith('id,'):
                    # 2行目以降にカラム名がある場合
                    header_line = f.readline()
                else:
                    header_line = first_line
                # DictReaderをカラム名行から開始
                reader = csv.DictReader(f, fieldnames=[h.strip() for h in header_line.strip().split(',')])
                for row in reader:
                    # 空行やidが空の行はスキップ
                    if not row.get("id") or row["id"] == "id":
                        continue
                    patents.append({
                        "id": row["id"],
                        "title": row["title"],
                        "assignee": row["assignee"],
                        "inventors": row["inventor/author"],
                        "priority_date": row["priority date"],
                        "filing_date": row["filing/creation date"],
                        "publication_date": row["publication date"],
                        "grant_date": row["grant date"],
                        "result_link": row["result link"]
                    })
            
            # JSONファイルに保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(patents, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"CSV to JSON conversion completed: {output_file}")
            return True
                
        except Exception as e:
            self.logger.error(f"CSV to JSON conversion error: {e}")
            return False
    
    def run_workflow(self) -> Dict:
        """メインワークフローの実行"""
        start_time = datetime.now()
        self.results["execution_summary"]["start_time"] = start_time.isoformat()
        self.results["execution_summary"]["status"] = "running"
        
        self.logger.info("Starting PatentInsight Orchestrator workflow")
        
        try:
            # ステップ1: CSVからJSONに変換
            if self.config["components"]["csv_to_json_converter"]["enabled"]:
                self._run_csv_to_json_converter()
                result = self.results["component_results"]["csv_to_json_converter"]
                if result["status"] != "completed":
                    raise Exception(f"CSV to JSON Converter failed: {result.get('error')}")
            
            # ステップ2: Patent Data Fetcher
            if self.config["components"]["patent_data_fetcher"]["enabled"]:
                self._run_patent_data_fetcher()
                result = self.results["component_results"]["patent_data_fetcher"]
                if result["status"] != "completed":
                    raise Exception(f"Patent Data Fetcher failed: {result.get('error')}")
            
            # ステップ3: Abstract Integrator (jqベース)
            if self.config["components"]["abstract_integrator"]["enabled"]:
                self._run_abstract_integrator()
                result = self.results["component_results"]["abstract_integrator"]
                if result["status"] != "completed":
                    raise Exception(f"Abstract Integrator failed: {result.get('error')}")
            
            # ステップ4: Relevance Scorer
            if self.config["components"]["relevance_scorer"]["enabled"]:
                self._run_relevance_scorer()
                result = self.results["component_results"]["relevance_scorer"]
                if result["status"] != "completed":
                    raise Exception(f"Relevance Scorer failed: {result.get('error')}")
            
            # 最終結果の生成
            self._generate_final_results()
            
            # 成功時の結果更新
            end_time = datetime.now()
            self.results["execution_summary"].update({
                "end_time": end_time.isoformat(),
                "total_duration": str(end_time - start_time),
                "status": "completed"
            })
            
            self.logger.info("PatentInsight Orchestrator workflow completed successfully")
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            self.results["execution_summary"]["status"] = "failed"
            self.results["error_log"].append(str(e))
            raise  # ここで必ず例外を再送出して即座に停止
        
        return self.results
    
    def test_csv_to_json_converter(self) -> bool:
        """CSV to JSON Converterの個別テスト"""
        self.logger.info("Testing CSV to JSON Converter")
        try:
            self._run_csv_to_json_converter()
            result = self.results["component_results"]["csv_to_json_converter"]
            if result["status"] == "completed":
                self.logger.info("✓ CSV to JSON Converter test passed")
                return True
            else:
                self.logger.error("✗ CSV to JSON Converter test failed")
                return False
        except Exception as e:
            self.logger.error(f"✗ CSV to JSON Converter test failed: {e}")
            return False
    
    def test_patent_data_fetcher(self) -> bool:
        """Patent Data Fetcherの個別テスト"""
        self.logger.info("Testing Patent Data Fetcher")
        try:
            # まずCSV to JSON converterを実行
            if not self.test_csv_to_json_converter():
                return False
            
            self._run_patent_data_fetcher()
            result = self.results["component_results"]["patent_data_fetcher"]
            if result["status"] == "completed":
                self.logger.info("✓ Patent Data Fetcher test passed")
                return True
            else:
                self.logger.error("✗ Patent Data Fetcher test failed")
                return False
        except Exception as e:
            self.logger.error(f"✗ Patent Data Fetcher test failed: {e}")
            return False
    
    def test_abstract_integrator(self) -> bool:
        """Abstract Integratorの個別テスト"""
        self.logger.info("Testing Abstract Integrator")
        try:
            self._run_abstract_integrator()
            result = self.results["component_results"]["abstract_integrator"]
            if result["status"] == "completed":
                self.logger.info("✓ Abstract Integrator test passed")
                return True
            else:
                self.logger.error("✗ Abstract Integrator test failed")
                return False
        except Exception as e:
            self.logger.error(f"✗ Abstract Integrator test failed: {e}")
            return False
    
    def test_relevance_scorer(self) -> bool:
        """Relevance Scorerの個別テスト"""
        self.logger.info("Testing Relevance Scorer")
        try:
            # まずAbstract Integratorを実行
            if not self.test_abstract_integrator():
                return False
            
            self._run_relevance_scorer()
            result = self.results["component_results"]["relevance_scorer"]
            if result["status"] == "completed":
                self.logger.info("✓ Relevance Scorer test passed")
                return True
            else:
                self.logger.error("✗ Relevance Scorer test failed")
                return False
        except Exception as e:
            self.logger.error(f"✗ Relevance Scorer test failed: {e}")
            return False
    
    def _run_csv_to_json_converter(self):
        """CSVからJSONへの変換"""
        self.logger.info("Running CSV to JSON Converter")
        
        try:
            # 入力ファイルの確認
            csv_file = self.config["input"]["csv_file"]
            if not Path(csv_file).exists():
                raise FileNotFoundError(f"Input CSV file not found: {csv_file}")
            
            # 出力ファイルパス
            output_file = self._get_timestamped_filename("converted_patents")
            output_path = Path(self.config["output"]["base_dir"]) / output_file
            
            # CSVからJSONに変換
            if self._convert_csv_to_json(csv_file, str(output_path)):
                # 結果の記録
                self.results["component_results"]["csv_to_json_converter"] = {
                    "status": "completed",
                    "input_file": csv_file,
                    "output_file": str(output_path)
                }
                
                self.logger.info(f"CSV to JSON conversion completed: {output_path}")
            else:
                raise Exception("CSV to JSON conversion failed")
            
        except Exception as e:
            self.logger.error(f"CSV to JSON converter failed: {e}")
            self.results["component_results"]["csv_to_json_converter"] = {
                "status": "failed",
                "error": str(e)
            }
            if not self.config["error_handling"]["continue_on_error"]:
                raise
    
    def _run_patent_data_fetcher(self):
        """Patent Data Fetcherの実行"""
        self.logger.info("Running Patent Data Fetcher")
        
        try:
            # CSV to JSON converterの結果を確認
            converter_result = self.results["component_results"].get("csv_to_json_converter", {})
            if converter_result.get("status") != "completed":
                raise Exception("CSV to JSON converter must complete successfully before Patent Data Fetcher")
            
            json_file = converter_result["output_file"]
            if not Path(json_file).exists():
                raise FileNotFoundError(f"Converted JSON file not found: {json_file}")
            
            # 追加: skip_abstract_fetch オプション対応
            if getattr(self, 'skip_abstract_fetch', False):
                self.logger.info("Skipping abstract fetching as per --skip_abstract_fetch option")
                # JSONファイルの特許データを読み込み、abstract等を空で埋める
                with open(json_file, 'r', encoding='utf-8') as f:
                    patent_data = json.load(f)
                for p in patent_data:
                    p["abstract"] = None
                    p["abstract_title"] = None
                    p["abstract_url"] = None
                    p["abstract_error"] = "Skipped by --skip_abstract_fetch"
                    p["abstract_retry_count"] = 0
                    p["abstract_source"] = "skipped"
            elif self.test_mode and self.mock_abstracts_file:
                self.logger.info("Using mock abstract fetching for test mode")
                patent_data = self._fetch_abstracts_with_mock(json_file)
            else:
                fetcher = PatentDataFetcher(json_file, abstracts_dir="data/abstracts")
                start_number = getattr(self, 'start_number', 1)
                batch_size = getattr(self, 'batch_size', None)
                patent_data = fetcher.extract_patent_data(start_number=start_number, batch_size=batch_size)
            
            # 結果の保存
            output_file = self._get_timestamped_filename("patents_with_abstracts")
            output_path = Path(self.config["output"]["base_dir"]) / output_file
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(patent_data, f, indent=2, ensure_ascii=False)
            
            # 結果の記録
            self.results["component_results"]["patent_data_fetcher"] = {
                "status": "completed",
                "processed_count": len(patent_data),
                "success_count": len(patent_data),
                "error_count": 0,
                "output_file": str(output_path)
            }
            
            self.logger.info(f"Patent Data Fetcher completed: {len(patent_data)} patents processed")
            
        except Exception as e:
            self.logger.error(f"Patent Data Fetcher failed: {e}")
            self.results["component_results"]["patent_data_fetcher"] = {
                "status": "failed",
                "error": str(e)
            }
            if not self.config["error_handling"]["continue_on_error"]:
                raise
    
    def _fetch_abstracts_with_mock(self, json_file: str) -> List[Dict]:
        """
        テストモード用のモックアブストラクト取得
        
        Args:
            json_file: 特許データJSONファイルパス
            
        Returns:
            List[Dict]: アブストラクト付き特許データ
        """
        try:
            import subprocess
            
            # 特許データを読み込み
            with open(json_file, 'r', encoding='utf-8') as f:
                patents = json.load(f)
            
            # モックアブストラクトデータを読み込み
            with open(self.mock_abstracts_file, 'r', encoding='utf-8') as f:
                mock_abstracts = json.load(f)
            
            # 各特許に対してモックアブストラクト取得を実行
            enhanced_patents = []
            for patent in patents:
                patent_id = patent.get("id")
                
                # モックアブストラクト取得スクリプトを実行
                cmd = [
                    sys.executable,
                    "test/mock_get_abst_patent.py",
                    patent_id,
                    self.mock_abstracts_file
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
                    enhanced_patent = patent.copy()
                    enhanced_patent.update({
                        "abstract": abstract_data.get("Abstract"),
                        "abstract_title": abstract_data.get("Title"),
                        "abstract_url": abstract_data.get("URL"),
                        "abstract_error": None
                    })
                else:
                    # 失敗時
                    enhanced_patent = patent.copy()
                    enhanced_patent.update({
                        "abstract": None,
                        "abstract_title": None,
                        "abstract_url": None,
                        "abstract_error": result.stderr
                    })
                
                enhanced_patents.append(enhanced_patent)
            
            self.logger.info(f"Mock abstract fetching completed: {len(enhanced_patents)} patents processed")
            return enhanced_patents
            
        except Exception as e:
            self.logger.error(f"Mock abstract fetching failed: {e}")
            raise
    
    def _run_abstract_integrator(self):
        """Abstract Integrator (jqベース) の実行"""
        self.logger.info("Running Abstract Integrator (jq-based)")
        
        try:
            # 入力ファイルの確認
            csv_file = self.config["input"]["csv_file"]
            abstracts_dir = "data/abstracts"  # 個別ファイル管理のディレクトリ
            
            if not Path(csv_file).exists():
                raise FileNotFoundError(f"Input CSV file not found: {csv_file}")
            if not Path(abstracts_dir).exists():
                self.logger.warning(f"Abstracts directory not found: {abstracts_dir}, creating...")
                Path(abstracts_dir).mkdir(parents=True, exist_ok=True)
            
            # Abstract Integratorの実行
            integrator = AbstractIntegrator(self.config["components"]["abstract_integrator"])
            output_file = self._get_timestamped_filename("integrated_patents")
            output_path = Path(self.config["output"]["base_dir"]) / output_file
            
            result = integrator.process(csv_file, abstracts_dir, str(output_path))
            
            # 結果の記録
            self.results["component_results"]["abstract_integrator"] = {
                "status": result["status"],
                "processed_count": result["processed_count"],
                "matched_count": result["matched_count"],
                "unmatched_count": result["unmatched_count"],
                "error_count": result["error_count"],
                "output_file": str(output_path),
                "errors": result["errors"]
            }
            
            if result["status"] == "completed":
                self.logger.info(f"Abstract Integrator completed: {result['processed_count']} patents integrated")
            else:
                self.logger.error(f"Abstract Integrator failed: {result['errors']}")
                if not self.config["error_handling"]["continue_on_error"]:
                    raise Exception(f"Abstract Integrator failed: {result['errors']}")
            
        except Exception as e:
            self.logger.error(f"Abstract Integrator failed: {e}")
            self.results["component_results"]["abstract_integrator"] = {
                "status": "failed",
                "error": str(e)
            }
            if not self.config["error_handling"]["continue_on_error"]:
                raise
    
    def _run_relevance_scorer(self):
        """Relevance Scorerの実行"""
        self.logger.info("Running Relevance Scorer")
        
        try:
            # 入力ファイルの確認（Abstract Integratorの出力）
            abstract_integrator_result = self.results["component_results"].get("abstract_integrator", {})
            if abstract_integrator_result.get("status") != "completed":
                raise Exception("Abstract Integrator must complete successfully before Relevance Scorer")
            
            input_file = abstract_integrator_result["output_file"]
            if not Path(input_file).exists():
                raise FileNotFoundError(f"Integrated patents file not found: {input_file}")
            
            # Relevance Scorerの実行
            keywords_file = self.scoring_keywords_file or self.config["components"]["relevance_scorer"]["keywords_file"]
            scorer = RelevanceScorer(keywords_file)
            
            with open(input_file, 'r', encoding='utf-8') as f:
                patent_data = json.load(f)
            
            scored_data = scorer.calculate_relevance_scores(patent_data)
            
            # 結果の保存（元の順序）
            output_file = self._get_timestamped_filename("scored_patents")
            output_path = Path(self.config["output"]["base_dir"]) / output_file
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(scored_data, f, indent=2, ensure_ascii=False)
            
            # スコア順にソートしたデータの作成と保存
            # NaNスコアを除外してソート
            valid_scored_data = [p for p in scored_data if not (isinstance(p.get("relevance_score"), float) and math.isnan(p.get("relevance_score")))]
            sorted_scored_data = sorted(valid_scored_data, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # ソート済みファイルの保存
            sorted_output_file = self._get_timestamped_filename("scored_patents_sorted")
            sorted_output_path = Path(self.config["output"]["base_dir"]) / sorted_output_file
            
            with open(sorted_output_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_scored_data, f, indent=2, ensure_ascii=False)
            
            # 結果の記録
            self.results["component_results"]["relevance_scorer"] = {
                "status": "completed",
                "processed_count": len(scored_data),
                "scored_count": len(scored_data),
                "valid_scored_count": len(valid_scored_data),
                "output_file": str(output_path),
                "sorted_output_file": str(sorted_output_path)
            }
            
            self.logger.info(f"Relevance Scorer completed: {len(scored_data)} patents scored")
            self.logger.info(f"Sorted output saved to: {sorted_output_path}")
            
        except Exception as e:
            self.logger.error(f"Relevance Scorer failed: {e}")
            self.results["component_results"]["relevance_scorer"] = {
                "status": "failed",
                "error": str(e)
            }
            if not self.config["error_handling"]["continue_on_error"]:
                raise
    
    def _generate_final_results(self):
        """最終結果の生成"""
        try:
            scorer_result = self.results["component_results"].get("relevance_scorer", {})
            if scorer_result.get("status") != "completed":
                return
            output_file = scorer_result["output_file"]
            with open(output_file, 'r', encoding='utf-8') as f:
                scored_data = json.load(f)
            # NaNを除外したスコアリスト
            valid_scored = [p for p in scored_data if not (isinstance(p.get("relevance_score"), float) and math.isnan(p.get("relevance_score")))]
            nan_count = len(scored_data) - len(valid_scored)
            total_patents = len(scored_data)
            high_relevance = sum(1 for p in valid_scored if p.get("relevance_score", 0) >= 30)
            medium_relevance = sum(1 for p in valid_scored if 10 <= p.get("relevance_score", 0) < 30)
            low_relevance = sum(1 for p in valid_scored if p.get("relevance_score", 0) < 10)
            # 上位特許の抽出（NaN除外）
            top_patents = sorted(valid_scored, key=lambda x: x.get("relevance_score", 0), reverse=True)[:10]
            self.results["final_results"] = {
                "total_patents": total_patents,
                "high_relevance_count": high_relevance,
                "medium_relevance_count": medium_relevance,
                "low_relevance_count": low_relevance,
                "nan_score_count": nan_count,
                "top_patents": [
                    {
                        "patent_id": p.get("id"),
                        "title": p.get("title"),
                        "relevance_score": p.get("relevance_score", 0),
                        "ranking": i + 1,
                        "abstract": p.get("abstract"),
                        "abstract_title": p.get("abstract_title"),
                        "abstract_url": p.get("abstract_url")
                    }
                    for i, p in enumerate(top_patents)
                ]
            }
            self.logger.info(f"Final results generated: {total_patents} patents analyzed")
        except Exception as e:
            self.logger.error(f"Failed to generate final results: {e}")
    
    def save_results(self, output_file: Optional[str] = None):
        """結果をJSONファイルに保存"""
        if output_file is None:
            output_file = self._get_timestamped_filename("orchestrator_results")
            output_path = Path(self.config["output"]["base_dir"]) / output_file
        else:
            output_path = Path(output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            raise
    
    def create_sorted_scored_file(self, input_file: str, output_file: Optional[str] = None) -> str:
        """既存のスコアリング結果ファイルからスコア順にソートしたファイルを生成"""
        try:
            # 入力ファイルの読み込み
            with open(input_file, 'r', encoding='utf-8') as f:
                scored_data = json.load(f)
            
            # NaNスコアを除外してソート
            valid_scored_data = [p for p in scored_data if not (isinstance(p.get("relevance_score"), float) and math.isnan(p.get("relevance_score")))]
            sorted_scored_data = sorted(valid_scored_data, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # 出力ファイル名の決定
            if output_file is None:
                input_path = Path(input_file)
                output_file = input_path.parent / f"{input_path.stem}_sorted{input_path.suffix}"
            
            # ソート済みファイルの保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_scored_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Sorted scored file created: {output_file}")
            self.logger.info(f"Total patents: {len(scored_data)}, Valid patents: {len(valid_scored_data)}")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create sorted scored file: {e}")
            raise
    
    def display_summary(self):
        """結果サマリーの表示"""
        summary = self.results["execution_summary"]
        final_results = self.results.get("final_results", {})
        
        print("\n" + "="*50)
        print("PatentInsight Orchestrator Results")
        print("="*50)
        
        print(f"Status: {summary['status']}")
        print(f"Duration: {summary.get('total_duration', 'N/A')}")
        
        if final_results:
            print(f"\nTotal Patents Processed: {final_results.get('total_patents', 0)}")
            print(f"High Relevance: {final_results.get('high_relevance_count', 0)}")
            print(f"Medium Relevance: {final_results.get('medium_relevance_count', 0)}")
            print(f"Low Relevance: {final_results.get('low_relevance_count', 0)}")
            print(f"NaN Score: {final_results.get('nan_score_count', 0)}")
            
            print("\nTop 10 Most Relevant Patents:")
            for patent in final_results.get("top_patents", [])[:10]:
                print(f"{patent['ranking']}. {patent['patent_id']} (Score: {patent['relevance_score']})")
                print(f"   {patent['title']}")
                if patent.get('abstract'):
                    # abstractの最初の200文字を表示（長すぎる場合は省略）
                    abstract_preview = patent['abstract'][:200] + "..." if len(patent['abstract']) > 200 else patent['abstract']
                    print(f"   Abstract: {abstract_preview}")
                print()
        
        if self.results["error_log"]:
            print(f"\nErrors: {len(self.results['error_log'])}")
            for error in self.results["error_log"][:5]:  # 最初の5件のみ表示
                print(f"  - {error}")

def main():
    """コマンドライン実行用のメイン関数"""
    parser = argparse.ArgumentParser(description="PatentInsight Orchestrator")
    parser.add_argument("--input", "-i", required=False,
                       help="Input CSV file path")
    parser.add_argument("--config", "-c",
                       help="Configuration file path")
    parser.add_argument("--output", "-o",
                       help="Output directory")
    parser.add_argument("--top-n", type=int, default=10,
                       help="Number of top patents to display")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--test", "-t", choices=["csv-converter", "data-fetcher", "abstract-integrator", "relevance-scorer", "all"],
                       help="Test individual components")
    parser.add_argument("--test-mode", action="store_true",
                       help="Enable test mode with mock components")
    parser.add_argument("--mock-abstracts", type=str,
                       help="Mock abstracts file path for test mode")
    parser.add_argument("--existing-abstracts", type=str,
                       help="Use existing abstracts file instead of fetching new ones")
    parser.add_argument("--start_number", type=int, default=1, help="Start number for batch processing (1-based index)")
    parser.add_argument("--batch_size", type=int, default=None, help="Batch size for batch processing")
    parser.add_argument("--skip_abstract_fetch", action="store_true", help="Skip abstract fetching and proceed with empty abstracts")
    parser.add_argument("--sort-scored-file", type=str, help="Create sorted version of existing scored patents file")
    parser.add_argument("--scoring-keywords", type=str, help="Scoring keywords JSON file (evaluation keywords)")
    
    args = parser.parse_args()
    
    # 設定の準備
    config_overrides = {}
    if args.input:
        config_overrides["input"] = {"csv_file": args.input}
    
    if args.output:
        config_overrides["output"] = {"base_dir": args.output}
    
    if args.verbose:
        config_overrides["logging"] = {"level": "DEBUG"}
    
    # オーケストレーターの実行
    orchestrator = PatentOrchestrator(
        args.config, 
        test_mode=args.test_mode,
        mock_abstracts_file=args.mock_abstracts,
        scoring_keywords_file=args.scoring_keywords,
        **config_overrides
    )
    # PatentDataFetcher用のバッチ処理パラメータをorchestratorにセット
    orchestrator.start_number = args.start_number
    orchestrator.batch_size = args.batch_size
    orchestrator.skip_abstract_fetch = args.skip_abstract_fetch
    
    try:
        if args.sort_scored_file:
            # 既存のスコアリング結果ファイルをソート
            output_file = orchestrator.create_sorted_scored_file(args.sort_scored_file)
            print(f"Sorted file created: {output_file}")
            sys.exit(0)
        elif args.test:
            # 個別コンポーネントのテスト
            success = False
            if args.test == "csv-converter":
                success = orchestrator.test_csv_to_json_converter()
            elif args.test == "data-fetcher":
                success = orchestrator.test_patent_data_fetcher()
            elif args.test == "abstract-integrator":
                success = orchestrator.test_abstract_integrator()
            elif args.test == "relevance-scorer":
                success = orchestrator.test_relevance_scorer()
            elif args.test == "all":
                success = orchestrator.test_relevance_scorer()  # 依存関係を含む全テスト
            
            sys.exit(0 if success else 1)
        else:
            # 通常のワークフロー実行
            if not args.input:
                print("Error: --input/-i argument is required for workflow execution")
                sys.exit(1)
            results = orchestrator.run_workflow()
            orchestrator.save_results()
            orchestrator.display_summary()
            
            # 終了コード
            sys.exit(0 if results["execution_summary"]["status"] == "completed" else 1)
        
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Workflow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 