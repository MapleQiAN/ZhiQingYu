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

    def _perform_chat_completion(self, chat_messages, mode: str) -> str:
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

