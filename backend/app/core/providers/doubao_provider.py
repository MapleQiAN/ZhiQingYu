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

    def _perform_text_completion(self, chat_messages) -> str | dict:
        """
        执行纯文本生成（不要求 JSON 格式）
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=chat_messages,
                temperature=0.7,
                max_tokens=500,
            )

            result_text = response.choices[0].message.content
            if result_text is None:
                raise ValueError("API响应格式错误：content为None")
            
            # 提取tokens使用信息
            usage_info = {}
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                usage_info = {
                    "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(usage, 'completion_tokens', 0),
                    "total_tokens": getattr(usage, 'total_tokens', 0),
                }
            
            if usage_info:
                return {
                    "text": result_text,
                    "usage": usage_info
                }
            return result_text
        except Exception as e:
            self.logger.error(f"[Doubao Provider] 文本生成失败: {str(e)}", exc_info=True)
            raise

    def _perform_chat_completion(self, chat_messages, mode: str) -> str | dict:
        # 如果是 text 模式，使用文本生成方法
        if mode == "text":
            return self._perform_text_completion(chat_messages)
        
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

