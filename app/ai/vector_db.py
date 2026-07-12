"""Vector Database wrapper using ChromaDB."""

import os
from typing import Any, Dict, List, Optional
from app.core.constants import CHROMA_COLLECTION_NAME


class VectorDatabase:
    """Wrapper class managing ChromaDB vector storage and index retrieval."""

    def __init__(
        self,
        persist_directory: str = "vector_database/chroma/",
        collection_name: str = CHROMA_COLLECTION_NAME,
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def initialize_db(self) -> None:
        """Initialize ChromaDB client and collection."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                os.makedirs(self.persist_directory, exist_ok=True)
                self._client = chromadb.PersistentClient(path=self.persist_directory)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name
                )
            except ImportError:
                self._client = None
                self._collection = None

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Add text documents (with precomputed embeddings) to vector collection.

        Args:
            documents: List of text content chunks.
            embeddings: Precomputed embedding vectors, one per document.
            metadatas: Metadata dictionaries.
            ids: Unique document IDs.
        """
        self.initialize_db()
        if self._collection:
            self._collection.add(
                documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
            )

    def similarity_search(self, query_embedding: List[float], k: int = 4) -> List[Dict[str, Any]]:
        """Perform vector similarity search against ChromaDB collection.

        Args:
            query_embedding: Precomputed embedding vector for the query text.
            k: Top-K results to retrieve.

        Returns:
            List of matching document metadata dicts.
        """
        self.initialize_db()
        if self._collection:
            results = self._collection.query(query_embeddings=[query_embedding], n_results=k)
            return results
        return []