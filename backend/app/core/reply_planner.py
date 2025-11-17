"""
回复规划模块
"""
from app.schemas.style import ParsedState, StyleProfile, InterventionConfig, ReplyPlan


class ReplyPlanner:
    """回复规划器"""
    
    def build_plan(
        self,
        parsed: ParsedState,
        style: StyleProfile,
        interventions: list[InterventionConfig],
    ) -> ReplyPlan:
        """
        构建回复规划
        
        Args:
            parsed: 情绪解析结果
            style: 当前风格
            interventions: 选定的干预模块
            
        Returns:
            ReplyPlan: 回复规划
        """
        # 默认三段式结构
        parts = ["emotion", "clarification", "action"]
        
        # 根据风格调整结构
        if style.id == "listener":
            # 极简倾听型：更多提问，行动建议减弱
            parts = ["emotion", "clarification"]  # 减少 action
        elif style.id == "coach":
            # 学长直给型：强化行动部分
            parts = ["emotion", "clarification", "action", "action"]  # 可以重复 action
        elif style.id == "crisis_safe":
            # 危机安全型：弱化第二、第三部分
            parts = ["emotion"]  # 主要只做情绪陪伴
        
        return ReplyPlan(
            style=style,
            interventions=[i.id for i in interventions],
            structure={
                "useThreePart": len(parts) >= 3,
                "parts": parts
            }
        )


