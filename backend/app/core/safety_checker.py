"""
安全与质量自检模块
"""
from typing import Literal
from pydantic import BaseModel
from app.schemas.style import ParsedState
from app.schemas.chat import ChatMessage


class QualityCheckResult(BaseModel):
    """质量检查结果"""
    passed: bool
    reason: str = ""


class SafetyChecker:
    """安全与质量检查器"""
    
    # 危险关键词列表
    DANGER_KEYWORDS = [
        "具体自伤方法",
        "如何自杀",
        "自杀步骤",
        "自伤工具",
        "如何伤害自己",
    ]
    
    # 极端表达关键词
    EXTREME_KEYWORDS = [
        "必须",
        "一定",
        "永远",
        "彻底失败",
        "完全不可能",
        "你根本",
        "你就是太",
    ]
    
    def check(
        self,
        reply_text: str,
        parsed: ParsedState,
    ) -> tuple[bool, str]:
        """
        检查回复的安全性和质量
        
        Args:
            reply_text: 回复文本
            parsed: 情绪解析结果
            
        Returns:
            tuple[bool, str]: (是否通过, 错误信息)
        """
        reply_lower = reply_text.lower()
        
        # 1. 检查是否包含危险内容
        for keyword in self.DANGER_KEYWORDS:
            if keyword in reply_lower:
                return False, f"包含危险内容: {keyword}"
        
        # 2. 检查是否包含极端表达（高风险场景更严格）
        if parsed.riskLevel == "high":
            for keyword in self.EXTREME_KEYWORDS:
                if keyword in reply_lower:
                    return False, f"高风险场景下不应使用极端表达: {keyword}"
        
        # 3. 检查是否明确承认了用户情绪（简单检查）
        emotion_keywords = ["感受", "情绪", "理解", "明白", "知道"]
        if not any(kw in reply_text for kw in emotion_keywords):
            # 这不是致命错误，只是质量提示
            pass
        
        # 4. 检查长度（避免过长或过短）
        if len(reply_text) < 10:
            return False, "回复过短"
        
        if len(reply_text) > 2000:
            return False, "回复过长"
        
        return True, ""
    
    def check_reply_quality(
        self,
        user_message: ChatMessage,
        assistant_reply: str,
        parsed: ParsedState,
    ) -> QualityCheckResult:
        """
        检查回复的质量
        
        Args:
            user_message: 用户消息
            assistant_reply: 助手回复文本
            parsed: 情绪解析结果
            
        Returns:
            QualityCheckResult: 质量检查结果
        """
        # 使用现有的 check 方法
        passed, reason = self.check(assistant_reply, parsed)
        
        return QualityCheckResult(
            passed=passed,
            reason=reason
        )


