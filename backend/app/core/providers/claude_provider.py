"""
Anthropic Claude Provider实现
"""
import os
import httpx
from typing import List, Dict

from app.core.providers.base_provider import JsonChatLLMProvider


class ClaudeProvider(JsonChatLLMProvider):
    """Anthropic Claude API实现"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        if not self.api_key:
            raise ValueError("API key is required for Claude provider")

    def _perform_chat_completion(self, chat_messages: List[Dict[str, str]], mode: str) -> str | dict:
        """调用Claude API"""
        # Claude API使用messages格式，需要分离system message
        messages = []
        system_message = None
        
        for msg in chat_messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "temperature": 0.7,
            "messages": messages,
        }
        
        if system_message:
            payload["system"] = system_message

        # Claude支持JSON格式输出，但需要通过工具调用或特殊提示
        # 这里我们依赖prompt中的JSON格式要求
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result_data = response.json()
            # Claude返回格式：content[0].text
            if "content" in result_data and len(result_data["content"]) > 0:
                result_text = result_data["content"][0]["text"]
                self.logger.info(f"[Claude Provider] API响应: {result_text}")
                
                # 提取tokens使用信息
                usage = result_data.get("usage", {})
                if usage:
                    return {
                        "text": result_text,
                        "usage": {
                            "prompt_tokens": usage.get("input_tokens", 0),
                            "completion_tokens": usage.get("output_tokens", 0),
                            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                        }
                    }
                return result_text
            
            raise ValueError(f"Unexpected Claude API response format: {result_data}")

