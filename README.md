# AICreateProjectByPMBOK

PMBOKに準拠したプロジェクト・ドキュメント（例: プロジェクト憲章、スコープ記述書、WBS、スケジュール概要、リスク登録簿、ステークホルダー登録簿、コミュニケーション計画など）を、ChatGPT(API)で半自動生成するPython CLIツールです。

- 生成形式: テキスト(.txt)／Excel(.xlsx)
- API不要のスタブモードあり（検証・テスト用）
- OpenAIおよびAzure OpenAI互換

## 特長

- PMBOKに整合する一般的なセクション構成を用いたテンプレート内蔵（原文引用はせず汎用的な見出しのみ）
- スタブ出力で検証をスムーズに（APIキーなしで動作確認可能）
- OpenAI/Azure OpenAIの双方に対応（モデル/デプロイ名切替）
- Excel雛形（リスク登録簿、ステークホルダー登録簿）を即利用可能
- CLIでの操作に加え、Pythonから関数呼び出しも可能

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

### ディレクトリ構成（抜粋）

```
AICreateProjectByPMBOK/
├─ pmbok_gpt/
│  ├─ __main__.py            # python -m pmbok_gpt のエントリ
│  ├─ __init__.py
│  ├─ cli.py                 # CLI定義（list/init/txt/excel/diag）
│  ├─ config.py              # 設定（pydantic-settings + dotenv）
│  ├─ providers.py           # Stub / OpenAI / AzureOpenAI
│  ├─ templates.py           # ドキュメントテンプレート定義
│  ├─ generator.py           # テキスト生成ロジック
│  └─ excel.py               # Excel雛形生成
├─ examples/
│  └─ project_sample.json    # サンプルのプロジェクト情報
├─ tests/
│  └─ test_excel.py          # Excel生成の簡易テスト
├─ .env.example
├─ requirements.txt
├─ README.md
└─ main.py                   # 直接起動用（任意）
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

### コマンドリファレンス

- `python -m pmbok_gpt list`
	- 生成対応している doc_type を一覧表示
- `python -m pmbok_gpt init`
	- `.env`（未存在なら作成）と `examples/project_sample.json` を配置
- `python -m pmbok_gpt txt --doc-type <key> --project-file <json> --out <path> [--language <ja|en>] [--note <str>]`
	- 指定テンプレートでテキストドキュメントを生成
- `python -m pmbok_gpt excel --type <risk-register|stakeholder-register> --out <xlsx>`
	- Excelの雛形を作成
- `python -m pmbok_gpt diag`
	- 現在の設定・キー有無・BASE_URL妥当性などを表示

### 対応 doc_type（要約）

- `project_charter`（プロジェクト憲章）
- `scope_statement`（スコープ記述書）
- `wbs_outline`（WBSアウトライン）
- `schedule_overview`（スケジュール概要）
- `risk_management_plan`（リスクマネジメント計画）
- `stakeholder_register`（ステークホルダー登録簿 概要）
- `communication_plan`（コミュニケーション計画）
- `quality_management_plan`（品質マネジメント計画）
- `procurement_plan`（調達マネジメント計画）
- `change_management_plan`（変更管理計画）
- `lessons_learned`（教訓）

### プロジェクト情報JSON（例と項目）

`examples/project_sample.json` の項目はカスタマイズ可能ですが、以下のような構造を推奨します。

```json
{
	"name": "次世代ECサイト刷新プロジェクト",
	"sponsor": "事業本部長",
	"objectives": ["CVRを1.5倍に向上", "検索UX改善とレコメンド導入"],
	"scope": {
		"in": ["フロントUI刷新", "検索/レコメンド機能", "決済ゲートウェイ刷新"],
		"out": ["倉庫WMSの刷新", "コールセンターSaaSの刷新"]
	},
	"constraints": ["8ヶ月以内にリリース", "既存会員DBは維持"],
	"assumptions": ["広告予算は現状維持", "主要サプライヤは継続契約"],
	"milestones": [{"name": "要件定義完了", "target": "2026-01-31"}],
	"budget": {"currency": "JPY", "amount": 120000000},
	"stakeholders": [{"name": "営業部", "interest": "在庫連携の安定"}],
	"risk_seeds": ["要件肥大化による遅延", "外部APIのスループット制限"]
}
```

ポイント:
- `objectives` や `milestones` は箇条書き/配列で記述すると自然な出力になりやすい
- `budget.amount` は数値（整数）・通貨コードは文字列を推奨
- フィールドは増減しても動作します（テンプレート＋プロンプトが柔軟に利用）

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

## Excel雛形の仕様

- リスク登録簿（risk-register）
	- 列: ID / リスク事象 / カテゴリ / 原因 / 影響 / 発生確率 / スコア(影響×確率) / 対応戦略 / 対応計画(要旨) / オーナー / トリガー / 状況 / メモ
	- スコア列は式 `=E{row}*F{row}` を自動設定
	- シート名: `RiskRegister`
- ステークホルダー登録簿（stakeholder-register）
	- 列: ID / 氏名(組織) / 役割 / 関心事 / 影響度(High/Med/Low) / 期待値 / 関与戦略 / コミュニケーション(頻度/媒体) / メモ
	- シート名: `Stakeholders`

## テンプレートの拡張方法

`pmbok_gpt/templates.py` に新しいドキュメントタイプを追加できます。

```python
DOC_TEMPLATES["issue_log"] = {
	"title": "課題ログ",
	"sections": [
		"課題一覧",
		"優先度と影響度",
		"対応方針と期日",
		"エスカレーションルール"
	],
}
```

追加後は以下で生成できます。
```powershell
python -m pmbok_gpt txt --doc-type issue_log --project-file examples/project_sample.json --out output/issue_log.txt
```

## Pythonから直接使う（API）

```python
from pmbok_gpt.generator import generate_text_document

