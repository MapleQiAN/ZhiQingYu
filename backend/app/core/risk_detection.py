"""
高危情绪检测模块
"""
from typing import Literal


# 高危关键词列表（中英文）
HIGH_RISK_KEYWORDS = [
    # 中文
    "不想活",
    "结束这一切",
    "活着没意义",
    "自杀",
    "想死",
    "不想活了",
    "结束生命",
    "离开这个世界",
    "自残",
    "伤害自己",
    "割腕",
    "跳楼",
    "上吊",
    "吃药",
    "结束自己",
    # 英文
    "suicide",
    "kill myself",
    "end my life",
    "want to die",
    "don't want to live",
    "self-harm",
    "cut myself",
    "hurt myself",
]


def detect_risk_level(content: str, intensity: int) -> Literal["normal", "high"]:
    """
    检测消息的风险级别
    
    Args:
        content: 消息内容
        intensity: 情绪强度（1-5）
        
    Returns:
        "normal" 或 "high"
    """
    content_lower = content.lower()
    
    # 检查是否包含高危关键词
    has_risk_keyword = any(keyword.lower() in content_lower for keyword in HIGH_RISK_KEYWORDS)
    
    # 如果包含高危关键词且情绪强度较高，判定为高风险
    if has_risk_keyword and intensity >= 4:
        return "high"
    
    # 如果包含高危关键词但强度较低，也判定为高风险（更保守的策略）
    if has_risk_keyword:
        return "high"
    
    return "normal"


def upgrade_risk_level_if_needed(original_risk: str, content: str, intensity: int) -> Literal["normal", "high"]:
    """
    如果需要，升级风险级别
    
    Args:
        original_risk: LLM判断的原始风险级别
        content: 消息内容
        intensity: 情绪强度
        
    Returns:
        最终的风险级别
    """
    detected_risk = detect_risk_level(content, intensity)
    
    # 如果规则检测到高风险，则升级
    if detected_risk == "high":
        return "high"
    
    return original_risk

