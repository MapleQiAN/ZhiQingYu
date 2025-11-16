"""
Ollama Provider实现（本地模型）
"""
import os
import json
import httpx
from app.core.llm_provider import LLMProvider, LLMResult
from app.schemas.chat import ChatMessage


class OllamaProvider(LLMProvider):
    """Ollama本地模型实现"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    def generate_reply(self, messages: list[ChatMessage]) -> LLMResult:
        """调用Ollama API生成回复"""
        # 构建system prompt
        system_prompt = self._build_system_prompt()
        
        # 转换消息格式
        chat_messages = [
            {"role": "system", "content": system_prompt}
        ]
        for msg in messages:
            chat_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": chat_messages,
                        "format": "json",
                        "stream": False
                    }
                )
                response.raise_for_status()
                
                result_data = response.json()
                result_text = result_data.get("message", {}).get("content", "{}")
                
                # 尝试解析JSON（Ollama可能返回带markdown的JSON）
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result_dict = json.loads(result_text)
                
                return LLMResult(
                    reply=result_dict.get("reply", ""),
                    emotion=result_dict.get("emotion", "neutral"),
                    intensity=result_dict.get("intensity", 2),
                    topics=result_dict.get("topics", []),
                    risk_level=result_dict.get("risk_level", "normal")
                )
        except Exception as e:
            # 如果调用失败，返回一个默认的安全回复
            return LLMResult(
                reply="抱歉，我现在无法处理你的消息。请稍后再试，或者联系专业心理支持。",
                emotion="neutral",
                intensity=2,
                topics=[],
                risk_level="normal"
            )
    
    def _build_system_prompt(self) -> str:
        """构建system prompt（与OpenAI相同）"""
        return """你是一位情绪陪伴助手，不是心理医生，不进行诊断，不提供药物建议。

你的任务是：
1. 理解用户当前的情绪和困扰场景
2. 用温和、现实的语气输出一段自然语言回复
3. 为用户这条消息打标签：
   - emotion: 从以下选项中选择一个：sadness, anxiety, anger, tired, joy, neutral, relief, calm
   - intensity: 1-5的整数，表示情绪强度
   - topics: 主题列表，如 ["study", "work", "relationship", "family", "self-doubt"] 等
4. 判断是否存在高危情绪（如自残/自杀意念），如果存在则 risk_level = "high"，否则为 "normal"

对于 risk_level = "high" 的情况，你的回复必须：
- 不提供任何具体方法或工具
- 强调理解和关心
- 引导用户联系现实世界可信的人（亲友、老师、医生等）
- 提醒用户尽快寻求专业心理或医疗帮助

请以严格的JSON格式输出，格式如下：
{
  "reply": "你的自然语言回复",
  "emotion": "情绪标签",
  "intensity": 情绪强度数字,
  "topics": ["主题1", "主题2"],
  "risk_level": "normal" 或 "high"
}

只输出JSON，不要包含任何其他文本。"""

