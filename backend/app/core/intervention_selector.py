"""
干预模块选择器
"""
from app.schemas.style import ParsedState, StyleProfile, InterventionConfig
from app.core.intervention_manager import get_intervention_manager


class InterventionSelector:
    """干预模块选择器"""
    
    def __init__(self):
        self.intervention_manager = get_intervention_manager()
    
    def select(
        self,
        parsed: ParsedState,
        style: StyleProfile,
    ) -> list[InterventionConfig]:
        """
        根据解析结果和风格选择适用的干预模块
        
        Args:
            parsed: 情绪解析结果
            style: 当前风格
            
        Returns:
            list[InterventionConfig]: 选定的干预模块列表
        """
        all_interventions = self.intervention_manager.get_all_interventions()
        selected = []
        
        for interv in all_interventions:
            if self._matches(interv, parsed, style):
                selected.append(interv)
        
        # 限制数量，每个角色最多选2个
        emotion_intervs = [i for i in selected if i.role == "emotion"][:2]
        clarification_intervs = [i for i in selected if i.role == "clarification"][:2]
        action_intervs = [i for i in selected if i.role == "action"][:2]
        
        return emotion_intervs + clarification_intervs + action_intervs
    
    def _matches(
        self,
        interv: InterventionConfig,
        parsed: ParsedState,
        style: StyleProfile,
    ) -> bool:
        """判断干预模块是否匹配"""
        triggers = interv.triggers
        
        # 检查情绪匹配
        if "emotions" in triggers:
            trigger_emotions = triggers["emotions"]
            if not any(e in trigger_emotions for e in parsed.emotions):
                return False
        
        # 检查场景匹配
        if "scenes" in triggers:
            trigger_scenes = triggers["scenes"]
            if parsed.scene not in trigger_scenes:
                return False
        
        # 检查强度范围
        if "intensityMin" in triggers:
            if parsed.intensity < triggers["intensityMin"]:
                return False
        
        if "intensityMax" in triggers:
            if parsed.intensity > triggers["intensityMax"]:
                return False
        
        # 检查风险等级
        if "riskLevels" in triggers:
            trigger_risk_levels = triggers["riskLevels"]
            if parsed.riskLevel not in trigger_risk_levels:
                return False
        
        # 检查风格白名单
        if "styleWhitelist" in triggers:
            trigger_styles = triggers["styleWhitelist"]
            if style.id not in trigger_styles:
                return False
        
        return True


