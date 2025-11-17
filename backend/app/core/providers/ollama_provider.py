"""
Ollama Provider实现（本地模型）
"""
import os
import json
import httpx
import logging
from app.core.llm_provider import LLMProvider, LLMResult
from app.schemas.chat import ChatMessage
from app.schemas.style import StyleProfile, ParsedState, ReplyPlan, InterventionConfig

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama本地模型实现"""
    
    def __init__(self, base_url: str = None, model: str = None):
        # 优先使用传入的参数，否则从环境变量读取
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
    
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
                        "stream": False,
                        "options": {
                            "num_predict": 2000  # 增加最大token数，允许更长的回复
                        }
                    }
                )
                response.raise_for_status()
                
                result_data = response.json()
                result_text = result_data.get("message", {}).get("content", "{}")
                logger.info(f"[Ollama Provider] 原始API响应: {result_text}")
                
                # 尝试解析JSON（Ollama可能返回带markdown的JSON）
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result_dict = json.loads(result_text)
                
                reply = result_dict.get("reply", "")
                logger.info(f"[Ollama Provider] 解析后的回复内容:")
                logger.info(f"  回复长度: {len(reply)} 字符")
                logger.info(f"  回复内容: {reply}")
                logger.info(f"  情绪: {result_dict.get('emotion', 'neutral')}")
                logger.info(f"  强度: {result_dict.get('intensity', 2)}")
                logger.info(f"  主题: {result_dict.get('topics', [])}")
                logger.info(f"  风险等级: {result_dict.get('risk_level', 'normal')}")
                
                return LLMResult(
                    reply=reply,
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
2. 用温和、现实的语气输出一段详细、丰富的自然语言回复
3. 为用户这条消息打标签：
   - emotion: 从以下选项中选择一个：sadness, anxiety, anger, tired, joy, neutral, relief, calm
   - intensity: 1-5的整数，表示情绪强度
   - topics: 主题列表，如 ["study", "work", "relationship", "family", "self-doubt"] 等
4. 判断是否存在高危情绪（如自残/自杀意念），如果存在则 risk_level = "high"，否则为 "normal"

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 尽量提供充分的共情、理解和建议
- 回复长度应该在500字以上，根据用户问题的复杂程度适当调整
- 可以包含具体的例子、场景描述、情感共鸣等内容
- 让用户感受到被充分理解和关心

对于 risk_level = "high" 的情况，你的回复必须：
- 不提供任何具体方法或工具
- 强调理解和关心
- 引导用户联系现实世界可信的人（亲友、老师、医生等）
- 提醒用户尽快寻求专业心理或医疗帮助
- 即使在这种情况下，也要提供充分的情感支持和理解

请以严格的JSON格式输出，格式如下：
{
  "reply": "你的详细自然语言回复（500字以上）",
  "emotion": "情绪标签",
  "intensity": 情绪强度数字,
  "topics": ["主题1", "主题2"],
  "risk_level": "normal" 或 "high"
}

只输出JSON，不要包含任何其他文本。"""
    
    def generate_structured_reply(
        self,
        messages: list[ChatMessage],
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: list[InterventionConfig],
    ) -> LLMResult:
        """生成结构化回复（支持风格系统和三段式结构）"""
        # 构建system prompt
        system_prompt = self._build_structured_system_prompt(parsed, style, plan, interventions)
        
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
                        "stream": False,
                        "options": {
                            "num_predict": 2000  # 增加最大token数，允许更长的回复
                        }
                    }
                )
                response.raise_for_status()
                
                result_data = response.json()
                result_text = result_data.get("message", {}).get("content", "{}")
                logger.info(f"[Ollama Provider] 结构化回复 - 原始API响应: {result_text}")
                
                # 尝试解析JSON（Ollama可能返回带markdown的JSON）
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result_dict = json.loads(result_text)
                
                # 合并三段式回复
                reply_parts = []
                if "emotion_reflection" in result_dict:
                    emotion_part = result_dict["emotion_reflection"]
                    logger.info(f"[Ollama Provider] 情绪镜像部分: {emotion_part} (长度: {len(emotion_part)})")
                    reply_parts.append(emotion_part)
                if "cognitive_clarification" in result_dict:
                    clarification_part = result_dict["cognitive_clarification"]
                    logger.info(f"[Ollama Provider] 认知澄清部分: {clarification_part} (长度: {len(clarification_part)})")
                    reply_parts.append(clarification_part)
                if "action_suggestions" in result_dict:
                    actions = result_dict["action_suggestions"]
                    if isinstance(actions, list):
                        actions_text = "\n\n".join(actions)
                        logger.info(f"[Ollama Provider] 行动建议部分: {actions_text} (长度: {len(actions_text)})")
                        reply_parts.append(actions_text)
                    else:
                        logger.info(f"[Ollama Provider] 行动建议部分: {actions} (长度: {len(actions)})")
                        reply_parts.append(actions)
                
                reply = "\n\n".join(reply_parts) if reply_parts else result_dict.get("reply", "")
                logger.info(f"[Ollama Provider] 最终合并后的完整回复:")
                logger.info(f"  总长度: {len(reply)} 字符")
                logger.info(f"  完整内容:\n{reply}")
                
                # 构建卡片数据
                card_data = {
                    "theme": result_dict.get("theme", ""),
                    "emotion_echo": result_dict.get("emotion_reflection", ""),
                    "clarification": result_dict.get("cognitive_clarification", ""),
                    "suggestion": result_dict.get("action_suggestions", [])
                }
                
                return LLMResult(
                    reply=reply,
                    emotion=result_dict.get("emotion", parsed.emotions[0] if parsed.emotions else "neutral"),
                    intensity=result_dict.get("intensity", parsed.intensity),
                    topics=result_dict.get("topics", [parsed.scene]),
                    risk_level=result_dict.get("risk_level", "high" if parsed.riskLevel == "high" else "normal"),
                    card_data=card_data
                )
        except Exception as e:
            # 如果调用失败，返回一个默认的安全回复
            return LLMResult(
                reply="抱歉，我现在无法处理你的消息。请稍后再试，或者联系专业心理支持。",
                emotion=parsed.emotions[0] if parsed.emotions else "neutral",
                intensity=parsed.intensity,
                topics=[parsed.scene],
                risk_level="high" if parsed.riskLevel == "high" else "normal"
            )
    
    def _build_structured_system_prompt(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: list[InterventionConfig],
    ) -> str:
        """构建支持风格系统的system prompt（与OpenAI相同）"""
        
        # 风格描述
        tone_desc = {
            "gentle": "温和、柔和",
            "neutral": "中性、冷静",
            "firm": "坚定、直接",
            "playful": "轻松、友好",
        }.get(style.tone, "温和")
        
        directness_desc = {
            1: "非常委婉",
            2: "委婉",
            3: "适中",
            4: "直接",
            5: "非常直接",
        }.get(style.directness, "适中")
        
        # 干预模块描述
        from app.core.conversation_algorithm import INTERVENTION_DESCRIPTIONS
        interv_descs = []
        for interv in interventions:
            desc = INTERVENTION_DESCRIPTIONS.get(interv.id, f"干预模块: {interv.id}")
            interv_descs.append(f"- {interv.id}: {desc}")
        interv_text = "\n".join(interv_descs) if interv_descs else "无特定干预模块"
        
        # 结构描述
        parts_desc = {
            "emotion": "情绪镜像与安抚",
            "clarification": "解释与澄清",
            "action": "小步行动建议",
        }
        structure_text = " → ".join([parts_desc.get(p, p) for p in plan.structure.get("parts", [])])
        
        prompt = f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的目标是：接住用户情绪，帮助澄清问题，并给出小而可行的建议。

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 尽量提供充分的共情、理解和建议
- 每部分内容都应该充实，情绪镜像部分至少200-300字，解释澄清部分至少200-300字，行动建议部分至少100-200字
- 可以包含具体的例子、场景描述、情感共鸣等内容
- 让用户感受到被充分理解和关心

