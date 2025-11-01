from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, List

import typer
from rich import print

from .config import AppSettings
from .providers import get_provider


SCHEMA_DESCRIPTION_BASIC = {
    "name": "string (プロジェクト名)",
    "sponsor": "string (スポンサー/意思決定者)",
    "objectives": ["string", "string", "..."],
    "scope": {
        "in": ["string", "..."],
        "out": ["string", "..."],
    },
    "constraints": ["string", "..."],
    "assumptions": ["string", "..."],
    "milestones": [{"name": "string", "target": "YYYY-MM-DD"}],
    "budget": {"currency": "string", "amount": 0},
    "stakeholders": [{"name": "string", "interest": "string"}],
    "risk_seeds": ["string", "..."]
}

SCHEMA_DESCRIPTION_EXTENDED = {
    **SCHEMA_DESCRIPTION_BASIC,
    "project_code": "string (社内プロジェクトコード)",
    "department": "string (主担当部門)",
    "acceptance_criteria": ["string", "..."],
    "non_functional_requirements": ["string (性能/可用性/保守性等)", "..."],
    "compliance_requirements": ["string (法令/規程/監査対応)", "..."],
    "data_classification": "string (公開/社外秘/機密など)",
    "communication_cadence": ["string (例: 週次定例/日次進捗)", "..."],
    "dependencies": ["string (外部/内部依存)", "..."],
    "wbs": [
        {"deliverable": "string", "work_packages": ["string", "..."]}
    ],
    "governance": {
        "change_control_board": "string (CCBの有無/構成)",
        "escalation_path": "string (エスカレーション先)"
    }
}


SYSTEM_WIZARD_PROMPT = (
    "あなたはプロジェクト計画の要件聞き取りを行うアシスタントです。"
    "次のJSONスキーマに沿って、足りない情報を少しずつ丁寧に質問し、ユーザーの短い回答をもとに進めてください。"
    "一度に3問以内。簡潔に。重要度の高い項目（名称・目的・スコープ・マイルストーン・予算・リスク）を優先。"
    "ユーザーが『出力』と入力したら、下記スキーマにぴったり合致する有効なJSONのみを返してください（前後説明なし）。"
)


FINALIZE_INSTRUCTION = (
    "これまでの会話の内容から、指定スキーマに完全準拠したJSONのみを返してください。"
    "必ず valid JSON 形式（コードブロックやコメント、説明は不要）。"
)


def _print_assistant(content: str) -> None:
    print(f"[bold cyan]Assistant[/bold cyan]:\n{content}\n")


