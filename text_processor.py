"""
Text processing and chunking module.
"""
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class TextProcessor:
    """Process and chunk text documents."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the text processor.
        
        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.
        
        Args:
            documents: List of Document objects to split
            
        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks

    # Backwards-compatible API
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Backwards-compatible wrapper used by older callers (pipeline).
        Delegates to `split_documents`.
        """
        return self.split_documents(documents)
    
    def split_text(self, text: str) -> List[str]:
        """
        Split a single text string into chunks.
        
        Args:
            text: Text string to split
            
        Returns:
            List of text chunks
        """
        return self.text_splitter.split_text(text)
