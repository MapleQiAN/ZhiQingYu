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
        # plan: Optional[dict] = None,
    ) -> tuple[bool, str]:
        """
        检查回复的安全性和质量（增强版：支持5步骤检查）
        
        Args:
            reply_text: 回复文本
            parsed: 情绪解析结果
            plan: 回复规划（可选，用于检查步骤必需要素）
            
        Returns:
            tuple[bool, str]: (是否通过, 错误信息)
        """
        reply_lower = reply_text.lower()
        
        # 1. 检查是否包含危险内容（自伤、他伤、自杀方法等）
        for keyword in self.DANGER_KEYWORDS:
            if keyword in reply_lower:
                return False, f"包含危险内容: {keyword}"
        
        # 2. 检查是否包含诊断性语言（禁止做诊断）
        diagnosis_keywords = ["抑郁症", "焦虑症", "强迫症", "双相", "精神分裂", "你有病", "你得了", "diagnosis", "disorder"]
        for keyword in diagnosis_keywords:
            if keyword in reply_lower:
                return False, f"不应使用诊断性语言: {keyword}"
        
        # 3. 检查是否包含羞辱式话语
        shaming_keywords = ["你太懒", "你矫情", "你太敏感", "你太脆弱", "你太自私", "你太笨"]
        for keyword in shaming_keywords:
            if keyword in reply_lower:
                return False, f"不应使用羞辱式话语: {keyword}"
        
        # 4. 检查是否包含极端表达（高风险场景更严格）
        if parsed.riskLevel == "high":
            for keyword in self.EXTREME_KEYWORDS:
                if keyword in reply_lower:
                    return False, f"高风险场景下不应使用极端表达: {keyword}"
        
        # 5. 检查是否明确承认了用户情绪（Step 1的必需要素）
        emotion_keywords = ["感受", "情绪", "理解", "明白", "知道", "感到", "觉得"]
        if not any(kw in reply_text for kw in emotion_keywords):
            # 这不是致命错误，只是质量提示
            pass
        
        # 6. 检查是否提供了自伤/自杀的具体方法（严格禁止）
        if parsed.hasSelfHarmKeywords:
            method_keywords = ["如何", "怎么", "方法", "步骤", "how to", "way to"]
            if any(kw in reply_lower for kw in method_keywords):
                # 如果同时包含自伤关键词和方法关键词，可能是危险内容
                if any(kw in reply_lower for kw in ["自杀", "自残", "self-harm", "suicide"]):
                    return False, "不应提供自伤/自杀的具体方法"
        
        # 7. 检查长度（避免过长或过短）
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


