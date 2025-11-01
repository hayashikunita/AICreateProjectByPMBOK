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
- プロジェクトJSON作成ウィザード: `wizard`

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
AICPM_USE_RESPONSES_API=false
AICPM_FALLBACK_TO_STUB_ON_EMPTY=true
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
├─ streamlit_app.py          # Web UI（Streamlit）
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

### プロジェクトJSONを対話で作成（ウィザード）

ChatGPT（またはスタブ）と対話しながら、`examples/project_sample.json` と同等スキーマのJSONを作成します。

```
# スタブで試す（API不要）
$env:AICPM_USE_STUB="true"
python -m pmbok_gpt wizard --out examples/project_from_wizard.json

# 実APIで対話（OpenAI例）
$env:AICPM_USE_STUB="false"; $env:OPENAI_API_KEY="<your-key>"
python -m pmbok_gpt wizard --out examples/project_from_wizard.json --language ja
```

ヒント:
- 対話中、終了したくなったら「出力」と入力すると最終JSONを出します。
- スタブ時はローカル質問フローで作成します。

### Web UIで作成（Streamlit）

表形式で項目を編集しながらプロジェクトJSONを作成できます。保存/ダウンロード、さらにそのJSONからドキュメント生成も可能です。

```
# 1) 依存インストール済みの場合はスキップ
python -m pip install -r requirements.txt

# 2) Streamlit サーバ起動
streamlit run streamlit_app.py

# ブラウザで開く URL がターミナルに表示されます（通常 http://localhost:8501）
```

ヒント:
- サイドバーで basic / extended を切替できます（extended は会社標準の項目も収集）。
- テーブルの各列は自由に行追加・編集できます。
- 右下の「JSONプレビュー」「保存」「JSONダウンロード」を活用してください。
- 画面下部の「ドキュメント生成」で、その場でtxtを出力できます。

#### UIの主な操作と説明

- 実行設定（プロバイダ）
	- provider: `stub`（課金なし・動作確認用）、`openai`、`azure` から選択
	- model/temperature/max_tokens を調整できます（Azureでは model はデプロイ名）
	- Responses API を優先（OpenAIのみ）: Chat Completions ではなく Responses API を優先して呼び出します。gpt-5 系など新仕様モデルでの互換性向上に有効です。
	- 空出力時にスタブへフォールバック: LLMが空の本文を返した場合でも空ファイルにしないための保険です。無効のまま空が返るとエラーになります。
	- OpenAI 選択時:
		- OPENAI_API_KEY を入力（環境変数の代わりにUI入力で上書き可能）
		- OPENAI_BASE_URL は互換API利用時のみ（未入力推奨）。入力する場合は http/https で始まる完全URL
	- Azure 選択時:
		- AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_VERSION を入力
		- model は「デプロイ名」を指定

- 入力ソース（ドキュメント生成用）
	- 「現在の画面の内容」… UIで入力中のJSONをそのまま使用
	- 「JSONファイルから」… 既存のJSONファイルをアップロードして使用

- 生成中の表示（UIUX）
	- ドキュメント生成中は「作成中…」とスピナーに加え、プログレスバーと経過時間を表示します
	- JSONプレビュー/保存の際も「作業中…」が一時的に表示され、完了後に成功メッセージへ切り替わります
	- 生成完了後は、作成されたテキストの内容を画面下部にプレビュー表示します

補足（自動リトライ）:
- OpenAI を選択しており「Responses API を優先」がOFFの状態で生成に失敗した場合、UIは自動的に Responses API へ切り替えて再試行します。再試行結果はその場でプレビュー表示されます。

### 🎥 デモ動画（準備中）

このセクションにアプリの操作動画を掲載します。以下のいずれかの方法で追加できます。

