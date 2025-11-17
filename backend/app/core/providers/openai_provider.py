"""
OpenAI Provider实现
"""
import os
from openai import OpenAI

from app.core.providers.base_provider import JsonChatLLMProvider


class OpenAIProvider(JsonChatLLMProvider):
    """OpenAI API实现（兼容OpenAI API格式的其他提供商）"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not self.api_key:
            raise ValueError("API key is required for OpenAI provider")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _perform_chat_completion(self, chat_messages, mode: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content
        self.logger.info(f"[OpenAI Provider] API响应: {result_text}")
        return result_text