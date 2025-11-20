"""
Ollama Provider实现（本地模型）
"""
import os
import httpx

from app.core.providers.base_provider import JsonChatLLMProvider


class OllamaProvider(JsonChatLLMProvider):
    """Ollama本地模型实现"""

    def __init__(self, base_url: str = None, model: str = None):
        super().__init__()
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")

    def _perform_text_completion(self, chat_messages) -> str | dict:
        """
        执行纯文本生成（不要求 JSON 格式）
        """
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": chat_messages,
                        "stream": False,
                        "options": {
                            "num_predict": 500,
                        },
                    },
                )
                response.raise_for_status()

                result_data = response.json()
                result_text = result_data.get("message", {}).get("content", "")
                if not result_text:
                    raise ValueError("API响应格式错误：content为空")
                
                return result_text
        except Exception as e:
            self.logger.error(f"[Ollama Provider] 文本生成失败: {str(e)}", exc_info=True)
            raise

    def _perform_chat_completion(self, chat_messages, mode: str) -> str | dict:
        # 如果是 text 模式，使用文本生成方法
        if mode == "text":
            return self._perform_text_completion(chat_messages)
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "num_predict": 2000,
                    },
                },
            )
            response.raise_for_status()

            result_data = response.json()
            result_text = result_data.get("message", {}).get("content", "{}")
            self.logger.info(f"[Ollama Provider] API响应: {result_text}")
            return result_text

