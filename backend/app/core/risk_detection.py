"""
高危情绪检测模块（增强版：支持三级风险）
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

# 中等风险关键词
MEDIUM_RISK_KEYWORDS = [
    "绝望",
    "没有希望",
    "hopeless",
    "desperate",
    "撑不下去",
    "活不下去",
    "没有意义",
    "看不到未来",
    "看不到希望",
]

# 自伤关键词
SELF_HARM_KEYWORDS = [
    "自残", "自伤", "割腕", "跳楼", "上吊", "吃药", "结束生命",
    "self-harm", "cut myself", "hurt myself", "kill myself"
]

# 暴力关键词
VIOLENCE_KEYWORDS = [
    "伤害", "报复", "打", "kill", "hurt", "violence", "attack", "伤害别人"
]


def detect_risk_level(content: str, intensity: int) -> Literal["low", "medium", "high"]:
    """
    检测消息的风险级别（三级：low/medium/high）
    
    Args:
        content: 消息内容
        intensity: 情绪强度（1-10）
        
    Returns:
        "low", "medium" 或 "high"
    """
    content_lower = content.lower()
    
    # 检查是否包含高危关键词
    has_high_risk_keyword = any(keyword.lower() in content_lower for keyword in HIGH_RISK_KEYWORDS)
    has_medium_risk_keyword = any(keyword.lower() in content_lower for keyword in MEDIUM_RISK_KEYWORDS)
    
    # 高风险：包含高危关键词
    if has_high_risk_keyword:
        return "high"
    
    # 中等风险：包含中等风险关键词 或 情绪强度很高(>=8)
    if has_medium_risk_keyword or intensity >= 8:
        return "medium"
    
    return "low"


def detect_self_harm_keywords(content: str) -> bool:
    """检测是否包含自伤关键词"""
    content_lower = content.lower()
    return any(keyword.lower() in content_lower for keyword in SELF_HARM_KEYWORDS)


def detect_violence_keywords(content: str) -> bool:
    """检测是否包含暴力关键词"""
    content_lower = content.lower()
    return any(keyword.lower() in content_lower for keyword in VIOLENCE_KEYWORDS)


def upgrade_risk_level_if_needed(original_risk: str, content: str, intensity: int) -> Literal["low", "medium", "high"]:
    """
    如果需要，升级风险级别（支持三级）
    
    Args:
        original_risk: LLM判断的原始风险级别
        content: 消息内容
        intensity: 情绪强度
        
    Returns:
        最终的风险级别
    """
    detected_risk = detect_risk_level(content, intensity)
    
    # 风险级别优先级：high > medium > low
    risk_priority = {"low": 1, "medium": 2, "high": 3}
    original_priority = risk_priority.get(original_risk, 1)
    detected_priority = risk_priority.get(detected_risk, 1)
    
    # 如果规则检测到的风险更高，则升级
    if detected_priority > original_priority:
        return detected_risk
    
    return original_risk

