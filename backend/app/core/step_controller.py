"""
步骤控制层：管理5步骤对话流程、快速/深聊模式、体验模式
"""
from typing import Literal, Optional
from app.schemas.style import (
    ParsedState, UserProfile, ConversationState, ReplyPlan, StyleProfile
)


class StepController:
    """步骤控制器"""
    
    # 体验模式与步骤的映射关系
    EXPERIENCE_MODE_STEPS = {
        "A": {  # "只是想被好好听一听"
            "enabled_steps": [1, 2, 5],
            "weakened_steps": [3, 4],
            "focus": "emotion_listening"
        },
        "B": {  # "想搞懂自己怎么了"
            "enabled_steps": [1, 2, 3, 5],
            "weakened_steps": [4],
            "focus": "understanding"
        },
        "C": {  # "想要具体怎么做的建议"
            "enabled_steps": [1, 3, 4, 5],
            "weakened_steps": [2],
            "focus": "action"
        },
        "D": {  # "想系统聊一聊（深聊模式）"
            "enabled_steps": [1, 2, 3, 4, 5],
            "weakened_steps": [],
            "focus": "deep_conversation"
        }
    }
    
    def determine_mode_and_steps(
        self,
        parsed: ParsedState,
        user_profile: UserProfile,
        conversation_state: Optional[ConversationState],
        user_input: str
    ) -> tuple[Literal["quick", "deep"], list[int], Optional[Literal["A", "B", "C", "D"]]]:
        """
        确定当前对话模式和要执行的步骤
        
        Args:
            parsed: 情绪解析结果
            user_profile: 用户配置
            conversation_state: 对话状态（可能为None，表示新对话）
            user_input: 用户输入（用于检测模式切换指令）
            
        Returns:
            (模式, 步骤列表, 体验模式)
        """
        # 1. 检测用户是否明确要求切换模式
        experience_mode = self._detect_experience_mode_from_input(user_input)
        if not experience_mode and user_profile.preferredExperienceMode:
            experience_mode = user_profile.preferredExperienceMode
        if not experience_mode and conversation_state:
            experience_mode = conversation_state.experienceMode
        
        # 2. 检测是否要求深聊模式
        deep_mode_keywords = ["系统聊", "深聊", "详细聊", "慢慢聊", "一步步", "分步"]
        quick_mode_keywords = ["快速", "简单", "简短", "直接"]
        
        is_deep_mode = any(kw in user_input for kw in deep_mode_keywords)
        is_quick_mode = any(kw in user_input for kw in quick_mode_keywords)
        
        # 3. 如果已有对话状态且处于深聊模式，继续深聊
        if conversation_state and conversation_state.currentMode == "deep":
            if not is_quick_mode:  # 用户没有明确要求切换回快速模式
                is_deep_mode = True
        
        # 4. 根据体验模式确定步骤
        if experience_mode == "D" or is_deep_mode:
            # 深聊模式：根据对话进度决定执行哪个步骤
            mode = "deep"
            steps = self._get_next_step_for_deep_mode(conversation_state, parsed)
        else:
            # 快速模式：根据体验模式决定执行哪些步骤
            mode = "quick"
            steps = self._get_steps_for_quick_mode(experience_mode, parsed)
        
        return mode, steps, experience_mode
    
    def _detect_experience_mode_from_input(self, user_input: str) -> Optional[Literal["A", "B", "C", "D"]]:
        """从用户输入中检测体验模式"""
        user_lower = user_input.lower()
        
        # 模式A：只想被听
        if any(kw in user_lower for kw in ["只想被听", "只想倾诉", "只想聊聊", "听我说", "想说话"]):
            return "A"
        
        # 模式B：想搞懂
        if any(kw in user_lower for kw in ["想搞懂", "想理解", "为什么会", "怎么回事", "为什么会这样"]):
            return "B"
        
        # 模式C：想要建议
        if any(kw in user_lower for kw in ["怎么办", "建议", "方法", "怎么做", "如何做"]):
            return "C"
        
        # 模式D：系统深聊
        if any(kw in user_lower for kw in ["系统聊", "深聊", "详细聊", "一步步", "慢慢来"]):
            return "D"
        
        return None
    
    def _get_steps_for_quick_mode(
        self,
        experience_mode: Optional[Literal["A", "B", "C", "D"]],
        parsed: ParsedState
    ) -> list[int]:
        """快速模式：根据体验模式返回要执行的步骤列表"""
        if not experience_mode:
            # 没有指定体验模式，根据用户目标推断
            if parsed.userGoal == "want_listen":
                experience_mode = "A"
            elif parsed.userGoal == "want_clarification":
                experience_mode = "B"
            elif parsed.userGoal == "want_plan":
                experience_mode = "C"
            else:
                # 默认：快速模式执行所有步骤（简化版）
                return [1, 2, 3, 4, 5]
        
        if experience_mode in self.EXPERIENCE_MODE_STEPS:
            return self.EXPERIENCE_MODE_STEPS[experience_mode]["enabled_steps"]
        
        # 默认：执行所有步骤
        return [1, 2, 3, 4, 5]
    
    def _get_next_step_for_deep_mode(
        self,
        conversation_state: Optional[ConversationState],
        parsed: ParsedState
    ) -> list[int]:
        """深聊模式：根据对话进度返回下一步要执行的步骤"""
        if not conversation_state or conversation_state.currentStep is None:
            # 新对话，从Step 1开始
            return [1]
        
        current_step = conversation_state.currentStep
        completed_steps = set(conversation_state.completedSteps)
        
        # 如果当前步骤已完成，进入下一步
        if current_step in completed_steps:
            next_step = current_step + 1
            if next_step > 5:
                # 所有步骤完成，可以重新开始或结束
                return [5]  # 最后一步：收尾
            return [next_step]
        
        # 当前步骤未完成，继续执行当前步骤
        return [current_step]
    
    def update_conversation_state(
        self,
        conversation_state: Optional[ConversationState],
        executed_steps: list[int],
        mode: Literal["quick", "deep"],
        experience_mode: Optional[Literal["A", "B", "C", "D"]],
        step_content: Optional[dict] = None
    ) -> ConversationState:
        """
        更新对话状态
        
        Args:
            conversation_state: 当前对话状态（可能为None）
            executed_steps: 本轮执行的步骤列表
            mode: 当前模式
            experience_mode: 当前体验模式
            step_content: 步骤内容（用于记录历史）
            
        Returns:
            更新后的对话状态
        """
        if not conversation_state:
            conversation_state = ConversationState()
        
        conversation_state.currentMode = mode
        conversation_state.experienceMode = experience_mode
        
        # 更新步骤进度
        if mode == "deep":
            # 深聊模式：记录当前步骤和完成情况
            if executed_steps:
                conversation_state.currentStep = executed_steps[0]  # 深聊模式一次只执行一个步骤
                if step_content:
                    # 标记当前步骤为已完成
                    if conversation_state.currentStep not in conversation_state.completedSteps:
                        conversation_state.completedSteps.append(conversation_state.currentStep)
                        # 记录步骤历史
                        conversation_state.stepHistory.append({
                            "step": conversation_state.currentStep,
                            "content": step_content
                        })
        else:
            # 快速模式：标记所有执行的步骤为已完成
            for step in executed_steps:
                if step not in conversation_state.completedSteps:
                    conversation_state.completedSteps.append(step)
                    if step_content and step in step_content:
                        conversation_state.stepHistory.append({
                            "step": step,
                            "content": step_content.get(step, {})
                        })
        
        return conversation_state

