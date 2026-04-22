from langchain_huggingface import HuggingFaceEmbeddings
from .providers.LocalEmbeddingProvider import LocalEmbeddingProvider
from .LLMEnums import EmbeddingEnums

class EmbeddingProviderFactory:
    def __init__(self, config: dict):
        self.config = config

    def create(self, provider: str, model_name: str = None):
        if provider == EmbeddingEnums.LOCAL_EMBEDDING.value:
            return LocalEmbeddingProvider()
        elif provider == EmbeddingEnums.HUGGINGFACE.value:
            return HuggingFaceEmbeddings(model_name=model_name)
        elif provider == EmbeddingEnums.OPENAI.value:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=model_name,
                base_url="https://models.github.ai/inference",
                api_key=self.config.OPENAI_API_KEY
            )
        return None