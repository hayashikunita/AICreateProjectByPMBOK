# AICreateProjectByPMBOK

PMBOKに準拠したプロジェクト・ドキュメント（例: プロジェクト憲章、スコープ記述書、WBS、スケジュール概要、リスク登録簿、ステークホルダー登録簿、コミュニケーション計画など）を、ChatGPT(API)で半自動生成するPython CLIツールです。

- 生成形式: テキスト(.txt)／Excel(.xlsx)
- API不要のスタブモードあり（検証・テスト用）
- OpenAIおよびAzure OpenAI互換

## 主なコマンド

- 一覧表示: `list`
- テキスト生成: `txt`
- Excel雛形生成: `excel`
- 初期化: `init`

## セットアップ

1. Python 3.10+ を用意します。
2. 依存をインストールします（下の「Try it」を参照）。
3. `.env` を作成し API キー等を設定します（`.env.example` 参照）。

### .env の例

```
# OpenAI の場合
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=

# Azure OpenAI の場合（どちらか一方を使用）
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# アプリ設定
AICPM_MODEL=gpt-4o-mini
AICPM_USE_STUB=false
AICPM_DEFAULT_LANGUAGE=ja
```

## 使い方

- ドキュメントタイプの一覧
```
python -m pmbok_gpt list
```

- テキストドキュメントを生成
```
python -m pmbok_gpt txt --doc-type project_charter --project-file examples/project_sample.json --out output/project_charter.txt
```

- Excel雛形（リスク登録簿）を生成
```
python -m pmbok_gpt excel --type risk-register --out output/risk_register.xlsx
```

> 注: 初回は `python -m pmbok_gpt init` を実行すると、`.env` のひな型とサンプルプロジェクトJSONを配置します。

## すべてのタイプの実行確認（例）

以下は PowerShell での確認例です。最初にスタブモードをONにして、全てのテキストdoc_typeを生成し、次にExcelの2タイプを生成します。

```
# スタブモードON（API不要）
$env:AICPM_USE_STUB="true"

# プロジェクトJSONは init で作成されたサンプルを使用
# 出力先は output/checks/ 以下に作成
python -m pmbok_gpt txt --doc-type project_charter         --project-file examples/project_sample.json --out output/checks/project_charter.txt
python -m pmbok_gpt txt --doc-type scope_statement         --project-file examples/project_sample.json --out output/checks/scope_statement.txt
python -m pmbok_gpt txt --doc-type wbs_outline             --project-file examples/project_sample.json --out output/checks/wbs_outline.txt
python -m pmbok_gpt txt --doc-type schedule_overview       --project-file examples/project_sample.json --out output/checks/schedule_overview.txt
python -m pmbok_gpt txt --doc-type risk_management_plan    --project-file examples/project_sample.json --out output/checks/risk_management_plan.txt
python -m pmbok_gpt txt --doc-type stakeholder_register    --project-file examples/project_sample.json --out output/checks/stakeholder_register.txt
python -m pmbok_gpt txt --doc-type communication_plan      --project-file examples/project_sample.json --out output/checks/communication_plan.txt
python -m pmbok_gpt txt --doc-type quality_management_plan --project-file examples/project_sample.json --out output/checks/quality_management_plan.txt
python -m pmbok_gpt txt --doc-type procurement_plan        --project-file examples/project_sample.json --out output/checks/procurement_plan.txt
python -m pmbok_gpt txt --doc-type change_management_plan  --project-file examples/project_sample.json --out output/checks/change_management_plan.txt
python -m pmbok_gpt txt --doc-type lessons_learned         --project-file examples/project_sample.json --out output/checks/lessons_learned.txt

# Excelの2タイプ
python -m pmbok_gpt excel --type risk-register        --out output/risk_register.xlsx
python -m pmbok_gpt excel --type stakeholder-register --out output/stakeholder_register.xlsx
```

ヒント:
- 実APIで生成したい場合は `AICPM_USE_STUB=false` にし、OpenAI なら `OPENAI_API_KEY` を設定して同じコマンドを実行してください。
- `python -m pmbok_gpt list` で doc_type の一覧を確認できます。