project = {
		"name": "デモ案件",
		"objectives": ["品質向上", "工数削減"],
}

path = generate_text_document(
		doc_type="project_charter",
		project_context=project,
		out_path="output/demo_charter.txt",
)
print("saved:", path)
```

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

## セキュリティ/プライバシー

- 機密情報や個人情報は、プロンプトに含める前に匿名化・要約・伏せ字などのガードを検討してください。
- `.env` はリポジトリにコミットしないでください（APIキー流出防止）。
- 出力ファイル（txt/xlsx）はアクセス権限・保管先のポリシーに従って取り扱ってください。

## よくある質問（FAQ）

- Q: 出力が「【スタブ出力】」になります。
	- A: `python -m pmbok_gpt diag` で `provider: stub` / `use_stub: True` になっていないか確認し、`AICPM_USE_STUB=false` に切り替えてください。
- Q: APIConnectionError や UnsupportedProtocol が出ます。
	- A: `OPENAI_BASE_URL` の設定を確認。未設定に戻すか、`https://...` で始まる完全なURLにしてください。
- Q: Azure OpenAI でモデル名は何を入れる？
	- A: モデル名ではなく「デプロイ名」を `AICPM_MODEL` に設定します。
- Q: 英語出力にしたい。
	- A: `--language en` を指定するか、`.env` の `AICPM_DEFAULT_LANGUAGE=en` に変更します。
- Q: 会社独自の章立てにしたい。
	- A: `templates.py` に社内標準の doc_type を追加・編集してください。

## テスト

開発時に最低限のテストを実行できます。

```powershell
pytest -q
```

## 今後の拡張アイデア

- Word/PDF出力（python-docx, reportlab等）
- セクション単位の追記・更新ワークフロー
- 出力のバージョン管理/差分比較
- 役割（RACI）や品質メトリクスのExcelテンプレート追加

## 免責

- 出力は補助であり、最終責任はプロジェクトマネージャにあります。
- 機密情報は取り扱いに十分ご注意ください。
