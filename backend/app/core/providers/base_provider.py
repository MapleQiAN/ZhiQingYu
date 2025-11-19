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
            result = self._perform_chat_completion(chat_messages, mode="simple")
            # result可以是字符串（旧格式）或字典（新格式，包含text和usage）
            if isinstance(result, dict):
                result_text = result.get("text", "")
                usage_info = result.get("usage", {})
            else:
                result_text = result
                usage_info = {}
            
            # 检查result_text是否有效
            if not result_text or (isinstance(result_text, str) and not result_text.strip()):
                self.logger.error("[LLM Provider] API返回的文本为空")
                raise ValueError("API返回的文本为空")
            
            result_dict = self._parse_json_payload(result_text)
            llm_result = self._build_simple_result(result_dict, messages)
            # 设置tokens信息
            if usage_info:
                llm_result.prompt_tokens = usage_info.get("prompt_tokens")
                llm_result.completion_tokens = usage_info.get("completion_tokens")
                llm_result.total_tokens = usage_info.get("total_tokens")
            return llm_result
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
            result = self._perform_chat_completion(chat_messages, mode="structured")
            # result可以是字符串（旧格式）或字典（新格式，包含text和usage）
            if isinstance(result, dict):
                result_text = result.get("text", "")
                usage_info = result.get("usage", {})
            else:
                result_text = result
                usage_info = {}
            
            # 检查result_text是否有效
            if not result_text or (isinstance(result_text, str) and not result_text.strip()):
                self.logger.error("[LLM Provider] API返回的文本为空")
                raise ValueError("API返回的文本为空")
            
            result_dict = self._parse_json_payload(result_text)
            llm_result = self._build_structured_result(result_dict, parsed, messages)
            # 设置tokens信息
            if usage_info:
                llm_result.prompt_tokens = usage_info.get("prompt_tokens")
                llm_result.completion_tokens = usage_info.get("completion_tokens")
                llm_result.total_tokens = usage_info.get("total_tokens")
            return llm_result
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

    def generate_deep_chat_reply(
        self,
        messages: List[ChatMessage],
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: List[InterventionConfig],
    ) -> LLMResult:
        """
        深聊模式：分别调用5次AI请求，每个步骤一次，然后整合结果
        
        Args:
            messages: 对话消息列表
            parsed: 情绪解析结果
            style: 风格配置
            plan: 回复计划
            interventions: 干预模块列表
            
        Returns:
            LLMResult: 整合后的回复结果
        """
        self.logger.info("[Deep Chat] 开始深聊模式：分别生成5个步骤")
        
        # 存储每个步骤的结果
        step_results = {}
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        
        # 获取步骤内容规划
        step_contents = getattr(plan, 'stepContents', {})
        steps_to_execute = getattr(plan, 'stepsToExecute', [1, 2, 3, 4, 5])
        
        # 按顺序生成每个步骤
        for step_num in steps_to_execute:
            try:
                self.logger.info(f"[Deep Chat] 正在生成步骤 {step_num}")
                
                # 为当前步骤生成内容
                step_result = self.generate_single_step(
                    step_num=step_num,
                    messages=messages,
                    parsed=parsed,
                    style=style,
                    plan=plan,
                    interventions=interventions,
                    previous_steps=step_results  # 传递已完成的步骤，用于上下文
                )
                
                step_results[step_num] = step_result
                
                # 累加tokens
                if step_result.get("usage"):
                    total_prompt_tokens += step_result["usage"].get("prompt_tokens", 0)
                    total_completion_tokens += step_result["usage"].get("completion_tokens", 0)
                    total_tokens += step_result["usage"].get("total_tokens", 0)
                
            except Exception as e:
                self.logger.error(f"[Deep Chat] 步骤 {step_num} 生成失败: {str(e)}", exc_info=True)
                # 如果某个步骤失败，使用默认值
                step_results[step_num] = {"content": "", "data": {}}
        
        # 整合所有步骤的结果
        return self._build_deep_chat_result(step_results, parsed, total_prompt_tokens, total_completion_tokens, total_tokens, messages)

    def generate_single_step(
        self,
        step_num: int,
        messages: List[ChatMessage],
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: List[InterventionConfig],
        previous_steps: Dict[int, Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        为单个步骤生成内容
        
        Args:
            step_num: 步骤编号 (1-5)
            messages: 对话消息列表
            parsed: 情绪解析结果
            style: 风格配置
            plan: 回复计划
            interventions: 干预模块列表
            previous_steps: 已完成的步骤结果（用于上下文）
            
        Returns:
            包含步骤内容和usage信息的字典
        """
        if previous_steps is None:
            previous_steps = {}
        
        # 构建单个步骤的系统提示词
        system_prompt = self._build_single_step_system_prompt(
            step_num=step_num,
            parsed=parsed,
            style=style,
            plan=plan,
            interventions=interventions,
            previous_steps=previous_steps
        )
        
        # 格式化消息
        chat_messages = self._format_messages(system_prompt, messages)
        
        # 调用AI生成
        try:
            result = self._perform_chat_completion(chat_messages, mode="structured")
            
            # 解析结果
            if isinstance(result, dict):
                result_text = result.get("text", "")
                usage_info = result.get("usage", {})
            else:
                result_text = result
                usage_info = {}
            
            # 检查result_text是否有效
            if not result_text or (isinstance(result_text, str) and not result_text.strip()):
                self.logger.error(f"[Deep Chat] 步骤 {step_num} API返回的文本为空")
                raise ValueError(f"步骤 {step_num} API返回的文本为空")
            
            result_dict = self._parse_json_payload(result_text)
            
            return {
                "content": result_dict,
                "data": result_dict,
                "usage": usage_info
            }
        except Exception as e:
            self.logger.error(f"[Deep Chat] 步骤 {step_num} AI调用失败: {str(e)}", exc_info=True)
            return {
                "content": {},
                "data": {},
                "usage": {}
            }

    @abstractmethod
    def _perform_chat_completion(self, chat_messages: List[Dict[str, str]], mode: str) -> str | dict:
        """
        Subclasses must implement the actual API call and return raw JSON string or dict.
        
        Returns:
            str: Raw JSON string (legacy format)
            dict: {"text": str, "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}} (new format)
        """

    def _format_messages(self, system_prompt: str, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        formatted = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    def _parse_json_payload(self, payload: str) -> Dict[str, Any]:
        if payload is None:
            self.logger.error("[JSON Parser] payload为None")
            raise ValueError("无法解析JSON：payload为None")
        
        if not isinstance(payload, str):
            self.logger.error(f"[JSON Parser] payload类型错误: {type(payload)}")
            raise ValueError(f"无法解析JSON：payload类型错误，期望str，得到{type(payload)}")
        
        text = payload.strip()
        if not text:
            self.logger.error("[JSON Parser] payload为空字符串")
            raise ValueError("无法解析JSON：payload为空")
        
        # 处理常见的LLM输出包装，例如 ```json``` 或 ``` 块
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0]
        elif text.startswith("```") and "```" in text[3:]:
            text = text.split("```", 1)[1]
            text = text.split("```", 1)[0]
        
        # 移除可能存在的思考标签，例如 <think>...</think>
        for tag in ("think", "reasoning", "reflection"):
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            if start_tag in text and end_tag in text:
                text = text.split(end_tag, 1)[1]
        
        text = text.strip()
        if not text:
            self.logger.error("[JSON Parser] 清理后的文本为空")
            raise ValueError("无法解析JSON：清理后的文本为空")
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.logger.warning(f"[JSON Parser] JSON解析失败，尝试提取JSON对象: {str(e)}")
            extracted = self._extract_json_object(text)
            if extracted:
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    self.logger.error(f"[JSON Parser] 提取的JSON对象仍然无法解析: {extracted[:200]}")
                    raise ValueError(f"无法解析JSON：{str(e)}")
            self.logger.error(f"[JSON Parser] 无法从文本中提取JSON对象: {text[:200]}")
            raise ValueError(f"无法解析JSON：{str(e)}")

    def _extract_json_object(self, text: str) -> str | None:
        """
        从包含额外说明文字的文本中尝试提取第一个完整的JSON对象。
        """
        in_string = False
        escape = False
        depth = 0
        start_index = None
        for idx, char in enumerate(text):
            if in_string:
                if escape:
                    escape = False
                    continue
                if char == "\\":
                    escape = True
                    continue
                if char == '"':
                    in_string = False
                continue
            else:
                if char == '"':
                    in_string = True
                    continue
                if char == "{":
                    if depth == 0:
                        start_index = idx
                    depth += 1
                elif char == "}":
                    if depth > 0:
                        depth -= 1
                        if depth == 0 and start_index is not None:
                            return text[start_index : idx + 1]
        return None

    def _build_simple_result(self, result_dict: Dict[str, Any], messages: List[ChatMessage] = None) -> LLMResult:
        reply = result_dict.get("reply", "")
        
        # 提取用户提问内容
        user_question = None
        if messages:
            user_messages = [msg.content for msg in messages if msg.role == "user"]
            if user_messages:
                if len(user_messages) == 1:
                    user_question = user_messages[0].strip()
                else:
                    user_question = user_messages[-1].strip()
                    if len(user_question) < 20 and len(user_messages) > 1:
                        combined = " ".join(user_messages[-2:]).strip()
                        if len(combined) <= 200:
                            user_question = combined
        
        card_data = None
        if any(key in result_dict for key in ("theme", "emotion_reflection", "cognitive_clarification", "action_suggestions")):
            card_data = {
                "theme": result_dict.get("theme", ""),
                "user_question": user_question,  # 用户提问内容
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
            prompt_tokens=None,  # 由子类在_perform_chat_completion中设置
            completion_tokens=None,
            total_tokens=None,
        )

    def _build_structured_result(self, result_dict: Dict[str, Any], parsed: ParsedState, messages: List[ChatMessage] = None) -> LLMResult:
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

            # 提取用户提问内容
            user_question = None
            if messages:
                user_messages = [msg.content for msg in messages if msg.role == "user"]
                if user_messages:
                    if len(user_messages) == 1:
                        user_question = user_messages[0].strip()
                    else:
                        user_question = user_messages[-1].strip()
                        if len(user_question) < 20 and len(user_messages) > 1:
                            combined = " ".join(user_messages[-2:]).strip()
                            if len(combined) <= 200:
                                user_question = combined

            card_data = {
                "theme": result_dict.get("theme", ""),
                "useThreePart": False,  # 标记为5步骤模式
                "user_question": user_question,  # 用户提问内容
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

            # 提取用户提问内容
            user_question = None
            if messages:
                user_messages = [msg.content for msg in messages if msg.role == "user"]
                if user_messages:
                    if len(user_messages) == 1:
                        user_question = user_messages[0].strip()
                    else:
                        user_question = user_messages[-1].strip()
                        if len(user_question) < 20 and len(user_messages) > 1:
                            combined = " ".join(user_messages[-2:]).strip()
                            if len(combined) <= 200:
                                user_question = combined

            card_data = {
                "theme": result_dict.get("theme", ""),
                "useThreePart": True,  # 标记为3卡片模式
                "user_question": user_question,  # 用户提问内容
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
            prompt_tokens=None,  # 由子类在_perform_chat_completion中设置
            completion_tokens=None,
            total_tokens=None,
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

    def _build_single_step_system_prompt(
        self,
        step_num: int,
        parsed: ParsedState,
        style: StyleProfile,
        plan: ReplyPlan,
        interventions: List[InterventionConfig],
        previous_steps: Dict[int, Dict[str, Any]] = None,
    ) -> str:
        """
        为单个步骤构建系统提示词
        
        Args:
            step_num: 步骤编号 (1-5)
            parsed: 情绪解析结果
            style: 风格配置
            plan: 回复计划
            interventions: 干预模块列表
            previous_steps: 已完成的步骤结果（用于上下文）
            
        Returns:
            系统提示词字符串
        """
        if previous_steps is None:
            previous_steps = {}
        
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

        risk_level_value = normalize_risk_level(parsed.riskLevel) if hasattr(parsed, 'riskLevel') else "low"

        # 获取当前步骤的规划内容
        step_contents = getattr(plan, 'stepContents', {})
        step_info = step_contents.get(step_num, {})
        required_elements = step_info.get("required_elements", {})
        
        # 步骤描述
        step_names = {
            1: "情绪接住 & 问题确认",
            2: "结构化拆解问题",
            3: "专业视角解释（说人话）",
            4: "小步可执行建议",
            5: "温柔收尾 & 小结"
        }
        step_name = step_names.get(step_num, f"步骤{step_num}")
        
        # 构建已完成的步骤上下文（用于后续步骤参考）
        previous_context = ""
        if previous_steps:
            previous_context = "\n\n已完成的步骤：\n"
            for prev_step_num in sorted(previous_steps.keys()):
                prev_data = previous_steps[prev_step_num].get("data", {})
                if prev_step_num == 1:
                    if prev_data.get("step1_emotion_mirror"):
                        previous_context += f"- 步骤1（情绪接住）：{prev_data.get('step1_emotion_mirror', '')[:100]}...\n"
                    if prev_data.get("step1_problem_restate"):
                        previous_context += f"- 步骤1（问题复述）：{prev_data.get('step1_problem_restate', '')[:100]}...\n"
                elif prev_step_num == 2:
                    if prev_data.get("step2_breakdown"):
                        previous_context += f"- 步骤2（问题拆解）：{prev_data.get('step2_breakdown', '')[:100]}...\n"
                elif prev_step_num == 3:
                    if prev_data.get("step3_explanation"):
                        previous_context += f"- 步骤3（专业解释）：{prev_data.get('step3_explanation', '')[:100]}...\n"
                elif prev_step_num == 4:
                    if prev_data.get("step4_suggestions"):
                        suggestions = prev_data.get("step4_suggestions", [])
                        if isinstance(suggestions, list):
                            previous_context += f"- 步骤4（行动建议）：{len(suggestions)}条建议\n"
                        else:
                            previous_context += f"- 步骤4（行动建议）：{str(suggestions)[:100]}...\n"
                elif prev_step_num == 5:
                    if prev_data.get("step5_summary"):
                        previous_context += f"- 步骤5（收尾小结）：{prev_data.get('step5_summary', '')[:100]}...\n"
        
        # 根据步骤编号构建不同的提示词
        if step_num == 1:
            # Step 1: 情绪接住 & 问题确认
            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的任务是：完成步骤1 - {step_name}

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 内容要充实，不能只是"下一步预告"
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

步骤1的具体要求：
- 情绪镜像：{required_elements.get('emotion_mirror', '识别并镜像用户情绪，明确点出1-2个情绪词')}
- 问题复述：{required_elements.get('problem_restate', '用自己的话复述用户问题，整理成更清晰的表达')}
{'- 正常化：' + required_elements.get('normalization', '') if required_elements.get('normalization') else ''}

{previous_context}

请以严格的JSON格式输出，格式如下：
{{
  "step1_emotion_mirror": "情绪镜像句子（识别并镜像用户情绪，明确点出1-2个情绪词，200-300字）",
  "step1_problem_restate": "问题复述段落（用自己的话复述用户问题，整理成更清晰的表达，300-500字）",
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{risk_level_value}"
}}

只输出JSON，不要包含任何其他文本。"""

        elif step_num == 2:
            # Step 2: 结构化拆解问题
            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的任务是：完成步骤2 - {step_name}

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 内容要充实，不能只是"下一步预告"
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

当前用户状态：
- 情绪: {', '.join(parsed.emotions)}
- 强度: {parsed.intensity}/10
- 场景: {parsed.scene}
- 风险等级: {parsed.riskLevel}
- 用户目标: {parsed.userGoal}

建议采用的干预模块：
{interv_text}

步骤2的具体要求：
- 问题拆解：将问题拆成2-3个层面（现实层/情绪层/思维层），用用户的内容作为例子
- 每个层面都要详细说明，不能只是简单列举
- 用用户的具体内容作为例子来说明每个层面

{previous_context}

请以严格的JSON格式输出，格式如下：
{{
  "step2_breakdown": "问题拆解内容（将问题拆成2-3个层面，用用户的内容作为例子，500-800字）",
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{risk_level_value}"
}}

只输出JSON，不要包含任何其他文本。"""

        elif step_num == 3:
            # Step 3: 专业视角解释（说人话）
            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的任务是：完成步骤3 - {step_name}

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 内容要充实，不能只是"下一步预告"
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

当前用户状态：
- 情绪: {', '.join(parsed.emotions)}
- 强度: {parsed.intensity}/10
- 场景: {parsed.scene}
- 风险等级: {parsed.riskLevel}
- 用户目标: {parsed.userGoal}

建议采用的干预模块：
{interv_text}

步骤3的具体要求：
- 专业解释：引入1-2个心理学概念，用通俗语言解释，结合用户例子
- 不要使用过于专业的术语，要用"说人话"的方式解释
- 每个概念都要结合用户的具体情况来说明

{previous_context}

请以严格的JSON格式输出，格式如下：
{{
  "step3_explanation": "专业解释内容（引入1-2个心理学概念，用通俗语言解释，结合用户例子，500-800字）",
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{risk_level_value}"
}}

只输出JSON，不要包含任何其他文本。"""

        elif step_num == 4:
            # Step 4: 小步可执行建议
            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的任务是：完成步骤4 - {step_name}

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 内容要充实，不能只是"下一步预告"
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

当前用户状态：
- 情绪: {', '.join(parsed.emotions)}
- 强度: {parsed.intensity}/10
- 场景: {parsed.scene}
- 风险等级: {parsed.riskLevel}
- 用户目标: {parsed.userGoal}

建议采用的干预模块：
{interv_text}

步骤4的具体要求：
- 行动建议：提供1-3条具体可执行建议，每条包含做什么、什么时候做、大约多久（5-30分钟可完成）
- 每条建议都要具体、可操作，不能是空泛的"要努力"、"要加油"等
- 建议要小而可行，让用户能够立即开始执行

{previous_context}

对于 risk_level = "high" 的情况，必须：
- 不提供任何具体方法或工具
- 强调理解和关心
- 引导用户联系现实世界可信的人（亲友、老师、医生等）
- 提醒用户尽快寻求专业心理或医疗帮助

请以严格的JSON格式输出，格式如下：
{{
  "step4_suggestions": ["建议1（做什么、什么时候做、大约多久）", "建议2", "建议3"],
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{risk_level_value}"
}}

只输出JSON，不要包含任何其他文本。"""

        elif step_num == 5:
            # Step 5: 温柔收尾 & 小结
            return f"""你是一个情绪陪伴 AI，受过基础心理学训练，但不是医生，不进行诊断或治疗。

你的任务是：完成步骤5 - {step_name}

重要要求：
- 你的回复应该详细、丰富、有深度，不要过于简短
- 内容要充实，不能只是"下一步预告"
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

当前用户状态：
- 情绪: {', '.join(parsed.emotions)}
- 强度: {parsed.intensity}/10
- 场景: {parsed.scene}
- 风险等级: {parsed.riskLevel}
- 用户目标: {parsed.userGoal}

建议采用的干预模块：
{interv_text}

步骤5的具体要求：
- 收尾小结：简要回顾本轮做了什么，肯定用户努力，提供温和的延续方向
- 回顾要简洁但全面，涵盖前面4个步骤的主要内容
- 肯定用户的努力和勇气，给予鼓励
- 提供温和的延续方向，不要给用户压力

{previous_context}

请以严格的JSON格式输出，格式如下：
{{
  "step5_summary": "收尾小结（简要回顾、肯定用户努力、提供延续方向，300-500字）",
  "theme": "本次对话的核心主题（简洁概括，10-20字）",
  "emotion": "情绪标签（从用户情绪中选择一个）",
  "intensity": {parsed.intensity},
  "topics": ["主题1", "主题2"],
  "risk_level": "{risk_level_value}"
}}

只输出JSON，不要包含任何其他文本。"""

        else:
            # 未知步骤，返回通用提示词
            return f"""你是一个情绪陪伴 AI，请完成步骤{step_num}。"""

    def _build_deep_chat_result(
        self,
        step_results: Dict[int, Dict[str, Any]],
        parsed: ParsedState,
        total_prompt_tokens: int,
        total_completion_tokens: int,
        total_tokens: int,
        messages: List[ChatMessage] = None,
    ) -> LLMResult:
        """
        整合5个步骤的结果，构建最终的LLMResult
        
        Args:
            step_results: 每个步骤的结果字典 {step_num: {content: dict, data: dict, usage: dict}}
            parsed: 情绪解析结果
            total_prompt_tokens: 总prompt tokens
            total_completion_tokens: 总completion tokens
            total_tokens: 总tokens
            
        Returns:
            LLMResult: 整合后的回复结果
        """
        # 整合所有步骤的数据
        combined_data = {
            "theme": "",
            "step1_emotion_mirror": "",
            "step1_problem_restate": "",
            "step2_breakdown": "",
            "step3_explanation": "",
            "step4_suggestions": [],
            "step5_summary": "",
            "emotion": parsed.emotions[0] if parsed.emotions else "neutral",
            "intensity": parsed.intensity,
            "topics": [parsed.scene],
            "risk_level": normalize_risk_level(parsed.riskLevel) if hasattr(parsed, 'riskLevel') else "low"
        }
        
        # 从每个步骤的结果中提取数据
        for step_num in [1, 2, 3, 4, 5]:
            step_data = step_results.get(step_num, {}).get("data", {})
            
            if step_num == 1:
                combined_data["step1_emotion_mirror"] = step_data.get("step1_emotion_mirror", "")
                combined_data["step1_problem_restate"] = step_data.get("step1_problem_restate", "")
                # 从step1获取emotion和topics（如果存在）
                if step_data.get("emotion"):
                    combined_data["emotion"] = step_data["emotion"]
                if step_data.get("topics"):
                    combined_data["topics"] = step_data["topics"]
            elif step_num == 2:
                combined_data["step2_breakdown"] = step_data.get("step2_breakdown", "")
            elif step_num == 3:
                combined_data["step3_explanation"] = step_data.get("step3_explanation", "")
            elif step_num == 4:
                suggestions = step_data.get("step4_suggestions", [])
                if isinstance(suggestions, list):
                    combined_data["step4_suggestions"] = suggestions
                else:
                    combined_data["step4_suggestions"] = [suggestions] if suggestions else []
            elif step_num == 5:
                combined_data["step5_summary"] = step_data.get("step5_summary", "")
                # 从step5获取theme（如果存在）
                if step_data.get("theme"):
                    combined_data["theme"] = step_data["theme"]
                # 从step5获取risk_level（如果存在）
                if step_data.get("risk_level"):
                    combined_data["risk_level"] = normalize_risk_level(step_data["risk_level"])
        
        # 构建回复文本（整合所有步骤）
        reply_parts = []
        
        # Step 1
        if combined_data["step1_emotion_mirror"] or combined_data["step1_problem_restate"]:
            step1_parts = []
            if combined_data["step1_emotion_mirror"]:
                step1_parts.append(combined_data["step1_emotion_mirror"])
            if combined_data["step1_problem_restate"]:
                step1_parts.append(combined_data["step1_problem_restate"])
            if step1_parts:
                reply_parts.append("\n\n".join(step1_parts))
        
        # Step 2
        if combined_data["step2_breakdown"]:
            reply_parts.append(combined_data["step2_breakdown"])
        
        # Step 3
        if combined_data["step3_explanation"]:
            reply_parts.append(combined_data["step3_explanation"])
        
        # Step 4
        if combined_data["step4_suggestions"]:
            suggestions = combined_data["step4_suggestions"]
            if isinstance(suggestions, list):
                reply_parts.append("\n\n".join(suggestions))
            else:
                reply_parts.append(suggestions)
        
        # Step 5
        if combined_data["step5_summary"]:
            reply_parts.append(combined_data["step5_summary"])
        
        reply = "\n\n".join(reply_parts) if reply_parts else "抱歉，我无法生成回复。"
        
        # 提取用户提问内容
        user_question = None
        if messages:
            # 收集所有用户消息
            user_messages = [msg.content for msg in messages if msg.role == "user"]
            if user_messages:
                # 如果只有一条用户消息，直接使用
                if len(user_messages) == 1:
                    user_question = user_messages[0].strip()
                else:
                    # 如果有多条，可以总结或使用最后一条
                    # 这里使用最后一条用户消息，因为它通常是最新的问题
                    user_question = user_messages[-1].strip()
                    # 如果最后一条太短，可以结合前面的消息
                    if len(user_question) < 20 and len(user_messages) > 1:
                        # 结合最后两条用户消息
                        combined = " ".join(user_messages[-2:]).strip()
                        if len(combined) <= 200:  # 限制长度
                            user_question = combined
        
        # 构建card_data
        card_data = {
            "theme": combined_data["theme"],
            "useThreePart": False,  # 标记为5步骤模式
            "user_question": user_question,  # 用户提问内容
            "step1_emotion_mirror": combined_data["step1_emotion_mirror"],
            "step1_problem_restate": combined_data["step1_problem_restate"],
            "step2_breakdown": combined_data["step2_breakdown"],
            "step3_explanation": combined_data["step3_explanation"],
            "step4_suggestions": combined_data["step4_suggestions"],
            "step5_summary": combined_data["step5_summary"],
        }
        
        return LLMResult(
            reply=reply,
            emotion=combined_data["emotion"],
            intensity=combined_data["intensity"],
            topics=combined_data["topics"],
            risk_level=combined_data["risk_level"],
            card_data=card_data,
            prompt_tokens=total_prompt_tokens if total_prompt_tokens > 0 else None,
            completion_tokens=total_completion_tokens if total_completion_tokens > 0 else None,
            total_tokens=total_tokens if total_tokens > 0 else None,
        )

