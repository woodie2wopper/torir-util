#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoX_dataset.jsonを読み込み、patent_orchestrator.pyを適切な引数で実行するパーサスクリプト
"""
import json
import sys
import subprocess
from pathlib import Path

REQUIRED_KEYS = [
    "search_result_file",
    "scoring_keywords_file",
    "output_dir"
]


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_and_run_dataset.py <NoX_dataset.json> [--skip-abstract-fetch]")
        sys.exit(1)
    
    # アブストラクトスキップオプションの確認
    skip_abstract_fetch = "--skip-abstract-fetch" in sys.argv

    dataset_path = Path(sys.argv[1])
    if not dataset_path.exists():
        print(f"Error: dataset.json not found: {dataset_path}")
        sys.exit(1)

    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # 必須項目チェック
    for key in REQUIRED_KEYS:
        if key not in dataset:
            print(f"Error: Required key '{key}' not found in {dataset_path.name}")
            sys.exit(1)

    # パス解決
    base_dir = dataset_path.parent
    input_csv = str((base_dir / dataset["search_result_file"]).resolve())
    scoring_keywords = str((base_dir / dataset["scoring_keywords_file"]).resolve())
    output_dir = str((base_dir / dataset["output_dir"]).resolve())

    # 出力ディレクトリがなければ作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # patent_orchestrator.pyのパス
    orchestrator_path = Path(__file__).parent / "patent_orchestrator.py"

    # コマンド組み立て
    cmd = [
        sys.executable,
        str(orchestrator_path),
        "--input", input_csv,
        "--output", output_dir,
        "--scoring-keywords", scoring_keywords
    ]
    
    # アブストラクトスキップオプションを追加
    if skip_abstract_fetch:
        cmd.append("--skip_abstract_fetch")

    print("[INFO] Running command:")
    print(" ".join(cmd))

    # 実行
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("[INFO] Workflow completed successfully.")
        else:
            print(f"[ERROR] Workflow failed with exit code {result.returncode}.")
    except Exception as e:
        print(f"[ERROR] Failed to run orchestrator: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 