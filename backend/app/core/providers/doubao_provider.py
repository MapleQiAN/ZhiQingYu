"""
字节豆包 Provider实现（兼容OpenAI API格式）
"""
import os
from openai import OpenAI

from app.core.providers.base_provider import JsonChatLLMProvider


class DoubaoProvider(JsonChatLLMProvider):
    """字节豆包 API实现（使用OpenAI兼容格式）"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__()
        self.api_key = api_key or os.getenv("DOUBAO_API_KEY")
        self.base_url = base_url or os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = model or os.getenv("DOUBAO_MODEL", "ep-20241201220000-xxxxx")

        if not self.api_key:
            raise ValueError("API key is required for Doubao provider")

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
        self.logger.info(f"[Doubao Provider] API响应: {result_text}")
        return result_text

