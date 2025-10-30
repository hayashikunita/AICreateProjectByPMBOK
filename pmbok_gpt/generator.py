from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .config import AppSettings
from .providers import get_provider
from .templates import DOC_TEMPLATES


SYSTEM_PROMPT = (
    "あなたは経験豊富なプロジェクトマネージャ支援AIです。" 
    "PMBOKに整合する一般的な構成と用語を用いて、過度に冗長にならず、実務に使える明確さで記述してください。" 
    "出力は指定言語で、見出しと箇条書きを組み合わせ、読みやすく整理してください。"
)


def build_messages(
    language: str,
    doc_type: str,
    project_context: Dict[str, Any],
    extra_instructions: Optional[str] = None,
) -> List[Dict[str, str]]:
    if doc_type not in DOC_TEMPLATES:
        raise ValueError(f"Unknown doc_type: {doc_type}")

    tpl = DOC_TEMPLATES[doc_type]
    sections = tpl["sections"]  # type: ignore

    user_payload = {
        "language": language,
        "doc_type": doc_type,
        "title": tpl.get("title"),
        "sections": sections,
        "project": project_context,
        "format": {
            "headings": True,
            "bullets": True,
            "section_numbering": True,
        },
        "notes": extra_instructions or "",
    }
    content = (
        "以下の条件で、指定のドキュメントを作成してください。\n"
        f"言語: {language}\n"
        f"ドキュメント種別: {tpl.get('title')} ({doc_type})\n"
        "セクション（順序厳守）:\n- セクション1: "
        + "\n- セクション: ".join(str(s) for s in sections)
        + "\n"
        "体裁: 見出し + 箇条書き + 短い説明\n"
        "厳禁: 機密情報の推測、虚偽の数値、PMBOK原文の複製\n"
        "プロジェクト情報(JSON):\n"
        + json.dumps(project_context, ensure_ascii=False, indent=2)
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def generate_text_document(
    doc_type: str,
    project_context: Dict[str, Any],
    *,
    out_path: str,
    language: Optional[str] = None,
    extra_instructions: Optional[str] = None,
    settings: Optional[AppSettings] = None,
) -> str:
    settings = settings or AppSettings()
    language = language or settings.default_language
    provider = get_provider(settings)

    messages = build_messages(language, doc_type, project_context, extra_instructions)
    text = provider.generate(messages)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path
