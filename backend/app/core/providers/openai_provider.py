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

    def _perform_chat_completion(self, chat_messages, mode: str) -> str | dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=chat_messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000,
            )
            
            # 检查响应是否有效
            if not response or not hasattr(response, 'choices'):
                self.logger.error("[OpenAI Provider] API响应中没有choices字段")
                raise ValueError("API响应格式错误：缺少choices字段")
            
            if not response.choices or len(response.choices) == 0:
                self.logger.error("[OpenAI Provider] API响应中choices为空")
                raise ValueError("API响应格式错误：choices为空")
            
            choice = response.choices[0]
            if not hasattr(choice, 'message') or not choice.message:
                self.logger.error("[OpenAI Provider] API响应中message字段缺失")
                raise ValueError("API响应格式错误：缺少message字段")
            
            result_text = choice.message.content
            if result_text is None:
                self.logger.error("[OpenAI Provider] API响应中content为None")
                raise ValueError("API响应格式错误：content为None")
            
            self.logger.info(f"[OpenAI Provider] API响应: {result_text[:200]}...")  # 只记录前200字符
            
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
            self.logger.error(f"[OpenAI Provider] API调用失败: {str(e)}", exc_info=True)
            # 记录完整的响应信息以便调试
            if 'response' in locals():
                self.logger.error(f"[OpenAI Provider] 响应对象: {response}")
                if hasattr(response, 'choices'):
                    self.logger.error(f"[OpenAI Provider] choices数量: {len(response.choices) if response.choices else 0}")
            raise