当前风格配置：
- 语气: {tone_desc}
- 直白程度: {directness_desc} (1-5，当前为{style.directness})
- 共情比重: {style.emotionFocus}/5
- 理性分析比重: {style.analysisDepth}/5
- 行动建议比重: {style.actionFocus}/5
- 幽默程度: {style.jokingLevel}/5
- 对敏感话题的安全偏好: {style.safetyBias}

请遵守：
- 不使用羞辱、不鼓励自责、不鼓励自伤或他伤
- 避免极端措辞（如"必须"、"永远"、"完全不可能"）
- 避免人格评判（如"你就是太懒"）
- 先回应情绪，再谈分析或建议

当前用户状态：
- 情绪: {', '.join(parsed.emotions)}
- 强度: {parsed.intensity}/10
- 场景: {parsed.scene}
- 风险等级: {parsed.riskLevel}
- 用户目标: {parsed.userGoal}

建议采用的干预模块：
{interv_text}

回复结构要求（按顺序）：
{structure_text}

请按照上述结构生成回复，每部分要自然衔接。对于 risk_level = "high" 的情况，必须：
- 不提供任何具体方法或工具
- 强调理解和关心
- 引导用户联系现实世界可信的人（亲友、老师、医生等）
- 提醒用户尽快寻求专业心理或医疗帮助

请以严格的JSON格式输出，格式如下：
{{
  "theme": "本次对话的核心主题（简洁概括，10-20字）",
  "emotion_reflection": "情绪镜像与安抚部分的内容（情感回音）",
  "cognitive_clarification": "解释与澄清部分的内容（认知澄清）",
  "action_suggestions": ["行动建议1", "行动建议2", "行动建议3"],
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{'high' if parsed.riskLevel == 'high' else 'normal'}"
}}

注意：
- theme 字段是本次对话的核心主题，要简洁明了
- 如果结构中没有某个部分（如listener风格可能没有action），则对应字段可以为空字符串或空数组
- emotion_reflection 对应"情感回音"板块
- cognitive_clarification 对应"认知澄清"板块
- action_suggestions 对应"建议"板块

只输出JSON，不要包含任何其他文本。"""
        
        return prompt