- リポジトリ内に動画を同梱（mp4）: `docs/demo.mp4` を追加すると、以下のリンク/埋め込みで閲覧できます（未配置の場合は404になります）。
	- 直接リンク: [デモ動画 (mp4)](docs/demo.mp4)
	- 埋め込み（GitHubの表示環境によってはプレーヤーが出ない場合があります）:

		<!-- ファイルを追加したら、下のブロックのコメントを外してください -->
		<!--
		<video src="docs/demo.mp4" controls width="720">
			お使いの環境では動画を再生できません。こちらから直接ダウンロードしてください:
			<a href="docs/demo.mp4">docs/demo.mp4</a>
		</video>
		-->


#### 会社標準の必須項目（拡張レベル）

ウィザードは既定で「extended」レベルで、以下の項目も収集します（例）。

- project_code（社内プロジェクトコード）
- department（主担当部門）
- acceptance_criteria（受入基準）
- non_functional_requirements（性能/可用性/保守性 等）
- compliance_requirements（法令/社内規程/監査対応）
- data_classification（公開/社外秘/機密）
- communication_cadence（会議/レポート頻度）
- dependencies（外部/内部依存）
- wbs（最上位成果物とワークパッケージ）
- governance（CCBの有無/構成、エスカレーション先）

最小限だけで良い場合は basic に変更できます。

```
python -m pmbok_gpt wizard --level basic --out examples/project_basic.json
```

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
	- 現在の設定・キー有無・BASE_URL妥当性などを表示（`use_responses_api` と `fallback_to_stub_on_empty` の状態も表示）

### 対応 doc_type（詳細）

以下の doc_type を指定して、それぞれの目的に沿ったテキスト文書を生成できます。各タイプの「典型セクション」はテンプレートの章立ての目安です。

#### project_charter（プロジェクト憲章）
- 目的: プロジェクト開始の正式承認と全体像の共有
- 典型セクション:
	- 背景・目的 / 目標（KPI）
	- スコープ概要（含む/含まない）
	- 成功基準・受入基準 / 主要マイルストーン
	- 予算とリソース概算 / 体制・役割（スポンサー/PM 等）
	- 制約・前提 / 主要リスク / 承認
- 推奨入力: name, sponsor, objectives, scope.in/out, milestones, budget, constraints, assumptions, stakeholders
- 出力のコツ: 1〜3ページ程度の簡潔さを重視し、成功基準を測定可能にする

#### scope_statement（スコープ記述書）
- 目的: 成果物と作業の境界（IN/OUT）を明確化
- 典型セクション:
	- 目的と背景 / プロダクトスコープ / プロジェクトスコープ
	- 成果物一覧と受入基準 / 除外事項（Out of Scope）
	- 制約・前提 / ハイレベルWBS / 変更管理の取り扱い
- 推奨入力: objectives, scope.in/out, acceptance_criteria（拡張）, non_functional_requirements, dependencies
- 出力のコツ: IN/OUTを箇条書きで具体化し、受入基準を客観的に

#### wbs_outline（WBSアウトライン）
- 目的: 成果物ベースで作業分解し、管理しやすくする
- 典型セクション:
	- 成果物ツリー（上位成果物 → 作業パッケージ）
	- WBSダイアグラム/辞書（簡易） / 前提・制約
	- マイルストーンとの対応付け
- 推奨入力: wbs（拡張）、なければ scope と milestones から推論
- 出力のコツ: 成果物名は名詞、作業パッケージは動詞＋目的語で粒度を揃える（深さ2〜3層が目安）

#### schedule_overview（スケジュール概要）
- 目的: 主要マイルストーン中心に期間計画の全体像を提示
- 典型セクション:
	- マイルストーン一覧 / 概要ガント（文章表現）
	- クリティカルな依存関係 / 主要前提・制約
	- 日程上のリスク / コミュニケーション（進捗会議等）
- 推奨入力: milestones, dependencies, communication_cadence（拡張）
- 出力のコツ: 詳細タスクは避け、意思決定に必要な粒度に留める

#### risk_management_plan（リスクマネジメント計画）
- 目的: リスクの識別・分析・対応・監視の標準手順を定義
- 典型セクション:
	- 方針と目的 / 役割と責任 / リスク分類（RBS）
	- 評価基準（確率×影響、スコア閾値、許容度）
	- プロセス: 識別 → 定性/定量分析 → 対応計画 → 監視/レビュー
	- レポート頻度・会議体 / ツール・台帳
