"""
Shared JSON chat provider utilities.
"""
import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List

from app.core.llm_provider import LLMProvider, LLMResult
from app.schemas.chat import ChatMessage
from app.schemas.style import StyleProfile, ParsedState, ReplyPlan, InterventionConfig


class JsonChatLLMProvider(LLMProvider):
    """Common logic for providers that expect JSON structured chat completions."""

    SAFE_REPLY = "抱歉，我现在无法处理你的消息。请稍后再试，或者联系专业心理支持。"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def generate_reply(self, messages: List[ChatMessage]) -> LLMResult:
        system_prompt = self._build_system_prompt()
        chat_messages = self._format_messages(system_prompt, messages)

        try:
            result_text = self._perform_chat_completion(chat_messages, mode="simple")
            result_dict = self._parse_json_payload(result_text)
            return self._build_simple_result(result_dict)
        except Exception:
            self.logger.exception("[LLM Provider] generate_reply failed, returning safe response")
            return LLMResult(
                reply=self.SAFE_REPLY,
                emotion="neutral",
                intensity=2,
                topics=[],
                risk_level="normal",
            )

    def generate_structured_reply(
        self,
        messages: List[ChatMessage],
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: List[InterventionConfig],
    ) -> LLMResult:
        system_prompt = self._build_structured_system_prompt(parsed, style, plan, interventions)
        chat_messages = self._format_messages(system_prompt, messages)

        try:
            result_text = self._perform_chat_completion(chat_messages, mode="structured")
            result_dict = self._parse_json_payload(result_text)
            return self._build_structured_result(result_dict, parsed)
        except Exception:
            self.logger.exception("[LLM Provider] generate_structured_reply failed, returning safe response")
            return LLMResult(
                reply=self.SAFE_REPLY,
                emotion=parsed.emotions[0] if parsed.emotions else "neutral",
                intensity=parsed.intensity,
                topics=[parsed.scene],
                risk_level="high" if parsed.riskLevel == "high" else "normal",
            )

    @abstractmethod
    def _perform_chat_completion(self, chat_messages: List[Dict[str, str]], mode: str) -> str:
        """Subclasses must implement the actual API call and return raw JSON string."""

    def _format_messages(self, system_prompt: str, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        formatted = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    def _parse_json_payload(self, payload: str) -> Dict[str, Any]:
        text = payload.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0]
        elif text.startswith("```") and "```" in text[3:]:
            text = text.split("```", 1)[1]
            text = text.split("```", 1)[0]
        return json.loads(text.strip())

    def _build_simple_result(self, result_dict: Dict[str, Any]) -> LLMResult:
        reply = result_dict.get("reply", "")
        card_data = None
        if any(key in result_dict for key in ("theme", "emotion_reflection", "cognitive_clarification", "action_suggestions")):
            card_data = {
                "theme": result_dict.get("theme", ""),
                "emotion_echo": result_dict.get("emotion_reflection", ""),
                "clarification": result_dict.get("cognitive_clarification", ""),
                "suggestion": result_dict.get("action_suggestions", []),
            }

        intensity = self._normalize_intensity(result_dict.get("intensity", 5), fallback=5)

        return LLMResult(
            reply=reply,
            emotion=result_dict.get("emotion", "neutral"),
            intensity=intensity,
            topics=result_dict.get("topics", []),
            risk_level=result_dict.get("risk_level", "normal"),
            card_data=card_data,
        )

    def _build_structured_result(self, result_dict: Dict[str, Any], parsed: ParsedState) -> LLMResult:
        reply_parts: List[str] = []
        if "emotion_reflection" in result_dict:
            reply_parts.append(result_dict["emotion_reflection"])
        if "cognitive_clarification" in result_dict:
            reply_parts.append(result_dict["cognitive_clarification"])
        if "action_suggestions" in result_dict:
            actions = result_dict["action_suggestions"]
            if isinstance(actions, list):
                reply_parts.append("\n\n".join(actions))
            else:
                reply_parts.append(actions)

        reply = "\n\n".join(reply_parts) if reply_parts else result_dict.get("reply", "")

        card_data = {
            "theme": result_dict.get("theme", ""),
            "emotion_echo": result_dict.get("emotion_reflection", ""),
            "clarification": result_dict.get("cognitive_clarification", ""),
            "suggestion": result_dict.get("action_suggestions", []),
        }

        intensity = self._normalize_intensity(
            result_dict.get("intensity", parsed.intensity),
            fallback=parsed.intensity,
        )

        return LLMResult(
            reply=reply,
            emotion=result_dict.get("emotion", parsed.emotions[0] if parsed.emotions else "neutral"),
            intensity=intensity,
            topics=result_dict.get("topics", [parsed.scene]),
            risk_level=result_dict.get("risk_level", "high" if parsed.riskLevel == "high" else "normal"),
            card_data=card_data,
        )

    def _normalize_intensity(self, raw_value: Any, fallback: int) -> int:
        if isinstance(raw_value, (int, float)):
            if 1 <= raw_value <= 5:
                raw_value = int((raw_value - 1) * 2.25 + 1)
            value = int(raw_value)
            return max(1, min(10, value))
        return fallback

    def _build_system_prompt(self) -> str:
        return """你是一位情绪陪伴助手，不是心理医生，不进行诊断，不提供药物建议。

你的任务是：
1. 理解用户当前的情绪和困扰场景
2. 用温和、现实的语气输出一段详细、丰富的自然语言回复
3. 为用户这条消息打标签：
   - emotion: 从以下选项中选择一个：sadness, anxiety, anger, guilt, shame, fear, tired, overwhelmed, confusion, joy, relief, calm, neutral
   - intensity: 1-10的整数，表示情绪强度（1-3为轻度，4-6为中度，7-8为重度，9-10为极重度）
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

    def _build_structured_system_prompt(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: List[InterventionConfig],
    ) -> str:
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

        from app.core.conversation_algorithm import INTERVENTION_DESCRIPTIONS

        interv_descs = []
        for interv in interventions:
            desc = INTERVENTION_DESCRIPTIONS.get(interv.id, f"干预模块: {interv.id}")
            interv_descs.append(f"- {interv.id}: {desc}")
        interv_text = "\n".join(interv_descs) if interv_descs else "无特定干预模块"

        parts_desc = {
            "emotion": "情绪镜像与安抚",
            "clarification": "解释与澄清",
            "action": "小步行动建议",
        }
        structure_text = " → ".join([parts_desc.get(p, p) for p in plan.structure.get("parts", [])])

        risk_level_value = "high" if parsed.riskLevel == "high" else "normal"

        return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

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
  "risk_level": "{risk_level_value}"
}}

注意：
- theme 字段是本次对话的核心主题，要简洁明了
- 如果结构中没有某个部分（如listener风格可能没有action），则对应字段可以为空字符串或空数组
- emotion_reflection 对应"情感回音"板块
- cognitive_clarification 对应"认知澄清"板块
- action_suggestions 对应"建议"板块

只输出JSON，不要包含任何其他文本。"""

