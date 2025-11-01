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
        """Call Chat Completions with compatibility fallbacks:
        - max_tokens -> fallback to max_completion_tokens when required
        - temperature unsupported -> fallback to API default by omitting temperature
        - If content is empty, fallback to Responses API
        """
        _ensure_messages(messages)

        def _call(use_completion_param: bool, include_temperature: bool, include_response_format: bool):
            params: Dict[str, Any] = {
                "model": self.settings.model,
                "messages": messages,
            }
            if include_temperature:
                params["temperature"] = self.settings.temperature
            if include_response_format:
                # 新仕様モデルでの安全なテキスト出力を促す。未対応モデルではフォールバックする
                params["response_format"] = {"type": "text"}
            if use_completion_param:
                params["max_completion_tokens"] = self.settings.max_tokens
            else:
                params["max_tokens"] = self.settings.max_tokens
            return self.client.chat.completions.create(**params)

        def _extract_text_from_chat(resp: Any) -> str:
            try:
                choices = getattr(resp, "choices", []) or []
                texts: List[str] = []
                for ch in choices:
                    msg = getattr(ch, "message", None)
                    if msg is None:
                        continue
                    content = getattr(msg, "content", None)
                    if content:
                        texts.append(str(content))
                return "\n\n".join([t for t in texts if t.strip()])
            except Exception:
                return ""

        def _call_responses_api(messages: List[Dict[str, str]]) -> str:
            # メッセージを単一テキストに畳み込み
            prompt_lines = [f"{m.get('role','user').upper()}:\n{m.get('content','')}" for m in messages]
            prompt = "\n\n".join(prompt_lines)
            r_params: Dict[str, Any] = {
                "model": self.settings.model,
                "input": prompt,
            }
            # 出力長の指定が必要なモデル向けにまずは設定、エラーなら外して再試行
            try:
                r_params["max_output_tokens"] = self.settings.max_tokens
                r = self.client.responses.create(**r_params)
            except Exception:
                r_params.pop("max_output_tokens", None)
                r = self.client.responses.create(**r_params)

            text2 = getattr(r, "output_text", None)
            if text2 and str(text2).strip():
                return str(text2)
            try:
                outputs = getattr(r, "output", None) or getattr(r, "outputs", None) or []
                chunks: List[str] = []
                for out in outputs:
                    cont = getattr(out, "content", None) or []
                    for item in cont:
                        if getattr(item, "type", "") == "output_text":
                            val = getattr(item, "text", "")
                            if val:
                                chunks.append(str(val))
                if chunks:
                    return "\n".join(chunks)
            except Exception:
                pass
            return ""

        # Responses API を優先する条件
        model_l = (self.settings.model or "").lower()
        prefer_responses = self.settings.use_responses_api or model_l.startswith("gpt-5") or "gpt-5" in model_l

        if prefer_responses:
            text_r = _call_responses_api(messages)
            if text_r and text_r.strip():
                return text_r
            # Responsesでダメなら従来の Chat Completions にもトライ

        # GPT-5 系のモデル名では temperature を最初から送らない（仕様互換）
        default_include_temp = not (model_l.startswith("gpt-5") or "gpt-5" in model_l)

        try:
            resp = _call(use_completion_param=False, include_temperature=default_include_temp, include_response_format=True)
        except Exception as e:
            msg = str(e)
            # max_tokens が非対応 → max_completion_tokens に切替
            if "max_tokens" in msg and "max_completion_tokens" in msg:
                try:
                    resp = _call(use_completion_param=True, include_temperature=True, include_response_format=True)
                except Exception as e2:
                    msg2 = str(e2)
                    # temperature が非対応 → temperature を省略
                    if "temperature" in msg2 and ("unsupported" in msg2 or "Only the default" in msg2):
                        resp = _call(use_completion_param=True, include_temperature=False, include_response_format=True)
                    # response_format が非対応 → 省略
                    elif "response_format" in msg2 and ("unsupported" in msg2 or "Invalid" in msg2 or "Unknown" in msg2):
                        resp = _call(use_completion_param=True, include_temperature=True, include_response_format=False)
                    else:
                        raise
            # temperature が非対応（max_tokensは許容）
            elif "temperature" in msg and ("unsupported" in msg or "Only the default" in msg):
                # omit temperature with original max_tokens param
                try:
                    resp = _call(use_completion_param=False, include_temperature=False, include_response_format=True)
                except Exception as e3:
                    # さらに max_tokens も非対応だった場合の合わせ技
                    msg3 = str(e3)
                    if "max_tokens" in msg3 and "max_completion_tokens" in msg3:
                        resp = _call(use_completion_param=True, include_temperature=False, include_response_format=True)
                    elif "response_format" in msg3 and ("unsupported" in msg3 or "Invalid" in msg3 or "Unknown" in msg3):
                        resp = _call(use_completion_param=False, include_temperature=False, include_response_format=False)
                    else:
                        raise
            # response_format が非対応（max_tokens/temperatureは許容）
            elif "response_format" in msg and ("unsupported" in msg or "Invalid" in msg or "Unknown" in msg):
                try:
                    resp = _call(use_completion_param=False, include_temperature=True, include_response_format=False)
                except Exception as e4:
                    msg4 = str(e4)
                    if "max_tokens" in msg4 and "max_completion_tokens" in msg4:
                        resp = _call(use_completion_param=True, include_temperature=True, include_response_format=False)
                    elif "temperature" in msg4 and ("unsupported" in msg4 or "Only the default" in msg4):
                        resp = _call(use_completion_param=False, include_temperature=False, include_response_format=False)
                    else:
                        raise
            else:
                raise

        text = _extract_text_from_chat(resp)
        if text and text.strip():
            return text

        # 最後の手段: Responses API での再試行
        text_r2 = _call_responses_api(messages)
        if text_r2 and text_r2.strip():
            return text_r2

        return ""


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

        def _call(use_completion_param: bool, include_temperature: bool, include_response_format: bool):
            params: Dict[str, Any] = {
                "model": self.settings.model,
                "messages": messages,
            }
            if include_temperature:
                params["temperature"] = self.settings.temperature
            if include_response_format:
                params["response_format"] = {"type": "text"}
            if use_completion_param:
                params["max_completion_tokens"] = self.settings.max_tokens
            else:
                params["max_tokens"] = self.settings.max_tokens
            return self.client.chat.completions.create(**params)

        model_l = (self.settings.model or "").lower()
        default_include_temp = not (model_l.startswith("gpt-5") or "gpt-5" in model_l)

        try:
            resp = _call(use_completion_param=False, include_temperature=default_include_temp, include_response_format=True)
        except Exception as e:
            msg = str(e)
            if "max_tokens" in msg and "max_completion_tokens" in msg:
                try:
                    resp = _call(use_completion_param=True, include_temperature=True, include_response_format=True)
                except Exception as e2:
                    msg2 = str(e2)
                    if "temperature" in msg2 and ("unsupported" in msg2 or "Only the default" in msg2):
                        resp = _call(use_completion_param=True, include_temperature=False, include_response_format=True)
                    elif "response_format" in msg2 and ("unsupported" in msg2 or "Invalid" in msg2 or "Unknown" in msg2):
                        resp = _call(use_completion_param=True, include_temperature=True, include_response_format=False)
                    else:
                        raise
            elif "temperature" in msg and ("unsupported" in msg or "Only the default" in msg):
                try:
                    resp = _call(use_completion_param=False, include_temperature=False, include_response_format=True)
                except Exception as e3:
                    msg3 = str(e3)
                    if "max_tokens" in msg3 and "max_completion_tokens" in msg3:
                        resp = _call(use_completion_param=True, include_temperature=False, include_response_format=True)
                    elif "response_format" in msg3 and ("unsupported" in msg3 or "Invalid" in msg3 or "Unknown" in msg3):
                        resp = _call(use_completion_param=False, include_temperature=False, include_response_format=False)
                    else:
                        raise
            elif "response_format" in msg and ("unsupported" in msg or "Invalid" in msg or "Unknown" in msg):
                try:
                    resp = _call(use_completion_param=False, include_temperature=True, include_response_format=False)
                except Exception as e4:
                    msg4 = str(e4)
                    if "max_tokens" in msg4 and "max_completion_tokens" in msg4:
                        resp = _call(use_completion_param=True, include_temperature=True, include_response_format=False)
                    elif "temperature" in msg4 and ("unsupported" in msg4 or "Only the default" in msg4):
                        resp = _call(use_completion_param=False, include_temperature=False, include_response_format=False)
                    else:
                        raise
            else:
                raise

        return resp.choices[0].message.content or ""


def get_provider(settings: AppSettings):
    kind = settings.provider_kind()
    if kind == "stub":
        return StubProvider(settings)
    if kind == "azure":
        return AzureOpenAIProvider(settings)
    return OpenAIProvider(settings)
