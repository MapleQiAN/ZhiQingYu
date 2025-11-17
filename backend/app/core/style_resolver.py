"""
风格决策模块
"""
from app.schemas.style import StyleProfile, ParsedState, UserProfile
from app.core.style_manager import get_style_manager


class StyleResolver:
    """风格决策器"""
    
    def __init__(self):
        self.style_manager = get_style_manager()
    
    def resolve(
        self,
        user_profile: UserProfile,
        parsed: ParsedState,
    ) -> StyleProfile:
        """
        根据用户偏好和当前状态选择实际使用的风格
        
        Args:
            user_profile: 用户配置
            parsed: 情绪解析结果
            
        Returns:
            StyleProfile: 选定的风格
        """
        # 1. 高风险情绪统一切换到危机安全风格
        if parsed.riskLevel == "high":
            crisis_style = self.style_manager.get_style("crisis_safe")
            if crisis_style:
                return crisis_style
        
        # 2. 本轮临时 override，优先级 > 持久偏好
        if user_profile.recentStyleOverrideId:
            override_style = self.style_manager.get_style(user_profile.recentStyleOverrideId)
            if override_style:
                return override_style
        
        # 3. 用户持久偏好
        if user_profile.preferredStyleId:
            preferred_style = self.style_manager.get_style(user_profile.preferredStyleId)
            if preferred_style:
                return preferred_style
        
        # 4. 没设置偏好时的自适应策略
        # 情绪强度高时偏向 comfort
        if parsed.intensity >= 7:
            comfort_style = self.style_manager.get_style("comfort")
            if comfort_style:
                return comfort_style
        
        # 学习/规划场景可偏向 coach/growth
        if parsed.scene in ["exam", "study", "career"]:
            growth_style = self.style_manager.get_style("growth")
            if growth_style:
                return growth_style
        
        # 默认使用混合的 mentor 风格
        return self.style_manager.get_default_style()