def _local_stub_wizard(extended: bool = True) -> Dict[str, Any]:
    """スタブ時のローカル質問フロー（API不要）。"""
    print("[bold]スタブモード: ローカル質問フローでJSONを作成します。[/bold]")
    name = typer.prompt("プロジェクト名")
    sponsor = typer.prompt("スポンサー/意思決定者")
    objectives = typer.prompt("目的（; 区切りで複数）")
    scope_in = typer.prompt("スコープ(含む)（; 区切り）")
    scope_out = typer.prompt("スコープ(含まない)（; 区切り）", default="")
    constraints = typer.prompt("制約（; 区切り）", default="")
    assumptions = typer.prompt("前提（; 区切り）", default="")
    ms1 = typer.prompt("主要マイルストーン名(1件目)", default="")
    ms1_date = typer.prompt("主要マイルストーン日付(YYYY-MM-DD)", default="")
    budget_currency = typer.prompt("予算通貨コード(例: JPY)", default="JPY")
    budget_amount = typer.prompt("予算額(整数)", default="0")
    sh1 = typer.prompt("主要ステークホルダー(例: 営業部)", default="")
    sh1_interest = typer.prompt("ステークホルダーの関心事(例: 在庫連携の安定)", default="")
    risks = typer.prompt("リスクの種（; 区切り）", default="")

    def split(s: str) -> List[str]:
        return [x.strip() for x in s.split(";") if x.strip()] if s else []

    data: Dict[str, Any] = {
        "name": name,
        "sponsor": sponsor,
        "objectives": split(objectives),
        "scope": {
            "in": split(scope_in),
            "out": split(scope_out),
        },
        "constraints": split(constraints),
        "assumptions": split(assumptions),
        "milestones": [],
        "budget": {"currency": budget_currency or "JPY", "amount": int(budget_amount or 0)},
        "stakeholders": [],
        "risk_seeds": split(risks),
    }
    if ms1:
        data["milestones"].append({"name": ms1, "target": ms1_date or ""})
    if sh1:
        data["stakeholders"].append({"name": sh1, "interest": sh1_interest or ""})

    if extended:
        project_code = typer.prompt("社内プロジェクトコード", default="")
        department = typer.prompt("主担当部門", default="")
        acc = typer.prompt("受入基準（; 区切り）", default="")
        nfr = typer.prompt("非機能要件（性能/可用性等；; 区切り）", default="")
        comp = typer.prompt("コンプライアンス要求（; 区切り）", default="")
        classify = typer.prompt("データ区分（例: 社外秘/機密/公開）", default="")
        cadence = typer.prompt("コミュニケーション頻度（; 区切り）", default="")
        deps = typer.prompt("依存関係（; 区切り）", default="")
        wbs_delivs = typer.prompt("WBS最上位成果物（; 区切り）", default="")
        ccb = typer.prompt("CCB(変更管理委員会)の有無/構成", default="")
        esc = typer.prompt("エスカレーション先", default="")

        data.update({
            "project_code": project_code,
            "department": department,
            "acceptance_criteria": split(acc),
            "non_functional_requirements": split(nfr),
            "compliance_requirements": split(comp),
            "data_classification": classify,
            "communication_cadence": split(cadence),
            "dependencies": split(deps),
            "wbs": [{"deliverable": d, "work_packages": []} for d in split(wbs_delivs)],
            "governance": {"change_control_board": ccb, "escalation_path": esc},
        })
    return data


def run_project_wizard(
    out_path: str,
    *,
    language: Optional[str] = None,
    settings: Optional[AppSettings] = None,
    max_turns: int = 8,
    level: str = "extended",
) -> str:
    """ChatGPT（またはスタブ）と対話して、プロジェクトJSONを作成する。"""
    settings = settings or AppSettings()
    language = language or settings.default_language
    provider = get_provider(settings)

    # スタブ時はローカル質問でJSONを生成
    if settings.provider_kind() == "stub":
        data = _local_stub_wizard(extended=(level != "basic"))
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path

    # LLM対話フロー
    schema = SCHEMA_DESCRIPTION_EXTENDED if level != "basic" else SCHEMA_DESCRIPTION_BASIC
    messages = [
        {"role": "system", "content": SYSTEM_WIZARD_PROMPT},
        {
            "role": "user",
            "content": (
                "言語: "
                + language
                + "\n以下のJSONスキーマに従って情報収集を進めてください。ユーザーが『出力』と入力したら最終JSONのみ出力。\nスキーマ: "
                + json.dumps(schema, ensure_ascii=False)
            ),
        },
    ]

    print("[bold]ChatGPTと対話を開始します。質問に短く回答してください。終了したいときは『出力』と入力。[/bold]")

    for _ in range(max_turns):
        assistant = provider.generate(messages)
        _print_assistant(assistant)
        user_input = typer.prompt("あなたの回答（または '出力' で確定）")
        messages.append({"role": "user", "content": user_input})
        if user_input.strip() in {"出力", "finish", "final", "done"}:
            break

    # 最終JSONの出力を依頼
    messages.append({"role": "user", "content": FINALIZE_INSTRUCTION})
    raw = provider.generate(messages)

    # JSONとしてパース（2回までリトライ）
    parsed: Optional[Dict[str, Any]] = None
    last_error = None
    for _ in range(2):
        try:
            parsed = json.loads(raw)
            break
        except Exception as e:  # JSONデコード失敗時は再依頼
            last_error = e
            messages.append({
                "role": "user",
                "content": "前回の出力は有効なJSONではありません。コードブロックや説明を排し、JSONのみを返してください。"
            })
            raw = provider.generate(messages)

    if parsed is None:
        raise RuntimeError(f"JSONの生成に失敗しました: {last_error}\n出力: {raw[:400]}")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[green]保存しました:[/green] {out_path}")
    return out_path