- 推奨入力: risk_seeds, stakeholders, communication_cadence
- 出力のコツ: スコアマトリクスと閾値を明記し、レビュー頻度を具体化

#### stakeholder_register（ステークホルダー登録簿 概要）
- 目的: 利害関係者の基本属性と対応方針を一覧化
- 典型セクション:
	- 一覧表（氏名/組織、役割、関心事、影響度、期待値、関与方針、コミュニケーション）
	- マッピング（影響度×関心）
- 推奨入力: stakeholders, governance（拡張）, communication_cadence
- 出力のコツ: 影響度は High/Med/Low などに正規化し、対応方針を1行で明快に

#### communication_plan（コミュニケーション計画）
- 目的: 誰に何をどの頻度/媒体で共有するかを定義
- 典型セクション:
	- 利害関係者別の情報ニーズ / 媒体・頻度・責任者
	- 会議体（定例名、目的、参加者、議題）
	- エスカレーション経路 / メッセージテンプレート
- 推奨入力: stakeholders, communication_cadence, governance
- 出力のコツ: 表形式で「対象→内容→頻度→媒体→責任者」を揃える

#### quality_management_plan（品質マネジメント計画）
- 目的: 品質目標・基準・保証/管理方法を取り決める
- 典型セクション:
	- 品質方針 / 目標と指標（KPI）
	- 基準・規格・順守事項（コンプライアンス）
	- 品質保証（プロセス/監査/レビュー）
	- 品質管理（検査/受入試験/欠陥管理）
	- 不適合の扱いと是正予防
- 推奨入力: non_functional_requirements, compliance_requirements, acceptance_criteria
- 出力のコツ: 測定可能な指標と受入基準を明確化

#### procurement_plan（調達マネジメント計画）
- 目的: 外部調達の方針・方式・スケジュール・責任分担を定義
- 典型セクション:
	- 調達範囲/品目 / 契約方式（固定・準委任 等）
	- 調達スケジュール / 役割と責任 / ベンダ評価基準
	- リスク・予備費 / 監視・検収・支払
- 推奨入力: dependencies（外部依存）, budget, governance
- 出力のコツ: 社内ルールに沿う前提と承認フローを明記

#### change_management_plan（変更管理計画）
- 目的: 変更申請から承認・実装・クローズまでの統制手順を明確化
- 典型セクション:
	- 変更の定義/分類 / 申請→評価→承認→実装→クローズのフロー
	- 影響分析（スコープ/スケジュール/コスト/品質/リスク）
	- CCB（変更管理委員会）の構成・開催頻度 / ツール・台帳
	- SLA/リードタイム / コミュニケーション
- 推奨入力: governance.change_control_board, communication_cadence
- 出力のコツ: トレーサビリティ（要求→変更→成果物）を意識

#### lessons_learned（教訓）
- 目的: 次回に活かす学びを体系化
- 典型セクション:
	- 概要 / うまくいった点 / 改善すべき点 / 次回の推奨
	- カテゴリ別（スコープ/スケジュール/コスト/品質/リスク/コミュニケーション/調達）
	- 参考資料・リンク
- 推奨入力: 任意（プロジェクト情報全般を参照）
- 出力のコツ: 行動可能な提言（Who/When/How）まで落とし込む

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

7. 空出力エラー（LLMが空の本文を返しました）
	- メッセージ例: `LLMが空の本文を返しました。フォールバックは無効です（AICPM_FALLBACK_TO_STUB_ON_EMPTY=false）。`
	- 対処:
		- Streamlit UI の「Responses API を優先（OpenAIのみ）」を有効にして再実行（gpt-5 系で有効）
		- または「空出力時にスタブへフォールバック」を有効にして空ファイルを回避（注意書きを付与してスタブ出力に切替）
		- CLI/環境変数の場合は `.env` に `AICPM_USE_RESPONSES_API=true` または `AICPM_FALLBACK_TO_STUB_ON_EMPTY=true` を設定

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
