"""
Vector store module for document embeddings and similarity search using ChromaDB.
Supports open-source embedding models from HuggingFace.
"""
import os
from typing import List, Optional, Dict
from pathlib import Path
from loguru import logger

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
# Utility to filter out complex metadata types (lists/dicts) before upsert
from langchain_community.vectorstores.utils import filter_complex_metadata

from config import Config, get_config


class VectorStore:
    """Manage vector embeddings and similarity search with ChromaDB."""
    
    def __init__(
        self,
        config: Optional[Config] = None,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize the vector store with ChromaDB and HuggingFace embeddings.
        
        Args:
            config: Configuration object
            persist_directory: Directory to persist the vector store
            collection_name: Name of the collection
        """
        self.config = config or get_config()
        self.persist_directory = persist_directory or self.config.vector_store.persist_directory
        self.collection_name = collection_name or self.config.vector_store.collection_name
        
        # Initialize embeddings with HuggingFace
        logger.info(f"Loading embedding model: {self.config.model.embedding_model}")
        
        model_kwargs = {
            'device': self.config.model.embedding_device
        }
        
        encode_kwargs = {
            'normalize_embeddings': True  # For cosine similarity
        }
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.model.embedding_model,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        logger.info("Embedding model loaded successfully")
        
        self.vectorstore = None
    
    def create_vectorstore(self, documents: List[Document]) -> None:
        """
        Create a new vector store from documents.
        
        Args:
            documents: List of Document objects to embed
        """
        logger.info(f"Creating vector store with {len(documents)} documents...")
        
        # Create directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Filter out complex metadata values (lists/dicts) that Chroma cannot upsert
        safe_documents = filter_complex_metadata(documents)

        # Create ChromaDB vector store
        self.vectorstore = Chroma.from_documents(
            documents=safe_documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
            collection_metadata={"hnsw:space": self.config.vector_store.distance_metric}
        )
        
        logger.info(f"Vector store created and persisted to {self.persist_directory}")
    
    def load_vectorstore(self) -> None:
        """Load an existing vector store from disk."""
        if not Path(self.persist_directory).exists():
            raise FileNotFoundError(
                f"Vector store not found at {self.persist_directory}. "
                "Please create one first."
            )
        
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
        
        logger.info(f"Vector store loaded from {self.persist_directory}")
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add new documents to existing vector store.
        
        Args:
            documents: List of Document objects to add
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Load or create one first.")
    # Ensure metadata is safe before adding
        try:
            safe_documents = filter_complex_metadata(documents)
        except Exception:
            # If filtering fails for some reason, fall back to original documents
            logger.warning("filter_complex_metadata failed; adding original documents (may fail on upsert)")
            safe_documents = documents

        self.vectorstore.add_documents(safe_documents)
        logger.info(f"Added {len(safe_documents)} documents to vector store")
    
    def similarity_search(
        self, 
        query: str, 
        k: Optional[int] = None,
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Query string
            k: Number of results to return (uses config default if None)
            filter: Metadata filter for search
            
        Returns:
            List of similar Document objects
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Load or create one first.")
        
        k = k or self.config.vector_store.top_k
        
        return self.vectorstore.similarity_search(
            query, 
            k=k,
            filter=filter
        )
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: Optional[int] = None,
        filter: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Search for similar documents with relevance scores.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of tuples (Document, score)
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Load or create one first.")
        
        k = k or self.config.vector_store.top_k
        
        return self.vectorstore.similarity_search_with_score(query, k=k, filter=filter)
    
    def as_retriever(self, **kwargs):
        """Get vector store as a retriever for chains."""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Load or create one first.")
        
        search_kwargs = {"k": self.config.vector_store.top_k, **kwargs.get("search_kwargs", {})}
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
    
    def delete_collection(self) -> None:
        """Delete the vector store collection."""
        if self.vectorstore is not None:
            self.vectorstore.delete_collection()
            logger.info(f"Deleted collection: {self.collection_name}")

    def get_collection_stats(self) -> Dict:
        """Return basic stats about the collection (best-effort).

        Returns a dict with keys: collection_name, persist_directory, document_count (if available).
        This method is defensive because different Chroma wrappers expose different internals.
        """
        if self.vectorstore is None:
            return {
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "document_count": 0,
            }

        try:
            # Try common attributes first
            count = None

            # langchain_community Chroma may expose a `collection` attribute
            col = getattr(self.vectorstore, "collection", None) or getattr(self.vectorstore, "_collection", None)

            # If collection object is available, try several ways to get a count
            if col is not None:
                try:
                    # some wrappers provide a `count` method
                    count = col.count()
                except Exception:
                    try:
                        # or a get() returning ids
                        data = col.get()
                        count = len(data.get("ids", []))
                    except Exception:
                        count = None

            # Fallback: some wrappers expose client and collection_name
            if count is None and hasattr(self.vectorstore, "client"):
                try:
                    client = getattr(self.vectorstore, "client")
                    if hasattr(client, "get_collection"):
                        col2 = client.get_collection(self.collection_name)
                        try:
                            count = col2.count()
                        except Exception:
                            data = col2.get()
                            count = len(data.get("ids", []))
                except Exception:
                    count = None

            return {
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "document_count": count if count is not None else "unknown",
            }
        except Exception as e:
            logger.warning(f"Failed to get collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "document_count": "error",
                "error": str(e),
            }
