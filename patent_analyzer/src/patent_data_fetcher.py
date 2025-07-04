#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PatentDataFetcher: JSONファイルから特許データを抽出し、Google Patentsからアブストラクトを取得する
"""

import json
import logging
import time
import subprocess
import sys
from typing import List, Dict, Optional
from urllib.parse import urlparse
from pathlib import Path


class PatentDataFetcher:
    """JSONファイルから特許データを抽出し、Google Patentsからアブストラクトを取得する"""
    
    def __init__(self, json_file_path: str, delay: float = 2.0, max_retries: int = 3, timeout: int = 30, abstracts_dir: str = "data/abstracts"):
        """
        JSONファイルパスを初期化
        
        Args:
            json_file_path: 特許データJSONファイルパス
            delay: リクエスト間の遅延時間（秒）
            max_retries: 最大リトライ回数
            timeout: タイムアウト時間（秒）
            abstracts_dir: アブストラクト個別ファイルの保存ディレクトリ
        """
        self.json_file_path = json_file_path
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.abstracts_dir = Path(abstracts_dir)
        self.abstracts_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def extract_patent_data(self, start_number: int = 1, batch_size: int = None) -> List[Dict[str, str]]:
        """
        JSONから特許データを抽出し、アブストラクトを取得
        Args:
            start_number: 開始インデックス（1始まり）
            batch_size: バッチサイズ（Noneなら全件）
        Returns:
            List[Dict]: 拡張特許データリスト
        """
        try:
            # JSONファイル読み込み
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                patent_data = json.load(f)
            self.logger.info(f"Loaded {len(patent_data)} patents from {self.json_file_path}")
            # 特許データの抽出とバリデーション
            valid_patents = []
            invalid_count = 0
            for patent in patent_data:
                if self._validate_patent_record(patent):
                    valid_patents.append(patent)
                else:
                    invalid_count += 1
                    self.logger.warning(f"Invalid patent record: {patent.get('id', 'Unknown')}")
            if invalid_count > 0:
                self.logger.warning(f"Skipped {invalid_count} invalid patent records")
            # バッチ範囲の決定
            total = len(valid_patents)
            start_idx = max(0, start_number - 1)
            if batch_size is not None:
                end_idx = min(start_idx + batch_size, total)
            else:
                end_idx = total
            batch_patents = valid_patents[start_idx:end_idx]
            enhanced_patents = []
            skipped_count = 0
            processed_count = 0
            print(f"\n--- Processing patents {start_idx+1} to {end_idx} of {total} ---", file=sys.stdout)
            for i, patent in enumerate(batch_patents, start=start_idx+1):
                patent_id = patent.get("id")
                patent_url = patent.get("result_link")
                print(f"Now processing: {patent_id} {patent_url}", file=sys.stdout)
                enhanced_patent = self._fetch_abstract_for_patent(patent)
                enhanced_patents.append(enhanced_patent)
                # スキップされたかどうかをチェック
                if enhanced_patent.get("abstract_source") == "cached_file":
                    skipped_count += 1
                elif enhanced_patent.get("abstract_source") in ["newly_fetched", "error_saved", "timeout_saved", "exception_saved"]:
                    processed_count += 1
                # リクエスト間の遅延（スキップされた場合は短縮）
                if i < end_idx:
                    if enhanced_patent.get("abstract_source") == "cached_file":
                        time.sleep(0.5)
                    else:
                        time.sleep(self.delay)
            print(f"\n--- Summary ---", file=sys.stdout)
            print(f"Processed: {processed_count} patents", file=sys.stdout)
            print(f"Skipped: {skipped_count} patents (already had abstracts)", file=sys.stdout)
            print(f"Total: {len(enhanced_patents)} patents", file=sys.stdout)
            self.logger.info(f"Successfully processed {processed_count} patents, skipped {skipped_count} patents with existing abstracts (batch)")
            return enhanced_patents
        except FileNotFoundError:
            self.logger.error(f"JSON file not found: {self.json_file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during data extraction: {e}")
            raise
    
    def _fetch_abstract_for_patent(self, patent: Dict) -> Dict:
        """
        単一の特許に対してアブストラクトを取得（個別ファイル管理）
        
        Args:
            patent: 特許データ辞書
            
        Returns:
            Dict: アブストラクト情報を含む拡張された特許データ
        """
        patent_id = patent.get("id")
        patent_url = patent.get("result_link")
        
        # 元の特許データをコピー
        enhanced_patent = patent.copy()
        
        # 既存のアブストラクトファイルをチェック
        existing_abstract = self._load_existing_abstract(patent_id)
        if existing_abstract and existing_abstract.get("Abstract") and existing_abstract.get("Abstract").strip():
            print(f"Skipping {patent_id} - abstract file already exists", file=sys.stdout)
            self.logger.info(f"Skipped {patent_id} - abstract file already exists")
            
            # 既存のアブストラクト情報を追加
            enhanced_patent.update({
                "abstract": existing_abstract.get("Abstract"),
                "abstract_title": existing_abstract.get("Title"),
                "abstract_url": existing_abstract.get("URL"),
                "abstract_error": existing_abstract.get("Error"),
                "abstract_retry_count": existing_abstract.get("RetryCount", 0),
                "abstract_source": "cached_file"
            })
            return enhanced_patent
        
        try:
            # get_abst_patent.pyスクリプトを実行してアブストラクトを取得
            cmd = [
                sys.executable,
                "src/get_abst_patent.py",
                "-i",
                patent_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # 成功時：アブストラクトデータを解析
                abstract_data = json.loads(result.stdout)
                
                # 個別ファイルに保存
                self._save_abstract_to_file(patent_id, abstract_data)
                
                # アブストラクト情報を追加
                enhanced_patent.update({
                    "abstract": abstract_data.get("Abstract"),
                    "abstract_title": abstract_data.get("Title"),
                    "abstract_url": abstract_data.get("URL"),
                    "abstract_error": None,
                    "abstract_retry_count": abstract_data.get("RetryCount", 0),
                    "abstract_source": "newly_fetched"
                })
                
                self.logger.debug(f"Successfully fetched and saved abstract for {patent_id}")
                
            else:
                # 失敗時：エラー情報を記録
                error_data = {
                    "Abstract": None,
                    "Title": None,
                    "URL": patent_url,
                    "Error": result.stderr.strip(),
                    "RetryCount": 0
                }
                self._save_abstract_to_file(patent_id, error_data)
                
                enhanced_patent.update({
                    "abstract": None,
                    "abstract_title": None,
                    "abstract_url": None,
                    "abstract_error": result.stderr.strip(),
                    "abstract_retry_count": 0,
                    "abstract_source": "error_saved"
                })
                
                self.logger.warning(f"Failed to fetch abstract for {patent_id}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            error_data = {
                "Abstract": None,
                "Title": None,
                "URL": patent_url,
                "Error": "Timeout while fetching abstract",
                "RetryCount": 0
            }
            self._save_abstract_to_file(patent_id, error_data)
            
            enhanced_patent.update({
                "abstract": None,
                "abstract_title": None,
                "abstract_url": None,
                "abstract_error": "Timeout while fetching abstract",
                "abstract_retry_count": 0,
                "abstract_source": "timeout_saved"
            })
            self.logger.warning(f"Timeout while fetching abstract for {patent_id}")
            
        except Exception as e:
            error_data = {
                "Abstract": None,
                "Title": None,
                "URL": patent_url,
                "Error": str(e),
                "RetryCount": 0
            }
            self._save_abstract_to_file(patent_id, error_data)
            
            enhanced_patent.update({
                "abstract": None,
                "abstract_title": None,
                "abstract_url": None,
                "abstract_error": str(e),
                "abstract_retry_count": 0,
                "abstract_source": "exception_saved"
            })
            self.logger.error(f"Error fetching abstract for {patent_id}: {e}")
        
        return enhanced_patent
    
    def _get_abstract_file_path(self, patent_id: str) -> Path:
        """特許IDに対応するアブストラクトファイルパスを取得"""
        return self.abstracts_dir / f"{patent_id}.json"
    
    def _load_existing_abstract(self, patent_id: str) -> Optional[Dict]:
        """既存のアブストラクトファイルを読み込み"""
        abstract_file = self._get_abstract_file_path(patent_id)
        if abstract_file.exists():
            try:
                with open(abstract_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load existing abstract for {patent_id}: {e}")
        return None
    
    def _save_abstract_to_file(self, patent_id: str, abstract_data: Dict):
        """アブストラクトデータを個別ファイルに保存"""
        abstract_file = self._get_abstract_file_path(patent_id)
        try:
            with open(abstract_file, 'w', encoding='utf-8') as f:
                json.dump(abstract_data, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Saved abstract to {abstract_file}")
        except Exception as e:
            self.logger.error(f"Failed to save abstract for {patent_id}: {e}")
    
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