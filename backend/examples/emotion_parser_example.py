"""
情感解析器使用示例
演示如何使用增强版情感解析器
"""
from app.schemas.chat import ChatMessage
from app.core.emotion_parser_adapter import (
    parse_user_message,
    parse_user_message_with_confidence
)
from app.core.enhanced_emotion_parser import EnhancedEmotionParser


def example_basic_usage():
    """示例1：基本用法"""
    print("=" * 50)
    print("示例1：基本用法")
    print("=" * 50)
    
    message = ChatMessage(
        role="user",
        content="我最近考试压力很大，非常焦虑，不知道该怎么办"
    )
    
    # 使用适配器解析（自动选择最佳模式）
    parsed = parse_user_message(
        message=message,
        history=[],
        llm_provider=None,  # 不使用LLM，仅使用增强算法
        use_enhanced=True
    )
    
    print(f"用户消息: {message.content}")
    print(f"检测到的情绪: {parsed.emotions}")
    print(f"情绪强度: {parsed.intensity}/10")
    print(f"场景: {parsed.scene}")
    print(f"风险等级: {parsed.riskLevel}")
    print(f"用户目标: {parsed.userGoal}")
    print()


def example_with_confidence():
    """示例2：获取置信度"""
    print("=" * 50)
    print("示例2：获取置信度")
    print("=" * 50)
    
    message = ChatMessage(
        role="user",
        content="呵呵，真好"  # 可能是反讽，需要LLM增强
    )
    
    parsed, confidence = parse_user_message_with_confidence(
        message=message,
        history=[],
        llm_provider=None,  # 不使用LLM
        use_enhanced=True
    )
    
    print(f"用户消息: {message.content}")
    print(f"检测到的情绪: {parsed.emotions}")
    print(f"置信度: {confidence:.2f}")
    
    if confidence < 0.5:
        print("⚠️  置信度较低，建议使用LLM增强或人工复核")
    elif confidence < 0.8:
        print("⚠️  置信度中等，建议使用LLM增强")
    else:
        print("✅ 置信度较高，可以直接使用")
    print()


def example_with_history():
    """示例3：使用历史上下文"""
    print("=" * 50)
    print("示例3：使用历史上下文")
    print("=" * 50)
    
    history = [
        ChatMessage(role="user", content="我最近工作压力很大"),
        ChatMessage(role="assistant", content="我理解你的压力，能具体说说吗？"),
    ]
    
    message = ChatMessage(
        role="user",
        content="真的很累，感觉要崩溃了"
    )
    
    parsed = parse_user_message(
        message=message,
        history=history,
        use_enhanced=True
    )
    
    print(f"历史消息数: {len(history)}")
    print(f"当前消息: {message.content}")
    print(f"检测到的情绪: {parsed.emotions}")
    print(f"情绪强度: {parsed.intensity}/10")
    print(f"场景: {parsed.scene}")
    print("💡 注意：历史上下文有助于识别持续困扰和情绪趋势")
    print()


def example_emotion_trend():
    """示例4：情绪趋势分析"""
    print("=" * 50)
    print("示例4：情绪趋势分析")
    print("=" * 50)
    
    # 模拟一个情绪逐渐恶化的对话历史
    history = [
        ChatMessage(role="user", content="最近有点焦虑"),
        ChatMessage(role="assistant", content="能具体说说吗？"),
        ChatMessage(role="user", content="考试压力很大，很焦虑"),
        ChatMessage(role="assistant", content="我理解你的感受"),
    ]
    
    # 为历史消息添加情绪信息（模拟）
    for i, msg in enumerate(history):
        if msg.role == "user":
            if i == 0:
                msg.emotion = "anxiety"
                msg.intensity = 4
            elif i == 2:
                msg.emotion = "anxiety"
                msg.intensity = 6
    
    message = ChatMessage(
        role="user",
        content="我真的要崩溃了，完全不知道该怎么办"
    )
    
    parser = EnhancedEmotionParser(enable_llm=False)
    parsed, confidence = parser.parse(message, history)
    
    # 分析趋势
    trend = parser._analyze_emotion_trend(history, parsed)
    
    print("对话历史:")
    for i, msg in enumerate(history):
        if msg.role == "user":
            intensity = getattr(msg, 'intensity', '?')
            emotion = getattr(msg, 'emotion', '?')
            print(f"  轮次{i+1}: {msg.content} (情绪: {emotion}, 强度: {intensity})")
    
    print(f"\n当前消息: {message.content}")
    print(f"当前情绪: {parsed.emotions}, 强度: {parsed.intensity}")
    print(f"\n趋势分析:")
    print(f"  方向: {trend.direction}")
    print(f"  强度变化: {trend.intensity_change:+d}")
    print(f"  是否持续困扰: {trend.is_persistent}")
    
    if trend.direction == "rising" and trend.is_persistent:
        print("⚠️  警告：情绪持续恶化，需要重点关注")
    print()


def example_complex_cases():
    """示例5：复杂情况处理"""
    print("=" * 50)
    print("示例5：复杂情况处理")
    print("=" * 50)
    
    test_cases = [
        {
            "content": "我真的很开心，呵呵",
            "description": "反讽表达（表面开心，实际可能不开心）"
        },
        {
            "content": "我不不不是不开心",
            "description": "多重否定（表达复杂）"
        },
        {
            "content": "说不清，可能有点焦虑吧",
            "description": "模糊表达"
        },
        {
            "content": "好累好累好累",
            "description": "重复字（强调情绪）"
        },
    ]
    
    parser = EnhancedEmotionParser(enable_llm=False)
    
    for case in test_cases:
        message = ChatMessage(role="user", content=case["content"])
        parsed, confidence = parser.parse(message, [])
        
        print(f"描述: {case['description']}")
        print(f"消息: {case['content']}")
        print(f"解析结果: 情绪={parsed.emotions}, 强度={parsed.intensity}, 置信度={confidence:.2f}")
        
        is_complex = parser._is_complex_case(message, parsed)
        print(f"是否复杂情况: {is_complex}")
        if is_complex:
            print("💡 建议：使用LLM增强以获得更准确的结果")
        print()


def example_intensity_calculation():
    """示例6：多因素强度计算"""
    print("=" * 50)
    print("示例6：多因素强度计算")
    print("=" * 50)
    
    test_cases = [
        {
            "content": "有点焦虑",
            "expected": "低强度（4-5）"
        },
        {
            "content": "非常焦虑！",
            "expected": "中高强度（7-8，感叹号增强）"
        },
        {
            "content": "考试压力很大，非常非常焦虑！！！",
            "expected": "高强度（8-9，场景+强度词+感叹号）"
        },
        {
            "content": "好累好累好累",
            "expected": "中强度（5-6，重复字增强）"
        },
    ]
    
    parser = EnhancedEmotionParser(enable_llm=False)
    
    for case in test_cases:
        message = ChatMessage(role="user", content=case["content"])
        parsed, _ = parser.parse(message, [])
        
        print(f"消息: {case['content']}")
        print(f"检测情绪: {parsed.emotions}")
        print(f"计算强度: {parsed.intensity}/10 (预期: {case['expected']})")
        print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("情感解析器使用示例")
    print("=" * 50 + "\n")
    
    # 运行所有示例
    example_basic_usage()
    example_with_confidence()
    example_with_history()
    example_emotion_trend()
    example_complex_cases()
    example_intensity_calculation()
    
    print("=" * 50)
    print("所有示例运行完成！")
    print("=" * 50)

