# llm_factory.py

from llm_providers.gemini import GeminiProvider
from llm_providers.openai import OpenAIProvider
from llm_providers.claude import ClaudeProvider
# O Deepseek usa a classe OpenAIProvider, então não precisamos de importação extra

def get_llm_provider(provider_name, api_key, model_config):
    """
    Retorna uma instância do provedor de LLM apropriado.
    """
    if provider_name == "Gemini":
        return GeminiProvider(api_key=api_key, model_name=model_config['model'])
        
    elif provider_name == "OpenAI":
        return OpenAIProvider(api_key=api_key, model_name=model_config['model'])
        
    elif provider_name == "Claude":
        return ClaudeProvider(api_key=api_key, model_name=model_config['model'])
        
    elif provider_name == "Deepseek":
        return OpenAIProvider(
            api_key=api_key,
            model_name=model_config['model'],
            api_base_url="https://api.deepseek.com"
        )
        
    elif provider_name == "Moonshot Kimi":
        return OpenAIProvider(
            api_key=api_key,
            model_name=model_config['model'],
            api_base_url="https://api.moonshot.cn/v1"
        )
        
    else:
        raise ValueError(f"Provedor desconhecido: {provider_name}")