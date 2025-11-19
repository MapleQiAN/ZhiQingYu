"""
Shared JSON chat provider utilities.
"""
import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List, Literal, Optional

from app.core.llm_provider import LLMProvider, LLMResult
from app.core.prompt_builder import (
    build_simple_prompt,
    build_structured_prompt,
    build_single_step_prompt,
    normalize_risk_level,
    extract_user_question,
    normalize_intensity,
)
from app.schemas.chat import ChatMessage
from app.schemas.style import StyleProfile, ParsedState, ReplyPlan, InterventionConfig


class JsonChatLLMProvider(LLMProvider):
    """Common logic for providers that expect JSON structured chat completions."""

    SAFE_REPLY = "抱歉，我现在无法处理你的消息。请稍后再试，或者联系专业心理支持。"

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def generate_reply(self, messages: List[ChatMessage]) -> LLMResult:
        system_prompt = build_simple_prompt()
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
        conversation_stage: Optional[Literal["chatting", "exploring", "summarizing", "inviting", "card_generated"]] = None,
    ) -> LLMResult:
        system_prompt = build_structured_prompt(parsed, style, plan, interventions, conversation_stage)
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
        system_prompt = build_single_step_prompt(
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
        user_question = extract_user_question(messages) if messages else None
        
        card_data = None
        if any(key in result_dict for key in ("theme", "emotion_reflection", "cognitive_clarification", "action_suggestions")):
            card_data = {
                "theme": result_dict.get("theme", ""),
                "user_question": user_question,  # 用户提问内容
                "emotion_echo": result_dict.get("emotion_reflection", ""),
                "clarification": result_dict.get("cognitive_clarification", ""),
                "suggestion": result_dict.get("action_suggestions", []),
            }

        intensity = normalize_intensity(result_dict.get("intensity", 5), fallback=5)

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
            user_question = extract_user_question(messages) if messages else None

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
            user_question = extract_user_question(messages) if messages else None

            card_data = {
                "theme": result_dict.get("theme", ""),
                "useThreePart": True,  # 标记为3卡片模式
                "user_question": user_question,  # 用户提问内容
                "emotion_echo": result_dict.get("emotion_reflection", ""),
                "clarification": result_dict.get("cognitive_clarification", ""),
                "suggestion": result_dict.get("action_suggestions", []),
            }

        intensity = normalize_intensity(
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
        user_question = extract_user_question(messages) if messages else None
        
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


