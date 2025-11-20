"""
Google Gemini Provider实现
"""
import os
import httpx
from typing import List, Dict

from app.core.providers.base_provider import JsonChatLLMProvider


class GeminiProvider(JsonChatLLMProvider):
    """Google Gemini API实现"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = base_url or os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-pro")

        if not self.api_key:
            raise ValueError("API key is required for Gemini provider")

    def _perform_text_completion(self, chat_messages: List[Dict[str, str]]) -> str | dict:
        """
        执行纯文本生成（不要求 JSON 格式）
        """
        try:
            # 转换消息格式：Gemini使用parts格式
            contents = []
            system_instruction = None
            
            for msg in chat_messages:
                if msg["role"] == "system":
                    # Gemini API需要system instruction作为单独的字段
                    system_instruction = {"parts": [{"text": msg["content"]}]}
                else:
                    # 转换角色：user -> user, assistant -> model
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })

            url = f"{self.base_url}/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            
            payload = {
                "contents": contents,
            }
            if system_instruction:
                payload["systemInstruction"] = system_instruction

            # 添加生成配置（不要求 JSON 格式）
            payload["generationConfig"] = {
                "temperature": 0.7,
                "maxOutputTokens": 500,
            }

            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, params=params, json=payload)
                response.raise_for_status()
                
                result_data = response.json()
                # Gemini返回格式：candidates[0].content.parts[0].text
                if "candidates" in result_data and len(result_data["candidates"]) > 0:
                    candidate = result_data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            result_text = parts[0]["text"]
                            return result_text
                
                raise ValueError(f"Unexpected Gemini API response format: {result_data}")
        except Exception as e:
            self.logger.error(f"[Gemini Provider] 文本生成失败: {str(e)}", exc_info=True)
            raise

    def _perform_chat_completion(self, chat_messages: List[Dict[str, str]], mode: str) -> str | dict:
        """调用Gemini API"""
        # 如果是 text 模式，使用文本生成方法
        if mode == "text":
            return self._perform_text_completion(chat_messages)
        
        # 转换消息格式：Gemini使用parts格式
        contents = []
        system_instruction = None
        
        for msg in chat_messages:
            if msg["role"] == "system":
                # Gemini API需要system instruction作为单独的字段
                system_instruction = {"parts": [{"text": msg["content"]}]}
            else:
                # 转换角色：user -> user, assistant -> model
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

        url = f"{self.base_url}/models/{self.model}:generateContent"
        params = {"key": self.api_key}
        
        payload = {
            "contents": contents,
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        # 添加生成配置
        payload["generationConfig"] = {
            "temperature": 0.7,
            "maxOutputTokens": 2000,
            "responseMimeType": "application/json"
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, params=params, json=payload)
            response.raise_for_status()
            
            result_data = response.json()
            # Gemini返回格式：candidates[0].content.parts[0].text
            if "candidates" in result_data and len(result_data["candidates"]) > 0:
                candidate = result_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        result_text = parts[0]["text"]
                        self.logger.info(f"[Gemini Provider] API响应: {result_text}")
                        return result_text
            
            raise ValueError(f"Unexpected Gemini API response format: {result_data}")

