"""
情感解析器适配器
提供向后兼容的接口，支持逐步迁移到增强版解析器
"""
from typing import Optional, Tuple
from app.schemas.chat import ChatMessage
from app.schemas.style import ParsedState
from app.core.llm_provider import LLMProvider
# 延迟导入以避免循环导入
# from app.core.conversation_algorithm import parse_user_message as rule_based_parse
from app.core.enhanced_emotion_parser import EnhancedEmotionParser, parse_user_message_enhanced


# 全局配置：是否启用增强版解析器
ENABLE_ENHANCED_PARSER = True  # 可以通过环境变量控制


def parse_user_message(
    message: ChatMessage,
    history: list[ChatMessage] = None,
    llm_provider: Optional[LLMProvider] = None,
    use_enhanced: Optional[bool] = None
) -> ParsedState:
    """
    解析用户消息（适配器接口，向后兼容）
    
    这个函数会根据配置自动选择使用规则匹配或增强版解析器
    
    Args:
        message: 用户消息
        history: 对话历史
        llm_provider: LLM提供者（可选，用于增强版解析器）
        use_enhanced: 是否强制使用增强版（None表示根据配置自动选择）
        
    Returns:
        ParsedState: 解析结果
    """
    # 决定是否使用增强版
    should_use_enhanced = use_enhanced
    if should_use_enhanced is None:
        should_use_enhanced = ENABLE_ENHANCED_PARSER
    
    # 如果启用增强版且有LLM提供者，使用增强版
    if should_use_enhanced and llm_provider is not None:
        try:
            parsed, confidence = parse_user_message_enhanced(
                message=message,
                history=history,
                llm_provider=llm_provider,
                enable_llm=True
            )
            # 可以在这里记录置信度（如果需要）
            return parsed
        except Exception as e:
            # 增强版失败，回退到规则匹配
            print(f"增强版解析失败，回退到规则匹配: {e}")
            # 延迟导入以避免循环导入
            from app.core.conversation_algorithm import parse_user_message as rule_based_parse
            return rule_based_parse(message, history)
    
    # 使用增强版但不启用LLM（只使用多因素强度计算等增强功能）
    if should_use_enhanced:
        try:
            parser = EnhancedEmotionParser(llm_provider=None, enable_llm=False)
            parsed, confidence = parser.parse(message, history)
            return parsed
        except Exception as e:
            print(f"增强版解析失败，回退到规则匹配: {e}")
            # 延迟导入以避免循环导入
            from app.core.conversation_algorithm import parse_user_message as rule_based_parse
            return rule_based_parse(message, history)
    
    # 使用原始规则匹配
    # 延迟导入以避免循环导入
    from app.core.conversation_algorithm import parse_user_message as rule_based_parse
    return rule_based_parse(message, history)


def parse_user_message_with_confidence(
    message: ChatMessage,
    history: list[ChatMessage] = None,
    llm_provider: Optional[LLMProvider] = None,
    use_enhanced: Optional[bool] = None
) -> Tuple[ParsedState, float]:
    """
    解析用户消息并返回置信度（新接口）
    
    Args:
        message: 用户消息
        history: 对话历史
        llm_provider: LLM提供者（可选）
        use_enhanced: 是否使用增强版
        
    Returns:
        (ParsedState, confidence): 解析结果和置信度（0-1）
    """
    should_use_enhanced = use_enhanced if use_enhanced is not None else ENABLE_ENHANCED_PARSER
    
    if should_use_enhanced:
        try:
            return parse_user_message_enhanced(
                message=message,
                history=history,
                llm_provider=llm_provider,
                enable_llm=(llm_provider is not None)
            )
        except Exception as e:
            print(f"增强版解析失败，回退到规则匹配: {e}")
            # 延迟导入以避免循环导入
            from app.core.conversation_algorithm import parse_user_message as rule_based_parse
            parsed = rule_based_parse(message, history)
            # 规则匹配的默认置信度
            return parsed, 0.7
    
    # 规则匹配模式
    # 延迟导入以避免循环导入
    from app.core.conversation_algorithm import parse_user_message as rule_based_parse
    parsed = rule_based_parse(message, history)
    return parsed, 0.7  # 规则匹配的默认置信度

