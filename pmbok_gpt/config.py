from __future__ import annotations

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# .env を OS 環境変数に読み込む（pydantic-settings の読み込みとは独立に）
# これにより model_post_init の os.getenv(...) が期待通りに動作します。
load_dotenv()


class AppSettings(BaseSettings):
    """アプリ全体の設定（環境変数で上書き可能）。

    AICPM_ プレフィックスの環境変数を自動で読み込みます（例: AICPM_MODEL、AICPM_USE_STUB）。
    OpenAI/Azureの資格情報は、別環境変数（OPENAI_*, AZURE_OPENAI_*）を直接参照します。
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="AICPM_", extra="ignore")

    # AICPM_ で上書き
    model: str = "gpt-4o-mini"
    temperature: float = 0.4
    max_tokens: int = 1800
    use_stub: bool = False
    default_language: str = "ja"
    # LLMが空の本文を返した場合にスタブへ自動フォールバックするか（既定: True）
    fallback_to_stub_on_empty: bool = True
    # Chat Completions ではなく Responses API を優先的に使うか（OpenAI のみ）
    use_responses_api: bool = False

    # OpenAI（個別の環境変数から読み込み）
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None

    # Azure OpenAI（個別の環境変数から読み込み）
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = "2024-08-01-preview"

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        import os
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", self.openai_base_url)
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", self.azure_openai_api_key)
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint)
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", self.azure_openai_api_version)

    def provider_kind(self) -> str:
        if self.use_stub:
            return "stub"
        if self.azure_openai_api_key and self.azure_openai_endpoint:
            return "azure"
        return "openai"
