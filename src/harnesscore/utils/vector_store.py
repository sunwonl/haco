import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class LocalVectorStore:
    """A lightweight vector store for project knowledge, persisted in .harness/vectors/."""
    
    def __init__(self, storage_dir: str, api_key: str, model_name: str = "models/text-embedding-004"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key
        )
        
        self.index_path = self.storage_dir / "index.json"
        self.vectors_path = self.storage_dir / "embeddings.npy"
        
        self.chunks: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None
        
        self.load()

    def load(self):
        """Loads index and vector data from disk if they exist."""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
        
        if self.vectors_path.exists():
            self.vectors = np.load(self.vectors_path)

    def save(self):
        """Saves current index and vectors to disk."""
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        
        if self.vectors is not None:
            np.save(self.vectors_path, self.vectors)

    async def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """Embeds and adds new texts to the store (Async)."""
        if not texts:
            return
            
        new_embeddings = await self.embeddings_model.aembed_documents(texts)
        self._process_new_embeddings(texts, new_embeddings, metadatas)

    def add_texts_sync(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """Embeds and adds new texts to the store (Sync)."""
        if not texts:
            return
            
        new_embeddings = self.embeddings_model.embed_documents(texts)
        self._process_new_embeddings(texts, new_embeddings, metadatas)

    def _process_new_embeddings(self, texts, embeddings, metadatas):
        new_vectors = np.array(embeddings, dtype=np.float32)
        
        if self.vectors is None:
            self.vectors = new_vectors
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])
            
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            self.chunks.append({
                "text": text,
                "metadata": metadata
            })
        
        self.save()

    async def similarity_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Finds most similar chunks to the query using cosine similarity (Async)."""
        if self.vectors is None or len(self.chunks) == 0:
            return []
            
        query_embedding = await self.embeddings_model.aembed_query(query)
        return self._search_vectors(query_embedding, k)

    def similarity_search_sync(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Finds most similar chunks to the query using cosine similarity (Sync)."""
        if self.vectors is None or len(self.chunks) == 0:
            return []
            
        query_embedding = self.embeddings_model.embed_query(query)
        return self._search_vectors(query_embedding, k)

    def _search_vectors(self, query_embedding, k):
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        # Calculate cosine similarity: (A dot B) / (||A|| * ||B||)
        dot_products = np.dot(self.vectors, query_vec)
        norms = np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(query_vec)
        similarities = dot_products / (norms + 1e-9) # Avoid div by zero
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_k_indices:
            results.append({
                "text": self.chunks[idx]["text"],
                "metadata": self.chunks[idx]["metadata"],
                "score": float(similarities[idx])
            })
        
        return results

    def clear(self):
        """Resets the store."""
        self.chunks = []
        self.vectors = None
        if self.index_path.exists(): self.index_path.unlink()
        if self.vectors_path.exists(): self.vectors_path.unlink()
