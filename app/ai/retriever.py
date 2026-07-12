"""Retriever module connecting query text to relevant contextual knowledge chunks."""

from typing import Any, Dict, List
from app.ai.embeddings import EmbeddingService
from app.ai.vector_db import VectorDatabase


class Retriever:
    """Retrieval engine for fetching relevant store knowledge and book catalog contexts."""

    def __init__(self, vector_db: VectorDatabase, embedding_service: EmbeddingService) -> None:
        self.vector_db = vector_db
        self.embedding_service = embedding_service

    def get_relevant_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top-K most relevant context chunks for a user query.

        Args:
            query: Natural language user question.
            top_k: Number of relevant knowledge chunks to retrieve.

        Returns:
            List of context document dictionaries.
        """
        query_vector = self.embedding_service.embed_text(query)
        raw_results = self.vector_db.similarity_search(query_embedding=query_vector, k=top_k)
        if not raw_results or not raw_results.get("documents"):
            return [
                {
                    "content": "Online Book Store offers free shipping on orders over $50. Return policy allows returns within 30 days of delivery.",
                    "source": "store_policies_faq",
                }
            ]
        
        docs = []
        for idx, doc_content in enumerate(raw_results["documents"][0]):
            metadata = raw_results["metadatas"][0][idx] if raw_results.get("metadatas") else {}
            docs.append({
                "content": doc_content,
                "source": metadata.get("source", "knowledge_base"),
            })
        return docs
