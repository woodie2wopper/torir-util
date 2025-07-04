# Mail Converter

AppleMailのメールをテキストファイルに変換するツール

## 概要

Mail Converterは、AppleMailのメールをテキストファイルとして保存し、ファイル名に日時と件名を含めるツールです。文字コードをUTF-8に変換して保存します。

## ディレクトリ構成

```
mail_converter/
├── src/                    # ソースコード
│   ├── mail-converter.py   # メインPythonスクリプト
│   └── MailSaver.applescript # AppleScript
├── docs/                   # ドキュメント
│   └── mail-converter.md   # 詳細仕様書
├── data/                   # データディレクトリ
├── logs/                   # ログファイル
└── README.md               # このファイル
```

## 機能

- **メール変換**: AppleMailのメールをテキストファイルに変換
- **ファイル命名**: 日時と件名を含むファイル名で保存
- **文字コード変換**: UTF-8エンコーディングに変換
- **AppleScript連携**: MailSaver.applescriptとの連携

## 使用方法

### 基本的な使用

```bash
# メールコンバーターの実行
python3 mail_converter/src/mail-converter.py
```

### AppleScriptの実行

```bash
# AppleScriptの実行
osascript mail_converter/src/MailSaver.applescript
```

## 入力・出力

### 入力
- AppleMailのメールデータ

### 出力
- テキストファイル（UTF-8エンコーディング）
- ファイル名形式: `YYYY-MM-DD_HHMMSS_件名.txt`

## 詳細仕様書

詳細な仕様については [docs/mail-converter.md](docs/mail-converter.md) を参照してください。

## 依存関係

- Python 3.x
- AppleScript（macOS）
- AppleMail

## ライセンス

このツールは教育・研究目的で作成されています。 