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

def parse_japanese_date(date_str):
    """日本語の日付文字列を解析する"""
    # 曜日の日本語名を英語に変換する辞書
    weekdays = {
        '月曜日': 'Monday',
        '火曜日': 'Tuesday',
        '水曜日': 'Wednesday',
        '木曜日': 'Thursday',
        '金曜日': 'Friday',
        '土曜日': 'Saturday',
        '日曜日': 'Sunday'
    }
    
    # 曜日を英語に変換
    for jp, en in weekdays.items():
        date_str = date_str.replace(jp, en)
    
    try:
        # 日付を解析
        date_obj = datetime.strptime(date_str, '%Y年%m月%d日 %A %H:%M:%S')
        return date_obj
    except ValueError:
        return None

def convert_to_utf8(input_file, output_dir):
    """メールファイルをUTF-8に変換し、日付をファイル名に追加する"""
    try:
        # 入力ファイルの存在確認
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"入力ファイルが見つかりません: {input_file}")

        # 出力ディレクトリの存在確認と作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # ファイルの内容を読み込み
        with open(input_file, 'rb') as f:
            content = f.read()

        # nkfコマンドでUTF-8に変換
        result = subprocess.run(['nkf', '-w', input_file], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"nkfコマンドの実行に失敗しました: {result.stderr}")

        # ヘッダー情報を抽出
        content_lines = result.stdout.split('\n')
        date_line = next((line for line in content_lines if line.startswith('Date: ')), None)
        subject_line = next((line for line in content_lines if line.startswith('Subject: ')), None)

        # 日付情報を抽出
        if date_line:
            date_str = date_line.replace('Date: ', '').strip()
            date_obj = parse_japanese_date(date_str)
            if date_obj:
                # 日付をYYMMDD_HHMMSS形式で出力
                formatted_date = date_obj.strftime('%y%m%d_%H%M%S')
            else:
                # 日付解析に失敗した場合は現在時刻を使用
                formatted_date = datetime.now().strftime('%y%m%d_%H%M%S')
        else:
            formatted_date = datetime.now().strftime('%y%m%d_%H%M%S')

        # 件名を抽出して整形
        if subject_line:
            subject = subject_line.replace('Subject: ', '').strip()
            # 特殊文字を除去し、スペースをハイフンに置換
            safe_subject = re.sub(r'[\\/*?:"<>|()\[\]{}]', '', subject)  # 括弧類も除去
            safe_subject = safe_subject.replace(' ', '-')
            # 連続するハイフンを1つに
            safe_subject = re.sub(r'-+', '-', safe_subject)
            # 先頭と末尾のハイフンを除去
            safe_subject = safe_subject.strip('-')
            # 20文字に制限
            safe_subject = safe_subject[:20]
        else:
            safe_subject = 'no-subject'

        # 新しいファイル名を作成
        new_filename = f"{formatted_date}_{safe_subject}.txt"
        output_path = os.path.join(output_dir, new_filename)

        # 改行を統一（CRLFをLFに変換）
        content = result.stdout.replace('\r\n', '\n').replace('\r', '\n')

        # 変換した内容を保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

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
    parser.add_argument('-o', '--output-dir', help='出力ディレクトリのパス（デフォルト: 入力ディレクトリ内のexport-mail）')

    args = parser.parse_args()

    # 出力ディレクトリが指定されていない場合は、入力ディレクトリ内に作成
    if args.output_dir is None:
        args.output_dir = os.path.join(args.input_dir, 'export-mail')

    if not process_directory(args.input_dir, args.output_dir):
        sys.exit(1)

if __name__ == '__main__':
    main()


