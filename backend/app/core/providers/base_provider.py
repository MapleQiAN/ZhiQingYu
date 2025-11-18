"""
Shared JSON chat provider utilities.
"""
import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List, Literal

from app.core.llm_provider import LLMProvider, LLMResult
from app.schemas.chat import ChatMessage
from app.schemas.style import StyleProfile, ParsedState, ReplyPlan, InterventionConfig


def normalize_risk_level(risk_level: str) -> Literal["low", "medium", "high"]:
    """
    规范化风险级别，将旧版的 "normal" 映射为 "low"
    
    Args:
        risk_level: 原始风险级别（可能是 "normal", "low", "medium", "high"）
        
    Returns:
        规范化的风险级别（"low", "medium", 或 "high"）
    """
    if risk_level == "normal":
        return "low"
    if risk_level in ("low", "medium", "high"):
        return risk_level
    # 默认返回 low
    return "low"


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
                risk_level="low",
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
            # 规范化风险级别：parsed.riskLevel 可能是 "low", "medium", "high"
            parsed_risk = normalize_risk_level(parsed.riskLevel) if hasattr(parsed, 'riskLevel') else "low"
            return LLMResult(
                reply=self.SAFE_REPLY,
                emotion=parsed.emotions[0] if parsed.emotions else "neutral",
                intensity=parsed.intensity,
                topics=[parsed.scene],
                risk_level=parsed_risk,
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
            risk_level=normalize_risk_level(result_dict.get("risk_level", "normal")),
            card_data=card_data,
        )

    def _build_structured_result(self, result_dict: Dict[str, Any], parsed: ParsedState) -> LLMResult:
        # 判断是否包含5步骤数据
        has_five_steps = any(
            key.startswith("step") and key.endswith(("_emotion_mirror", "_problem_restate", "_breakdown", "_explanation", "_suggestions", "_summary"))
            for key in result_dict.keys()
        )
        
        if has_five_steps:
            # 5步骤模式：构建5步骤的回复和card_data
            reply_parts: List[str] = []
            
            # Step 1: 情绪接住 & 问题确认
            if result_dict.get("step1_emotion_mirror") or result_dict.get("step1_problem_restate"):
                step1_parts = []
                if result_dict.get("step1_emotion_mirror"):
                    step1_parts.append(result_dict["step1_emotion_mirror"])
                if result_dict.get("step1_problem_restate"):
                    step1_parts.append(result_dict["step1_problem_restate"])
                if step1_parts:
                    reply_parts.append("\n\n".join(step1_parts))
            
            # Step 2: 结构化拆解问题
            if result_dict.get("step2_breakdown"):
                reply_parts.append(result_dict["step2_breakdown"])
            
            # Step 3: 专业视角解释
            if result_dict.get("step3_explanation"):
                reply_parts.append(result_dict["step3_explanation"])
            
            # Step 4: 小步可执行建议
            if result_dict.get("step4_suggestions"):
                suggestions = result_dict["step4_suggestions"]
                if isinstance(suggestions, list):
                    reply_parts.append("\n\n".join(suggestions))
                else:
                    reply_parts.append(suggestions)
            
            # Step 5: 温柔收尾 & 小结
            if result_dict.get("step5_summary"):
                reply_parts.append(result_dict["step5_summary"])
            
            reply = "\n\n".join(reply_parts) if reply_parts else result_dict.get("reply", "")

            card_data = {
                "theme": result_dict.get("theme", ""),
                "useThreePart": False,  # 标记为5步骤模式
                "step1_emotion_mirror": result_dict.get("step1_emotion_mirror", ""),
                "step1_problem_restate": result_dict.get("step1_problem_restate", ""),
                "step2_breakdown": result_dict.get("step2_breakdown", ""),
                "step3_explanation": result_dict.get("step3_explanation", ""),
                "step4_suggestions": result_dict.get("step4_suggestions", []),
                "step5_summary": result_dict.get("step5_summary", ""),
            }
        else:
            # 简洁模式（3卡片模式）：使用原来的格式
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
                "useThreePart": True,  # 标记为3卡片模式
                "emotion_echo": result_dict.get("emotion_reflection", ""),
                "clarification": result_dict.get("cognitive_clarification", ""),
                "suggestion": result_dict.get("action_suggestions", []),
            }

        intensity = self._normalize_intensity(
            result_dict.get("intensity", parsed.intensity),
            fallback=parsed.intensity,
        )

        # 规范化风险级别：从 result_dict 获取，如果没有则使用 parsed.riskLevel
        raw_risk = result_dict.get("risk_level")
        if raw_risk is None:
            # 如果没有从 LLM 返回，使用 parsed 的值
            raw_risk = parsed.riskLevel if hasattr(parsed, 'riskLevel') else "low"
        normalized_risk = normalize_risk_level(raw_risk)
        
        return LLMResult(
            reply=reply,
            emotion=result_dict.get("emotion", parsed.emotions[0] if parsed.emotions else "neutral"),
            intensity=intensity,
            topics=result_dict.get("topics", [parsed.scene]),
            risk_level=normalized_risk,
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
4. 判断风险级别：risk_level 必须是 "low"（低风险）、"medium"（中等风险）或 "high"（高风险，如自残/自杀意念）

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 尽量提供充分的共情、理解和建议
- 回复长度应该在1200字以上，根据用户问题的复杂程度适当调整
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
  "reply": "你的详细自然语言回复（1200字以上）",
  "emotion": "情绪标签",
  "intensity": 情绪强度数字,
  "topics": ["主题1", "主题2"],
  "risk_level": "low"、"medium" 或 "high"（"low"表示低风险，"medium"表示中等风险，"high"表示高风险）
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

        # 规范化风险级别：parsed.riskLevel 应该是 "low", "medium", 或 "high"
        risk_level_value = normalize_risk_level(parsed.riskLevel) if hasattr(parsed, 'riskLevel') else "low"

        # 判断是否使用5步骤模式（当useThreePart为False且stepsToExecute不为空时）
        use_five_steps = (
            not plan.structure.get("useThreePart", True) and 
            hasattr(plan, 'stepsToExecute') and 
            len(plan.stepsToExecute) > 0
        )

        if use_five_steps:
            # 5步骤模式：生成5步骤的card_data
            steps_desc = []
            step_contents = getattr(plan, 'stepContents', {})
            
            step_names = {
                1: "情绪接住 & 问题确认",
                2: "结构化拆解问题",
                3: "专业视角解释（说人话）",
                4: "小步可执行建议",
                5: "温柔收尾 & 小结"
            }
            
            for step_num in plan.stepsToExecute:
                step_name = step_names.get(step_num, f"步骤{step_num}")
                step_info = step_contents.get(step_num, {})
                required_elements = step_info.get("required_elements", {})
                
                step_desc = f"步骤{step_num}：{step_name}\n"
                if step_num == 1:
                    step_desc += f"  - 情绪镜像：{required_elements.get('emotion_mirror', '识别并镜像用户情绪')}\n"
                    step_desc += f"  - 问题复述：{required_elements.get('problem_restate', '用自己的话复述用户问题')}\n"
                elif step_num == 2:
                    step_desc += f"  - 问题拆解：将问题拆成2-3个层面（现实层/情绪层/思维层），用用户的内容作为例子\n"
                elif step_num == 3:
                    step_desc += f"  - 专业解释：引入1-2个心理学概念，用通俗语言解释，结合用户例子\n"
                elif step_num == 4:
                    step_desc += f"  - 行动建议：提供1-3条具体可执行建议，每条包含做什么、什么时候做、大约多久（5-30分钟可完成）\n"
                elif step_num == 5:
                    step_desc += f"  - 收尾小结：简要回顾本轮做了什么，肯定用户努力，提供温和的延续方向\n"
                
                steps_desc.append(step_desc)
            
            steps_text = "\n".join(steps_desc)
            
            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的目标是：按照5步骤系统，从5个层面来回应用户。

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 每个步骤都要独立完整，单独作为一条回复时也能让用户获得实质性的帮助
- 每个步骤的内容要充实，不能只是"下一步预告"
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

本轮要执行的步骤（按顺序）：
{steps_text}

请按照上述步骤生成回复，每个步骤要自然衔接。对于 risk_level = "high" 的情况，必须：
- 不提供任何具体方法或工具
- 强调理解和关心
- 引导用户联系现实世界可信的人（亲友、老师、医生等）
- 提醒用户尽快寻求专业心理或医疗帮助

请以严格的JSON格式输出，格式如下：
{{
  "theme": "本次对话的核心主题（简洁概括，10-20字）",
  "step1_emotion_mirror": "Step 1的情绪镜像句子（识别并镜像用户情绪，明确点出1-2个情绪词）",
  "step1_problem_restate": "Step 1的问题复述段落（用自己的话复述用户问题，整理成更清晰的表达）",
  "step2_breakdown": "Step 2的问题拆解内容（将问题拆成2-3个层面，用用户的内容作为例子）",
  "step3_explanation": "Step 3的专业解释内容（引入1-2个心理学概念，用通俗语言解释，结合用户例子）",
  "step4_suggestions": ["Step 4的建议1（做什么、什么时候做、大约多久）", "Step 4的建议2", "Step 4的建议3"],
  "step5_summary": "Step 5的收尾小结（简要回顾、肯定用户努力、提供延续方向）",
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{risk_level_value}"
}}

注意：
- theme 字段是本次对话的核心主题，要简洁明了
- 如果某个步骤不在stepsToExecute中，则对应字段可以为空字符串或空数组
- step1_emotion_mirror 和 step1_problem_restate 是Step 1的两个必需要素
- step2_breakdown 是Step 2的必需要素
- step3_explanation 是Step 3的必需要素
- step4_suggestions 是Step 4的必需要素（数组格式，每条建议要具体可执行）
- step5_summary 是Step 5的必需要素

只输出JSON，不要包含任何其他文本。"""
        else:
            # 简洁模式（3卡片模式）：使用原来的格式
            parts_desc = {
                "emotion": "情绪镜像与安抚",
                "clarification": "解释与澄清",
                "action": "小步行动建议",
            }
            structure_text = " → ".join([parts_desc.get(p, p) for p in plan.structure.get("parts", [])])

            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的目标是：接住用户情绪，帮助澄清问题，并给出小而可行的建议。

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 尽量提供充分的共情、理解和建议
- 每部分内容都应该充实，情绪镜像部分至少500字，解释澄清部分至少500字，行动建议部分至少300字
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

