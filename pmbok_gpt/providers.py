from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .config import AppSettings


def _ensure_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    for m in messages:
        if "role" not in m or "content" not in m:
            raise ValueError("messages must be a list of {role, content}")
    return messages


class StubProvider:
    """API不要のスタブ。各セクション見出しをダミーで埋めます。"""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    def generate(self, messages: List[Dict[str, str]]) -> str:
        _ensure_messages(messages)
        # 最後のユーザーメッセージからセクション名をざっくり抽出
        text = messages[-1]["content"]
        sections = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- ") and any(k in line.lower() for k in ["section", "セクション", "章", "項"]):
                sections.append(line[2:])
        if not sections:
            # フォールバック：ダミー本文
            return (
                "【スタブ出力】\n\n"
                "1. 目的\n本文(スタブ)\n\n"
                "2. 範囲\n本文(スタブ)\n\n"
                "3. 体制\n本文(スタブ)\n"
            )
        body = ["【スタブ出力】"]
        for i, sec in enumerate(sections, start=1):
            body.append(f"\n{i}. {sec}\n本文(スタブ): {sec} の要点を箇条書きで3点。\n- ポイント1\n- ポイント2\n- ポイント3")
        return "\n".join(body)


class OpenAIProvider:
    def __init__(self, settings: AppSettings):
        from openai import OpenAI  # lazy import

        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.openai_base_url:
            os.environ["OPENAI_BASE_URL"] = settings.openai_base_url

        # OPENAI_BASE_URL が空文字や不正な場合をガード
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url is not None:
            base_url_stripped = base_url.strip()
            if base_url_stripped == "":
                # 空の場合は環境変数自体を外して、SDKのデフォルト(https://api.openai.com/v1)を使う
                os.environ.pop("OPENAI_BASE_URL", None)
            elif not (base_url_stripped.startswith("http://") or base_url_stripped.startswith("https://")):
                raise RuntimeError(
                    "OPENAI_BASE_URL が不正です。'https://...' で始まる完全なURLを設定してください。例: https://api.openai.com/v1"
                )

        # 明確なチェック
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY が設定されていません。.env または環境変数で設定してください。"
            )

        self.client = OpenAI()
        self.settings = settings

    def generate(self, messages: List[Dict[str, str]]) -> str:
        _ensure_messages(messages)
        resp = self.client.chat.completions.create(
            model=self.settings.model,
            messages=messages,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        return resp.choices[0].message.content or ""


class AzureOpenAIProvider:
    def __init__(self, settings: AppSettings):
        from openai import AzureOpenAI  # lazy import

        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            raise RuntimeError(
                "Azure OpenAI の資格情報が不足しています。AZURE_OPENAI_API_KEY と AZURE_OPENAI_ENDPOINT を設定してください。"
            )

        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self.settings = settings

    def generate(self, messages: List[Dict[str, str]]) -> str:
        _ensure_messages(messages)
        resp = self.client.chat.completions.create(
            model=self.settings.model,
            messages=messages,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        return resp.choices[0].message.content or ""


def get_provider(settings: AppSettings):
    kind = settings.provider_kind()
    if kind == "stub":
        return StubProvider(settings)
    if kind == "azure":
        return AzureOpenAIProvider(settings)
    return OpenAIProvider(settings)
