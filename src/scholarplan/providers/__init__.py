from .mock import MockLLMProvider

def build_provider(name: str):
    name = (name or "mock").lower()
    if name == "mock":
        return MockLLMProvider()
    if name == "lmstudio":
        from .lmstudio import LMStudioProvider
        return LMStudioProvider()
    if name == "azure":
        from .azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider()
    raise ValueError(f"Unknown provider: {name}")
