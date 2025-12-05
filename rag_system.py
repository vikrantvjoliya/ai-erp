"""
RAG (Retrieval-Augmented Generation) system implementation.
"""
from typing import List, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from vector_store import VectorStore
from config import Config


class RAGSystem:
    """Main RAG system for question answering."""
    
    DEFAULT_PROMPT_TEMPLATE = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Answer:"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        prompt_template: Optional[str] = None
    ):
        """
        Initialize the RAG system.
        
        Args:
            vector_store: VectorStore instance
            model_name: OpenAI model name
            temperature: Model temperature
            prompt_template: Custom prompt template
        """
        self.vector_store = vector_store
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name or Config.LLM_MODEL,
            temperature=temperature or Config.TEMPERATURE,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Setup prompt
        template = prompt_template or self.DEFAULT_PROMPT_TEMPLATE
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval chain
        self._create_qa_chain()
    
    def _create_qa_chain(self) -> None:
        """Create the retrieval QA chain."""
        if self.vector_store.vectorstore is None:
            raise ValueError("Vector store not initialized in VectorStore instance.")
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.vectorstore.as_retriever(
                search_kwargs={"k": Config.TOP_K}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )
    
    def query(self, question: str, return_source: bool = True) -> Dict:
        """
        Ask a question and get an answer.
        
        Args:
            question: Question to ask
            return_source: Whether to return source documents
            
        Returns:
            Dictionary with 'answer' and optionally 'source_documents'
        """
        result = self.qa_chain({"query": question})
        
        response = {
            "answer": result["result"],
        }
        
        if return_source and "source_documents" in result:
            response["source_documents"] = result["source_documents"]
            response["sources"] = self._format_sources(result["source_documents"])
        
        return response
    
    def _format_sources(self, documents: List[Document]) -> List[Dict]:
        """
        Format source documents for display.
        
        Args:
            documents: List of source documents
            
        Returns:
            List of formatted source information
        """
        sources = []
        for i, doc in enumerate(documents):
            source_info = {
                "index": i + 1,
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            }
            sources.append(source_info)
        return sources
    
    def chat(self, question: str) -> str:
        """
        Simplified chat interface that returns just the answer.
        
        Args:
            question: Question to ask
            
        Returns:
            Answer string
        """
        result = self.query(question, return_source=False)
        return result["answer"]
