"""
LLM Provider工厂，根据环境变量选择provider
"""
import os
from app.core.llm_provider import LLMProvider, MockLLMProvider
from app.core.providers.openai_provider import OpenAIProvider
from app.core.providers.ollama_provider import OllamaProvider


def get_llm_provider() -> LLMProvider:
    """
    根据环境变量获取LLM Provider实例
    
    环境变量 LLM_PROVIDER 可选值：
    - "openai": 使用OpenAI API
    - "ollama": 使用Ollama本地模型
    - 其他或未设置: 使用Mock实现
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_name == "openai":
        try:
            return OpenAIProvider()
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}, falling back to Mock")
            return MockLLMProvider()
    elif provider_name == "ollama":
        try:
            return OllamaProvider()
        except Exception as e:
            print(f"Failed to initialize Ollama provider: {e}, falling back to Mock")
            return MockLLMProvider()
    else:
        return MockLLMProvider()