## ドキュメントの考え方

本ツールは、PMBOKの知識エリアやプロセス群に整合するように、各ドキュメントのセクション構成をテンプレート化し、ChatGPTに与えるプロンプトを自動生成します。PMBOKの原文を複製せず、一般的・汎用的な構成名のみを使用しています。

## 拡張案

- 会社/部門のテンプレートを `templates.py` にカスタム追加
- セクションごとの粒度調整（箇条書き→詳細文章）
- Word/PDF出力（python-docx, reportlab 等）
- プロンプト/出力のバージョン管理

## Try it（開発用）

以下は PowerShell 用の例です。

```
# 依存のインストール
python -m pip install -r requirements.txt

# 初期化（.env とサンプルを作成）
python -m pmbok_gpt init

# スタブでテキスト生成（API不要）
$env:AICPM_USE_STUB="true"; python -m pmbok_gpt txt --doc-type project_charter --project-file examples/project_sample.json --out output/charter_stub.txt

# テスト実行（API不要）
pytest -q
```

## トラブルシューティング

OpenAI を使った生成で出力ができない/ファイルが作成されない場合は、以下を確認してください。

1. 設定の診断
	```powershell
	python -m pmbok_gpt diag
	```
	- provider が `openai` になっているか
	- `openai_api_key_set: True` になっているか（.env または環境変数）
	- model が有効なモデル（例: gpt-4o-mini）か

2. スタブがOFFになっているか
	- `.env` の `AICPM_USE_STUB=false` を確認、または以下で一時的に上書き
	```powershell
	$env:AICPM_USE_STUB="false"
	```

3. OpenAI の API キー設定
	- `.env` に `OPENAI_API_KEY=sk-...` を設定、または一時的に
	```powershell
	$env:OPENAI_API_KEY="<あなたのAPIキー>"
	```
	- 企業プロキシ等で互換エンドポイントを使う場合は `OPENAI_BASE_URL` も設定

4. 「スタブ出力」になってしまう
	- `diag` で `provider: stub` または `use_stub: True` になっているとスタブ出力になります。
	- 対処:
	  ```powershell
	  $env:AICPM_USE_STUB="false"
	  python -m pmbok_gpt diag   # provider: openai / use_stub: False を確認
	  ```

5. APIConnectionError / UnsupportedProtocol が出る
	- 多くの場合、`OPENAI_BASE_URL` が空文字や不正なURL（http/https で始まらない）です。
	- `diag` で `openai_base_url` と `openai_base_url_valid` を確認してください。
	- 対処:
	  - 基本は未設定でOK（デフォルトの https://api.openai.com/v1 を使用）。未設定に戻すには:
		 ```powershell
		 Remove-Item Env:OPENAI_BASE_URL -ErrorAction SilentlyContinue
		 ```
	  - 互換エンドポイントを使う場合は、必ず完全なURLを設定（例）
		 ```powershell
		 $env:OPENAI_BASE_URL="https://api.openai.com/v1"
		 ```

4. 実行例
	```powershell
	$env:AICPM_USE_STUB="false" ; $env:OPENAI_API_KEY="<あなたのAPIキー>"
	python -m pmbok_gpt txt --doc-type project_charter --project-file examples/project_sample.json --out output/project_charter_api.txt
	```

6. エラー内容の確認
	- 失敗時はエラーメッセージが表示されます。`OPENAI_API_KEY` 未設定やモデル権限エラーが代表例です。

### Azure OpenAI を使う場合のチェック
- `.env` または環境変数で以下が必要です。
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`（https:// で始まるURL）
  - `AZURE_OPENAI_API_VERSION`（例: 2024-08-01-preview）
  - `AICPM_MODEL` は「モデル名」ではなく「デプロイ名」を指定
- `diag` で `provider: azure` になっていることを確認してください。

## 免責

- 出力は補助であり、最終責任はプロジェクトマネージャにあります。
- 機密情報は取り扱いに十分ご注意ください。
