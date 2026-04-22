from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from .LLMEnums import LLMEnums

class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config

    def create(self, provider: str, model_id: str = None, model_temperature: float = 0.0):
        if provider == LLMEnums.OLLAMA.value:
            return ChatOllama(model=model_id, temperature=model_temperature)
        elif provider == LLMEnums.GOOGLE_GENAI.value:
            return ChatGoogleGenerativeAI(model=model_id, temperature=model_temperature)
        elif provider == LLMEnums.GROQ.value:
            return ChatGroq(model=model_id, temperature=model_temperature)
        elif provider == LLMEnums.OPENAI.value:
            return ChatOpenAI(model=model_id, base_url="https://models.github.ai/inference", api_key=self.config.OPENAI_API_KEY, temperature=model_temperature)
        
        return None


