"""Embedding Service wrapper using Sentence Transformers and LangChain embeddings."""

from typing import List, Optional
from app.core.config import settings
from app.core.constants import EMBEDDING_MODEL_NAME


class EmbeddingService:
    """Wrapper for generating vector embeddings using SentenceTransformers."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self) -> None:
        """Lazy load SentenceTransformer model if installed."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                self._model = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text input string.

        Args:
            text: Query or document text.

        Returns:
            List of floats representing vector embedding.
        """
        self._load_model()
        if self._model:
            return self._model.encode(text).tolist()
        # Fallback vector representation if sentence_transformers is uninitialized
        return [0.0] * 384

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of document strings.

        Args:
            documents: List of text documents.

        Returns:
            List of embedding vectors.
        """
        self._load_model()
        if self._model:
            return self._model.encode(documents).tolist()
        return [[0.0] * 384 for _ in documents]
