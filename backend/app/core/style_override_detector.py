"""
风格切换指令解析器
"""
from typing import Optional


class StyleOverrideDetector:
    """风格切换指令检测器"""
    
    # 风格关键词映射
    STYLE_KEYWORDS = {
        "comfort": ["温柔", "安慰", "温和", "轻柔", "gentle", "comfort"],
        "analyst": ["分析", "理性", "拆解", "分析一下", "analyze", "rational"],
        "coach": ["直接", "直说", "直给", "直接点", "direct", "straightforward"],
        "friend": ["像朋友", "轻松", "朋友", "轻松点", "friend", "casual"],
        "listener": ["听", "倾听", "只听", "listener", "listen"],
        "growth": ["成长", "长期", "习惯", "growth", "long-term"],
        "mentor": ["导师", "老师", "mentor", "teacher"],
    }
    
    def detect(self, user_text: str) -> Optional[str]:
        """
        检测用户是否要求切换风格
        
        Args:
            user_text: 用户输入文本
            
        Returns:
            Optional[str]: 风格ID，如果没有检测到则返回None
        """
        user_lower = user_text.lower()
        
        for style_id, keywords in self.STYLE_KEYWORDS.items():
            if any(keyword in user_lower for keyword in keywords):
                return style_id
        
        return None


