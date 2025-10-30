from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich import print

from .config import AppSettings
from .generator import generate_text_document
from .templates import DOC_TEMPLATES
from .excel import create_risk_register_excel, create_stakeholder_register_excel

app = typer.Typer(help="PMBOKドキュメント生成CLI")


@app.command()
def list():  # type: ignore[override]
    """生成可能なドキュメントタイプを一覧表示。"""
    for key, tpl in DOC_TEMPLATES.items():
        print(f"[bold]{key}[/bold]: {tpl.get('title')}")


@app.command()
def init():  # type: ignore[override]
    """.envとサンプルプロジェクトJSONを配置。"""
    root = Path.cwd()
    env_path = root / ".env"
    if not env_path.exists():
        example = (root / ".env.example")
        if example.exists():
            env_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print(f".env を作成しました: {env_path}")
        else:
            env_path.write_text("AICPM_USE_STUB=true\n", encoding="utf-8")
            print(f".env を作成しました(簡易): {env_path}")
    else:
        print(".env は既に存在します。")

    examples_dir = root / "examples"
    examples_dir.mkdir(exist_ok=True)
    sample_path = examples_dir / "project_sample.json"
    if not sample_path.exists():
        sample = {
            "name": "次世代ECサイト刷新プロジェクト",
            "sponsor": "事業本部長",
            "objectives": [
                "CVRを1.5倍に向上",
                "検索UX改善とレコメンド導入",
            ],
            "scope": {
                "in": ["フロントUI刷新", "検索/レコメンド機能", "決済ゲートウェイ刷新"],
                "out": ["倉庫WMSの刷新", "コールセンターSaaSの刷新"],
            },
            "constraints": ["8ヶ月以内にリリース", "既存会員DBは維持"],
            "assumptions": ["広告予算は現状維持", "主要サプライヤは継続契約"],
            "milestones": [
                {"name": "要件定義完了", "target": "2026-01-31"},
                {"name": "UAT完了", "target": "2026-04-30"},
            ],
            "budget": {"currency": "JPY", "amount": 120_000_000},
            "stakeholders": [
                {"name": "営業部", "interest": "在庫連携の安定"},
                {"name": "CS部", "interest": "問合せ削減"},
            ],
            "risk_seeds": [
                "要件肥大化による遅延",
                "外部APIのスループット制限",
            ],
        }
        sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"サンプルを作成しました: {sample_path}")
    else:
        print("サンプルは既に存在します。")


@app.command()
def txt(
    doc_type: str = typer.Option(..., help="ドキュメント種別キー（list参照）"),
    project_file: Path = typer.Option(..., exists=True, help="プロジェクト情報(JSON)"),
    out: Path = typer.Option(..., help="出力先のtxtファイルパス"),
    language: Optional[str] = typer.Option(None, help="言語(ja/en等)。未指定は設定値"),
    note: Optional[str] = typer.Option(None, help="追加指示(任意)"),
):
    settings = AppSettings()
    data = json.loads(project_file.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)

    path = generate_text_document(
        doc_type=doc_type,
        project_context=data,
        out_path=str(out),
        language=language,
        extra_instructions=note,
        settings=settings,
    )
    print(f"生成しました: {path}")


@app.command()
def excel(
    type: str = typer.Option(..., help="risk-register | stakeholder-register"),
    out: Path = typer.Option(..., help="出力先 .xlsx ファイルパス"),
):
    out.parent.mkdir(parents=True, exist_ok=True)
    if type == "risk-register":
        path = create_risk_register_excel(str(out))
    elif type == "stakeholder-register":
        path = create_stakeholder_register_excel(str(out))
    else:
        raise typer.BadParameter("type は 'risk-register' または 'stakeholder-register'")
    print(f"生成しました: {path}")


@app.command()
def diag():  # type: ignore[override]
    """環境設定の診断情報を表示します。"""
    settings = AppSettings()
    # 実効的な BASE_URL を確認（空文字は未設定扱い）
    base_url_env = (settings.openai_base_url or os.getenv("OPENAI_BASE_URL") or "").strip()
    base_url_effective = base_url_env if base_url_env else "(unset)"
    base_url_valid = (
        True if (not base_url_env) else (base_url_env.startswith("http://") or base_url_env.startswith("https://"))
    )
    info = {
        "provider": settings.provider_kind(),
        "model": settings.model,
        "use_stub": settings.use_stub,
        "language": settings.default_language,
        "openai_api_key_set": bool(settings.openai_api_key or os.getenv("OPENAI_API_KEY")),
        "openai_base_url": base_url_effective,
        "openai_base_url_valid": base_url_valid,
        "azure_api_key_set": bool(settings.azure_openai_api_key or os.getenv("AZURE_OPENAI_API_KEY")),
        "azure_endpoint": settings.azure_openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT") or "",
        "azure_api_version": settings.azure_openai_api_version,
    }
    print("[bold]診断結果[/bold]")
    for k, v in info.items():
        # APIキーは有無のみ表示
        print(f"- {k}: {v}")
