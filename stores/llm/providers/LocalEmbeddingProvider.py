from typing import Dict, List, Optional, Any, Callable, Union
import numpy as np
import os
from sentence_transformers import SentenceTransformer, models
from langchain.embeddings.base import Embeddings # Import the base class

class LocalEmbeddingProvider(Embeddings): # Inherit from Embeddings
    def __init__(self, 
                    model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
                    embedding_size: int = 384):

        self.model_id = model_id
        self.embedding_size = embedding_size
        self.embedding_model = self._init_model()
    
    def _init_model(self):
        """Initialize the embedding model."""
        transformer = models.Transformer(self.model_id, max_seq_length=128)
        pooling = models.Pooling(transformer.get_word_embedding_dimension(), pooling_mode="mean")
        normalize = models.Normalize()
        return SentenceTransformer(modules=[transformer, pooling, normalize])
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        if not self.embedding_model:
            self.embedding_model = self._init_model()
            
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        if not self.embedding_model:
            self.embedding_model = self._init_model()
            
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        
        return embedding.tolist()
