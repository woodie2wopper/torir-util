#!/usr/bin/env python3

# 2024-04-21 (c) toriR Lab.
# AppleScriptで選択されたメールを保存されたファイルをnkfでUTF-8に変換する

import os
import sys
import argparse
import subprocess
from datetime import datetime
import re
import glob

def convert_to_utf8(input_file, output_dir):
    """メールファイルをUTF-8に変換し、日付をファイル名に追加する"""
    try:
        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"入力ファイルが見つかりません: {input_file}")

        # 出力ディレクトリの存在確認と作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # ファイル名から日付情報を抽出
        filename = os.path.basename(input_file)
        date_match = re.match(r'(\d{8})_(\d{4})', filename)
        
        if date_match:
            date_str = date_match.group(1)
            time_str = date_match.group(2)
            # 日付を整形
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}_{time_str[:2]}:{time_str[2:]}"
        else:
            # 日付情報がない場合は現在時刻を使用
            formatted_date = datetime.now().strftime("%Y-%m-%d_%H:%M")

        # 新しいファイル名を作成
        new_filename = f"{formatted_date}_{filename}"
        output_path = os.path.join(output_dir, new_filename)

        # nkfコマンドでUTF-8に変換
        result = subprocess.run(['nkf', '-w', input_file], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"nkfコマンドの実行に失敗しました: {result.stderr}")

        # 変換した内容を保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.stdout)

        print(f"変換完了: {output_path}")
        return True

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}", file=sys.stderr)
        return False

def process_directory(input_dir, output_dir):
    """ディレクトリ内のすべてのテキストファイルを処理する"""
    if not os.path.exists(input_dir):
        print(f"入力ディレクトリが見つかりません: {input_dir}", file=sys.stderr)
        return False

    # テキストファイルを検索
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    if not txt_files:
        print(f"テキストファイルが見つかりません: {input_dir}", file=sys.stderr)
        return False

    success_count = 0
    for txt_file in txt_files:
        if convert_to_utf8(txt_file, output_dir):
            success_count += 1

    print(f"\n処理完了: {success_count}/{len(txt_files)} ファイルを変換しました")
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='メールファイルをUTF-8に変換し、日付をファイル名に追加します')
    parser.add_argument('-i', '--input-dir', required=True, help='入力ディレクトリのパス')
    parser.add_argument('-o', '--output-dir', default='./export-mail', help='出力ディレクトリのパス（デフォルト: ./export-mail）')

    args = parser.parse_args()

    if not process_directory(args.input_dir, args.output_dir):
        sys.exit(1)

if __name__ == '__main__':
    main()


