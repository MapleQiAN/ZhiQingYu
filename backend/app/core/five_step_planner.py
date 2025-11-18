"""
5步骤回复规划器：规划Step 1-5的具体内容
"""
from typing import Optional
from app.schemas.style import (
    ParsedState, StyleProfile, ReplyPlan, InterventionConfig
)


class FiveStepPlanner:
    """5步骤回复规划器"""
    
    def plan_steps(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        interventions: list[InterventionConfig],
        steps_to_execute: list[int],
        conversation_state: Optional[dict] = None
    ) -> ReplyPlan:
        """
        规划5步骤的具体内容
        
        Args:
            parsed: 情绪解析结果
            style: 当前风格
            interventions: 干预模块列表
            steps_to_execute: 要执行的步骤列表 (1-5)
            conversation_state: 对话状态（可选，用于多轮对话）
            
        Returns:
            ReplyPlan: 包含步骤规划的回复计划
        """
        step_contents = {}
        
        for step_num in steps_to_execute:
            if step_num == 1:
                step_contents[1] = self._plan_step1(parsed, style)
            elif step_num == 2:
                step_contents[2] = self._plan_step2(parsed, style, conversation_state)
            elif step_num == 3:
                step_contents[3] = self._plan_step3(parsed, style, interventions, conversation_state)
            elif step_num == 4:
                step_contents[4] = self._plan_step4(parsed, style, interventions, conversation_state)
            elif step_num == 5:
                step_contents[5] = self._plan_step5(parsed, style, conversation_state)
        
        # 构建ReplyPlan（保持兼容性）
        # useThreePart: False表示使用5步骤模式（5卡片），True表示使用简洁模式（3卡片）
        # 当执行5步骤时，useThreePart应该为False
        # 只有当明确需要简洁模式时（如某些特定风格），才设置为True
        structure = {
            "useThreePart": False,  # 默认使用5步骤模式
            "parts": self._map_steps_to_parts(steps_to_execute)
        }
        
        return ReplyPlan(
            style=style,
            interventions=[i.id for i in interventions],
            structure=structure,
            stepsToExecute=steps_to_execute,
            stepContents=step_contents
        )
    
    def _plan_step1(self, parsed: ParsedState, style: StyleProfile) -> dict:
        """
        Step 1: 情绪接住 & 问题确认
        
        必需要素：
        - emotion_mirror: 情绪镜像句子
        - problem_restate: 问题复述段落
        - normalization: 简单正常化（可选）
        """
        # 提取主要情绪（1-2个）
        main_emotions = parsed.emotions[:2] if len(parsed.emotions) > 0 else ["neutral"]
        emotion_names = {
            "anxiety": "焦虑", "sadness": "难过", "anger": "愤怒", "guilt": "内疚",
            "shame": "羞耻", "fear": "害怕", "tired": "疲惫", "overwhelmed": "崩溃",
            "confusion": "困惑", "joy": "开心", "relief": "放松", "calm": "平静",
            "neutral": "平静"
        }
        emotion_text = "、".join([emotion_names.get(e, e) for e in main_emotions])
        
        return {
            "step": 1,
            "goal": "让用户感到被听懂",
            "required_elements": {
                "emotion_mirror": f"识别到用户的主要情绪：{emotion_text}",
                "problem_restate": parsed.problemSummary or "用户当前面临的问题",
                "normalization": "这种感受在类似情境中很常见" if parsed.intensity < 8 else None
            },
            "style_guidance": {
                "tone": "gentle" if style.tone == "gentle" else "neutral",
                "length": "medium" if style.emotionFocus >= 4 else "short"
            }
        }
    
    def _plan_step2(self, parsed: ParsedState, style: StyleProfile, conversation_state: Optional[dict]) -> dict:
        """
        Step 2: 结构化拆解问题
        
        必需要素：
        - problem_parts: 至少2-3个拆解的部分（现实层/情绪层/思维层）
        - examples: 每一部分都要用用户的内容作为例子
        - optional_question: 可选的引导问题
        """
        # 根据场景和情绪推断问题层面
        parts = []
        
        # 现实层：如果涉及具体任务、时间、外部要求
        if parsed.scene in ["exam", "study", "work", "career"]:
            parts.append({
                "layer": "现实层",
                "description": "具体的时间、任务量、外部要求等",
                "example_hint": "用户提到的具体任务或时间压力"
            })
        
        # 情绪层：总是存在
        parts.append({
            "layer": "情绪层",
            "description": "当前的感受和情绪反应",
            "example_hint": f"用户感受到的{parsed.emotions[0] if parsed.emotions else '情绪'}"
        })
        
        # 思维层：如果涉及认知模式
        if parsed.intensity >= 5:
            parts.append({
                "layer": "思维层",
                "description": "可能存在的思维模式（如灾难化、完美主义等）",
                "example_hint": "用户可能存在的思维倾向"
            })
        
        return {
            "step": 2,
            "goal": "把混乱拆成可处理的部分",
            "required_elements": {
                "problem_parts": parts[:3],  # 最多3个部分
                "optional_question": "哪一部分对你来说最重？" if style.useGentleQuestions else None
            },
            "style_guidance": {
                "tone": "neutral" if style.analysisDepth >= 4 else "gentle",
                "structure": "clear_listing"
            }
        }
    
    def _plan_step3(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        interventions: list[InterventionConfig],
        conversation_state: Optional[dict]
    ) -> dict:
        """
        Step 3: 专业视角解释（说人话）
        
        必需要素：
        - concept: 引入1-2个心理学概念
        - plain_explanation: 通俗解释
        - user_example: 结合用户例子
        - normalization: 轻度正常化
        """
        # 根据情绪和干预模块选择合适的概念
        concepts = []
        
        # 检查干预模块
        for interv in interventions:
            if interv.id == "catastrophizing_identification":
                concepts.append({
                    "name": "灾难化思维",
                    "plain_explanation": "就是会把事情的结果想得特别糟糕，放大负面可能性",
                    "user_example_hint": "用户可能过度担心最坏的结果"
                })
            elif interv.id == "perfectionism_identification":
                concepts.append({
                    "name": "完美主义倾向",
                    "plain_explanation": "对自己要求很高，觉得'不够完美就是失败'",
                    "user_example_hint": "用户可能对自己要求过高"
                })
        
        # 如果没有匹配的干预模块，根据情绪推断
        if not concepts:
            if "anxiety" in parsed.emotions:
                concepts.append({
                    "name": "焦虑反应",
                    "plain_explanation": "面对压力时，身体和大脑会进入'备战状态'，这是正常的保护机制",
                    "user_example_hint": "用户当前的焦虑反应"
                })
            elif "guilt" in parsed.emotions or "shame" in parsed.emotions:
                concepts.append({
                    "name": "自我批评模式",
                    "plain_explanation": "习惯性地对自己过于严厉，把问题都归因于自己",
                    "user_example_hint": "用户可能对自己过于苛刻"
                })
        
        return {
            "step": 3,
            "goal": "给用户一个'原来如此'的理解",
            "required_elements": {
                "concepts": concepts[:2],  # 最多2个概念
                "normalization": "这种模式在压力环境下很常见" if parsed.intensity < 8 else None
            },
            "style_guidance": {
                "tone": "neutral" if style.analysisDepth >= 4 else "gentle",
                "use_psycho_education": style.usePsychoEducation
            }
        }
    
    def _plan_step4(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        interventions: list[InterventionConfig],
        conversation_state: Optional[dict]
    ) -> dict:
        """
        Step 4: 小步可执行建议
        
        必需要素：
        - suggestions: 1-3条具体建议
        - each_suggestion: 包含做什么、什么时候做、大约多久
        - suggestion_types: 情绪缓解类/任务推进类/认知练习类
        """
        suggestions = []
        
        # 根据干预模块生成建议
        for interv in interventions:
            if interv.id == "breathing_exercise":
                suggestions.append({
                    "type": "情绪缓解类",
                    "action": "做一次4-7-8呼吸练习",
                    "when": "现在就可以",
                    "duration": "2-3分钟",
                    "details": "吸气4秒，屏息7秒，呼气8秒，重复3-5次"
                })
            elif interv.id == "task_breakdown":
                suggestions.append({
                    "type": "任务推进类",
                    "action": "把大任务拆成3-5个小步骤",
                    "when": "今天或明天",
                    "duration": "10-15分钟",
                    "details": "写下每个小步骤，从最简单的开始"
                })
            elif interv.id == "behavioral_activation":
                suggestions.append({
                    "type": "情绪缓解类",
                    "action": "做一个5分钟的小行动",
                    "when": "接下来1小时内",
                    "duration": "5分钟",
                    "details": "可以是整理桌面、听一首歌、做几个深呼吸等"
                })
        
        # 如果没有匹配的干预模块，提供通用建议
        if not suggestions:
            if parsed.intensity >= 7:
                suggestions.append({
                    "type": "情绪缓解类",
                    "action": "暂时离开当前环境，做几个深呼吸",
                    "when": "现在",
                    "duration": "3-5分钟",
                    "details": "找一个安静的地方，专注于呼吸"
                })
            else:
                suggestions.append({
                    "type": "认知练习类",
                    "action": "写下当前最担心的3件事",
                    "when": "今天",
                    "duration": "10分钟",
                    "details": "把担心写下来，可以帮助理清思路"
                })
        
        return {
            "step": 4,
            "goal": "从'只会想'进入'能做一点点'",
            "required_elements": {
                "suggestions": suggestions[:3],  # 最多3条建议
                "gentle_reminder": "做不到也没关系，不用给自己压力" if style.tone == "gentle" else None
            },
            "style_guidance": {
                "tone": "firm" if style.actionFocus >= 4 else "gentle",
                "directness": style.directness
            }
        }
    
    def _plan_step5(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        conversation_state: Optional[dict]
    ) -> dict:
        """
        Step 5: 温柔收尾 & 小结
        
        必需要素：
        - review: 简要回顾本轮做了什么
        - affirmation: 肯定用户的努力
        - continuation: 温和的延续方向
        - professional_reminder: 必要时提醒现实支持（高风险或长期困扰）
        """
        review_items = []
        if conversation_state and "stepHistory" in conversation_state:
            for step_record in conversation_state["stepHistory"]:
                step_num = step_record.get("step")
                if step_num == 1:
                    review_items.append("理清了你的情绪和问题")
                elif step_num == 2:
                    review_items.append("拆解了问题的结构")
                elif step_num == 3:
                    review_items.append("理解了背后的模式")
                elif step_num == 4:
                    review_items.append("定下了小计划")
        
        affirmations = [
            "你愿意讲清楚这些，已经很不容易了",
            "你愿意思考这些问题，说明你在努力",
            "你愿意尝试改变，这本身就是进步"
        ]
        
        continuation = "执行完这次小计划之后，可以再来看看效果"
        if parsed.riskLevel == "high" or parsed.intensity >= 8:
            continuation = "如果情况持续，建议考虑现实中的支持或专业人士的帮助"
        
        return {
            "step": 5,
            "goal": "让对话有圆满的结束感",
            "required_elements": {
                "review": review_items,
                "affirmation": affirmations[0] if affirmations else "你已经很努力了",
                "continuation": continuation,
                "professional_reminder": parsed.riskLevel == "high" or parsed.intensity >= 8
            },
            "style_guidance": {
                "tone": "gentle",
                "length": "short"
            }
        }
    
    def _map_steps_to_parts(self, steps: list[int]) -> list[str]:
        """将步骤编号映射到旧的三段式结构（保持兼容性）"""
        parts = []
        if 1 in steps:
            parts.append("emotion")
        if 2 in steps or 3 in steps:
            parts.append("clarification")
        if 4 in steps:
            parts.append("action")
        return parts if parts else ["emotion"]

